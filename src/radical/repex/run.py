#!/usr/bin/env python

from radical.entk import AppManager, ResourceManager
from SyncEx import SynchronousExchange
import os, time, pprint
import radical.utils as ru
import radical.analytics as ra
import radical.entk as re
import pickle
# ------------------------------------------------------------------------------
# Set default verbosity


os.environ['RADICAL_SAGA_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['RADICAL_ENMD_PROFILING']       = '1'
os.environ['RADICAL_PILOT_PROFILE']        = 'True'
os.environ['RADICAL_ENMD_PROFILE']         = 'True'
os.environ['RADICAL_ENTK_PROFILE']         = 'True'
os.environ['RADICAL_ENTK_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']         = '2000'
os.environ['RADICAL_VERBOSE']              = 'INFO'
os.environ['RADICAL_PILOT_PROFILE']        = 'True'
os.environ['RADICAL_REPEX_SYNCEX_PROFILE'] = 'True'
os.environ['RADICAL_REPEX_RUN_PROFILE']    = 'True'
os.environ['RADICAL_PILOT_DBURL']          = "mongodb://smush:key1209@ds117848.mlab.com:17868/db_repex_1"



#---------------------------------------#
## User settings

Replicas       = 128
Replica_Cores  = 20
Cycles         = 10    #0 cycles = no exchange
Resource       = 'xsede.supermic' #'ncsa.bw_aprun'
Pilot_Cores    = Replica_Cores * (Replicas)
#Pilot_Cores    = Replica_Cores * 32
ExchangeMethod = 'exchangeMethods/TempEx.py' #/path/to/your/exchange/method
MD_Executable  = '/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/sander.MPI'  #'/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI' #/path/to/your/MD/Executable

#MD_Executable = '/u/sciteam/mushnoor/amber/amber14/bin/sander.MPI'
timesteps      = 3000 #Number of timesteps between exchanges

#---------------------------------------#
                                                
if __name__ == '__main__':

    res_dict = {
                'resource': Resource,
                'walltime': 30,
                'cores': Pilot_Cores,
                'access_schema': 'gsissh',
                #'queue': 'debug',
                'queue': 'workq',
                'project': 'TG-MCB090174',
                #'project': 'bamm',
                }

    uid1 = ru.generate_id('radical.repex.run')
    logger = ru.get_logger('radical.repex.run')
    prof = ru.Profiler(name=uid1)
    prof.prof('Create_Workflow_0', uid=uid1)

    

                       

    synchronousExchange=SynchronousExchange()
    

    rman                    = ResourceManager(res_dict)
    appman                  = AppManager(autoterminate=False, port=33068)  # Create Application Manager 
    appman.resource_manager = rman  # Assign resource manager to the Application Manager   
    
        

    Exchange                = synchronousExchange.InitCycle(Replicas, Replica_Cores, MD_Executable, ExchangeMethod, timesteps)
    

    appman.assign_workflow(set([Exchange])) # Assign the workflow as a set of Pipelines to the Application Manager 

    prof.prof('Run_Cycle_0', uid=uid1)

    appman.run() # Run the Application Manager 

    prof.prof('End_Cycle_0', uid=uid1)

      

    
    for Cycle in range (Cycles):

        prof.prof('Create_Workflow_{0}'.format(Cycle+1), uid=uid1)

                          
        Exchange_gen            = synchronousExchange.GeneralCycle(Replicas, Replica_Cores, Cycle, MD_Executable, ExchangeMethod)
        
        appman.assign_workflow(set([Exchange_gen])) # Assign the workflow as a set of Pipelines to the Application Manager       

        prof.prof('Run_Cycle_{0}'.format(Cycle+1), uid=uid1)

                            

        appman.run() # Run the Application Manager

        prof.prof('End_Cycle_{0}'.format(Cycle+1), uid=uid1)

    appman.resource_terminate()

    mdtasks  = synchronousExchange.mdtasklist
    extasks  = synchronousExchange.extasklist

    pwd = os.getcwd()
    session = ra.Session(sid   = './%s'%appman.sid,
                         stype = 'radical.entk',
                         src   = pwd)


    mdtask_uid_map = dict()
    for task in mdtasks:
        mdtask_uid_map[task.name] = task.uid
        #print task.name

    extask_uid_map = dict()
    for task in extasks:
        extask_uid_map[task.name] = task.uid

        
    def get_mdtask_uids(task_names_list):
        return [mdtask_uid_map[task.name] for task in task_names_list]
    def get_extask_uids(task_names_list):
        return [extask_uid_map[task.name] for task in task_names_list]

    #Write MD and EX task lists to files

    with open('MDLIST_%s'%appman.sid, 'wb') as mdlist:
        pickle.dump(get_mdtask_uids(mdtasks), mdlist)

    with open('EXLIST_%s'%appman.sid, 'wb') as exlist:
        pickle.dump(get_extask_uids(extasks), exlist)
                    
 
    with open('MDLIST_%s'%appman.sid, 'rb') as mdlist:
        md_task_list=pickle.load(mdlist)

    with open('EXLIST_%s'%appman.sid, 'rb') as exlist:
        ex_task_list=pickle.load(exlist)
                

    md                      = session.filter(etype='task', inplace=False,  uid=md_task_list)
    md_scheduling_durations = md.duration([re.states.SCHEDULED, re.states.SUBMITTED])
    md_dequeuing_durations = md.duration([re.states.COMPLETED, re.states.DONE])
    md_durations            = md.duration([re.states.SUBMITTED, re.states.COMPLETED])

    ex                      = session.filter(etype='task', inplace=False,  uid=ex_task_list)
    ex_scheduling_durations = ex.duration([re.states.SCHEDULED, re.states.SUBMITTED])
    ex_dequeuing_durations = ex.duration([re.states.COMPLETED, re.states.DONE])
    ex_durations            = ex.duration([re.states.SUBMITTED, re.states.COMPLETED])

    total                   = session.filter(etype='task', inplace=False)
    total_durations         = total.duration([re.states.SCHEDULED, re.states.DONE])

    print "Total MD duration is ", md_durations
    print "MD Scheduling duration is ", md_scheduling_durations
    print "MD Dequeuing  duration is ", md_dequeuing_durations
    print "Total EX duration is ", ex_durations
    print "EX Scheduling duration is ", ex_scheduling_durations
    print "EX Dequeuing  duration is ", ex_dequeuing_durations
    print "total duration is " , total_durations

    
