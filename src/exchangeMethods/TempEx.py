#!/usr/bin/env python

import os
import sys
import math
import numpy as np

####------------


Rep = sys.argv[1]
Replicas = int(Rep)
Col1=[]
Col2=[]
def TemperatureExchange(Replicas):
    exchangeList = range(Replicas)
    #random.shuffle(exchangeList)
    #####Read the mdinfo files######

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
                
    #print Replica_Energies
    #print Replica_Temps
    ##### Perform Exchange Computation


    #Build exchange matrix [matrix of dimensionless energies, E/kT]
    Kb = 0.0019872041    #Boltzmann Constant in kcal/mol
    Replica_Temps = np.array(Replica_Temps)
    Replica_Energies = np.array(Replica_Energies)
    #Exchange_Matrix = np.multiply(Replica_Energies, np.reciprocal(np.multiply(Kb, Replica_Temps))) ###Might not be correct
    Replica_Temps = np.reciprocal(np.multiply(Kb,Replica_Temps))
    #Consider all pairs for exchange
    print Replica_Temps
    exchangeList = []
    for i in range (Replicas):
        for j in range (Replicas):
            p = math.exp(np.multiply((Replica_Energies[i]-Replica_Energies[j]),(Replica_Temps[i]-Replica_Temps[j])))
            ###Once an exchange partner is found, move to the next i
              #Find mechanism to skip values of i that have found exchange pairs as j              
            if p > 1:
                exchangeList.append('%d %d'%(i, j))
                #i ,j append i,j to exchangeList
                break
            else:
                q = random.rand()
                if q < p:
                    exchangeList.append('%d %d'%(i, j))
                    #i,j append i,j to exchangeList
                    break
                else:
                    exchangeList.append('%d %d'%(i, i))
                

    f = open('exchangePairs.txt', 'w')
    for p in exchangePairs:
        line = ' '.join(str(x) for x in p)
        f.write(line + '\n')
    f.close
                    
TemperatureExchange(Replicas)

                                                                
