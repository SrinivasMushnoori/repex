#!/usr/bin/env python

from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager 
import os


## OUTDATED, TO BE REMOVED

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
    

if __name__ == '__main__':

    # Create a Pipeline object
    p = Pipeline()
    # Bookkeeping
    stage_uids = list()
    task_uids = dict()

    Stages = 3
    Replicas = 2
    Replica_Cores = 32

    Pilot_Cores = Replicas * Replica_Cores

    
    for N_Stg in range(Stages):
        stg =  Stage() ## initialization
        task_uids['Stage_%s'%N_Stg] = list()

        #####Initial MD stage  

        if N_Stg == 0:
            for n0 in range(Replicas):
                t = Task()
                t.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine  
                t.upload_input_data = ['inpcrd', 'prmtop', 'mdin_{0}'.format(n0)] 
                t.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/'] 
                t.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out']
                t.cores = Replica_Cores
                stg.add_tasks(t)
                task_uids['Stage_%s'%N_Stg].append(t.uid)
            p.add_stages(stg)
            stage_uids.append(stg.uid) 



        #####Exchange Stages    
        elif N_Stg != 0 and N_Stg%2 = 1:
            t = Task()
            t.executable = ['python']
            t.upload_input_data = ['exchangeMethods/RandEx.py']
            #t.link_input_data = ['']
            t.arguments = ['RandEx.py', Replicas]
            t.cores = 1
            t.mpi = False
            t.download_output_data = ['exchangePairs.txt'] 
            stg.add_tasks(t)
            task_uids['Stage_%s'%N_Stg].append(t.uid)
            p.add_stages(stg)
            stage_uids.append(stg.uid)
            


        ######Subsequent MD stages    
        else:
            ### Open file,
            ExchangePairs = []
            with open('exchangePairs.txt', "rb") as file
            ### read file into list,
            ### use list ot populate data staging placeholders
                for i in file.readlines():
                    tmp = i.split(" ")
                    try:
                        ExchangePairs.append((int(tmp[0]), int(tmp[1])))
                    except:pass

            ###AND THEN, define the task
            for n0 in range(Replicas):
                t = Task()
                t.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine  
                t.copy_input_data = ['$Pipeline_%s_Stage_%s_Task_%s/restrt > inpcrd'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),
                                     '$Pipeline_%s_Stage_%s_Task_%s/prmtop'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0]),
                                     '$Pipeline_%s_Stage_%s_Task_%s/mdin'%(p.uid, stage_uids[N_Stg-1], task_uids['Stage_%s'%(N_Stg-1)][n0])]
                
                t.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/'] 
                t.arguments = ['-O', '-i', 'mdin', '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out']
                t.cores = Replica_Cores
                stg.add_tasks(t)
                task_uids['Stage_%s'%N_Stg].append(t.uid)
            p.add_stages(stg)
            stage_uids.append(stg.uid)          

 
    # Create a dictionary describe four mandatory keys:
    # resource, walltime, cores and project
    # resource is 'local.localhost' to execute locally
    res_dict = {

            'resource': 'ncsa.bw_aprun',
            'walltime': 30,
            'cores': Pilot_Cores,
            'access_schema': 'gsissh',
            'queue': 'debug',
            'project': 'bamm',
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
