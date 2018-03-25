#!/usr/bin/env python

import os
import sys
import math
import random


####------------

Rep = sys.argv[1]
Cycle = int(sys.argv[2])
Replicas = int(Rep)
Col1=[]
Col2=[]
def RandomExchange(Replicas,Cycle):
    exchangeList1 = range(Replicas)
    random.shuffle(exchangeList1)
    exchangeList2 = range(Replicas)
    random.shuffle(exchangeList2)

    Col1 = exchangeList1
    Col2 = exchangeList2
    ####exchangePairs = list(tuple) 
    exchangePairs = zip(Col1, Col2)
    ##Output exchange pairs to file

    f = open('exchangePairs_{0}.dat'.format(Cycle), 'w')
    for p in exchangePairs:
        line = ' '.join(str(x) for x in p)
        f.write(line + '\n')
    f.close
        
RandomExchange(Replicas,Cycle)
