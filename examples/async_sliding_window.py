#!/usr/bin/env python

import os
import time
import tarfile
import writeInputs
import threading as mt

import radical.entk  as re
import radical.utils as ru

#os.environ['RADICAL_VERBOSE'] = 'INFO'
os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

os.environ['RADICAL_PILOT_DBURL'] = 'mongodb://smush:key1209@ds263816.mlab.com:63816/repex_db_2'
          #'mongodb://smush:key1209@ds141786.mlab.com:41786/repex_db_1'
           


RMQ_PORT = int(os.environ.get('RMQ_PORT', 32769))
SANDER   = ['/home/scm177/mantel/AMBER/amber14/bin/sander']

# This is the Async Implementation that uses the "sliding window" approach. 
# Two immediate actions needed: 
# 1) Remove exchanged replicas from waiting list, (Implemented, needs testing) 
# 2) The Exchange method needs ways to accept replica RID's as inputs 
# as well as the mechanism to rename appropriate files. 



# ------------------------------------------------------------------------------
#
def void():
    # entk needs callables as post_exec conditionals, even if there is nothing
    # to do...
    pass


# ------------------------------------------------------------------------------
#
class Exchange(re.AppManager):
    '''
    A ReplicaExchange class owns a number of replicas and signs responsible for
    their exchange algorthm.  G
    '''

    def __init__(self, size, exchange_size, window_size, min_cycles, min_temp, max_temp,
                 timesteps, basename, executable, cores):

        self._size          = size
        self._exchange_size = exchange_size
        self._window_size   = window_size
        self._min_cycles    = min_cycles
        self._min_temp      = min_temp
        self._max_temp      = max_temp
        self._timesteps     = timesteps
        self._basename      = basename
        self._executable    = executable
        self._cores         = cores
        self._lock          = mt.Lock()

        self._log = ru.Logger('radical.repex.exc')

        # inintialize the entk app manager
        re.AppManager.__init__(self, autoterminate=False, port=RMQ_PORT) 
        self.resource_desc = {"resource" : 'local.localhost',
                              "walltime" : 30,
                              "cpus"     : 4}                                

        # this is ugly
        self._sbox          = '$Pipeline_untarPipe_Stage_untarStg_Task_untarTsk'
        self._cnt           = 0  # count exchanges
        self._replicas      = list()
        self._waitlist      = list()
        #self._exchange_list = list()  # Sublist of self._waitlist that performs an exchange

        # create the required number of replicas
        for i in range(self._size):

            replica = Replica(check_ex  = self._check_exchange,
                              check_res = self._check_resume,
                              rid       = i,
                              sbox      = self._sbox,
                              cores     = self._cores, 
                              exe       = self._executable)

            self._replicas.append(replica)

        #@property  ### This should be a replica property
        #def ex_list(self):   
        #    return self.exchange_list

    # --------------------------------------------------------------------------
    #
    def setup(self):

        self._log.debug('exc setup')

        # prepare input for all replicas
        writeInputs.writeInputs(max_temp=self._max_temp,
                                min_temp=self._min_temp,
                                replicas=self._size,
                                timesteps=self._timesteps,
                                basename=self._basename)

        # and tar it up
        tar = tarfile.open("input_files.tar", "w")
        for name in [self._basename + ".prmtop",
                     self._basename + ".inpcrd",
                     self._basename + ".mdin"]:
            tar.add(name)

        for replica in self._replicas:
            tar.add  ('mdin-%s-0' % replica.rid) #how does this work
            os.remove('mdin-%s-0' % replica.rid)
            
        tar.close()

        # create a single pipeline with one stage to transfer the tarball
        task = re.Task()
        task.name              = 'untarTsk'
        task.executable        = ['python']
        task.upload_input_data = ['untar_input_files.py', 'input_files.tar']
        task.arguments         = ['untar_input_files.py', 'input_files.tar']
        task.cpu_reqs          = 1
        task.post_exec         = []

        stage = re.Stage()
        stage.name = 'untarStg'
        stage.add_tasks(task)

        setup = re.Pipeline()
        setup.name = 'untarPipe'
        setup.add_stages(stage)

        # run the setup pipeline
        self.workflow = set([setup]) 
        self.run() 


    # --------------------------------------------------------------------------
    #
    def execute(self):
        '''
        First stage data, then start the actual repex workload
        '''

        self.setup()

        # run the replica pipelines
        self._log.debug('exc repex')
        self.workflow = set(self._replicas)
        self.run() 


    # --------------------------------------------------------------------------
    #
    def terminate(self):

        self._log.debug('exc term')

        self.resource_terminate()


    # --------------------------------------------------------------------------
    #
    def _check_exchange(self, replica):
        '''
        add this replica to the wait list, and check if we have sufficient
        replicas for an exchange.  If no, just wait for the next one.
        If yes, we request an exchange over the collected suspended replicas
        in the waitlist.  We abuse the current replica to run that exchange
        stage for us.

        Sliding Window model: We are to only perform exchange on a sublist 
        from the waitlist of replicas. We select this sublist based on parameter
        (T in this case) proximity. Width of the sliding window is user defined. 
        This is just exchange_size. 

        Here's how it's supposed to work:

        1) Sliding window operates on global waitlist every time a new replica is added
        2) If no compatible replicas are found, Sliding window returns nothing.
        3) If a set of compatible replicas is found, an exchange list is returned and pushed immediately to the replica hosting the exchange task. 
        4) Replica should have a "get property" function to retrieve the exchange list from the exchange object.
        5) Exchange object should have a "@property" that returns the exchange list.
        '''
        
        # mark this replica for the next exchange
        # multiple replicas can trigger this, therefore lock needed
        with self._lock:

            self._waitlist.append(replica)
            self._log.debug('=== %s check exchange (%d >= %d?)', replica.rid, len(self._waitlist), self._exchange_size)
            print "waitlist is: ",[replica.rid for replica in self._waitlist]
            self._latest_replica = self._waitlist[-1]

            # Sort the waitlist as soon as a new replica is added.
        
            self._sorted_waitlist = sorted(self._waitlist, key=lambda x: x.rid) # We're sorting by RID here since RID's are assigned in sorted order with
                                                                                # Temperature (or whatever paramater is of interest to us)
        
            print "sorted waitlist is: ", [replica.rid for replica in self._sorted_waitlist]


        # Now we generate a sublist called exchange_list, within which an exchange is performed. This is done with
        # the sliding_window function



            exchange_list = self._sliding_window(self._sorted_waitlist, self._exchange_size, self._window_size)
        
            #print "exchange list returned by sliding window is: ", [rep.rid for rep in exchange_list]
            #rep = None
            
            if not exchange_list:

            #print "exchange size is ", self._exchange_size, " and exchange list length is ", len(self._exchange_list)
            # just suspend this replica and wait for the next
                self._log.debug('=== %s suspend', replica.rid)
                #print "replica ", replica.rid, " should suspend now"  # If this is triggered by the replica that has just added itself, it should 
                                                                      # not repeatedly try to suspend the same replica
                try:
                    print "latest replica is " , self._latest_replica.rid, " and should suspend now."
                    self._latest_replica.suspend()
                    #print "replica ", self._latest_replica.rid, " should suspend now" 
                except:
                    print "replica ", replica.rid, " is already suspended, moving on"
            else:
                print "adding exchange stage for replicas ", [x.rid for x in exchange_list]

                replica._add_ex_stage(exchange_list)

                for replica in exchange_list:
                    try:
                        self._sorted_waitlist.remove(replica)
                    except:
                        print "replica ", replica.rid, " isn't here."
             
    
                print "Replicas that have been pushed to exchange and removed from exchange list: ", [replica.rid for replica in exchange_list]
                print "Replicas that are still in the sorted waitlist: ", [replica.rid for replica in self._sorted_waitlist]
            
                self._waitlist = self._sorted_waitlist
                print "Replicas that are still in the global waitlist: ", [replica.rid for replica in self._waitlist]

    # --------------------------------------------------------------------------
    #
    
    def _sliding_window(self, sorted_waitlist, exchange_size, window_size):
        '''
        This is an auxiliary function that accepts as input the sorted waitlist and 
        the number of replicas needed for an exchange. It then generates sublists from 
        the sorted waitlist. These sublists contain "compatible" replicas 
        that can proceed to perform exchanges amongst themselves.
        '''
        '''

        Basically, 
        1) Have waitlist 
        2) pass window over list 
        3) if criteria fulfilled, return entire sublist as one big block 
        4) else return nothing

        Pseudocode should look like:

        def find_sublist(things, criteria, listsize)
            sublist = list()
            for thing in things:
                if thing is outside of window:
                    sublist = list()   # new empty list
                if thing matches criteria:
                    sublist.append(thing)
            if len(sublist) >= listsize:
            return sublist
        '''

 
        
        last_range    = None
        exchange_list = list()
        #print "trying to iterate over sorted_waitlist"
        for replica in sorted_waitlist:  
            #print "loop entered successfully"
            if last_range and replica in last_range: 
                continue

            #rid_start = replica.rid    
            rid_end   = replica.rid + window_size
            starting_index=sorted_waitlist.index(replica)
            #print starting_index, "is starting index, sleeping now"
            #time.sleep(10)

            exchange_list = [sorted_waitlist[index] for index in range(starting_index,len(sorted_waitlist)) if sorted_waitlist[index].rid < rid_end] 
            # create a list of replica IDs to check 
            # against to avoid duplication
            last_range = [r for r in exchange_list]  
        
        # Check size of list returned by sliding window 
        
        if len(exchange_list) < exchange_size:     #### "exchange list" appears to not exist.       
            return 
        else:
            print "exchange list size is ",len(exchange_list)
            return exchange_list



    def _check_resume(self, replica):
        '''
        This is triggered after the exchange stage from above.  Resume all
        suspended replicas, and also add a new MD stage for those which did not
        reach end of cycles.
        '''

        self._log.debug('=== %s check resume', replica.rid)

        resumed = list() # replicas that have been resumed

        ### This section has an issue

        for _r in replica.resume_list: 
        
            if _r.cycle <= self._min_cycles:
                print "adding MD stage for replica ", _r.rid
                _r.add_md_stage()
                print "Replica ", _r.rid, " with pipeline ID ",_r.name," has stages ", [plnstg.luid for plnstg in _r.stages]

            # make sure we don't resume the current replica
            if replica.rid != _r.rid:
                self._log.debug('=== %s resume', _r.rid)
                try:
                    _r.resume()
                    print "added MD stage, resuming replica ", _r.rid
                    print "Replica ", _r.rid, " with pipeline ID ",_r.name," has state history ", _r.state_history
                    #print "Replica ", _r.rid, " with pipeline ID ",_r.name," has stages ", [plnstg.name for plnstg in _r.stages]
                    resumed.append(_r.rid)
                except:
                    self._log.exception('=== %s resume failed', _r.rid)
                    time.sleep(10)
                    raise

        # reset exchange_list, increase exchange counter
        #self._exchange_list = list()
        return resumed
        self._cnt += 1


