#!~/numpy_env/bin/python

import platform

platform.python_version()

import os
import sys
import math
import numpy as np
import random
####------------



Replicas = int(sys.argv[1])
Cycle = int(sys.argv[2])

def TemperatureExchange(Replicas):
    exchangeList = range(Replicas)
    #exchangeLog=open("exchange.log", "w+")
    #####Read the mdinfo files######

    Temp = 0.0
    PotEng = 0.0
    Replica_Temps = []
    Replica_Energies = []
    for n in range (Replicas):
        with open('mdinfo_{0}'.format(n),'r') as f: #Perhaps it's possible to read the outfile instead of mdinfo?
            lines = f.readlines()
        
            for i,j in enumerate(lines):
                if "TEMP(K)" in lines[i]:
                    Temp = float(lines[i].split()[8])
                    Replica_Temps.append(Temp)
                
                elif "EPtot" in lines[i]:
                    PotEng = float(lines[i].split()[8])
                    Replica_Energies.append(PotEng)
       
                
    #print Replica_Energies
    #print Replica_Temps
    ##### Perform Exchange Computation


    #Build exchange matrix [matrix of dimensionless energies, E/kT]

    Kb = 0.0019872041    #Boltzmann Constant in kcal/mol

    Replica_Temps = np.array(Replica_Temps)
    print Replica_Temps

    Replica_Energies = np.array(Replica_Energies)
    print Replica_Energies

    Replica_Temps = np.reciprocal(np.multiply(Kb,Replica_Temps)) # Turns this into dimensionless temperatures (beta)
    print Replica_Temps

    ###Consider all pairs for exchange
    #print Replica_Temps

    exchangeList = []

    for i in range (Replicas):
        for j in range (Replicas):
            if j == i:
                continue
            else:
                E_diff = Replica_Energies[i]-Replica_Energies[j]
                T_diff = Replica_Temps[i]-Replica_Temps[j]
                product = np.multiply(E_diff, T_diff)
                p = math.exp(product)
                print E_diff, T_diff, product, p
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
    
    with open('exchangePairs_{0}.dat'.format(Cycle), 'w') as f:
        for p in exchangeList:
            print p, p[0], p[1]
            row_str = str(p[0]) + " " + str(p[1]) 
            f.write(p)
            f.write('\n')

                    
TemperatureExchange(Replicas)

                                                                
