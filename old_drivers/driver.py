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
    global init_sandbox
    init_sandbox='$Pipeline_%s_Stage_%s_Task_%s'%(setup_p.name, untar_stg.name, untar_tsk.name)
    print init_sandbox
    return setup_p

####_----------------------------------------------------------init replicas

class Replica(object):

    def __init__(self):

        self.state_history = []

    def replica_pipeline(self, rid, cycle, replica_cores, md_executable, timesteps, init_sandbox):
   
        p_replica = Pipeline()
        md_tsk = Task()
        md_stg = Stage()
        md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
        md_tsk.link_input_data += ['%s/inpcrd'%init_sandbox, '%s/prmtop'%init_sandbox, '%s/mdin-{replica}-{cycle}'.format(replica=rid, cycle=0)%init_sandbox]
        md_tsk.arguments = ['-O', 
                            '-i', 'mdin-{replica}'.format(replica=rid), 
                            '-p', 'prmtop', 
                            '-c', 'inpcrd', 
                            '-o', 'out',
                            '-r', 'restrt',
                            '-x', 'mdcrd',
                            '-inf', 'mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle)]
        md_tsk.executable = ['/home/scm177/mantel/AMBER/amber14/bin/sander']
        md_tsk.cpu_reqs = {
                            'processes': replica_cores,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
        }
        md_tsk.pre_exec   = ['export dummy_variable=19']
         
        md_stg.add_tasks(md_tsk)

	    def synchronicity_function():
            """
            Function sets replica state to "waiting", moves on to searching for other replicas in the
            same state. As long as the number of replicas is less than the threshold set by wait_ratio, it 
            keeps stalling with a sleep(1). The number of replicas in Waiting state is maintained client 
            side. Once the number is reached, the function returns True and moves on to the Ex step by triggering
            the func_on_true function that generates an exchange stage. Any other replicas that transition to 
            "waiting" state after this transition directly to MD. This is done by returning False if number of 
            replicas waiting is equal to or greater than the threshold and triggering func_on_false, which sets 
            up an MD stage.   

            MAJOR issue: This is triggering the EX task in all pipelines that enter the EX phase. It should be triggered
            in only the FIRST pipeline of the waiting list. The other pipelines need to stall until the EX task completes
            in the first pipeline of the lot. 

            """


	        replica_state = 'WAITING'
	        self.state_history.append(replica_state) 
	        global wait_ratio
	        
	        while wait_ratio < 0.5:

	            
	    
	    def exchange_function():
	        ex_tsk = Task()
            ex_stg = Stage()
            ex_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
            ex_tsk.link_input_data += ['%s/inpcrd'%init_sandbox, '%s/prmtop'%init_sandbox, '%s/mdin-{replica}-{cycle}'.format(replica=rid, cycle=0)%init_sandbox]
            ex_tsk.arguments = [ 'mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle)] #This needs to be fixed
            ex_tsk.executable = ['t_ex_gibbs.py']
            ex_tsk.cpu_reqs = {
                            'processes': 1,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
                              }
            ex_tsk.pre_exec   = ['export dummy_variable=19']
         
            ex_stg.add_tasks(ex_tsk)
	    
	    def md_function(): 
	    
            md_tsk = Task()
            md_stg = Stage()
            md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=rid, cycle=cycle)
            md_tsk.link_input_data += ['%s/inpcrd'%init_sandbox, '%s/prmtop'%init_sandbox, '%s/mdin-{replica}-{cycle}'.format(replica=rid, cycle=0)%init_sandbox]
            md_tsk.arguments = ['-O', 
                            '-i', 'mdin-{replica}'.format(replica=rid), 
                            '-p', 'prmtop', 
                            '-c', 'inpcrd', 
                            '-o', 'out',
                            '-r', 'restrt',
                            '-x', 'mdcrd',
                            '-inf', 'mdinfo-{replica}-{cycle}'.format(replica=rid, cycle=cycle)]
            md_tsk.executable = ['/home/scm177/mantel/AMBER/amber14/bin/sander']
            md_tsk.cpu_reqs = {
                            'processes': replica_cores,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
            }
            md_tsk.pre_exec   = ['export dummy_variable=19']
         
            md_stg.add_tasks(md_tsk)

	        md_stg.post_exec = {
	                            'condition': synchronicity_function,
	                            'on_true': exchange_function,
	                            'on_false': md_function
	                        }  
        

            p_replica.add_stages(md_stg)
	    
        return p_replica  

	    


            

system = setup_replicas(replicas, min_temp, max_temp, timesteps, basename)
replica=[]
replica_pipelines = []
for rid in range(replicas):
	#print rid
    replica = Replica()

    r_pipeline = replica.replica_pipeline(rid, cycle, replica_cores, md_executable, timesteps, init_sandbox)
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
