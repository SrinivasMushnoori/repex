#!/usr/bin/env python

import radical.utils as ru
#import radical.analytics as ra
import radical.entk as re
from radical.entk import Pipeline, Stage, Task, AppManager
import os
import tarfile
import writeInputs
import time
import git
#import replica




#os.environ['RADICAL_SAGA_VERBOSE']         = 'INFO'
os.environ['RADICAL_ENTK_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']         = '2000'
#os.environ['RADICAL_VERBOSE']              = 'INFO'


"""
Every instance of the Replica object instantiates a pipeline for itself. Once the pipeline is created, an MD task is carried out.
The End of this MD task/stage, every replica transitions into a wait state, all the while looking for other replicas that are also
waiting. The number of replicas waiting is written to a list that has a maximum size limit. As soon as this limit is reached the
replicas on the list begin to exchange and the list is emptied. The list can now be populated by new replicas finishing their MD
stages. Termination criterion: ALL replicas have performed at least N exchange attempts (i.e. "cycles" specified by the user).

There are 3 data structures maintained here:
1) List of replicas that have completed MD and are awaiting exchange.
2) Array containing the number of times each replica has exchanged.
3) Dictionary containing locations of all replica sandboxes.      

"""



replicas = 4
replica_cores = 1
min_temp = 100
max_temp = 200
timesteps = 1000
basename = 'ace-ala'
cycle = 1
md_executable = '/home/scm177/mantel/AMBER/amber14/bin/sander'
SYNCHRONICITY = 0.5
wait_ratio = 0
max_waiting_list = 2
waiting_replicas = []
min_completed_cycles = 3

replica_cycles = [0]*replicas
wait_count = 0


def setup_replicas(replicas, min_temp, max_temp, timesteps, basename):

    writeInputs.writeInputs(max_temp=max_temp, min_temp=min_temp, replicas=replicas, timesteps=timesteps, basename=basename)
    tar = tarfile.open("input_files.tar", "w")
    for name in [basename + ".prmtop", basename + ".inpcrd", basename + ".mdin"]:
        tar.add(name)
    for r in range(replicas):
        tar.add('mdin-{replica}-{cycle}'.format(replica=r, cycle=0))
    tar.close()
    for r in range(replicas):
        os.remove('mdin-{replica}-{cycle}'.format(replica=r, cycle=0))



    setup_p = Pipeline()
    setup_p.name = 'untarPipe'

    repo = git.Repo('.', search_parent_directories=True)
    aux_function_path = repo.working_tree_dir


    untar_stg = Stage()
    untar_stg.name = 'untarStg'

    #Untar Task
        
    untar_tsk = Task()
    untar_tsk.name = 'untarTsk'
    untar_tsk.executable = ['python']
    untar_tsk.upload_input_data = ['untar_input_files.py', 'input_files.tar']
    untar_tsk.arguments = ['untar_input_files.py', 'input_files.tar']
    untar_tsk.cpu_reqs = 1
    untar_tsk.post_exec = []
    untar_stg.add_tasks(untar_tsk)
    setup_p.add_stages(untar_stg)
    global replica_sandbox
    replica_sandbox='$Pipeline_%s_Stage_%s_Task_%s'%(setup_p.name, untar_stg.name, untar_tsk.name)
    return setup_p

####_----------------------------------------------------------init replicas

