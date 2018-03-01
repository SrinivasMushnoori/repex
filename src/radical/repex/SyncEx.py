import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import os
import tarfile


class Replica(object):

    #A replica class to hold replica information, potentially useful for replica states in asynchronous exchange

    def __init__(self, rid, Temp, EPtot, rstate):
        self.rid    = rid     #Replica ID
        self.Temp   = Temp    #Replica Temp
        self.EPtot  = EPtot   #Replica Potential Energy
        self.rstate = rstate  #Replica State




class GROMACSTask(Task):

    # GROMACS specific MD task class

    def __init__(self, cores, mpi=True):

        super(GROMACSTask, self).__init__()
        self.executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI']
        self.cores      = cores
        self.pre_exec   = ['module load amber']
        #self.post_exec = [''] #Post exec is not useful here, but may be useful for something like a GROMACS class...
        self.mpi        = mpi
                                                            
                                        


class AMBERTask(Task):

    # AMBER specific MD task class.
    
    def __init__(self, cores, mpi=True):
                 
        super(AMBERTask, self).__init__()
        self.executable = ['/usr/local/packages/amber/16/INTEL-140-MVAPICH2-2.0/bin/pmemd.MPI']
        self.cores      = cores
        self.pre_exec   = ['module load amber']
        #self.post_exec = [''] #Post exec is not useful here, but may be useful for something like a GROMACS class...
        self.mpi        = mpi

    
class SynchronousExchange(AMBERTask,Replica):

    """ 
    Defines the Synchronous Replica Exchange Workflow. InitCycle() creates the workflow for the first cycle, i.e. 
    the first MD phase and the subsequent exchange computation. GeneralCycle() then creates the workflows for all 
    subsequent cycles. Each cycle (MD plus immediate exchange computation) must be specified as separate workflows.                                        
    """
    
   


    def __init__(self):
        
       
        self.Book = [] #Bookkeeping, maintains a record of all MD tasks carried out

    def Replica_Init(self,Replicas):

        Replica_List=dict()

        for r in range(Replicas):
            Replica_List[r] = Replica
            (Replica_List[r]).rstate = 'I' #Initialize with idle state
            
            
           


    def InitCycle(self, Replicas, Replica_Cores, MD_Executable, ExchangeMethod):     # "Cycle" = 1 MD stage plus the subsequent exchange computation

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

        md_dict    = dict() #Bookkeeping
        tar_dict   = dict() #Bookkeeping


        #Create Tarball of input data

        tar = tarfile.open("Input_Files.tar","w")
        for name in ["prmtop", "inpcrd", "mdin"]:
            tar.add(name)
        #for r in range (Replicas):
            #tar.add('mdin_{0}'.format(r))
        tar.close()
        
        
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

        md_stg = Stage()
        #self._prof.prof('InitMD_0', uid=self._uid)

        # MD tasks

        #For all replicas, link MD run input files from the Untar directory


        #Note to self: I should probably create an MD Task class in order to abstract the MD engine details....

        #Replica_List=[]
        
        for r in range (Replicas):

            
            md_tsk                  = AMBERTask(cores=Replica_Cores)
            md_tsk.link_input_data += [
                                       '%s/inpcrd'%tar_dict[0],
                                       '%s/prmtop'%tar_dict[0],
                                       #'%s/mdin_{0}'.format(r)%tar_dict[0]  #Use for full temperature exchange
                                       '%s/mdin'%tar_dict[0]  #Testing only
                                       ] 
            #md_tsk.pre_exec         = ['export AMBERHOME=$HOME/amber/amber14/'] #Should be abstracted from the user?
            md_tsk.arguments        = ['-O','-p','prmtop', '-i', 'mdin',        #'mdin_{0}'.format(r), # Use this for full Temperature Exchange
                                       '-c','inpcrd','-o','out_{0}'.format(r),
                                       '-inf','mdinfo_{0}'.format(r)]
            md_dict[r]              = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)

            md_stg.add_tasks(md_tsk)
            #task_uids.append(md_tsk.uid)
        p.add_stages(md_stg)
        #stage_uids.append(md_stg.uid)
                                                    

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
        #stage_uids.append(ex_stg.uid)
        self.Book.append(md_dict)
        #print self.Book
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
            md_tsk                 = Task()
            md_tsk.executable      = [MD_Executable]  #MD Engine, Blue Waters
            md_tsk.link_input_data = ['%s/restrt > inpcrd'%(self.Book[Cycle-1][ExchangeArray[r]]),
                                      '%s/prmtop'%(self.Book[0][r]),
                                      #'%s/prmtop'%(self.Tarball_path[0]),
                                      #'%s/mdin_{0}'.format(r)%(self.Book[k-1][r])]

                                      '%s/mdin'%(self.Book[0][r])]
                                      #'%s/mdin'%(self.Tarball_path[0])]

            #md_tsk.pre_exec        = ['export AMBERHOME=$HOME/amber/amber14/'] # Should be abstracted from user?
            md_tsk.pre_exec       = ['module load amber']
            #md_tsk.arguments      = ['-O', '-i', 'mdin_{0}'.format(r), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(r),'-inf', 'mdinfo_{0}'.format(r)]
            md_tsk.arguments       = ['-O', '-i', 'mdin', '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(r),'-inf', 'mdinfo_{0}'.format(r)]
            md_tsk.cores           = Replica_Cores
            md_tsk.mpi             = True
            md_dict[r]             = '$Pipeline_%s_Stage_%s_Task_%s'%(q.uid, md_stg.uid, md_tsk.uid)
            md_stg.add_tasks(md_tsk)

            #task_uids.append(md_tsk.uid)
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

        q.add_stages(ex_stg)

        #stage_uids.append(ex_stg.uid)

        self.Book.append(md_dict)

        #self._prof.prof('EndEx_{0}'.format(Cycle), uid=self._uid)
        #print d
            #print self.Book
        return q


    def mdtasklist():
        return self.md_task_list
 
    def extasklist():
        return self.ex_task_list







                            

                                                                                               
