
<img src="https://travis-ci.org/SrinivasMushnoori/RepEx_3.0.svg?branch=master" alt="Travis CI"/>

# Enhanced RepEx

[WIP]: The backbone of the RepEx replica Exchange package implemented via the Ensemble Toolkit 0.6 API.

src/driverMultipleAppManager.py: main EnTK script. Uses the PST abstractions to generate replica exchange workflows to be executed on remote resource. Currently, every MD phase and successive exchange computation are defined as independent pipelines. Since the entire exchange pattern needs to be known a priori, this allows for the invocation of multiple instances of the EnTK appmanager and submit each "pipeline" as a separate workflow. 

src/exchangeMethods: Exchange Methods, T_Exchange being implemented currently.U_Exchange, S_Exchange and pH_Exchange will be implemented later during the development cycle. 



old_drivers/driver.py: run script in EnTK 0.4.6 API, no longer supported, to be removed.

# Instructions: 
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
python run.py
```
