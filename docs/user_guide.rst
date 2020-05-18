.. _user_guide:


**********
User Guide
**********

*1. Invoking RepEx*

Once you have installed RepEx, you can run synchronous replica exchange workloads. To invoke repex, run::

    repex simconfig.json resconfig.json

*2. Configuration Files*

You will notice that this requires two ``.json`` files, one for simulation configuration ``simconfig.json`` and one for resource configuration ``resconfig.json``
A simulation is completely described by these two files. 

*2.1 The Simulation Configuration File*

The Simulation configuration file looks like::



``
{
    "config" : {
        # parameters for ensemble creation and execution. Self explanatory.
        "min_temp"       : 300,
        "max_temp"       : 400,
        "timesteps"      : 10,
        "replicas"       : 4,
        "cycles"         : 3
    },

    "data" : {
        # input data dir to be staged, output data to be fetched
        # same paths are used within pilot sandbox
        
        "inputs"         : "inputs/",
        "outputs"        : "outputs/"
    },

    "prepare"            : {
        # what to run to prepare input data for all replicas.
        # workload_md.py contains a function "prepare_md" that handles the preparation of all replica input files.
        # Modify this function as per workload. 
        "algorithm"      : "examples/workload_md.py:prepare_md",
        "basename"       : "examples/FF"
    },

    "md" : {
        # workload for the MD stage (task description + data dependencies)
        # "executable" specifies the location of the MD executable on the target resource. 
        # The "arguments" field consists of all MD arguments.
        # "cpu_reqs" specifies resource requirements per replica.
        # "pre_exec" specifies any pre-MD commands needed to run. Since this example uses gromacs, we're running "grompp" here
        # "post_exec" specifies post-MD commands. Since gromacs does not generate a file containing Potential Energy and 
        # Temperature in human readable format at te end of the run by default, we create one using "gmx energy" in post exec.
        "executable"     : "/home/srinivas/Downloads/gromacs-2019.4/build/bin/gmx",
        "arguments"      : [ "mdrun",
                            "-s",      "sys.tpr", 
                            "-deffnm", "sys", 
                            "-c",      "outcrd.gro", 
                            "-e",      "sys.edr"

                           ],
        "cpu_reqs"       : {"processes"          : 1,
                            "threads_per_process": 1,
                            "thread_type"        : null,
                            "process_type"       : null
                           },
        "pre_exec"       : ["/home/srinivas/Downloads/gromacs-2019.4/build/bin/gmx grompp -f mdin.mdp -c inpcrd.gro -o sys.tpr -p sys.top"],
        "post_exec"      : ["/home/srinivas/Downloads/gromacs-2019.4/build/bin/gmx energy -f sys.edr -b 0.25 < inp.ener > mdinfo"], 

        # always linked. These are the input files for all replicas.
        #                   inputs          > cycle n
        "inputs"         : ["mdin.mdp.%(rid)s > mdin.mdp",
                            "sys.top          > sys.top",
                            "sys.itp          > sys.itp",
                            "inp.ener         > inp.ener",
                            "martini_v2.2.itp > martini_v2.2.itp"],

        # Config 0 only linked for cycle 0
        #                    inputs         > cycle 0
        "inputs_0"       : ["inpcrd.gro.%(rid)s > inpcrd.gro"],

      # # linked from cycle n to cycle n+1. Specifically the output configurations at the end of each MD cycle.
      
    
        "ex_2_md"        : ["outcrd.gro.%(rid)s > inpcrd.gro"], 

        # stage back output from all cycles
        # 
        "outputs"        : ["outcrd.gro         > outcrd.gro.%(rid)s.%(cycle)04d"],

        # only staged back from last cycle (n/a)
        "outputs_n"      : ["outcrd.gro         > outcrd.gro.%(rid)s.last"]
    },

    # "selection" specifies the selection algorithm. In most 1 dimensional exchange cases, leave the "algoritm" field unchanged. 
    # "exchange_size" specifies how many replicas must complete MD at minimum to be able to attempt exchange. Please ensure that
    # the total number of replicas is a whole number multiple of this field.

    "selection" : {
        "algorithm"      : "examples/algorithm_select_all.py:select_replicas_all",
        "exchange_size"  : 4
    },

    "exchange" : {
        # workload for the EX stage (algorithm + data dependencies). Modify the "exchange_algorithm.py" file to perform a different
        # flavour of replica exchange, such as umbrella sampling, etc. Currently configured for temperature. 
        "algorithm"      : "examples/exchange_algorithm.py:exchange_by_temperature",
        
        # for each replica in ex_list
        #                    md file > exchange file
        "md_2_ex"        : ["mdinfo  > mdinfo.%(rid)s",
                            "outcrd.gro  > outcrd.gro.%(rid)s"],
        # exchange happens on these
        "ex_data"        : ["outcrd.gro.%(rid)s"]
    }
}

