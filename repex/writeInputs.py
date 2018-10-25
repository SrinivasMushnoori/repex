import os
import sys
import fileinput
import shutil
import math


def writeInputs(max_temp, min_temp, replicas, timesteps, basename):

    max_temp = max_temp
    min_temp = min_temp
    replicas = replicas
    timesteps = timesteps

    #Geometric temperature distribution

    temps_list = [min_temp + x * (max_temp - min_temp) / replicas for x in range(replicas)]
    
    
    # Exponential temperature distribution
    #temps_list_unrounded = [min_temp*math.exp(r*0.02) for r in range(replicas)] ### You can chang the 0.02 to any value you want
    #temps_list = [ round(elem, 2) for elem in temps_list_unrounded ]
    
    
    
    #print len(Temps_List)
    ## for every entry in Temp_list
    ##    create new copy of mdin_{n}
    ##    Find and replace temperature in the file
    ##    write new file
    InputFile = os.getcwd() + "/" + basename + ".mdp"

    for i in range(len(temps_list)):

        mdinFile = open(os.getcwd() + '/' + basename + '.mdp', 'r')
        tbuffer = mdinFile.read()
        tbuffer = tbuffer.replace("@temperature@", str(temps_list[i]))
        tbuffer = tbuffer.replace("@timesteps@", str(timesteps))
        mdinFile.close()

        w_file = open('replica_{0}.mdp'.format(i), "w")
        w_file.write(tbuffer)
        w_file.close()
