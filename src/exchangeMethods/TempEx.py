#!/usr/bin/env python

import os
import sys
import math
#import numpy as np

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
                

    ##### Perform Exchange Computation

             




    #Col1 = exchangeList[:len(exchangeList)/2]
    #Col2= exchangeList[len(exchangeList)/2:]
    ####exchangePairs = list(tuple)
    #exchangePairs = zip(Col1, Col2)
    ##Output exchange pairs to file

    #f = open('exchangePairs.txt', 'w')
    #for p in exchangePairs:
        #line = ' '.join(str(x) for x in p)
        #f.write(line + '\n')
    #f.close
TemperatureExchange(Replicas)

                                                                
