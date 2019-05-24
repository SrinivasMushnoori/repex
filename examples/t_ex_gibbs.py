#!/usr/bin/env python

import platform

platform.python_version()

import os
import sys
import math
import numpy as np
import random
####------------



path = os.getcwd()
md_out_files = []
for i in os.listdir(path):
    if os.path.isfile(os.path.join(path,i)) and 'mdinfo' in i:
        md_out_files.append(i)
replicas = [int(file.split('-')[1]) for file in md_out_files]
cycles   = [int(file.split('-')[2]) for file in md_out_files]

sandbox = str(sys.argv[1])

def gibbs_exchange(r_i, replicas, swap_matrix):


    #evaluate all i-j swap probabilities
    ps = [0.0]*len(replicas)
    #print replicas

    j = 0


        
    for r_j in range(len(replicas)):
        ps[j] = -(swap_matrix[r_i][r_j] + swap_matrix[r_j][r_i] - 
                  swap_matrix[r_i][r_i] - swap_matrix[r_j][r_j]) 
        # print ps[j]
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
    # index of swap replica within replicas_waiting list   #MAJOR problem here. Fix tomorrow
    j = replicas
    while j > (len(replicas) - 1):
        j = weighted_choice_sub(ps)
        #print j
        
    
    r_j = j
    #print r_j
    return r_j

   


#------------

def reduced_potential(temperature, potential):

    Kb = 0.0019872041    #Boltzmann Constant in kcal/mol (AMBER uses kcal/mol for some reason. I wonder if the bond lengths are handled internally in inches.)
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

    for file in md_out_files:
        #filename = md_out_files[file]
        with open(file) as f: 
            lines = f.readlines()
        
            for i,j in enumerate(lines):
                if "TEMP(K)" in lines[i]:
                    temp = float(lines[i].split()[8])
                    temperatures.append(temp)
                
                elif "EPtot" in lines[i]:
                    pot_eng = float(lines[i].split()[8])
                    energies.append(pot_eng)

#######----------------------------------------------------------------------------------------------------------------------------------

    swap_matrix = [[ 0. for j in range(len(replicas))] for i in range(len(replicas))]

    for i in range(len(replicas)):
        for j in range(len(replicas)):      
            swap_matrix[i][j] = reduced_potential(temperatures[j], energies[i])
    #print swap_matrix
    return swap_matrix



def t_exchange(replicas, swap_matrix):
    exchange_list = []
    for r_i in range(len(replicas)):
        r_j = gibbs_exchange(r_i, replicas, swap_matrix)
        exchange_pair = []

        exchange_pair.append([replicas[r_i],cycles[r_i]])
        exchange_pair.append([replicas[r_j],cycles[r_j]])
        #print exchange_pair
        exchange_list.append(exchange_pair)


    #cycle = 0
    with open('exchangePairs.dat', 'w') as f:
        f.write("replicas and cycles are: ")
        f.write('\n')
        for file in md_out_files:
            f.write(file)
            f.write('\n')
        for pair in exchange_list:
            row_str = str(pair[0]) + " " + str(pair[1]) 
            f.write(row_str)
            f.write('\n')

    for pair in exchange_list:
        print pair

    ### Use os.symlink here.
        src = sandbox + '/mdcrd-' + str(pair[0][0]) + '-' + str(pair[0][1])
        dst = sandbox + '/inpcrd-' + str(pair[1][0]) + '-' + str(pair[1][1]+1)
        print src, '>', dst 
        try:
            os.symlink(src, dst)
        except OSError:
            pass

#replicas = len(md_out_files)

swap_matrix=build_swap_matrix(replicas)

t_exchange(replicas, swap_matrix)

                                                                
