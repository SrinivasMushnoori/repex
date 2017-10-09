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
    # Bookkeeping
    stage_uids = list()
    task_uids = dict()
    Stages = 20
    Replicas = 2
    for N_Stg in range(Stages):
        stg =  Stage() ## initialization
        task_uids['Stage_%s'%N_Stg] = list()
        if N_Stg == 0:
            for n0 in range(Replicas):
                t = Task()
                t.executable = ['/usr/local/packages/gromacs/5.1.4/INTEL-140-MVAPICH2-2.0/bin/gmx_mpi_d']  #MD Engine  
                t.upload_input_data = ['in.gro', 'in.top', 'FNF.itp', 'martini_v2.2.itp', 'in.mdp'] 
                t.pre_exec = ['module load gromacs', '/usr/local/packages/gromacs/5.1.4/INTEL-140-MVAPICH2-2.0/bin/gmx_mpi_d grompp -f in.mdp -c in.gro -o in.tpr -p in.top'] 
                t.arguments = ['mdrun', '-s', 'in.tpr', '-deffnm', 'out']
                t.cores = 20
                stg.add_tasks(t)
                task_uids['Stage_%s'%N_Stg].append(t.uid)
            p.add_stages(stg)
            stage_uids.append(stg.uid) 



        else:
        
            for n0 in range(Replicas):
                t = Task()
                t.executable = ['/usr/local/packages/gromacs/5.1.4/INTEL-140-MVAPICH2-2.0/bin/gmx_mpi_d']  #MD Engine  
                t.copy_input_data = ['$Pipeline_%s_Stage_%s_Task_%s/out.gro > in.gro'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]), '$Pipeline_%s_Stage_%s_Task_%s/in.top'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),  '$Pipeline_%s_Stage_%s_Task_%s/FNF.itp'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),  '$Pipeline_%s_Stage_%s_Task_%s/martini_v2.2.itp'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),  '$Pipeline_%s_Stage_%s_Task_%s/in.mdp'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0])]
                t.pre_exec = ['module load gromacs', '/usr/local/packages/gromacs/5.1.4/INTEL-140-MVAPICH2-2.0/bin/gmx_mpi_d grompp -f in.mdp -c in.gro -o in.tpr -p in.top'] 
                t.arguments = ['mdrun', '-s', 'in.tpr', '-deffnm', 'out']
                t.cores = 20
                stg.add_tasks(t)
                task_uids['Stage_%s'%N_Stg].append(t.uid)
            p.add_stages(stg)
            stage_uids.append(stg.uid)          

 
    # Create a dictionary describe four mandatory keys:
    # resource, walltime, cores and project
    # resource is 'local.localhost' to execute locally
    res_dict = {

            #'resource': 'local.localhost',
            'resource': 'xsede.supermic',
            'walltime': 60,
            'cores': 40,
            'access_schema': 'gsissh',
            'queue': 'workq',
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
