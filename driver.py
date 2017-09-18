### RepEx in EnTK 0.4.6 API: Incomplete

#!/usr/bin/env python

import sys
import os
import json
import shutil

from radical.ensemblemd import Kernel
from radical.ensemblemd import PoE
from radical.ensemblemd import EoP
from radical.ensemblemd import EnsemblemdError
from radical.ensemblemd import ResourceHandle

#Used to register user defined kernels
from radical.ensemblemd.engine import get_engine




# ------------------------------------------------------------------------------
# Set default verbosity

if os.environ.get('RADICAL_ENTK_VERBOSE') == None:
	os.environ['RADICAL_ENTK_VERBOSE'] = 'REPORT'


# ------------------------------------------------------------------------------
#


class RunExchange(PoE):

    def __init__(self, stages, instances):
		PoE.__init__(self, stages, instances)


        ##Stage1:GROMPP 
    def stage_1(self, instance):
        k1 = Kernel(name="md.gromacs")
	k1.upload_input_data  = ['in.gro', 'in.top', '*.itp', 'in.mdp'] 
        k1.executable = ['path/to/gromacs/gmx']
        k1.arguments = ['grompp', '-f', 'in.mdp', '-c', 'in.gro', '-o', 'in.tpr', '-p', 'in.top']
        k1.cores = 1
        
        return k1


        ##Stage2:MDRUN
    def stage_2(self, instance):
        k2 = Kernel(name="md.gromacs")
        k2.link_input_data = ['$STAGE_1/in.tpr > in.tpr']
        k2.executable = ['path/to/gromacs/gmx']    
        k2.arguments = ['mdrun', '-s', 'in.tpr', '-deffnm', 'out']
        k2.cores = 1              
        
        return k2

        ##Stage3:Exchange
    #def stage_3(self,instance):
        #k3 = Kernel(name="exchange")
        #### Explicitly define and instantiate Exchange method, for now, exchange is hard-coded

          







# ------------------------------------------------------------------------------
#
if __name__ == "__main__":

	# use the resource specified as argument, fall back to localhost
	if   len(sys.argv)  > 2: 
		print 'Usage:\t%s [resource]\n\n' % sys.argv[0]
		sys.exit(1)
	elif len(sys.argv) == 2: 
		resource = sys.argv[1]
	else: 
		resource = 'local.localhost'

	try:

		with open('%s/config.json'%os.path.dirname(os.path.abspath(__file__))) as data_file:    
			config = json.load(data_file)

		# Create a new resource handle with one resource and a fixed
		# number of cores and runtime.
		cluster = ResourceHandle(
				resource=resource,
				cores=config[resource]["cores"],
				walltime=15,
				#username=None,

				project=config[resource]['project'],
				access_schema = config[resource]['schema'],
				queue = config[resource]['queue'],
				#database_url='mongodb://138.201.86.166:27017/ee_exp_4c',
			)

		# Allocate the resources. 
		cluster.allocate()

		# Set the 'instances' of the pipeline to 16. This means that 16 instances
		# of each pipeline stage are executed.
		#
		# Execution of the 16 pipeline instances can happen concurrently or
		# sequentially, depending on the resources (cores) available in the
		# SingleClusterEnvironment.
		ccount = RunExchange(stages=3,instances=2)

		cluster.run(ccount)

		

	except EnsemblemdError, er:

		print "Ensemble MD Toolkit Error: {0}".format(str(er))
		raise # Just raise the execption again to get the backtrace

	try:
		cluster.deallocate()
	except:
		pass
