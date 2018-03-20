import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import writeInputs
import os
import tarfile


class GROMACSTask(Task):

    # GROMACS specific MD task class, global

    def __init__(self, cores, mpi=True):

        super(GROMACSTask, self).__init__()
        self._executable = ['']
        self._cores      = cores
        self._pre_exec   = ['module load gromacs']
        self._post_exec = ['gmx energy < Energy.input'] 
        self._mpi        = mpi
                                                            
                                        


class AMBERTask(Task):

    # AMBER specific MD task class, global
    
    def __init__(self, cores, mpi=True):
                 
        super(AMBERTask, self).__init__()
        self._executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI']
        self._cores      = cores
        self._pre_exec   = ['module load amber'] #For BW make a pre-exec that points to $AMBERHOME correctly  ['export AMBERHOME=$HOME/amber/amber14/']
        #self._post_exec = [''] #Post exec is not useful here, but may be useful for something like a GROMACS class...
        self._mpi        = mpi

    
class Replica(object):

    """ 
    Defines the Replica object. replicaInit() is a class method that creates the workflow for the first cycle, i.e. 
    the setup and  first MD phase.  Exchange() is the exchange method. MD() is the MD method.                                         
    """
    
   


    def __init__(self):
        
       
        self.replica_id = replica_id   
        self.rstate = 'I'

    def replicaInit(self,replicas):

        #Nothing actually happens to a replica object here, this is just bookkeeping
        #potentially for a state/event model in the future

        #Replica_List[r]).rstate = 'I' #Initialize with idle state
            
            
           


    def init_replica(self, replicas, replica_cores, mdExecutable, exchangeMethod):     # "Cycle" = 1 MD stage plus the subsequent exchange computation

        """ 
        Initial cycle consists of:
        1) Create tarball of MD input data 
        2) Transfer the tarball to pilot sandbox
        3) Untar the tarball
        4) Run first MD Cycle
        """    
        
        #Initialize Pipeline
        
        p = Pipeline()

        md_dict    = dict() #Bookkeeping
        tar_dict   = dict() #Bookkeeping

        ##Write the input files

        writeInputs.writeInputs(max_temp=400 ,min_temp=200 ,replicas=replicas,timesteps=1000)       


        #Create Tarball of input data

        tar = tarfile.open("Input_Files.tar","w")
        for name in ["prmtop", "inpcrd"]:
            tar.add(name)
        for r in range (replicas):
            tar.add('mdin_{0}'.format(r))
        tar.close()

        #Delete all mdin files from local (they're in the tarball, no need to have them around)

        for r in range(replicas)
            os.remove('mdin_{0}'.format(r))
        
        #Create Untar Stage

        untar_stg = Stage()
        #self._prof.prof('InitTar', uid=self._uid)
        #Untar Task

        untar_tsk                   = Task()
        untar_tsk.executable        = ['python']
        
        untar_tsk.upload_input_data = ['untar_input_files.py','Input_Files.tar']
        untar_tsk.arguments         = ['untar_input_files.py','Input_Files.tar']
        untar_tsk.cores             = 1

        untar_stg.add_tasks(untar_tsk)
        p.add_stages(untar_stg)

             
        tar_dict[0] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid,
                                                       untar_stg.uid,
                                                       untar_tsk.uid)
                 


        # First MD stage: needs to be defined separately since workflow is not built from a predetermined order


    def md(self,replica_cores,replica_id):
        
        md_stg = Stage()
    
        md_tsk                  = AMBERTask(cores=replica_cores)
        md_tsk.link_input_data += [
                                   '%s/inpcrd'%tar_dict[0],
                                   '%s/prmtop'%tar_dict[0],
                                   '%s/mdin_{0}'.format(r)%tar_dict[0]]
                                      
        md_tsk.arguments        = ['-O','-p','prmtop', '-i','mdin_{0}'.format(replica_id), # Use this for full Temperature Exchange
                                   '-c','inpcrd','-o','out_{0}'.format(replica_id),
                                   '-inf','mdinfo_{0}'.format(replica_id)]
        md_dict[r]              = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)

        md_stg.add_tasks(md_tsk)
        self.md_task_list.append(md_tsk.uid)
        #p.add_stages(md_stg)
        #stage_uids.append(md_stg.uid)
                                                    

    def exchange(self, Replicas, ):
        # First Exchange Stage
        
        ex_stg = Stage()
        #self._prof.prof('InitEx_0', uid=self._uid)
        # Create Exchange Task. Exchange task performs a Metropolis Hastings thermodynamic balance condition
        # check and spits out the exchangePairs.dat file that contains a sorted list of ordered pairs. 
        # Said pairs then exchange configurations by linking output configuration files appropriately.

        ex_tsk                      = Task()
        ex_tsk.executable           = ['python']
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
        self.ex_task_list.append(ex_tsk.uid)
        self.Book.append(md_dict)
        return p

                                                                                        
    def GeneralCycle(self, Replicas, Replica_Cores, Cycle, MD_Executable, ExchangeMethod):

        """
        All cycles after the initial cycle
        Pulls up exchange pairs file and generates the new workflow
        """


        
        with open('exchangePairs_{0}.dat'.format(Cycle),'r') as f:  # Read exchangePairs.dat
            ExchangeArray = []
            for line in f:
                ExchangeArray.append(int(line.split()[1]))
                #ExchangeArray.append(line)
                #print ExchangeArray
                    

        q = Pipeline()
        #Bookkeeping
        stage_uids = list()
        task_uids = list() ## = dict()
        md_dict = dict()


        #Create initial MD stage


        md_stg = Stage()
        #self._prof.prof('InitMD_{0}'.format(Cycle), uid=self._uid)
        for r in range (Replicas):
            md_tsk                 = AMBERTask(cores=Replica_Cores)
            md_tsk.link_input_data = ['%s/restrt > inpcrd'%(self.Book[Cycle-1][ExchangeArray[r]]),
                                      '%s/prmtop'%(self.Book[0][r]),
                                      #'%s/prmtop'%(self.Tarball_path[0]),
                                      #'%s/mdin_{0}'.format(r)%(self.Book[k-1][r])]

                                      '%s/mdin'%(self.Book[0][r])]
                                      #'%s/mdin'%(self.Tarball_path[0])]

            #md_tsk.arguments      = ['-O', '-i', 'mdin_{0}'.format(r), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(r),'-inf', 'mdinfo_{0}'.format(r)]
            md_tsk.arguments       = ['-O', '-i', 'mdin', '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(r),'-inf', 'mdinfo_{0}'.format(r)]
            md_dict[r]             = '$Pipeline_%s_Stage_%s_Task_%s'%(q.uid, md_stg.uid, md_tsk.uid)
            self.md_task_list.append(md_tsk.uid)
            md_stg.add_tasks(md_tsk)
        

        
        q.add_stages(md_stg)
                 
                                                                                            
                                                                                              
        ex_stg = Stage()

        #Create Exchange Task
        ex_tsk                      = Task()
        ex_tsk.executable           = ['python']
        ex_tsk.upload_input_data    = [ExchangeMethod]
        for r in range (Replicas):

            ex_tsk.link_input_data += ['%s/mdinfo_%s'%(md_dict[r],r)]

        ex_tsk.arguments            = ['TempEx.py','{0}'.format(Replicas), '{0}'.format(Cycle+1)]
        ex_tsk.cores                = 1
        ex_tsk.mpi                  = False
        ex_tsk.download_output_data = ['exchangePairs_{0}.dat'.format(Cycle+1)] # Finds exchange partners, also  Generates exchange history trace

        ex_stg.add_tasks(ex_tsk)

        #task_uids.append(ex_tsk.uid)
        self.ex_task_list.append(ex_tsk.uid)

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







                            

                                                                                               
