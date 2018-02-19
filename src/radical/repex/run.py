#!/usr/bin/env python

from radical.entk import AppManager, ResourceManager
from SyncEx import SynchronousExchange
import os
# ------------------------------------------------------------------------------
# Set default verbosity

os.environ['RADICAL_SAGA_VERBOSE']   = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']  = 'True'
os.environ['RADICAL_ENMD_PROFILING'] = '1'
os.environ['RADICAL_PILOT_PROFILE']  = 'True'
os.environ['RADICAL_ENMD_PROFILE']   = 'True'
os.environ['RADICAL_ENTK_VERBOSE']   = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']  = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']   = '2000'
os.environ['RADICAL_VERBOSE']        = 'INFO'
os.environ['RADICAL_PILOT_PROFILE']  = 'True'
os.environ['RADICAL_PILOT_DBURL']    = "mongodb://smush:key1209@ds117848.mlab.com:17868/db_repex_1"

#---------------------------------------#
## User settings

Replicas       = 32
Replica_Cores  = 32
Cycles         = 50    #0 cycles = no exchange
Resource       = 'ncsa.bw_aprun'
Pilot_Cores    = Replica_Cores * (Replicas + 1)
ExchangeMethod = 'exchangeMethods/TempEx.py' 
MD_Executable  = '/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI'

#---------------------------------------#

                                                
if __name__ == '__main__':

    res_dict = {
                'resource': Resource,
                'walltime': 250,
                'cores': Pilot_Cores,
                'access_schema': 'gsissh',
                'queue': 'normal',
                #'queue': 'workq',
                #'project': 'TG-MCB090174',
                'project': 'bamm',
                }

    SynchronousExchange=SynchronousExchange()
    

    rman                    = ResourceManager(res_dict)
    appman                  = AppManager(autoterminate=False, port=33004)  # Create Application Manager 
    appman.resource_manager = rman  # Assign resource manager to the Application Manager   


    Exchange                = SynchronousExchange.InitCycle(Replicas, Replica_Cores, MD_Executable, ExchangeMethod)
    
    appman.assign_workflow(set([Exchange])) # Assign the workflow as a set of Pipelines to the Application Manager 

    appman.run() # Run the Application Manager 
    
    

    for Cycle in range (Cycles):
        
        Exchange            = SynchronousExchange.GeneralCycle(Replicas, Replica_Cores, Cycle, MD_Executable, ExchangeMethod)
        
    
        appman.assign_workflow(set([Exchange])) # Assign the workflow as a set of Pipelines to the Application Manager       

        appman.run() # Run the Application Manager



    appman.resource_terminate()
