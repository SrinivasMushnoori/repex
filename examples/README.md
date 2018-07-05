## RepEx Workload

Test Workload for the DA Scheduler testing.

This workload consists of 8 replicas that perform Synchronous exchange. 
Each replica performs 20 MD stages with 19 exchange stages. Each replica runs for 2000 timesteps between exchanges. This is considered a low rate of attempted exchanges.  
From EnTK's perspective, there is 1 `EnTK` pipeline, 40 `EnTK` stages, and either 1 or 8 `EnTK` task per stage depending on whether it is an MD stage or Exchange stage. Each MDtask receives 20 cores. Currently, this workload is configured to execute on SuperMIC. Use the `rabbitmq` docker instance `33068` on the RADICAL VM-2. This instance has been reserved for RepEx development. 
Expect this workload to run for approximately 30 minutes. 

### Instructions: 
* Install following stack:
```
To be updated
```

Set the following environmental variables:

```
To be updated
```
