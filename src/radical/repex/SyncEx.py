import radical.utils as ru
from radical.entk import Pipeline, Stage, Task
import os


"""
Defines the Synchronous Replica Exchange Workflow. InitCycle() creates the workflow for the first cycle, i.e.
the first MD stage and the subsequent exchange computation. Cycle() then creates the workflows for all subsequent 
cycles. Each phase (MD plus immediate exchange computation) must be specified as separate workflows.
"""
Book = [] #Bookkeeping, maintains a record of all MD tasks carried out

def InitCycle(Replicas, Replica_Cores, MD_Executable, ExchangeMethod):     # "Cycle" = 1 MD stage plus the subsequent exchange computation

    #Initialize Pipeline
    p = Pipeline()

    md_dict    = dict() #Bookkeeping
    tar_dict   = dict() #Bookkeeping


    #Create Tarball of input data

        


    #Create Untar Stage
    untar_stg = Stage()
    #Untar Task
    untar_tsk                   = Task()
    untar_tsk.executable        = ['python']
    untar_tsk.upload_input_data = ['untar_input_files.py','../../Input_Files.tar']
    untar_tsk.arguments         = ['untar_input_files.py','Input_Files.tar']
    untar_tsk.cores             = 1

    untar_stg.add_tasks(untar_tsk)
    p.add_stages(untar_stg)


    tar_dict[0] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid,
                                                   untar_stg.uid,
                                                   untar_tsk.uid)
    print tar_dict[0]
    # First MD stage: needs to be defined separately since workflow is not built from a predetermined order
    md_stg = Stage()


    # MD tasks

    for r in range (Replicas):
        md_tsk                  = Task()
        md_tsk.executable       = [MD_Executable]
        md_tsk.link_input_data += ['%s/inpcrd'%tar_dict[0],
                                   '%s/prmtop'%tar_dict[0],
                                   #'%s/mdin_{0}'.format(r)%tar_dict[0]
                                   '%s/mdin'%tar_dict[0] 
                                   ] 
        md_tsk.pre_exec         = ['export AMBERHOME=$HOME/amber/amber14/'] #Should be abstracted from the user?
        md_tsk.arguments        = ['-O','-p','prmtop', '-i', 'mdin',               #'mdin_{0}'.format(r), # Use this for full Temperature Exchange
                                   '-c','inpcrd','-o','out_{0}'.format(r),
                                   '-inf','mdinfo_{0}'.format(r)]
        md_tsk.cores = Replica_Cores
        md_tsk.mpi = True
        md_dict[r] = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)

        md_stg.add_tasks(md_tsk)
        #task_uids.append(md_tsk.uid)
    p.add_stages(md_stg)
    #stage_uids.append(md_stg.uid)
                                                

    # First Exchange Stage
    ex_stg = Stage()

    # Create Exchange Task. Exchange task performs a Metropolis Hastings thermodynamic balance condition
    # and spits out the exchangePairs.dat file that contains a sorted list of ordered pairs. 
    # Said pairs then exchange configurations by linking output configuration files appropriately.

    ex_tsk                      = Task()
    ex_tsk.executable           = ['python']
    #ex_tsk.upload_input_data    = ['exchangeMethods/TempEx.py']
    ex_tsk.upload_input_data    = [ExchangeMethod]  
    for r in range (Replicas):
        ex_tsk.link_input_data     += ['%s/mdinfo_%s'%(md_dict[r],r)]
    ex_tsk.arguments            = ['TempEx.py','{0}'.format(Replicas)]
    ex_tsk.cores                = 1
    ex_tsk.mpi                  = False
    ex_tsk.download_output_data = ['exchangePairs.dat']
    ex_stg.add_tasks(ex_tsk)
    #task_uids.append(ex_tsk.uid)
    p.add_stages(ex_stg)
    #stage_uids.append(ex_stg.uid)
    Book.append(md_dict)
    #print Book
    return p

                                                                                    
def Cycle(Replicas, Replica_Cores, Cycles, MD_Executable, ExchangeMethod):

    """
    All cycles after the initial cycle
    """

    with open("exchangePairs.dat","r") as f:  # Read exchangePairs.dat
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
    for r in range (Replicas):
        md_tsk                 = Task()
        md_tsk.executable      = [MD_Executable]  #MD Engine, Blue Waters
        md_tsk.link_input_data = ['%s/restrt > inpcrd'%(Book[Cycle-1][ExchangeArray[r]]),
                                  '%s/prmtop'%(Book[Cycle-1][r]),
                                  #'%s/mdin_{0}'.format(r)%(Book[k-1][r])]
                                  '%s/mdin'%(Book[Cycle-1][r])]

        md_tsk.pre_exec        = ['export AMBERHOME=$HOME/amber/amber14/'] # Should be abstracted from user?
        #md_tsk.pre_exec       = ['module load amber']
        #md_tsk.arguments      = ['-O', '-i', 'mdin_{0}'.format(n0), '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(n0),'-inf', 'mdinfo_{0}'.format(n0)]
        md_tsk.arguments       = ['-O', '-i', 'mdin', '-p', 'prmtop', '-c', 'inpcrd', '-o', 'out_{0}'.format(r),'-inf', 'mdinfo_{0}'.format(r)]
        md_tsk.cores           = Replica_Cores
        md_tsk.mpi             = True
        md_dict[r]             = '$Pipeline_%s_Stage_%s_Task_%s'%(p.uid, md_stg.uid, md_tsk.uid)
        md_stg.add_tasks(md_tsk)

        #task_uids.append(md_tsk.uid)
    q.add_stages(md_stg)
             
                                                                                         
                                                                                          
    ex_stg= Stage()
    #Create Exchange Task
    ex_tsk = Task()
    ex_tsk.executable = ['python']
    ex_tsk.upload_input_data = ['exchangeMethods/TempEx.py']
    for n1 in range (Replicas):
        #print d[n1]

        ex_tsk.link_input_data += ['%s/mdinfo_%s'%(d[n1],n1)]

    ex_tsk.arguments = ['TempEx.py','{0}'.format(Replicas)]
    ex_tsk.cores = 1
    ex_tsk.mpi = False
    ex_tsk.download_output_data = ['exchangePairs.dat']
    ex_stg.add_tasks(ex_tsk)
    #task_uids.append(ex_tsk.uid)
    q.add_stages(ex_stg)
    #stage_uids.append(ex_stg.uid)
    Book.append(md_dict)
        #print d
        #print Book
    return q

#p = InitCycle(Replicas, Replica_Cores, MD_Executable, ExchangeMethod)
#q = Cycle(Replicas, Replica_Cores, Cycles, MD_Executable, ExchangeMethod)

#return (p, q)
                                                                            
