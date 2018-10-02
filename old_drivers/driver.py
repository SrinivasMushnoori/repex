#!/usr/bin/env python

import radical.utils as ru
import radical.analytics as ra
import radical.entk as re
from radical.entk import Pipeline, Stage, Task, AppManager
import os
import tarfile
import writeInputs
import time
import git
#import replica




os.environ['RADICAL_SAGA_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['RADICAL_PROFILE']              = 'True'
os.environ['RADICAL_ENTK_PROFILE']         = 'True'
os.environ['RADICAL_ENTK_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']         = '2000'
os.environ['RADICAL_VERBOSE']              = 'INFO'
os.environ['RADICAL_PILOT_PROFILE']        = 'True'
os.environ['RADICAL_REPEX_SYNCEX_PROFILE'] = 'True'
os.environ['RADICAL_REPEX_RUN_PROFILE']    = 'True'

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
waiting_replicas = []



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
    print replica_sandbox
    return setup_p

####_----------------------------------------------------------init replicas

class Replica(object):

    def __init__(self):

        self.dummy = 'dummy'

    def replica_pipeline(self, rid, cycle, replica_cores, md_executable, timesteps, replica_sandbox):
   
        p_replica = Pipeline()
        md_tsk = Task()
        md_stg = Stage()
        md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
        md_tsk.link_input_data += ['%s/inpcrd'%replica_sandbox, '%s/prmtop'%replica_sandbox, '%s/mdin-{replica}-{cycle}'.format(replica=rid, cycle=0)%replica_sandbox]
        md_tsk.arguments = ['-O', 
                            '-i', 'mdin-{replica}-{cycle}'.format(replica=rid, cycle=cycle-1), 
                            '-p', 'prmtop', 
                            '-c', 'inpcrd', 
                            '-o', 'out-{replica}-{cycle}'.format(replica=rid, cycle=cycle),
                            '-r', '%s/restrt-{replica}-{cycle}'.format(replica=rid, cycle=cycle)%replica_sandbox,
                            '-x', 'mdcrd-{replica}-{cycle}'.format(replica=rid, cycle=cycle),
                            '-inf', '%s/mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle)%replica_sandbox]
        md_tsk.executable = ['/home/scm177/mantel/AMBER/amber14/bin/sander']
        md_tsk.cpu_reqs = {
                            'processes': replica_cores,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
        }
        md_tsk.pre_exec   = ['export dummy_variable=19']
         
        md_stg.add_tasks(md_tsk)

	    #def synchronicity_function():
	    #    replica_state = 'W'
	    #    global wait_ratio
	        #wait_ratio = 
	        #while wait_ratio < 0.5:
	            
	    
	    #def exchange_function():
	        #exchange_function
	    
	    #def md_function(): 
	    
	    
	        #md_function

	    #md_stg.post_exec = {
	    #                        'condition': synchronicity_function,
	    #                        'on_true': exchange_function,
	    #                        'on_false': md_function
	    #                    }  
        p_replica.add_stages(md_stg)
	    
        return p_replica  

	    


            

system = setup_replicas(replicas, min_temp, max_temp, timesteps, basename)
#replica_sandbox = untar_tsk.path
replica=[]
replica_pipelines = []
for rid in range(replicas):
	#print rid
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
