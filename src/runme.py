#!/usr/bin/env python

from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager
#from exchangeMethods import RandEx 
import os
# ------------------------------------------------------------------------------
# Set default verbosity

os.environ['RADICAL_SAGA_VERBOSE'] = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'
os.environ['RADICAL_ENMD_PROFILING'] = '1'
os.environ['RADICAL_PILOT_PROFILE'] = 'True'
os.environ['RADICAL_ENMD_PROFILE'] = 'True'
os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT'] = '2000'
os.environ['RADICAL_VERBOSE'] = 'INFO'
os.environ['RADICAL_PILOT_PROFILE'] = 'True'
os.environ['RADICAL_PILOT_DBURL'] = "mongodb://smush:key1209@ds117848.mlab.com:17868/db_repex_1"

#---------------------------------------#
## User Settings

Replicas = 8
Replica_Cores = 20
Cycles = 10
#Resource = 'xsede.comet_ssh'
#---------------------------------------#


Book = []

Pilot_Cores = (Replicas + 1) * Replica_Cores   

def init_cycle():

    # Create Pipeline Obj

    p = Pipeline()

    #Bookkeeping
    stage_uids = list()
    task_uids = list() ## = dict()
    d = dict()    

    #Create initial MD stage

    md_stg = Stage()

    #Create MD task
    for n0 in range (Replicas):    
        md_tsk = Task()
        #md_tsk.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine, BW
        md_tsk.executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI'] #MD Engine, SuperMIC
        #md_tsk.executable = ['/opt/amber/bin/pmemd.MPI']
        md_tsk.upload_input_data = ['inpcrd', 'prmtop', 'mdin_{0}'.format(n0)]
        #md_tsk.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/']
        md_tsk.pre_exec = ['module load amber']    
        md_tsk.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out', '-inf', 'mdinfo_{0}'.format(n0)]
        md_tsk.cores = Replica_Cores
        md_tsk.mpi = True
        d[n0] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)

        md_stg.add_tasks(md_tsk)
        task_uids.append(md_tsk.uid)
    p.add_stages(md_stg)
    stage_uids.append(md_stg.uid)
    #print d 
    #Create Exchange Stage
    
    ex_stg = Stage()

    #Create Exchange Task

    ex_tsk = Task()
    ex_tsk.executable = ['python']
    ex_tsk.upload_input_data = ['exchangeMethods/TempEx.py']
    for n1 in range (Replicas):
        ex_tsk.link_input_data += ['%s/mdinfo_%s'%(d[n1],n1)]
    
    ex_tsk.arguments = ['TempEx.py','{0}'.format(Replicas)]
    ex_tsk.cores = 1
    ex_tsk.mpi = False
    ex_tsk.download_output_data = ['exchangePairs.dat']
    ex_stg.add_tasks(ex_tsk)
    task_uids.append(ex_tsk.uid)
    p.add_stages(ex_stg)
    stage_uids.append(ex_stg.uid)
    Book.append(d)
    #print Book
    return p


def cycle(k):


    #read exchangePairs.dat
    #
    with open("exchangePairs.dat","r") as f:
        ExchangeArray = []
        for line in f:
            ExchangeArray.append(int(line.split()[1]))
            #ExchangeArray.append(line)
        #print ExchangeArray    

    
    p = Pipeline()

    #Bookkeeping
    stage_uids = list()
    task_uids = list() ## = dict()
    d = dict() 

    #Create initial MD stage

    md_stg = Stage()

    #Create MD task
    for n0 in range (Replicas):
        md_tsk = Task()
        #md_tsk.executable = ['/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI']  #MD Engine, Blue Waters
        md_tsk.executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI'] #MD Engine, SuperMIC 
        #md_tsk.executable = ['/opt/amber/bin/pmemd.MPI']
        md_tsk.link_input_data = ['%s/restrt > inpcrd'%(Book[k-1][ExchangeArray[n0]]),
                                  '%s/prmtop'%(Book[k-1][n0]),
                                  '%s/mdin_{0}'.format(n0)%(Book[k-1][n0])]
                                   ##Above: Copy from previous PIPELINE, make sure bookkeeping is correct
                                   
                              
        #md_tsk.pre_exec = ['export AMBERHOME=$HOME/amber/amber14/'] #Preexec, BLue Waters
        md_tsk.pre_exec = ['module load amber']
        md_tsk.arguments = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out','-inf', 'mdinfo_{0}'.format(n0)]
        md_tsk.cores = Replica_Cores
        md_tsk.mpi = True
        d[n0] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)
        #print d
        md_stg.add_tasks(md_tsk)
        task_uids.append(md_tsk.uid)
    p.add_stages(md_stg)
    stage_uids.append(md_stg.uid)

    #Create exchange stage 

    ex_stg= Stage()
    
    #Create Exchange Task

    ex_tsk = Task()
    ex_tsk.executable = ['python']
    ex_tsk.upload_input_data = ['exchangeMethods/TempEx.py']
    for n1 in range (Replicas):
        #print d[n1]
        
        ex_tsk.link_input_data += ['%s/mdinfo_%s'%(d[n1],n1)]
    
    ex_tsk.arguments = ['TempEx.py','{0}'.format(Replicas)]
    ex_tsk.cores = 1
    ex_tsk.mpi = False
    ex_tsk.download_output_data = ['exchangePairs.dat']
    ex_stg.add_tasks(ex_tsk)
    task_uids.append(ex_tsk.uid)
    p.add_stages(ex_stg)
    stage_uids.append(ex_stg.uid)
    Book.append(d)
    #print d
    #print Book
    return p
                                                                    
                                                

if __name__ == '__main__':

    res_dict = {
                #'resource': 'ncsa.bw_aprun',
                'resource': 'xsede.supermic',
                #'resource': 'xsede.comet',
                'walltime': 30,
                'cores': Pilot_Cores,
                'access_schema': 'gsissh',
                #'queue': 'compute',
                'queue': 'workq',
                'project': 'TG-MCB090174',
                #'project': 'bamm',
                }

    

    rman = ResourceManager(res_dict)

     # Create Application Manager
    appman = AppManager(autoterminate=False, port=33004)

     # Assign resource manager to the Application Manager
    appman.resource_manager = rman
    p = init_cycle()
     # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set([p]))

     # Run the Application Manager
    appman.run()

    for k in range (Cycles):
        p = cycle(k)
        #print p.uid

        # Assign the workflow as a set of Pipelines to the Application Manager
        appman.assign_workflow(set([p]))

        # Run the Application Manager
        appman.run()



    appman.resource_terminate()
