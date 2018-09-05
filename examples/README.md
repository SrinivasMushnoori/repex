# 1D Synchronous Temperature Exchange:

Provided here are the files required to run 1 dimensional temperature replica exchange MD (1D-REMD) on a system of 4 single-core replicas of acetylated alanine dipeptide as a test case. This is executed on localhost.
To run:

```
repex simconfig.json resconfig.json
```


Set the following environmental variables before running:

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