# ------------------------------------------------------------------------------
#
class Replica(re.Pipeline):
    '''
    A `Replica` is an EnTK pipeline which consists of MD stages which are
    subject to an exchange algorithm
    The initial setup is for one MD stage - Exchange and more
    MD stages get added depending on runtime conditions.
    '''

    # --------------------------------------------------------------------------
    #
    def __init__(self, check_ex, check_res, rid, sbox, cores, exe):

        self._check_ex  = check_ex   # is called when checking for exchange
        self._check_res = check_res  # is called when exchange is done
        self._rid       = rid
        self._sbox      = sbox
        self._cores     = cores
        self._exe       = exe
        self._cycle     = 0  # initial cycle
        self._ex_list   = None   #This is a problem. As of 5/28/2019.  

        self._log = ru.Logger('radical.repex.rep')

        # entk pipeline initialization
        re.Pipeline.__init__(self)
        self.name = 'p_%s' % self.rid

        # add an initial md stage
        self.add_md_stage()


    @property
    def rid(self):   return self._rid

    @property
    def cycle(self): return self._cycle

    @property
    def exchange_list(self):
        return self._ex_list 
    
    @property
    def resume_list(self):
        return self._res_list


    # --------------------------------------------------------------------------
    #
    def add_md_stage(self):

        """
        Problem: add_md_stage only adds md tasks that initiate from "inpcrd" i.e. cycle 0. 
        Needs to accept input from previous MD stage. 
        """


        rid   = self._rid
        cycle = self._cycle
        sbox  = self._sbox
        cores = self._cores
        exe   = self._exe

        self._log.debug('=== %s add md (cycle %s)', rid, cycle)
       


        task = re.Task()
        task.name            = 'mdtsk-%s-%s'               % (      rid, cycle)
        if cycle == 0:
            task.link_input_data = ['%s/inpcrd > inpcrd-%s-%s' % (sbox, rid, cycle),
                                    '%s/prmtop'                % (sbox),
                                    '%s/mdin-%s-%s > mdin'     % (sbox, rid, cycle)]
        else:
            cycle_0 = '0'            
            task.link_input_data =  ['%s/inpcrd-%s-%s'         % (sbox, rid, cycle),
                                     '%s/prmtop'               % (sbox),
                                     '%s/mdin-%s-%s > mdin'    % (sbox, rid, cycle_0)]
                                      #['%s/mdcrd-out-%s-%s > inpcrd-%s-%s' % (sbox, rid, cycle, rid, cycle),
                                    

        task.arguments       = ['-O', 
                                '-i',   'mdin', 
                                '-p',   'prmtop', 
                                '-c',   'inpcrd-%s-%s'     % (      rid, cycle), 
                                '-o',   'out',
                                '-x',   '%s/mdcrd-%s-%s'   % (sbox, rid, cycle+1),
                                '-r',   '%s/inpcrd-%s-%s'  % (sbox, rid, cycle+1),
                                '-inf', '%s/mdinfo-%s-%s'  % (sbox, rid, cycle)]
        task.executable      = SANDER #[exe]
        task.cpu_reqs        = {'processes' : cores}
        task.pre_exec        = ['echo $SHARED'] #This will be different for different MD engines.

        stage = re.Stage()
        stage.add_tasks(task)
        stage.post_exec = self._after_md
        self.add_stages(stage)
        #print "stages in this pipeline are ", [plnstg.luid for plnstg in self.stages] 
        #for plstg in self.stages()print "stages in this pipeline are ", plstg.name   
        #stg_list = [sorted_waitlist[index] for index in range(starting_index,len(sorted_waitlist)) if sorted_waitlist[index].rid < rid_end]
    

    def _add_ex_stage(self,exchange_list):
        self._log.debug('=== %s exchange')
        self._ex_list = exchange_list  
        self._res_list = exchange_list
        

        task = re.Task()
        task.name       = 'extsk'
        task.executable = ['/home/scm177/VirtualEnvs/Env_RepEx/bin/python']
        task.upload_input_data = ['t_ex_gibbs.py']
        task.arguments  = ['t_ex_gibbs.py', self._sbox]

        for replica in exchange_list:  
            rid   = replica.rid 
            cycle = replica.cycle 
            task.link_input_data.append('%s/mdinfo-%s-%s' % (self._sbox, rid, cycle-1))  # % (self._sbox, rid, cycle))
        stage = re.Stage()
        stage.add_tasks(task)
            
        stage.post_exec = self._after_ex

        self.add_stages(stage)
        print "replica.add_stages has been executed"


        
    # --------------------------------------------------------------------------
    #
    def _after_md(self):
        '''
        after an md cycle, record its completion and check for exchange
        '''

        self._cycle += 1
        self._check_ex(self)


    # --------------------------------------------------------------------------
    #
    def _after_ex(self):
        '''
        after an ex cycle, trigger replica resumption
        '''

        self._check_res(self)

# ------------------------------------------------------------------------------
#
if __name__ == '__main__':


    exchange = Exchange(size          = 2,
                        exchange_size = 2,   # Exchange size is how big the exchange list needs to be to move to the exchange phase
                        window_size   = 2,   # Window size is the width of the sliding window
                        min_cycles    = 10, 
                        min_temp      = 300,
                        max_temp      = 320,
                        timesteps     = 100,
                        basename      = 'ace-ala', 
                        executable    = SANDER, 
                        cores         = 1)

    exchange.execute()       # run replicas and exchanges
    exchange.terminate()     # done


# ------------------------------------------------------------------------------
