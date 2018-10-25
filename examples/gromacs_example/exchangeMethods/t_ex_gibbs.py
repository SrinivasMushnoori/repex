#!/usr/bin/env python

import platform

platform.python_version()

import os
import sys
import math
import numpy as np
import random
####------------



replicas = int(sys.argv[1])
cycle = int(sys.argv[2])


def gibbs_exchange(r_i, replicas, swap_matrix):


    #evaluate all i-j swap probabilities
    ps = [0.0]*(replicas)

    j = 0
    for r_j in range(replicas):
        ps[j] = -(swap_matrix[r_i][r_j] + swap_matrix[r_j][r_i] - 
                  swap_matrix[r_i][r_i] - swap_matrix[r_j][r_j]) 
        #print ps[j]
        j += 1
        
    new_ps = []
    for item in ps:
        if item > math.log(sys.float_info.max): new_item=sys.float_info.max
        elif item < math.log(sys.float_info.min) : new_item=0.0
        else :
            new_item = math.exp(item)
        new_ps.append(new_item)
    ps = new_ps
    #print ps
    # index of swap replica within replicas_waiting list
    j = replicas
    while j > (replicas - 1):
        j = weighted_choice_sub(ps)
        #print j
        
    
    r_j = j
    #print r_j
    return r_j

#------------

def reduced_potential(temperature, potential):

    #Kb = 0.0019872041    #Boltzmann Constant in kcal/mol (AMBER uses kcal/mol for some reason. I wonder if the bond lengths are handled internally in inches.)
    Kb = 0.008314462175
    if temperature != 0:
        beta = 1. / (Kb*temperature)
    else:
        beta = 1. / Kb     
    return float(beta * potential)

#--------------


def weighted_choice_sub(weights):
    """Adopted from asyncre-bigjob [1]
    """

    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

#--------------


def build_swap_matrix(replicas):

    temp = 0.0
    pot_eng = 0.0
    temperatures = []
    energies = []

######---------------THIS section reads energy files, edit appropriately for your MD engine of choice----------------------------------

    for n in range (replicas):
        with open('mdinfo_{0}'.format(n),'r') as f: #Perhaps it's possible to read the outfile instead of mdinfo?
            lines = f.readlines()
        
            for i,j in enumerate(lines):
                if "Temperature" in lines[i]:
                    temp = float(lines[i].split()[1])
                    temperatures.append(temp)
                
                elif "Potential" in lines[i]:
                    pot_eng = float(lines[i].split()[1])
                    energies.append(pot_eng)

#######----------------------------------------------------------------------------------------------------------------------------------

    swap_matrix = [[ 0. for j in range(replicas)] for i in range(replicas)]

    for i in range(replicas):
        for j in range(replicas):      
            swap_matrix[i][j] = reduced_potential(temperatures[j], energies[i])
    #print swap_matrix
    return swap_matrix

swap_matrix=build_swap_matrix(replicas)

def t_exchange(replicas, swap_matrix):
    exchange_list = []
    for r_i in range(replicas):
        r_j = gibbs_exchange(r_i, replicas, swap_matrix)
        exchange_pair = []
        exchange_pair.append(r_i)
        exchange_pair.append(r_j)
        #print exchange_pair
        exchange_list.append(exchange_pair)

    #print exchange_list


    with open('exchangePairs_{0}.dat'.format(cycle), 'w') as f:
        for pair in exchange_list:
            row_str = str(pair[0]) + " " + str(pair[1]) 
            f.write(row_str)
            f.write('\n')

t_exchange(replicas, swap_matrix)

                                                                
