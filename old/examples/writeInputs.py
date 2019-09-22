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



    Temps_List = [
        min_temp + x * (max_temp - min_temp) / replicas
        for x in range(replicas)
    ]
   
    InputFile = os.getcwd() + "/" + basename + ".mdin"

    for i in range(len(Temps_List)):

        mdinFile = open(os.getcwd() + '/' + basename + '.mdin', 'r')
        tbuffer = mdinFile.read()
        tbuffer = tbuffer.replace("@temperature@", str(Temps_List[i]))
        tbuffer = tbuffer.replace("@timesteps@", str(timesteps))
        mdinFile.close()

        w_file = open('mdin-{0}-0'.format(i), "w")
        w_file.write(tbuffer)
        w_file.close()
