#!/usr/bin/env python

from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager
import os


## Uses the Pipeline of Ensembles to implement Synchronous Replica Exchange.
## There are 4 GROMACS replicas that run and exchange configurations as follows: 1 and 4, 2 and 3.
## Exchange scheme is currently hard-coded. To implement replica exchange, an Exchange method must be instantiated as a stage between two MD stages.
## This Exchange Method may be pulled from the original RepEx implementation as-is or with little modification....if we're lucky. 
## But of course, Murphy's Law exists.  


# ------------------------------------------------------------------------------
# Set default verbosity

if os.environ.get('RADICAL_ENTK_VERBOSE') == None:
    os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

#  Hard code the old defines/state names

if os.environ.get('RP_ENABLE_OLD_DEFINES') == None:
    os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'

if os.environ.get('RADICAL_PILOT_PROFILE') == None:
    os.environ['RADICAL_PILOT_PROFILE'] = 'True'

if os.environ.get('export RADICAL_PILOT_DBURL') == None:
    os.environ['export RADICAL_PILOT_DBURL'] = "mongodb://138.201.86.166:27017/ee_exp_4c"
    

if __name__ == '__main__':

    # Create a Pipeline object
    p = Pipeline()



    ##########----------###########

    ###Stage1=Simulation. Stage 2=Hardcoded copy followed by simulation.

    # Create stage.

  
    s1 = Stage()
    s1_task_uids = []
    s2 = Stage()
    s2_task_uids = []
    for cnt in range(4):

        # Create a Task object
        t1 = Task() ##GROMPP
        t1.executable = ['/opt/gromacs/bin/gmx_mpi']  #MD Engine  
        t1.upload_input_data = ['in.gro', 'in.top', 'FF.itp', 'matrini_v2.2.itp', 'in.mdp'] # Copy data from the local directory to the current task's location
        t1.pre_exec = ['export LD_LIBRARY_PATH=/share/apps/gpu/cuda-8.0/lib64:$LD_LIBRARY_PATH', 'grompp -f in.mdp -c in.gro -o in.tpr -p in.top'] 
        t1.arguments = ['mdrun', '-s', 'in.tpr', '-deffnm', 'out']
        t1.cores = 1



        # Add the Task to the Stage
        s1.add_tasks(t1)
        s1_task_uids.append(t1.uid)

    # Add Stage to the Pipeline
    p.add_stages(s1)

        # Create another Stage object to hold checksum tasks
    s2 = Stage() #HARD-CODED EXCHANGE FOLLOWED BY MD


    # Create a Task object
    t2 = Task()
    t2.executable = ['/home/ubuntu/gromacs/bin/gmx']  #MD Engine  
    
    # exchange happens here

    for n0 in range(1, 4):
        t2.copy_input_data += ['$Pipline_%s_Stage_%s_Task_%s/out.gro'%(p.uid, s1.uid, s1_task_uids[n0]), '$Pipline_%s_Stage_%s_Task_%s/in.top'%(p.uid, s1.uid, s1_task_uids[n0]),  '$Pipline_%s_Stage_%s_Task_%s/FF.itp'%(p.uid, s1.uid, s1_task_uids[n0]),  '$Pipline_%s_Stage_%s_Task_%s/martini_v2.2.itp'%(p.uid, s1.uid, s1_task_uids[n0]),  '$Pipline_%s_Stage_%s_Task_%s/in.mdp'%(p.uid, s1.uid, s1_task_uids[n0])]
        t2.pre_exec = ['grompp -f in.mdp -c out.gro -o in.tpr -p in.top']
        t2.arguments = ['mdrun', '-s', 'in.tpr', '-deffnm', 'out_exc'] 
        t2.cores = 1
 
        s2.add_tasks(t2)
        s2_task_uids.append(t2.uid)

    # Add Stage to the Pipeline
    p.add_stages(s2)
 
    # Create a dictionary describe four mandatory keys:
    # resource, walltime, cores and project
    # resource is 'local.localhost' to execute locally
    res_dict = {

            #'resource': 'local.localhost',
            'resource': 'xsede.comet',
            'walltime': 10,
            'cores': 2,
            'access_schema': 'gsissh',
            'queue': 'debug',
            'project': 'TG-MCB090174',
    }

    # Create Resource Manager object with the above resource description
    rman = ResourceManager(res_dict)

    # Create Application Manager
    appman = AppManager()

    # Assign resource manager to the Application Manager
    appman.resource_manager = rman

    # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set([p]))

    # Run the Application Manager
    appman.run()
