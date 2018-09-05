import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import os
import tarfile
import writeInputs
import time
import writeInputs

class Replica(object):

    #A replica class to hold replica information

    def __init__(self, rid, Temp, EPtot, rstate):
        self.rid    = rid     #Replica ID
        self.Temp   = Temp    #Replica Temp
        self.EPtot  = EPtot   #Replica Potential Energy
        self.rstate = rstate  #Replica State




class GROMACSTask(Task):

    # GROMACS specific MD task class

    def __init__(self, cores, mpi=True):

        super(GROMACSTask, self).__init__()
        self._executable = ['']
        self._cores      = cores
        self._pre_exec   = ['module load gromacs']
        self._post_exec = ['gmx energy < Energy.input'] 
        self._mpi        = mpi
                                                            
                                        


class AMBERTask(Task):

    # AMBER specific MD task class.
    
    def __init__(self, MD_Executable, cores):
                 
        super(AMBERTask, self).__init__()
        #self._executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI']
        self._executable = [MD_Executable]
        #self._cpu_reqs['processes']   = cores
        #self._cpu_reqs['process_type'] = '' 
        self._cpu_reqs = { 
                            'processes': cores,
                            'process_type': '',
                            'threads_per_process': 1,
                            'thread_type': None
                        }
        #self._lfs_per_process = 4096
        #self._pre_exec   = ['module load amber'] #For BW make a pre-exec that points to $AMBERHOME correctly  ['export AMBERHOME=$HOME/amber/amber14/']
        #self._post_exec = [''] #Post exec is not useful here, but may be useful for something like a GROMACS class...
        

    
