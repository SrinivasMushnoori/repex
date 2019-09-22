#!/usr/bin/env python

import radical.entk  as re

import os
import tarfile
import writeInputs

# unused
# import git


os.environ['RADICAL_VERBOSE']       = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']  = '2000'
os.environ['RADICAL_PILOT_DBURL']   = "mongodb://smush:key1209@ds147361.mlab.com:47361/db_repex_4"


replicas      = 4
replica_cores = 1
min_temp      = 100
max_temp      = 200
timesteps     = 500
basename      = 'ace-ala'
cycle         = 0
md_executable = '/home/scm177/mantel/AMBER/amber14/bin/sander'

# unused as of yet
# ASYNCHRONICITY = 0.5
# wait_ratio     = 0
# wait_count     = 0

# global variables
max_waiting_list     = 2
waiting_replicas     = list()
min_completed_cycles = 3

replica_cycles = [0] * replicas


# ------------------------------------------------------------------------------
#
def setup_replicas(replicas, min_temp, max_temp, timesteps, basename):

    writeInputs.writeInputs(max_temp=max_temp, min_temp=min_temp, 
                            replicas=replicas, timesteps=timesteps, 
                            basename=basename)

    tar = tarfile.open("input_files.tar", "w")
    for name in [basename + ".prmtop",
                 basename + ".inpcrd",
                 basename + ".mdin"]:
        tar.add(name)

    for r in range(replicas):
        tar.add  ('mdin-{replica}-{cycle}'.format(replica=r, cycle=0))
        os.remove('mdin-{replica}-{cycle}'.format(replica=r, cycle=0))

    tar.close()


    setup_p = re.Pipeline()
    setup_p.name = 'untarPipe'

  # # unused
  # repo = git.Repo('.', search_parent_directories=True)
  # aux_function_path = repo.working_tree_dir

    untar_stg = re.Stage()
    untar_stg.name = 'untarStg'

    # Untar Task

    untar_tsk = re.Task()
    untar_tsk.name              = 'untarTsk'
    untar_tsk.executable        = ['python']
    untar_tsk.upload_input_data = ['untar_input_files.py', 'input_files.tar']
    untar_tsk.arguments         = ['untar_input_files.py', 'input_files.tar']
    untar_tsk.cpu_reqs          = 1
    untar_tsk.post_exec         = []

    untar_stg.add_tasks(untar_tsk)
    setup_p.add_stages(untar_stg)

    replica_sandbox = '$Pipeline_%s_Stage_%s_Task_%s' \
                    % (setup_p.name, untar_stg.name, untar_tsk.name)

    return setup_p, replica_sandbox


