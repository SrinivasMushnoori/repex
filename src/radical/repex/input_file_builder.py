import os
import sys
import fileinput


#Create list of temperatures (change to a loop)
#Temp_list=['303.00', '323.00','343.00','363.00']

Max_Temp=500.00
Min_Temp=250.00
Replicas=1
timesteps='10000'

Temps_List=[Min_Temp + x*(Max_Temp-Min_Temp)/Replicas for x in range(Replicas)]
print len(Temps_List)
## for every entry in Temp_list
##    create new copy of mdin_{n}
##    Find and replace temperature in the file
##    write new file
InputFile="mdin"
Placeholder1 = 'xxxxx'
Placeholder2 = 'timesteps'
#print len(Temps_List)
for i in range (len(Temps_List)):
    #print Temps_List[i]
    mdinFile = open('mdin_{0}'.format(i),'r+')
    print mdinFile
    for line in fileinput.input(InputFile):
        if Placeholder1 in line:
            mdinFile.write(line.replace(Placeholder1,Temps_List[i]))
        elif Placeholder2 in line:
            mdinFile.write(line.replace(Placeholder2,timesteps))
    mdinFile.close()
