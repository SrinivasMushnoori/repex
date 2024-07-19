.. _examples:

********
Examples
********

1D Temperature Exchange

.. toctree::
   :maxdepth: 2


**1D Temperature Exchange:**


Provided here are the files required to run 1 dimensional temperature replica exchange MD (1D-REMD) on a system of 4 single-core replicas of diphenylalanine as a test case. This is executed on localhost.

Example files can be found at: https://github.com/SrinivasMushnoori/repex.gmx/tree/master/FF


To run::


    radical-epex workload_gmx.json resource_local.json

Ensure that you have the simulation files ready/prepared. 

Set the following environmental variables before running::


    export RADICAL_ENTK_PROFILE=True
    export RADICAL_ENTK_VERBOSE=INFO
    export SAGA_PTY_SSH_TIMEOUT=2000
    export RADICAL_VERBOSE=INFO
    export RADICAL_PROFILE=True
    export RADICAL_PILOT_DBURL=<rp_dburl_here>







