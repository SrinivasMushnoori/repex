import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import os, tarfile, glob, time, git
import writeInputs

class Replica(object):

    #A replica class to hold replica information

    def __init__(self, rid, Temp, EPtot, rstate):
        self.rid = rid  #Replica ID
        self.Temp = Temp  #Replica Temp
        self.EPtot = EPtot  #Replica Potential Energy
        self.rstate = rstate  #Replica State


class GROMACSTask(Task):

    # GROMACS specific MD task class

    def __init__(self, md_executable, cores, pre_exec):

        super(GROMACSTask, self).__init__()
        self._executable = [md_executable]
        self._cpu_reqs = {
            'processes': cores,
            'process_type': '',
            'threads_per_process': 1,
            'thread_type': None
        }
        #self._pre_exec = ['grompp'] ### Set at individual task level
        #self._post_exec = ['gmx energy -f *.edr -o out.xvg -b 1000000 < inp.ener'] ### Set at individual task level
        #self._mpi = mpi


class AMBERTask(Task):

    # AMBER specific MD task class.

    def __init__(self, md_executable, cores, pre_exec):

        super(AMBERTask, self).__init__()
        self._executable = [md_executable]
        self._cpu_reqs = {
            'processes': cores,
            'process_type': '',
            'threads_per_process': 1,
            'thread_type': None
        }
        self._pre_exec   = [pre_exec] #For BW make a pre-exec that points to $AMBERHOME correctly  ['export AMBERHOME=$HOME/amber/amber14/']
        #self._post_exec = [''] #Post exec is not useful here, but may be useful for something like a GROMACS class...


