#!/usr/bin/env python

from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager
#from exchangeMethods import RandEx 
import os
# ------------------------------------------------------------------------------
# Set default verbosity

if os.environ.get('RADICAL_ENTK_VERBOSE') == None:
    os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

#  Hard code the old defines/state names

if os.environ.get('RP_ENABLE_OLD_DEFINES') == None:
    os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'

if os.environ.get('RADICAL_PILOT_PROFILE') == None:
    os.environ['RADICAL_PILOT_PROFILE'] = 'True'

if os.environ.get('RADICAL_PILOT_DBURL') == None:
    os.environ['RADICAL_PILOT_DBURL'] = "mongodb://138.201.86.166:27017/ee_exp_4c"

#---------------------------------------#
## User Settings

Replicas = 8
Replica_Cores = 32
Cycles = 4

#---------------------------------------#




Pilot_Cores = Replicas * Replica_Cores    

def init_pipeline():

    # Create Pipeline Obj

    p = Pipeline()

    #Bookkeeping
    stage_uids = list()
    task_uids = list() ## = dict()
        

    #Create initial MD stage

    md_stg = Stage()

    #Create MD task
    for n0 in range (Replicas):    
        md_tsk = Task()
        md_tsk.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine
        md_tsk.upload_input_data = ['inpcrd', 'prmtop', 'mdin_{0}'.format(n0)]
        md_tsk.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/']
        md_tsk.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out']
        md_tsk.cores = Replica_Cores
        md_tsk.mpi = True
        md_stage.add_tasks(md_tsk)
        task_uids.append(md_tsk.uid)
    p.add_stages(md_stg)
    stage_uids.append(md_stg.uid)

    #Create Exchange Stage
    
    ex_stg = Stage()

    #Create Exchange Task

    ex_tsk = Task()
    ex_tsk.executable = ['python']
    ex_tsk.upload_input_data = ['exchangeMethods/RandEx.py']
    for n1 in range Replicas:
        ex_tsk.copy_input_data = ['$Pipeline_%s_Stage_%s_Task_%s/mdinfo > mdinfo_{0}'.format(n1)]
    
    ex_tsk.arguments = ['RandEx.py','{0}'.format(Replicas)]
    ex_tsk.cores = 1
    ex_tsk.mpi = False
    ex_tsk.download_output_data = ['exchangePairs.txt']
    ex_stg.add_tasks(ex_tsk)
    task_uids.append(ex_tsk.uid)
    p.add_stages(ex_stg)
    stage_uids.append(ex_stg.uid)

    return p


def general_pipeline():

    p = Pipeline()

    #Bookkeeping
    stage_uids = list()
    task_uids = list() ## = dict()


    #Create initial MD stage

    md_stg = Stage()

    #Create MD task
    for n0 in range (Replicas):
        md_tsk = Task()
        md_tsk.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine

        
        md_tsk.copy_input_data = ['$Pipeline_%s_Stage_%s_Task_%s/restrt > inpcrd'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),
                                  '$Pipeline_%s_Stage_%s_Task_%s/prmtop'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),
                                  '$Pipeline_%s_Stage_%s_Task_%s/mdin_{0}'.format(n0)%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0])]
                                   ##Above: Copy from previous PIPELINE, make sure bookkeeping is correct
                                   ##### Never used .format(n) AND a %s at the same time. Test, try.
                              
        md_tsk.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/']
        md_tsk.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out']
        md_tsk.cores = Replica_Cores
        md_tsk.mpi = True
        md_stg.add_tasks(md_tsk)
        task_uids.append(md_tsk.uid)
    p.add_stages(md_stg)
    stage_uids.append(md_stg.uid)

    #Create exchange stage 

    ex_stg= Stage()
    
    #Create Exchange Task

    ex_tsk = Task()
    ex_tsk.executable = ['python']
    ex_tsk.upload_input_data = ['exchangeMethods/RandEx.py']
    ex_tsk.arguments = ['RandEx.py','{0}'.format(Replicas)]
    ex_tsk.cores = 1
    ex_tsk.mpi = False
    ex_tsk.download_output_data = ['exchangePairs.txt']
    ex_stg.add_tasks(ex_tsk)
    task_uids.append(ex_tsk.uid)
    p.add_stages(ex_stg)
    stage_uids.append(ex_stg.uid)

    return p
                                                

if __name__ == '__main__':

    res_dict = {
                'resource': 'ncsa.bw_aprun',
                'walltime': 30,
                'cores': Pilot_Cores,
                'access_schema': 'gsissh',
                'queue': 'debug',
                'project': 'bamm',
                }

    rman = ResourceManager(res_dict)

     # Create Application Manager
    appman = AppManager(autoterminate=False)

     # Assign resource manager to the Application Manager
    appman.resource_manager = rman

    p = init_pipeline()
     # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set([p]))

     # Run the Application Manager
    appman.run()
    
    p = general_pipeline()
    #print p.uid

    # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set([p]))

    # Run the Application Manager
    appman.run()



    appman.resource_terminate()