class SynchronousExchange(object):

    """ 
    Defines the Synchronous Replica Exchange Workflow. InitCycle() creates the workflow for the first cycle, i.e. 
    the first MD phase and the subsequent exchange computation. GeneralCycle() then creates the workflows for all 
    subsequent cycles. Each cycle (MD plus immediate exchange computation) must be specified as separate workflows.                                        
    """
    
   


    def __init__(self):
        
       
        self.Book = [] #Bookkeeping, maintains a record of all MD tasks carried out
        self.md_task_list = []
        self.ex_task_list = []
        #self.test = 1

        self._uid = ru.generate_id('radical.repex.syncex')
        self._logger = ru.get_logger('radical.repex.syncex')
        self._prof = ru.Profiler(name=self._uid)
        self._prof.prof('Initinit', uid=self._uid)
 
        

    def Replica_Init(self,Replicas):

        #Nothing actually happens to a replica object here, this is just bookkeeping
        #potentially for a state/event model in the future

        Replica_List=dict()

        for r in range(Replicas):
            Replica_List[r] = Replica
            (Replica_List[r]).rstate = 'I' #Initialize with idle state
            
            
           


    def InitCycle(self, Replicas, Replica_Cores, MD_Executable, ExchangeMethod, timesteps, Basename): # "Cycle" = 1 MD stage plus the subsequent exchange computation

        """ 
        Initial cycle consists of:
        1) Create tarball of MD input data 
        2) Transfer the tarball to pilot sandbox
        3) Untar the tarball
        4) Run first Cycle
        """    
        
        #Initialize Pipeline
        #self._prof.prof('InitTar', uid=self._uid)
        p = Pipeline()
        p.name = 'initpipeline'

        md_dict    = dict() #Bookkeeping
        tar_dict   = dict() #Bookkeeping

        ##Write the input files

        self._prof.prof('InitWriteInputs', uid=self._uid)

                             

        writeInputs.writeInputs(max_temp=350,min_temp=250,replicas=Replicas,timesteps=timesteps, basename=Basename)

        self._prof.prof('EndWriteInputs', uid=self._uid)

        
        self._prof.prof('InitTar', uid=self._uid)
        #Create Tarball of input data

        tar = tarfile.open("Input_Files.tar","w")
        for name in [Basename+".prmtop", 
                     Basename+".inpcrd", 
                     Basename+".mdin"]:
            tar.add(name)
        for r in range (Replicas):
            tar.add('mdin_{0}'.format(r))
        tar.close()

        #delete all input files outside the tarball

        for r in range (Replicas):
            os.remove('mdin_{0}'.format(r))

        self._prof.prof('EndTar', uid=self._uid)

                
        #Create Untar Stage

        untar_stg = Stage()
        untar_stg.name = 'untarStg'
    
        #Untar Task

        untar_tsk                   = Task()
        untar_tsk.name              = 'untartsk'
        untar_tsk.executable        = ['python']
        
        untar_tsk.upload_input_data = ['untar_input_files.py','Input_Files.tar']
        untar_tsk.arguments         = ['untar_input_files.py','Input_Files.tar']
        untar_tsk.cpu_reqs          = 1
        #untar_tsk.post_exec         = ['']
        untar_stg.add_tasks(untar_tsk)
        p.add_stages(untar_stg)

             
        tar_dict[0] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.name,
                                                       untar_stg.name,
                                                       untar_tsk.name)
                 


        # First MD stage: needs to be defined separately since workflow is not built from a predetermined order

        md_stg = Stage()
        md_stg.name = 'mdstg0'
        self._prof.prof('InitMD_0', uid=self._uid)
        
        # MD tasks
               
        for r in range (Replicas):

            
            md_tsk                  = AMBERTask(cores=Replica_Cores, MD_Executable=MD_Executable)
            md_tsk.name             = 'mdtsk-{replica}-{cycle}'.format(replica=r,cycle=0)
            #md_tsk.pre_exec         = ['module load amber']
            md_tsk.link_input_data += [
                                       '%s/inpcrd'%tar_dict[0],
                                       '%s/prmtop'%tar_dict[0],
                                       '%s/mdin_{0}'.format(r)%tar_dict[0]  #Use for full temperature exchange
                                       ] 
            md_tsk.arguments        = ['-O',  
                                       '-p',  'prmtop', 
                                       '-i',  'mdin_{0}'.format(r), 
                                       '-c',  'inpcrd',
                                       '-o',  'out-{replica}-{cycle}'.format(replica=r,cycle=0),
                                       '-r',  'restrt'.format(replica=r,cycle=0), 
                                       #'-r',  'rstrt-{replica}-{cycle}'.format(replica=r,cycle=0), 
                                       '-x',  'mdcrd-{replica}-{cycle}'.format(replica=r,cycle=0),
                                       #'-o',  '$NODE_LFS_PATH/out-{replica}-{cycle}'.format(replica=r,cycle=0),
                                       #'-r',  '$NODE_LFS_PATH/rstrt-{replica}-{cycle}'.format(replica=r,cycle=0), 
                                       #'-x',  '$NODE_LFS_PATH/mdcrd-{replica}-{cycle}'.format(replica=r,cycle=0),
                                       '-inf','mdinfo_{0}'.format(r)]
            md_dict[r]              = '$Pipeline_%s_Stage_%s_Task_%s'%(p.name, md_stg.name, md_tsk.name)

            md_stg.add_tasks(md_tsk)
            self.md_task_list.append(md_tsk)
            #print md_tsk.uid
        p.add_stages(md_stg)
        #stage_uids.append(md_stg.uid)
                                                    

        # First Exchange Stage
        
        ex_stg = Stage()
        ex_stg.name = 'exstg0'
        self._prof.prof('InitEx_0', uid=self._uid)
        #with open('logfile.log', 'a') as logfile:
         #   logfile.write( '%.5f' %time.time() + ',' + 'InitEx0' + '\n')
        # Create Exchange Task. Exchange task performs a Metropolis Hastings thermodynamic balance condition
        # check and spits out the exchangePairs.dat file that contains a sorted list of ordered pairs. 
        # Said pairs then exchange configurations by linking output configuration files appropriately.

        ex_tsk                      = Task()
        ex_tsk.name                 = 'extsk0'
        #ex_tsk.pre_exec             = ['module load python/2.7.10']
        ex_tsk.executable           = ['/usr/bin/python']
        ex_tsk.upload_input_data    = [ExchangeMethod]  
        for r in range (Replicas):
            ex_tsk.link_input_data     += ['%s/mdinfo_%s'%(md_dict[r],r)]
        ex_tsk.arguments            = ['TempEx.py','{0}'.format(Replicas), '0']
        ex_tsk.cores                = 1
        ex_tsk.mpi                  = False
        ex_tsk.download_output_data = ['exchangePairs_0.dat']
        ex_stg.add_tasks(ex_tsk)
        #task_uids.append(ex_tsk.uid)
        p.add_stages(ex_stg)
        self.ex_task_list.append(ex_tsk)
        #self.ex_task_uids.append(ex_tsk.uid)
        self.Book.append(md_dict)
        return p

                                                                                        
    def GeneralCycle(self, Replicas, Replica_Cores, Cycle, MD_Executable, ExchangeMethod):

        """
        All cycles after the initial cycle
        Pulls up exchange pairs file and generates the new workflow
        """


        self._prof.prof('InitcreateMDwokflow_{0}'.format(Cycle), uid=self._uid)
        with open('exchangePairs_{0}.dat'.format(Cycle),'r') as f:  # Read exchangePairs.dat
            ExchangeArray = []
            for line in f:
                ExchangeArray.append(int(line.split()[1]))
                #ExchangeArray.append(line)
                #print ExchangeArray
                    

        q = Pipeline()
        q.name = 'genpipeline{0}'.format(Cycle)
        #Bookkeeping
        stage_uids = list()
        task_uids = list() ## = dict()
        md_dict = dict()


        #Create MD stage


        md_stg = Stage()
        md_stg.name = 'mdstage{0}'.format(Cycle)

        self._prof.prof('InitMD_{0}'.format(Cycle), uid=self._uid)
    
        for r in range (Replicas):
            md_tsk                 = AMBERTask(cores=Replica_Cores, MD_Executable=MD_Executable)
            md_tsk.name            = 'mdtsk-{replica}-{cycle}'.format(replica=r,cycle=Cycle)
            md_tsk.link_input_data = ['%s/restrt > inpcrd'%(self.Book[Cycle-1][ExchangeArray[r]]),
                                      '%s/prmtop'%(self.Book[0][r]),
                                      '%s/mdin_{0}'.format(r)%(self.Book[0][r])]
            
            
            ### The Following softlinking scheme is to be used ONLY if node local file system is to be used: not fully supported yet.
            #md_tsk.link_input_data = ['$NODE_LFS_PATH/rstrt-{replica}-{cycle}'.format(replica=ExchangeArray[r],cycle=Cycle-1) > '$NODE_LFS_PATH/inpcrd',
            #                          #'%s/restrt > inpcrd'%(self.Book[Cycle-1][ExchangeArray[r]]),
            #                          '%s/prmtop'%(self.Book[0][r]),
            #                          '%s/mdin_{0}'.format(r)%(self.Book[0][r])]

            md_tsk.arguments      = ['-O', 
                                     '-i', 'mdin_{0}'.format(r), 
                                     '-p', 'prmtop', 
                                     '-c', 'inpcrd',
                                     #'-c', 'rstrt-{replica}-{cycle}'.format(replica=r,cycle=Cycle-1),  
                                     '-o', 'out-{replica}-{cycle}'.format(replica=r,cycle=Cycle),
                                     '-r', 'rstrt-{replica}-{cycle}'.format(replica=r,cycle=Cycle),
                                     '-x', 'mdcrd-{replica}-{cycle}'.format(replica=r,cycle=Cycle),
                                     '-inf', 'mdinfo_{0}'.format(r)]
            #md_tsk.tag              = 'mdtsk-{replica}-{cycle}'.format(replica=r,cycle=0)
            md_dict[r]             = '$Pipeline_%s_Stage_%s_Task_%s'%(q.name, md_stg.name, md_tsk.name)
            self.md_task_list.append(md_tsk)
            md_stg.add_tasks(md_tsk)
        

        
        q.add_stages(md_stg)
                 
                                                                                            
                                                                                              
        ex_stg = Stage()
        ex_stg.name = 'exstg{0}'.format(Cycle+1)

        #Create Exchange Task
        ex_tsk                      = Task()
        ex_tsk.name                 = 'extsk{0}'.format(Cycle+1)
        ex_tsk.executable           = ['/usr/bin/python']#['/opt/python/bin/python']
        ex_tsk.upload_input_data    = [ExchangeMethod]
        for r in range (Replicas):

            ex_tsk.link_input_data += ['%s/mdinfo_%s'%(md_dict[r],r)]

        ex_tsk.arguments            = ['TempEx.py','{0}'.format(Replicas), '{0}'.format(Cycle+1)]
        ex_tsk.cores                = 1
        ex_tsk.mpi                  = False
        ex_tsk.download_output_data = ['exchangePairs_{0}.dat'.format(Cycle+1)] # Finds exchange partners, also  Generates exchange history trace

        ex_stg.add_tasks(ex_tsk)

        #task_uids.append(ex_tsk.uid)
        self.ex_task_list.append(ex_tsk)

        q.add_stages(ex_stg)

        #stage_uids.append(ex_stg.uid)

        self.Book.append(md_dict)
        #self._prof.prof('EndEx_{0}'.format(Cycle), uid=self._uid)
        #print d
        #print self.Book
        return q


    @property
    def totalmdlist(self):
        print 'Book is', self.Book
        return self.Book
    

    @property
    def mdtasklist(self):
        #print 'MD Task List:', self.md_task_list
        return self.md_task_list

    @property
    def extasklist(self):
        #print 'EX Task List', self.ex_task_list
        return self.ex_task_list







                            

                                                                                               
