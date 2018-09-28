#!/usr/bin/env python

import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import os
import tarfile
import writeInputs
import time
import git




def setup_replicas(self, replicas, min_temp, max_temp, timesteps, basename):

    writeInputs.writeInputs(max_temp=max_temp, min_temp=min_temp, replicas=replicas, timesteps=timesteps, basename=basename)
    tar = tarfile.open("input_files.tar", "w")
    for name in [basename + ".prmtop", basename + ".inpcrd", basename + ".mdin"]:
        tar.add(name)
    for r in range(replicas):
        tar.add('mdin_{0}'.format(r))
    tar.close()
    for r in range(replicas):
        os.remove('mdin_{0}'.format(r))



    setup_p = Pipeline()
    setup_p.name = 'setup_pipeline'

    repo = git.Repo('.', search_parent_directories=True)
    aux_function_path = repo.working_tree_dir


    untar_stg = Stage()
    untar_stg.name = 'untarStg'

    #Untar Task
        
    untar_tsk = Task()
    untar_tsk.name = 'untartsk'
    untar_tsk.executable = ['python']
    untar_tsk.upload_input_data = [str(aux_function_path)+'/repex/untar_input_files.py', 'Input_Files.tar']
    untar_tsk.arguments = ['untar_input_files.py', 'Input_Files.tar']
    untar_tsk.cpu_reqs = 1
    untar_tsk.post_exec = ['']
    untar_stg.add_tasks(untar_tsk)
    setup_p.add_stages(untar_stg)


    return setup_p




def init_replicas(self, replicas, replica_cores, md_executable, exchange_method, min_temp, max_temp, timesteps):