class SynchronousExchange(object):
    """ 
    Defines the Synchronous Replica Exchange Workflow. init_cycle() creates the workflow for the first cycle, i.e. 
    the first MD phase and the subsequent exchange computation. general_cycle() then creates the workflows for all 
    subsequent cycles. Each cycle (MD plus immediate exchange computation) must be specified as separate workflows.                                        
    """

    def __init__(self):

        self.book = [
        ]  #bookkeeping, maintains a record of all MD tasks carried out
        self.md_task_list = []
        self.ex_task_list = []


        self._uid = ru.generate_id('radical.repex.syncex')
        self._logger = ru.get_logger('radical.repex.syncex')
        self._prof = ru.Profiler(name=self._uid)
        self._prof.prof('Initinit', uid=self._uid)
 
    def init_cycle(self, replicas, replica_cores, python_path, md_executable, exchange_method, min_temp, max_temp, timesteps, basename, pre_exec):  # "cycle" = 1 MD stage plus the subsequent exchange computation
        """ 
        Initial cycle consists of:
        1) Create tarball of MD input data 
        2) Transfer the tarball to pilot sandbox
        3) Untar the tarball
        4) Run first cycle
        """

        #Initialize Pipeline
        self._prof.prof('InitTar', uid=self._uid)
        p = Pipeline()
        p.name = 'initpipeline'

        md_dict = dict()  #bookkeeping
        tar_dict = dict()  #bookkeeping

        #Write the input files

        self._prof.prof('InitWriteInputs', uid=self._uid)

        writeInputs.writeInputs(
            max_temp=max_temp,
            min_temp=min_temp,
            replicas=replicas,
            timesteps=timesteps,
            basename=basename)

        tar = tarfile.open("input_files.tar", "w")
        for name in glob.glob('*.itp')+glob.glob('*.gro')+glob.glob('*.top')+glob.glob('*.ener'): #this line has been edited for gromacs
            tar.add(name)
        for r in range(replicas):
            tar.add('replica_{0}.mdp'.format(r))
        tar.close()

        #delete all input files outside the tarball

        for r in range(replicas):
            os.remove('replica_{0}.mdp'.format(r))

   

        #Create Untar Stage

        repo = git.Repo('.', search_parent_directories=True)
        aux_function_path = repo.working_tree_dir


        untar_stg = Stage()
        untar_stg.name = 'untarStg'

        #Untar Task
        
        untar_tsk = Task()
        untar_tsk.name = 'untartsk'
        untar_tsk.executable = ['python']

        untar_tsk.upload_input_data = [str(aux_function_path)+'/repex/untar_input_files.py', 'input_files.tar']
        untar_tsk.arguments = ['untar_input_files.py', 'input_files.tar']
        untar_tsk.cpu_reqs = 1
        untar_stg.add_tasks(untar_tsk)
        p.add_stages(untar_stg)

        tar_dict[0] = '$Pipeline_%s_Stage_%s_Task_%s' % (p.name, untar_stg.name, untar_tsk.name)

        # First MD stage: needs to be defined separately since workflow is not built from a predetermined order, also equilibration needs to happen first. 

        md_stg = Stage()
        md_stg.name = 'mdstg0'
        self._prof.prof('InitMD_0', uid=self._uid)

        # MD tasks
        md_engine = "GROMACS"

        for r in range(replicas):
            
            if md_engine is "AMBER":
                md_tsk = AMBERTask(cores=replica_cores, md_executable=md_executable, pre_exec=pre_exec)
            elif md_engine is "GROMACS":
                md_tsk = GROMACSTask(cores=replica_cores, md_executable=md_executable, pre_exec=pre_exec)
            md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(replica=r, cycle=0)
            md_tsk.link_input_data += [
                '%s/FF.gro' % tar_dict[0],
                '%s/FF.top' % tar_dict[0],
                '%s/FF.itp' % tar_dict[0],
                '%s/martini_v2.2.itp' % tar_dict[0],
                '%s/replica_{0}.mdp'.format(r) % tar_dict[0],  #Use for full temperature exchange
                '%s/inp.ener' % tar_dict[0]
            ]
            #md_tsk.pre_exec = ['/opt/apps/intel17/impi17_0/gromacs/2016.3/bin/gmx' + ' grompp -f *.mdp -c FF.gro -o FF.tpr -p FF.top']
            md_tsk.pre_exec = [md_executable + ' grompp -f *.mdp -c FF.gro -o FF.tpr -p FF.top']
            md_tsk.arguments = [
                'mdrun','-s', 'FF.tpr', '-deffnm', '%s/FF-{replica}-{cycle}'.format(replica=r, cycle=0)%tar_dict[0], '-c', 'FF-out.gro', '-e', 'ener.edr'
                #'-p',
                #'prmtop',
                #'-i',
                #'mdin_{0}'.format(r),
                #'-c',
                #'inpcrd',
                #'-o',
                #'out-{replica}-{cycle}'.format(replica=r, cycle=0),
                #'-r',
                #'restrt'.format(replica=r, cycle=0),
                #'-x',
                #'mdcrd-{replica}-{cycle}'.format(replica=r, cycle=0),
                #'-inf',
                #'mdinfo_{0}'.format(r)
            ]
            #####In the next line I multiply the timesteps with size of 1 timestep. This should be user input. 
            #md_tsk.download_output_data = ['FF-out.gro']
            md_tsk.post_exec = [md_executable + ' energy -f *.edr -b {timesteps}'.format(timesteps=timesteps*0.025)+' < inp.ener > '+'mdinfo_{replica}'.format(replica=r)]
            md_dict[r] = '$Pipeline_%s_Stage_%s_Task_%s' % (
                p.name, md_stg.name, md_tsk.name)

            md_stg.add_tasks(md_tsk)
            self.md_task_list.append(md_tsk)
            #print md_tsk.uid
        p.add_stages(md_stg)
        #stage_uids.append(md_stg.uid)

        # First Exchange Stage

        ex_stg = Stage()
        ex_stg.name = 'exstg0'
        self._prof.prof('InitEx_0', uid=self._uid)

        # Create Exchange Task

        ex_tsk = Task()
        ex_tsk.name = 'extsk0'
        ex_tsk.executable = [python_path]
        ex_tsk.upload_input_data = [exchange_method]
        for r in range(replicas):
            ex_tsk.link_input_data += ['%s/mdinfo_%s' % (md_dict[r], r)]
        ex_tsk.pre_exec = [
                           'export LD_LIBRARY_PATH=/opt/intel/intelpython2/lib', 
                           'mv *.py exchange_method.py']
        ex_tsk.arguments = ['exchange_method.py', '{0}'.format(replicas), '0']
        ex_tsk.cores = 1
        ex_tsk.mpi = False
        ex_tsk.download_output_data = ['exchangePairs_0.dat']
        ex_stg.add_tasks(ex_tsk)
        #task_uids.append(ex_tsk.uid)
        p.add_stages(ex_stg)
        self.ex_task_list.append(ex_tsk)
        #self.ex_task_uids.append(ex_tsk.uid)
        self.book.append(md_dict)
        return p
         #def general_cycle(replicas, replica_cores, cycle, python_path, md_executable, exchange_method, pre_exec): 
    def general_cycle(self, replicas, replica_cores, cycle, python_path, md_executable, exchange_method, timesteps, pre_exec):
        """
        All cycles after the initial cycle
        Pulls up exchange pairs file and generates the new workflow
        """

        self._prof.prof('InitcreateMDwokflow_{0}'.format(cycle), uid=self._uid)
        with open('exchangePairs_{0}.dat'.format(cycle),
                  'r') as f:  # Read exchangePairs.dat
            exchange_array = []
            for line in f:
                exchange_array.append(int(line.split()[1]))
                #exchange_array.append(line)
                #print exchange_array

        q = Pipeline()
        q.name = 'genpipeline{0}'.format(cycle)
        #bookkeeping
        stage_uids = list()
        task_uids = list()  ## = dict()
        md_dict = dict()

        #Create MD stage
        md_engine = "GROMACS"
        md_stg = Stage()
        md_stg.name = 'mdstage{0}'.format(cycle)

        self._prof.prof('InitMD_{0}'.format(cycle), uid=self._uid)

        for r in range(replicas):
            if md_engine is "AMBER":
                md_tsk = AMBERTask(cores=replica_cores, md_executable=md_executable, pre_exec=pre_exec)
            elif md_engine is "GROMACS":
                md_tsk = GROMACSTask(cores=replica_cores, md_executable=md_executable, pre_exec=pre_exec)
            
            md_tsk.name = 'mdtsk-{replica}-{cycle}'.format(
                replica=r, cycle=cycle)
            md_tsk.link_input_data = [
                '%s/FF-out.gro > FF.gro' % (self.book[cycle - 1][exchange_array[r]]),
                '%s/FF.top' % (self.book[0][r]),
                '%s/FF.itp' % (self.book[0][r]),
                '%s/martini_v2.2.itp' % self.book[0][r],
                '%s/replica_{0}.mdp'.format(r) % (self.book[0][r]),
                '%s/inp.ener' % (self.book[0][r])
            ]

            ### The Following softlinking scheme is to be used ONLY if node local file system is to be used: not fully supported yet.
            #md_tsk.link_input_data = ['$NODE_LFS_PATH/rstrt-{replica}-{cycle}'.format(replica=exchange_array[r],cycle=cycle-1) > '$NODE_LFS_PATH/inpcrd',
            #                          #'%s/restrt > inpcrd'%(self.book[cycle-1][exchange_array[r]]),
            #                          '%s/prmtop'%(self.book[0][r]),
            #                          '%s/mdin_{0}'.format(r)%(self.Book[0][r])]
            md_tsk.pre_exec = [md_executable + ' grompp -f *.mdp -c FF.gro -o FF.tpr -p FF.top']
            md_tsk.arguments = ['mdrun','-s', 'FF.tpr', '-deffnm',  '%s/FF-{replica}-{cycle}'.format(replica=r, cycle=cycle)%tar_dict[0], '-c', 'FF-out.gro', '-e', 'ener.edr'
                # '-O',
                # '-i',
                # 'mdin_{0}'.format(r),
                # '-p',
                # 'prmtop',
                # '-c',
                # 'inpcrd',
                # #'-c', 'rstrt-{replica}-{cycle}'.format(replica=r,cycle=cycle-1),
                # '-o',
                # 'out-{replica}-{cycle}'.format(replica=r, cycle=cycle),
                # '-r',
                # 'restrt',
                # #'-r', 'rstrt-{replica}-{cycle}'.format(replica=r,cycle=cycle),
                # '-x',
                # 'mdcrd-{replica}-{cycle}'.format(replica=r, cycle=cycle),
                # '-inf',
                # 'mdinfo_{0}'.format(r)
            ]
            #####In the next line I multiply the timesteps with size of 1 timestep. This should be user input. 
            #md_tsk.download_output_data = ['FF-out.gro']
            md_tsk.post_exec = [md_executable + ' energy -f *.edr -b {timesteps}'.format(timesteps=timesteps*0.025)+' < inp.ener > '+'mdinfo_{replica}'.format(replica=r)]
            #md_tsk.tag              = 'mdtsk-{replica}-{cycle}'.format(replica=r,cycle=0)
            md_dict[r] = '$Pipeline_%s_Stage_%s_Task_%s' % (
                q.name, md_stg.name, md_tsk.name)
            self.md_task_list.append(md_tsk)
            md_stg.add_tasks(md_tsk)

        q.add_stages(md_stg)

        ex_stg = Stage()
        ex_stg.name = 'exstg{0}'.format(cycle + 1)

        #Create Exchange Task
        ex_tsk = Task()
        ex_tsk.name = 'extsk{0}'.format(cycle + 1)
        ex_tsk.executable = [python_path]#['/usr/bin/python']  #['/opt/python/bin/python']
        ex_tsk.upload_input_data = [exchange_method]
        for r in range(replicas):

            ex_tsk.link_input_data += ['%s/mdinfo_%s' % (md_dict[r], r)]
        ex_tsk.pre_exec = [
                           'export LD_LIBRARY_PATH=/opt/intel/intelpython2/lib',
                           'mv *.py exchange_method.py']
        ex_tsk.arguments = [
            'exchange_method.py', '{0}'.format(replicas), '{0}'.format(cycle + 1)
        ]
        ex_tsk.cores = 1
        ex_tsk.mpi = False
        ex_tsk.download_output_data = [
            'exchangePairs_{0}.dat'.format(cycle + 1)
        ]  # Finds exchange partners, also  Generates exchange history trace

        ex_stg.add_tasks(ex_tsk)

        #task_uids.append(ex_tsk.uid)
        self.ex_task_list.append(ex_tsk)

        q.add_stages(ex_stg)

        #stage_uids.append(ex_stg.uid)

        self.book.append(md_dict)
        #self._prof.prof('EndEx_{0}'.format(cycle), uid=self._uid)
        #print d
        #print self.book
        return q

    @property
    def totalmdlist(self):
        print 'book is', self.book
        return self.book

    @property
    def mdtasklist(self):
        #print 'MD Task List:', self.md_task_list
        return self.md_task_list

    @property
    def extasklist(self):
        #print 'EX Task List', self.ex_task_list
        return self.ex_task_list
