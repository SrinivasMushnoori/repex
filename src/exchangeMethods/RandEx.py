#!/usr/bin/env python

#imports
import os
import sys
import math
import time
import random
#import numpy as np

####------------


Rep = sys.argv[1]
Replicas = int(Rep)

def RandomExchange(Replicas):
#    Replicas = sys.argv
#    print Replicas
    exchangeList = range(Replicas)
    #print exchangeList
    random.shuffle(exchangeList)
    #print exchangeList
    for n in range (Replicas):
        if n < (Replicas/2):
            Col1 = exchangeList
            #print Col1
        else:
            Col2 = exchangeList
            #print Col2
    ####exchangePairs = list(tuple) 
    exchangePairs = zip(Col1, Col2)
    ##Output exchange pairs to file

    f = open('exchangePairs.txt', 'w')
    for p in exchangePairs:
        line = ' '.join(str(x) for x in p)
        f.write(line + '\n')
    f.close
        
RandomExchange(Replicas)
