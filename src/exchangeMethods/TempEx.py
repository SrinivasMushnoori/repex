#!/usr/bin/env python

import os
import sys
import math
import random


####------------


Rep = sys.argv[1]
Replicas = int(Rep)
Col1=[]
Col2=[]
def TemperatureExchange(Replicas):
    exchangeList = range(Replicas)
    #random.shuffle(exchangeList)
    #####Read the mdinfo files######




    #####




    Col1 = exchangeList[:len(exchangeList)/2]
    Col2= exchangeList[len(exchangeList)/2:]
    ####exchangePairs = list(tuple)
    exchangePairs = zip(Col1, Col2)
    ##Output exchange pairs to file

    f = open('exchangePairs.txt', 'w')
    for p in exchangePairs:
        line = ' '.join(str(x) for x in p)
        f.write(line + '\n')
    f.close
RandomExchange(Replicas)

                                                                