class Replica(object):

    def __init__(self):

        self.state_history = []

    def replica_pipeline(self, rid, cycle, replica_cores, md_executable, timesteps, replica_sandbox):

        def add_ex_stg(rid, cycle):
            #ex stg here
            ex_tsk = Task()
            ex_stg = Stage()
            ex_tsk.name = 'extsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
            for rid in range(len(waiting_replicas)):
                ex_tsk.link_input_data += ['%s/mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle)%replica_sandbox]
               
            ex_tsk.arguments = ['t_ex_gibbs_async.py', len(waiting_replicas)] #This needs to be fixed
            ex_tsk.executable = ['python']
            ex_tsk.cpu_reqs = {
                           'processes': 1,
                           'process_type': '',
                           'threads_per_process': 1,
                           'thread_type': None
                            }
            ex_tsk.pre_exec   = ['export dummy_variable=19']
             
            ex_stg.add_tasks(ex_tsk)
            return ex_stg
            

        def add_md_stg(rid,cycle):
            #md stg h
            md_tsk = Task()
            md_stg = Stage()
            md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
            md_tsk.link_input_data += ['%s/inpcrd' %replica_sandbox, 
                                   '%s/prmtop' %replica_sandbox, 
                                   '%s/mdin-{replica}-{cycle}'.format(replica=rid, cycle=0) %replica_sandbox]
            md_tsk.arguments = ['-O', 
                            '-i',   'mdin-{replica}-{cycle}'.format(replica=rid, cycle=0), 
                            '-p',   'prmtop', 
                            '-c',   'inpcrd', 
                            '-o',   'out',
                            '-r',   '%s/restrt-{replica}-{cycle}'.format(replica=rid, cycle=cycle) %replica_sandbox,
                            '-x',   'mdcrd',
                            '-inf', '%s/mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle) %replica_sandbox]
            md_tsk.executable = ['/home/scm177/mantel/AMBER/amber14/bin/sander']
            md_tsk.cpu_reqs = {
                            'processes': replica_cores,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
                               }
            md_tsk.pre_exec   = ['export dummy_variable=19', 'echo $SHARED']
         
            md_stg.add_tasks(md_tsk)
            md_stg.post_exec = {
                            'condition': synchronicity_function,
                            'on_true': propagate_cycle,
                            'on_false': end_func
                          } 

            return md_stg



        def synchronicity_function():
            """
            synchronicity function should evaluate the following:
            1) Has the replica in THIS pipeline completed enough cycles?
            2) If yes, Is the replica threshold met? I.e. is the exchange list large enough?
            3) If no, add to waiting list  
            4) Is the replica is THIS pipeline the LOWEST rid in the list?
            If 1 and 2 return True, the Synchronicity Function returns a True. 
            If the first is true and second is false, the synchronicity function returns False

            EXTREMELY IMPORTANT: Remember to clear replica related variables, replica lists etc., after the adaptivity 
            operations have completed! i.e. after the propagate_cycle() function. Not necessary to clear after end_func().
      
            """
            global replica_cycles
            global ex_pipeline
            global max_waiting_list
            global min_completed_cycles
            print replica_cycles, rid
            replica_cycles[rid] += 1
            print replica_cycles

            if min(replica_cycles) < min_completed_cycles: 
                waiting_replicas.append(rid)
                
                if len(waiting_replicas) < max_waiting_list:
                    p_replica.suspend()
                #p_replica.resume()  # There seems to be an issue here. We potentially need the "resume" function to be triggered
                                     # by a different pipeline.


                ex_pipeline = min(waiting_replicas)
                print "Synchronicity Function returns True"
                return True


            return False

      
        def propagate_cycle():
            """
            This function adds two stages to the pipeline: an exchange stage and an MD stage. 
            If the pipeline is not the "ex_pipeline", it stalls and adds only the MD stage until the EX pipeline has completed
            the EX task.
            """
            
            if rid is ex_pipeline: ### FIX THIS TO REFER TO THE CORRECT NAME OF THE EX PIPELINE

                # This adds an Ex task. 
                ex_stg = add_ex_stg(rid, cycle) 
                p_replica.add_stages(ex_stg)

                # And the next MD stage
                md_stg = add_md_stg(rid, cycle)
                p_replica.add_stages(md_stg)


            else:
                while ex_stg.state is not "COMPLETED":  ### FIX THIS TO REFER TO THE CORRECT NAME OF THE EX STAGE
                    #time.sleep(1)
                    pass
                md_stg = add_md_stg(rid, cycle)
                p_replica.add_stages(md_stg)

                waiting_replicas = []  # EMPTY REPLICA WAITING LIST 


        def end_func():
            print "DONE"


        
        p_replica = Pipeline()
        p_replica.name = 'p_{rid}'.format(rid=rid)
        md_stg = add_md_stg(rid, cycle)
        p_replica.add_stages(md_stg)

        return p_replica  

        


            

system = setup_replicas(replicas, min_temp, max_temp, timesteps, basename)
replica=[]
replica_pipelines = []
for rid in range(replicas):
    print rid
    replica = Replica()

    r_pipeline = replica.replica_pipeline(rid, cycle, replica_cores, md_executable, timesteps, replica_sandbox)
    replica_pipelines.append(r_pipeline)

os.environ['RADICAL_PILOT_DBURL'] = "mongodb://smush:key1209@ds147361.mlab.com:47361/db_repex_4"

res_dict ={
            "resource"      : 'local.localhost',
            "walltime"      : 30,
            "cpus"          : 4,


          }

appman               = AppManager(autoterminate=False, port=32769) 
appman.resource_desc = res_dict 
appman.workflow      = set([system]) 
appman.run() 
appman.workflow      = set(replica_pipelines)
appman.run() 
appman.resource_terminate()