# ------------------------------------------------------------------------------
# init replicas
class Replica(object):

    # --------------------------------------------------------------------------
    #
    def __init__(self):

        self.cycle = 0  # initial cycle


    # --------------------------------------------------------------------------
    #
    def replica_pipeline(self, rid, cycle, replica_cores, md_executable,
                         timesteps, replica_sandbox):

        # ----------------------------------------------------------------------
        def add_md_stg(rid,cycle):

            # md stg here
            print 'cycle: ', self.cycle

            md_tsk = re.Task()
            md_stg = re.Stage()
            md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle)

            md_tsk.link_input_data = ['%s/inpcrd > inpcrd-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle) % replica_sandbox, 
                                       '%s/prmtop' % replica_sandbox, 
                                       '%s/mdin-{replica}-{cycle} > mdin'.format(replica=rid, cycle=self.cycle) % replica_sandbox]
            md_tsk.arguments = ['-O', 
                                '-i',   'mdin', 
                                '-p',   'prmtop', 
                                '-c',   'inpcrd-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle), 
                                '-o',   'out',
                                '-x',   'mdcrd',
                                '-r',   '%s/inpcrd-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle + 1) % replica_sandbox,
                                '-inf', '%s/mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle)     % replica_sandbox]
            md_tsk.executable = [md_executable]
            md_tsk.cpu_reqs   = {'processes'          : replica_cores,
                                 'process_type'       : '',
                                 'threads_per_process': 1,
                                 'thread_type'        : None
                                 }
            md_tsk.pre_exec   = ['echo $SHARED']

            md_stg.add_tasks(md_tsk)
            md_stg.post_exec = {
                                'condition': post_md,
                                'on_true'  : start_ex,
                                'on_false' : suspend_replica
                               } 
            return md_stg
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def add_ex_stg(rid, cycle):

            # ex stg here
            ex_tsk = re.Task()
            ex_stg = re.Stage()
            ex_tsk.name = 'extsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)

            for rid in range(len(waiting_replicas)):
                ex_tsk.link_input_data += ['%s/mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=self.cycle) % replica_sandbox]

            ex_tsk.arguments  = ['t_ex_gibbs.py', len(waiting_replicas)]  # This needs to be fixed
            ex_tsk.executable = ['python']
            ex_tsk.cpu_reqs   = {'processes'          : 1,
                                 'process_type'       : '',
                                 'threads_per_process': 1,
                                 'thread_type'        : None
                                 }
            ex_stg.add_tasks(ex_tsk)
            ex_stg.post_exec = {'condition': post_ex,
                                'on_true'  : terminate_replicas,
                                'on_false' : continue_md
                               } 
            return ex_stg
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def post_md():

            global replica_cycles
            print 'replica cyles: %s [%]' % (replica_cycles, rid)

            self.cycle          += 1
            replica_cycles[rid] += 1
            print 'replica cyles: %s' % replica_cycles

            waiting_replicas.append(rid)

            if len(waiting_replicas) < max_waiting_list:
                return False
            return True


        # ----------------------------------------------------------------------
        def suspend_replica():
            p_replica.suspend()
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def start_ex():
            ex_stg = add_ex_stg(rid, cycle=self.cycle)
            p_replica.add_stages(ex_stg)
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def post_ex():

            if cycle > min_completed_cycles:
                return True    
            return False
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def terminate_replicas():

            # Resume all replicas in list without adding stages
            for rid in waiting_replicas:
                replica_pipelines[rid].resume()
            print "DONE"
        # ----------------------------------------------------------------------


        # ----------------------------------------------------------------------
        def continue_md():

            # This needs to resume replica_pipelines[rid]
            # for all rid's in wait list
            print "continuing replicas"
            global waiting_replicas

            for rid in waiting_replicas:
                try:
                    md_stg = add_md_stg(rid, cycle) 
                    replica_pipelines[rid].add_stages(md_stg)
                    if replica_pipelines[rid] is rid:
                        pass
                    else:
                        replica_pipelines[rid].resume()
                        # This is throwing an error: cannot resume itself since
                        # it is not suspended.  Since the pipeline that is
                        # triggering this choice is NOT suspended,
                        # pipeline.resume() fails. This seems to be happening on
                        # ALL pipelines somehow. 

                except:
                    print "replica is not suspended, cannot resume"

            waiting_replicas = []
        # ----------------------------------------------------------------------


        p_replica = re.Pipeline()
        p_replica.name = 'p_{rid}'.format(rid=rid)

        md_stg = add_md_stg(rid, cycle)
        p_replica.add_stages(md_stg)

        return p_replica  


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    system, replica_sandbox = setup_replicas(replicas, min_temp, max_temp,
                                             timesteps, basename)
    print 'replica sandbox:', replica_sandbox

    replica = list()
    replica_pipelines = list()

    for rid in range(replicas):

        print rid
        replica    = Replica()
        r_pipeline = replica.replica_pipeline(rid, cycle, replica_cores, 
                                              md_executable, timesteps,
                                              replica_sandbox)
        replica_pipelines.append(r_pipeline)


    appman = re.AppManager(autoterminate=False, port=32769) 
    appman.resource_desc = {"resource" : 'local.localhost',
                            "walltime" : 30,
                            "cpus"     : 4}                                

    appman.workflow = set([system]) 
    appman.run() 

    appman.workflow = set(replica_pipelines)
    appman.run() 

    appman.resource_terminate()

# ------------------------------------------------------------------------------

