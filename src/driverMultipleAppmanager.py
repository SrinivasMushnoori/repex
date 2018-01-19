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

    s1 = Stage()

    #Create MD task
    for n0 in range (Replicas):    
        t1 = Task()
        t1.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine
        t1.upload_input_data = ['inpcrd', 'prmtop', 'mdin_{0}'.format(n0)]
        t1.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/']
        t1.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out']
        t1.cores = Replica_Cores
        t1.mpi = True
        s1.add_tasks(t1)
        task_uids.append(t1.uid)
    p.add_stages(s1)
    stage_uids.append(s1.uid)

    #Create Exchange Stage
    
    s2 = Stage()

    #Create Exchange Task

    t2 = Task()
    t2.executable = ['python']
    t2.upload_input_data = ['exchangeMethods/RandEx.py']
    t2.arguments = ['RandEx.py','{0}'.format(Replicas)]
    t2.cores = 1
    t2.mpi = False
    t2.download_output_data = ['exchangePairs.txt']
    s2.add_tasks(t2)
    task_uids.append(t2.uid)
    p.add_stages(s2)
    stage_uids.append(s2.uid)

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
    
    #p = init_pipeline()
    #print p.uid

    # Assign the workflow as a set of Pipelines to the Application Manager
    #appman.assign_workflow(set([p]))

    # Run the Application Manager
    #appman.run()



    appman.resource_terminate()
