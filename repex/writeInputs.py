import os
import sys
import fileinput
import shutil


def writeInputs(max_temp, min_temp, replicas, timesteps, basename):

    max_temp = max_temp
    min_temp = min_temp
    replicas = replicas
    timesteps = timesteps

    #for i in range(replicas):
    #shutil.copy2('mdin', 'mdin_{0}'.format(i))

    Temps_List = [
        min_temp + x * (max_temp - min_temp) / replicas
        for x in range(replicas)
    ]
    #print len(Temps_List)
    ## for every entry in Temp_list
    ##    create new copy of mdin_{n}
    ##    Find and replace temperature in the file
    ##    write new file
    InputFile = os.getcwd() + "/" + basename + ".mdin"

    for i in range(len(Temps_List)):

        mdinFile = open(os.getcwd() + '/' + basename + '.mdin', 'r')
        tbuffer = mdinFile.read()
        tbuffer = tbuffer.replace("@temperature@", str(Temps_List[i]))
        tbuffer = tbuffer.replace("@timesteps@", str(timesteps))
        mdinFile.close()

        w_file = open('mdin_{0}'.format(i), "w")
        w_file.write(tbuffer)
        w_file.close()
