
<img src="https://travis-ci.org/SrinivasMushnoori/RepEx_3.0.svg?branch=master" alt="Travis CI"/>

# Enhanced RepEx

[WIP]: The backbone of the RepEx replica Exchange package implemented via the Ensemble Toolkit 0.6 API.

src/driverMultipleAppManager.py: main EnTK script. Uses the PST abstractions to generate replica exchange workflows to be executed on remote resource. Currently, every MD phase and successive exchange computation are defined as independent pipelines. Since the entire exchange pattern needs to be known a priori, this allows for the invocation of multiple instances of the EnTK appmanager and submit each "pipeline" as a separate workflow. 

src/exchangeMethods: Exchange Methods, T_Exchange being implemented currently.U_Exchange, S_Exchange and pH_Exchange will be implemented later during the development cycle. 



old_drivers/driver.py: run script in EnTK 0.4.6 API, no longer supported, to be removed.
