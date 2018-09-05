
<img src="https://travis-ci.org/SrinivasMushnoori/RepEx_3.0.svg?branch=master" alt="Travis CI"/>

# Enhanced RepEx

RepEx replica exchange package implemented via the Ensemble Toolkit 0.7 API.

# Documentation

https://repex-30.readthedocs.io/en/latest/


Before execution, set the following environmental variables:

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

Run as follows (ensure that you are in the "examples" directory):
```
repex simconfig.json resconfig_<resource>.json
```
on the appropriate computing resource.
