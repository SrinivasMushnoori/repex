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

os.environ['RADICAL_PILOT_DBURL'] = \
           'mongodb://smush:key1209@ds141786.mlab.com:41786/repex_db_1'


RMQ_PORT = int(os.environ.get('RMQ_PORT', 32769))
SANDER   = ['/home/scm177/mantel/AMBER/amber14/bin/sander']

# This is the Async Implementation that uses the "sliding window" approach. 
# Two immediate actions needed: 
# 1) Remove exchanged replicas from waiting list, (Implemented, needs testing) 
# 2) The Exchange method needs ways to accept replica RID's as inputs 
# as well as the mechanism to rename appropriate files. 
# 3) Line 224 is where it all seems to have gone wrong: the iterator in the loop has overridden the replica object. 


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
        self._exchange_list = list()  # Sublist of self._waitlist that performs an exchange

        # create the required number of replicas
        for i in range(self._size):

            replica = Replica(check_ex  = self._check_exchange,
                              check_res = self._check_resume,
                              rid       = i,
                              sbox      = self._sbox,
                              cores     = self._cores, 
                              exe       = self._executable)

            self._replicas.append(replica)


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
        # multiple replicas can trigger this, there fore lock needed
        with self._lock:

            self._waitlist.append(replica)
            self._log.debug('=== %s check exchange (%d >= %d?)', replica.rid, len(self._waitlist), self._exchange_size)
            print "waitlist is: ",[replica.rid for replica in self._waitlist]

            # Sort the waitlist as soon as a new replica is added.
        
            self._sorted_waitlist = sorted(self._waitlist, key=lambda x: x.rid) # We're sorting by RID here since RID's are assigned in sorted order with
                                                                 # Temperature (or whatever paramater is of interest to us)
        
            print "sorted waitlist is: ", [replica.rid for replica in self._sorted_waitlist]


        # Now we generate a sublist called exchange_list, within which an exchange is performed. This is done with
        # the sliding_window function



            self._exchange_list = self._sliding_window(self._sorted_waitlist, self._exchange_size, self._window_size)
        
            #print "exchange list returned by sliding window is: ", [replica.rid for replica in self._exchange_list]
            
            if not self._exchange_list:

            #print "exchange size is ", self._exchange_size, " and exchange list length is ", len(self._exchange_list)
            # just suspend this replica and wait for the next
                self._log.debug('=== %s suspend', replica.rid)
                print "replica ", replica.rid, " should suspend now"
                replica.suspend()
            else:
                exchange_list = self._exchange_list #Unclear if this is necessary
                replica.add_ex_stage(exchange_list)


                for replica in self._exchange_list:
                    try:
                        self._sorted_waitlist.remove(replica)
                    except:
                        print "replica ", replica.rid, " isn't here."
                #self._waitlist = self._sorted_waitlist
    
                print "Replicas that have been pushed to exchange and removed from exchange list: ", [replica.rid for replica in self._exchange_list]
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


        ##---------------FIX THIS-------------##
        ## POTENTIALLY INCORRECT: This operates with only one exchange list. Create 
        ## new exchange list out of global waitlist if the new replica is not within 
        ## window_size. This will work just fine when operated synchronously, but not 
        ## otherwise.
  
        last_window   = None     # avoid rechecking replicas
        last_range = None

        for replica in sorted_waitlist:  
            
            # ignore this replica if it was part of the last range
            if last_range and replica in last_range: 
                continue

            rid_start = replica.rid  #- window_size/2       
            rid_end   = rid_start + window_size

            # find replicas in list within that window
            rid_list =  [replica for replica in sorted_waitlist 
                    if (replica.rid >= rid_start and replica.rid <= rid_end)]
            print "rid_list in sliding window is: ", [replica.rid for replica in rid_list]

            #new_replica = list(set(rid_list) - set(self._exchange_list))  ### This line may no llonger be needed

            
            try:
                print "The new replica is ", new_replica[0].rid
                #if len(rid_list) < exchange_size:
                if len(self._exchange_list) < exchange_size:
                    self._exchange_list.append(new_replica[0]) 
            except:
                print "new_replica seems to not exist or something"
                print "Hit Ctrl+C in 10 seconds to terminate"
                time.sleep(10)
            #print "Exchange list generated by sliding window is: ", [replica.rid for replica in self._exchange_list] 

            # create a list of replica IDs to check 
            # against to avoid duplication
            last_range = [r for r in rid_list]  
        
        # Check size of list returned by sliding window 

        if len(self._exchange_list) < exchange_size:     #### "exchange list" appears to not even exist.       
            return
        else:
            return self._exchange_list



    def _check_resume(self, replica):
        '''
        This is triggered after the exchange stage from above.  Resume all
        suspended replicas, and also add a new MD stage for those which did not
        reach end of cycles.
        '''

        self._log.debug('=== %s check resume', replica.rid)


        for _replica in self._exchange_list:  #REPLICA SHOULD NOT BE USED AS AN ITERATOR

            if _replica.cycle <= self._min_cycles:
                # more work to d o for this replica
                _replica.add_md_stage()

            # make sure we don't resume the current replica
            if replica.rid != _replica.rid:
                self._log.debug('=== %s resume', _replica.rid)
                try:
                    _replica.resume()
                except:
                    self._log.exception('=== %s resume failed', _replica.rid)
                    time.sleep(10)
                    raise

        # reset exchange_list, increase exchange counter
        self._exchange_list = list()
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


    # --------------------------------------------------------------------------
    #
    def add_md_stage(self):


        rid   = self._rid
        cycle = self._cycle
        sbox  = self._sbox
        cores = self._cores
        exe   = self._exe

        self._log.debug('=== %s add md (cycle %s)', rid, cycle)

        task = re.Task()
        task.name            = 'mdtsk-%s-%s'               % (      rid, cycle)
        task.link_input_data = ['%s/inpcrd > inpcrd-%s-%s' % (sbox, rid, cycle),
                                 '%s/prmtop'               % (sbox),
                                 '%s/mdin-%s-%s > mdin'    % (sbox, rid, cycle)]
        task.arguments       = ['-O', 
                                '-i',   'mdin', 
                                '-p',   'prmtop', 
                                '-c',   'inpcrd-%s-%s'     % (      rid, cycle), 
                                '-o',   'out',
                                '-x',   'mdcrd',
                                '-r',   '%s/inpcrd-%s-%s'  % (sbox, rid, cycle),
                                '-inf', '%s/mdinfo-%s-%s'  % (sbox, rid, cycle)]
        task.executable      = SANDER #[exe]
        task.cpu_reqs        = {'processes' : cores}
        task.pre_exec        = ['echo $SHARED'] #This will be different for different MD engines.

        stage = re.Stage()
        stage.add_tasks(task)
        #try:
        #stage.post_exec = {'function' : self._after_md,
        #                       'args'    : []}
        stage.post_exec = self._after_md
        #except:
        #    stage.post_exec = {'condition': self._after_md,
        #                        'on_true': void,
        #                        'on_false': void}                  

        self.add_stages(stage)

    

    def _add_ex_stage(self,exchange_list):
        self._log.debug('=== %s exchange')

        task = re.Task()
        task.name       = 'extsk'
        task.executable = ['python']
        task.upload_input_data = ['t_ex_gibbs.py']
        task.arguments  = ['t_ex_gibbs.py', len(self._waitlist)]

        for replica in exchange_list:  
            rid   = replica.rid 
            cycle = replica.cycle 
            task.link_input_data.append('%s/mdinfo-%s-%s' 
                                          % (self._sbox, rid, cycle))
            stage = re.Stage()
            stage.add_tasks(task)
            
            stage.post_exec = replica._after_ex 

            replica.add_stages(stage)

            # Here we remove the replicas participating in the triggered exchange from the waitlist. 

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


    exchange = Exchange(size          = 6,
                        exchange_size = 3,   # Exchange size is how big the exchange list needs to be to move to the exchange phase
                        window_size   = 6,   # Window size is the width of the sliding window
                        min_cycles    = 0, 
                        min_temp      = 300,
                        max_temp      = 320,
                        timesteps     = 100,
                        basename      = 'ace-ala', 
                        executable    = SANDER, 
                        cores         = 1)

    exchange.execute()       # run replicas and exchanges
    exchange.terminate()     # done


# ------------------------------------------------------------------------------