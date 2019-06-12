#!/usr/bin/env python

import time, os
import random
import writeInputs
import threading as mt
import tarfile
import radical.entk  as re
import radical.utils as ru

#os.environ['RADICAL_VERBOSE'] = 'INFO'
os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

os.environ['RADICAL_PILOT_DBURL'] = 'mongodb://smush:key1209@ds263816.mlab.com:63816/repex_db_2'
          #'mongodb://smush:key1209@ds141786.mlab.com:41786/repex_db_1'
           


RMQ_PORT = int(os.environ.get('RMQ_PORT', 32769))
SANDER   = ['/home/scm177/mantel/AMBER/amber14/bin/sander']

t_0 = time.time()

# ------------------------------------------------------------------------------
#
def void():

    pass


# ------------------------------------------------------------------------------
#
class ReplicaExchange(re.AppManager):

    _glyphs = {re.states.INITIAL:    '+',
               re.states.SCHEDULING: '|',
               re.states.SUSPENDED:  '-',
               re.states.DONE:       ' ',
               re.states.FAILED:     '!',
               re.states.CANCELED:   'X'}


    # --------------------------------------------------------------------------
    #
    def __init__(self, ensemble_size, exchange_size, window_size, md_cycles, min_temp, max_temp, timesteps, basename, executable, cores):

        self._en_size = ensemble_size
        self._ex_size = exchange_size
        self._window_size = window_size
        self._cycles  = md_cycles
        self._min_temp      = min_temp
        self._max_temp      = max_temp
        self._timesteps     = timesteps
        self._basename      = basename
        self._executable    = executable
        self._cores         = cores
        self._lock = mt.Lock()
        self._log  = ru.Logger('radical.repex.exc')
        self._dout = open('dump.log', 'a')

        re.AppManager.__init__(self, autoterminate=False, port=5672) 
        self.resource_desc = {"resource" : 'local.localhost',
                              "walltime" : 30,
                              "cpus"     : 16}                                
        
        self._sbox          = '$Pipeline_untarPipe_Stage_untarStg_Task_untarTsk'
        self._cnt           = 0  # count exchanges
        self._replicas = list()
        self._waitlist = list()

        # create the required number of replicas
        for i in range(self._en_size):

            replica = Replica(check_ex  = self._check_exchange,
                              check_res = self._check_resume,
                              rid       = i,
                              sbox      = self._sbox,
                              cores     = self._cores, 
                              exe       = self._executable)

            self._replicas.append(replica)

        self._dump(msg='startup')

        # run the replica pipelines
        self.setup()
        self.workflow = set(self._replicas)
        self.run() 

    def setup(self):



        # prepare input for all replicas
        writeInputs.writeInputs(max_temp=self._max_temp,
                                min_temp=self._min_temp,
                                replicas=self._en_size,
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
    def _dump(self, msg=None, special=None, glyph=None ):

        if not msg:
            msg = ''

        self._dout.write(' | %7.2f |' % (time.time() - t_0))
        for r in self._replicas:
            if special and r in special:
                self._dout.write('%s' % glyph)
            else:
                self._dout.write('%s' % self._glyphs[r.state])
        self._dout.write('| %s\n' % msg)
        self._dout.flush()


    # --------------------------------------------------------------------------
    #
    def terminate(self):

        self._log.debug('exc term')
        self._dump(msg='terminate', special=self._replicas, glyph='=')
        self._dout.close()

        # we are done!
        self.resource_terminate()


    # --------------------------------------------------------------------------
    #
    def _check_exchange(self, replica):

        # This method races when concurrently triggered by multpiple replicas,
        # and it should be guarded by a lock.
        with self._lock:

            self._log.debug('=== %s check exchange : %d >= %d?',
                      replica.rid, len(self._waitlist), self._ex_size)

            self._waitlist.append(replica)

            exchange_list = self._find_exchange_list(self._ex_size, self._window_size)

            if not exchange_list:
                # nothing to do, Suspend this replica and wait until we get more
                # candidates and can try again
                self._log.debug('=== %s no  - suspend', replica.rid)
                replica.suspend()
                self._dump()
                return

            self._log.debug('=== %s yes - exchange', replica.rid)
            msg = " > %s: %s" % (replica.rid, [r.rid for r in exchange_list])
            self._dump(msg=msg, special=exchange_list, glyph='v')

            # we have a set of exchange candidates.  The current replica is
            # tasked to host the exchange task.
            replica.add_ex_stage(exchange_list)


    # --------------------------------------------------------------------------
    #
    def _find_exchange_list(self, exchange_size, window_size):
        '''
        This is the core algorithm: out of the list of eligible replicas, select
        those which should be part of an exchange step
        '''
        if len(self._waitlist) < self._ex_size:

            # not enough replicas to attempt exchange
            return 
        last_range    = None
        exchange_list = list()
        self._sorted_waitlist = sorted(self._waitlist, key=lambda x: x.rid)       
        for replica in self._sorted_waitlist:  

            if last_range and replica in last_range: 
                continue
            rid_end   = replica.rid + window_size
            starting_index=self._sorted_waitlist.index(replica)
            exchange_list = [self._sorted_waitlist[index] for index in range(starting_index,len(self._sorted_waitlist)) if self._sorted_waitlist[index].rid < rid_end] 

            last_range = [r for r in exchange_list]  

        for replica in exchange_list:
            self._waitlist.remove(replica)

        return exchange_list


    # --------------------------------------------------------------------------
    #
    def _check_resume(self, replica):

        self._dump()
        self._log.debug('=== %s check resume', replica.rid)

        resumed = list()  # list of resumed replica IDs

        msg = " < %s: %s" % (replica.rid, [r.rid for r in replica.exchange_list])
        self._dump(msg=msg, special=replica.exchange_list, glyph='^')

        # after a successfull exchange we revive all participating replicas.
        # For those replicas which did not yet reach min cycles, add an md
        # stage, all others we let die and add a new md stage for them.
        for _replica in replica.exchange_list:

            if _replica.cycle <= self._cycles:
                _replica.add_md_stage()

            # Make sure we don't resume the current replica
            if replica.rid != _replica.rid:

                try:
                    self._log.debug('=== %s resume', _replica.rid)
                    _replica.resume()
                    resumed.append(_replica.uid)
                except:
                    print "This replica is already resumed"

        return resumed


# ------------------------------------------------------------------------------
#
class Replica(re.Pipeline):
    '''
    A `Replica` is an EnTK pipeline which consists of alternating md and
    exchange stages.  The initial setup is for one MD stage - Exchange and more
    MD stages get added depending on runtime conditions.
    '''

    # --------------------------------------------------------------------------
    #
    def __init__(self, check_ex, check_res, rid, sbox, cores, exe):

        self._check_ex  = check_ex
        self._check_res = check_res
        self._rid       = rid
        self._sbox      = sbox
        self._cores     = cores
        self._exe       = exe

        self._cycle     = 0     # initial cycle
        self._ex_list   = None  # list of replicas used in exchange step

        re.Pipeline.__init__(self)
        self.name = 'p_%s' % self.rid
        self._log = ru.Logger('radical.repex.rep')

        # add an initial md stage
        self.add_md_stage()


    @property
    def rid(self):      return self._rid

    @property
    def cycle(self):    return self._cycle


    # --------------------------------------------------------------------------
    #
    @property
    def exchange_list(self):

        return self._ex_list


    # --------------------------------------------------------------------------
    #
    def add_md_stage(self):

        self._log.debug('=== %s add md', self.rid)

        rid   = self._rid
        cycle = self._cycle
        sbox  = self._sbox
        cores = self._cores
        exe   = self._exe



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
        stage.post_exec = self.check_exchange   #_after_md
        self.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def check_exchange(self):
        '''
        after an md cycle, record its completion and check for exchange
        '''

        self._cycle += 1
        self._check_ex(self)


    # --------------------------------------------------------------------------
    #
    def add_ex_stage(self, exchange_list):

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
            
        stage.post_exec = self.check_resume  #_after_ex

        self.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def check_resume(self):
        '''
        after an ex cycle, trigger replica resumption
        '''
        self._log.debug('=== check resume %s', self.rid)
        return self._check_res(self)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    exchange = ReplicaExchange(ensemble_size = 8, 
                               exchange_size = 8, 
                               window_size   = 8,
                               md_cycles     = 10, 
                               min_temp      = 300,
                               max_temp      = 320,
                               timesteps     = 100,
                               basename      = 'ace-ala', 
                               executable    = SANDER, 
                               cores         = 1)
    exchange.terminate()

# ------------------------------------------------------------------------------