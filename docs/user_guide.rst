.. _user_guide:


**********
User Guide
**********

***1. Invoking RepEx***

Once you have installed RepEx, you can run synchronous replica exchange workloads. To invoke repex, run::

    repex simconfig.json resconfig.json

***2. Configuration Files***

You will notice that this requires two ``.json`` files, one for simulation configuration ``simconfig.json`` and one for resource configuration ``resconfig.json``
A simulation is completely described by these two files. 

**2.1 The Simulation Configuration File**

The Simulation configuration file looks like::

    "replicas"       : 32,
    "replica_cores"  : 1,
    "cycles"         : 0,
    "exchangemethod" : "path/to/your/exchange/method", 
    "md_executable"  : "path/to/md/engine/executable", 
    "timesteps"      : 100,
    "basename"       : "chemical-system",
    "min_temp"       : 300,
    "max_temp"       : 550
        

Most of this file is self explanatory: it allows the user to input replica exchange simulation parameters such as number of replicas, cores per replica, timesteps between exchange attempts, and a temperature range. However, some caution is advised while setting the ``exchangemethod``, ``md_executable`` and ``basename`` entries. 


There are three mandatory keys here: ``resource`` , ``walltime`` and ``cpus`` .



*2.1.1 MD Executable*

The path to your MD executable on the *target* resource is specified here.

*2.1.2 Basename*

RepEx needs a basename to locate the files which will be used as input parameters for the MD component. These may include (depending on the MD engine) a coordinate file, a topology file, and a run-input file. 


*2.1.3 Exchange Method*

RepEx provides an interface that enables the user to write their own exchange methods. This method is defined by the user in an independent python file, and the abspath must be specified here. 


**2.2 The Resource Configuration Files**
 
The Resource configuration file specifies the target resource configuration::

	"resource"      : "resource.name",
	"walltime"      : 30,
	"cpus"          : 64,
	"gpus_per_node" : 0,
	"access_schema" : "gsissh",
	"queue"         : "debug",
	"project"       : "allocation"



***3. Defining the Exchange Method:***

Below is the ``Temperature Exchange`` method, as an illustration::

    #!/usr/bin/env python

    import os
    import sys
    import math
    import numpy as np
    import random
 
    Replicas = int(sys.argv[1])
    Cycle = int(sys.argv[2])

    def TemperatureExchange(Replicas):
        exchangeList = range(Replicas)
       
        #####Read the energy files, prepare energy matrix######

        Temp = 0.0
        PotEng = 0.0
        Replica_Temps = []
        Replica_Energies = []
        for n in range (Replicas):
            f = open('mdinfo_{0}'.format(n)) 
            lines = f.readlines()
            #f.close
            for i,j in enumerate(lines):
                if "TEMP(K)" in lines[i]:
                    Temp = float(lines[i].split()[8])
                
                    Replica_Temps.append(Temp)
                elif "EPtot" in lines[i]:
                    PotEng = float(lines[i].split()[8])
                    Replica_Energies.append(PotEng)
            f.close
                
        ##### Perform Exchange Computation


        #Build exchange matrix [matrix of dimensionless energies, E/kT]

        Kb = 0.0019872041    #Boltzmann Constant in kcal/mol

        Replica_Temps = np.array(Replica_Temps)

        Replica_Energies = np.array(Replica_Energies)

        Replica_Temps = np.reciprocal(np.multiply(Kb,Replica_Temps)) # Turns this into dimensionless temperatures (beta)
        #print Replica_Temps

        ###Consider all pairs for exchange
        #print Replica_Temps

        exchangeList = []

        for i in range (Replicas):
            for j in range (Replicas):
                p = math.exp(np.multiply((Replica_Energies[i]-Replica_Energies[j]),(Replica_Temps[i]-Replica_Temps[j])))
                print p
                ###Once an exchange partner is found, move to the next i
                  #Find mechanism to skip values of i that have found exchange pairs as j              
                if p > 1:
                    exchangeList.append('%d %d'%(i, j))
                    #i ,j append i,j to exchangeList
                    break
                else:
                    q = random.random()
                    if q < p:
                        exchangeList.append('%d %d'%(i, j))
                        #i,j append i,j to exchangeList
                        break
                    else:
                        exchangeList.append('%d %d'%(i, i))
                        break
    
        f = open('exchangePairs_{0}.dat'.format(Cycle), 'w')
        for p in exchangeList:
            line = ' '.join(str(x) for x in p)
            f.write(line + '\n')
        f.close
                    
    TemperatureExchange(Replicas)


There are two components to this method: (i) reading the energy files, and (ii) performing the exchange computation, i.e. determining all exchange pairs. The first component is dependent upon how the your preferred MD engine outputs energy information. In this example, the above method uses AMBER ``mdinfo`` files to generate an Energy matrix. The second component performs a standard Metropolis computation to find exchange pairs. 

