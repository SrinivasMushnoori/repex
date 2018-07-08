## RepEx Workload

Test Workload for the DA Scheduler testing.

This workload consists of 8 replicas that perform Synchronous exchange. 
Each replica performs 20 MD stages with 19 exchange stages. The last stage is a pseudo- exchange stage that performs the exchange computation one last time to complete the exchange trace. Each replica runs for 2000 timesteps between exchanges. This is considered a low rate of attempted exchanges. This system should maintain about a ~0.23 acceptance ratio, meaning that 77% of the exchanges are rejected, i.e. remain on the same nodes. 
From EnTK's perspective, there is 1 `EnTK` pipeline, 40 `EnTK` stages, and either 1 or 8 `EnTK` task per stage depending on whether it is an MD stage or Exchange stage. Each MDtask receives 20 cores. Currently, this workload is configured to execute on SuperMIC. Use the `rabbitmq` docker instance `33068` on the RADICAL VM-2. This instance has been reserved for RepEx development. 
Expect this workload to run for approximately 30 minutes. 

### Instructions: 
* Install following stack:
```
To be updated
```

Set the following environmental variables:

```
export RADICAL_SAGA_VERBOSE=INFO
export RP_ENABLE_OLD_DEFINES=True
export RADICAL_ENTK_PROFILE=True
export RADICAL_ENTK_VERBOSE=INFO
export SAGA_PTY_SSH_TIMEOUT=2000
export RADICAL_VERBOSE=INFO
export RADICAL_PROFILE=True
export RADICAL_REPEX_SYNCEX_PROFILE=True
export RADICAL_REPEX_RUN_PROFILE=True
export RADICAL_PILOT_DBURL=mongodb://smush:key1209@ds117848.mlab.com:17868/db_repex_1
```

Run as follows:
```
cd RepEx_3.0/src/radical/repex
python run.py
```