``






        

Most of this file is self explanatory: it allows the user to input replica exchange simulation parameters such as number of replicas, cores per replica, timesteps between exchange attempts, and a temperature range. However, some caution is advised while setting the ``exchangemethod``, ``md_executable`` and ``basename`` entries. 



*2.1.1 MD Executable*

The path to your MD executable on the *target* resource is specified here.

*2.1.2 Basename*

RepEx needs a basename to locate the files which will be used as input parameters for the MD component. These may include (depending on the MD engine) a coordinate file, a topology file, and a run-input file. 


*2.1.3 Exchange Method*

RepEx provides an interface that enables the user to write their own exchange methods. This method is defined by the user in an independent python file, and the abspath must be specified here. 


*2.2 The Resource Configuration Files*
 
The Resource configuration file specifies the target resource configuration::


``

{
    "rmq_host" : "localhost",
    "rmq_port" : 32769,

    "resource" : "local.localhost",
    "walltime" : 2880,
    "cpus"     : 8
}



``


There are three mandatory keys here: ``resource`` , ``walltime`` and ``cpus`` . 

If you are running RepEx on a remote HPC cluster (see `here <https://radicalpilot.readthedocs.io/en/latest/machconf.html#pre-configured-resources>`_ for supported resources) you will need additional entries in the resconfig file::


    "access_schema" : "<access_schema_here>",
    "queue"         : "<queue_name_here>",
    "project"       : "<allocation_number_here>"

See above link for more information on these additional entries.

*3. Defining the Exchange Method:*

There are two components to this method: (i) reading the energy files, and (ii) performing the exchange computation, i.e. determining all exchange pairs. The first component is dependent upon how the your preferred MD engine outputs energy information. In this example, the above method uses gromacs, and we generate the  ``mdinfo`` file to read and generate an Energy matrix. The second component performs a standard Metropolis computation to find exchange pairs. 

Below we see lines 115-130 the ``exchange_algorithm.py``  method, where reading the appropriate energy files is spcified.::

``
    ######---------------THIS section reads energy files, edit appropriately for your MD engine of choice----------------------------------

        for fname in glob.glob('mdinfo*'):

            with open('mdinfo.','r') as f: #Perhaps it's possible to read the outfile instead of mdinfo?
                lines = f.readlines()
            
                for i,j in enumerate(lines):
                    if "TEMP(K)" in lines[i]:
                        temp = float(lines[i].split()[8])
                        temperatures.append(temp)
                    
                    elif "EPtot" in lines[i]:
                        pot_eng = float(lines[i].split()[8])
                        energies.append(pot_eng)
``

Next, to find exchange pairs, we must first generate the swap matrix:

``        swap_matrix = [[ 0. for j in range(replicas)] for i in range(replicas)]

        for i in range(replicas):
            for j in range(replicas):      
                swap_matrix[i][j] = reduced_potential(temperatures[j], energies[i])
        #print swap_matrix
        return swap_matrix

    swap_matrix=build_swap_matrix(replicas)
    ``

The swap matrix is then employed by the ``gibbs_exchange`` function to determine exchange pairs. This may be modified depending on the flavour of replica exchange the user wishes to perform. A full description of the mathematics involved is beyond the scope of this doncumentation.







