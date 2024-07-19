#!/usr/bin/env python

from radical.entk import AppManager, ResourceManager
from SyncEx import InitCycle, Cycle
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

Replicas = 128
Replica_Cores = 32
Cycles = 0                     #0 cycles = no exchange
Resource = 'ncsa.bw_aprun'
Pilot_Cores = Replica_Cores * (Replicas + 1)
#MDE = 'amber' #MD Engine
ExchangeMethod = 'exchangeMethods/TempEx.py' 
MD_Executable = '/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI'

#---------------------------------------#


#p=SynchronousExchange(Replicas, Replica_Cores, Cycles, MD_Executable, ExchangeMethod)

p = InitCycle(Replicas, Replica_Cores, MD_Executable, ExchangeMethod)
#q = Cycle(Replicas, Replica_Cores, Cycles, MD_Executable, ExchangeMethod)
                                                
if __name__ == '__main__':

    res_dict = {
                'resource': Resource,
                'walltime': 200,
                'cores': Pilot_Cores,
                'access_schema': 'gsissh',
                'queue': 'normal',
                #'queue': 'workq',
                #'project': 'TG-MCB090174',
                'project': 'bamm',
                }

    

    rman = ResourceManager(res_dict)

     # Create Application Manager
    appman = AppManager(autoterminate=False, port=33004)

     # Assign resource manager to the Application Manager
    appman.resource_manager = rman
    #p = SynchronousExchange()
     # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set([p]))

     # Run the Application Manager
    appman.run()
    
    q = Cycle(Replicas, Replica_Cores, Cycles, MD_Executable, ExchangeMethod)

    for k in range (Cycles):
        p = cycle(k)
        #print p.uid

        # Assign the workflow as a set of Pipelines to the Application Manager
        appman.assign_workflow(set([q]))

        # Run the Application Manager
        appman.run()



    appman.resource_terminate()
