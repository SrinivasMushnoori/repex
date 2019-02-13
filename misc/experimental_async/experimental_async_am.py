#!/usr/bin/env python

import os
import time
import tarfile
import writeInputs

import radical.entk  as re
import radical.utils as ru

os.environ['RADICAL_SAGA_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['RADICAL_PROFILE']              = 'True'
os.environ['RADICAL_ENTK_PROFILE']         = 'True'
os.environ['RADICAL_ENTK_VERBOSE']         = 'INFO'
os.environ['RP_ENABLE_OLD_DEFINES']        = 'True'
os.environ['SAGA_PTY_SSH_TIMEOUT']         = '2000'
os.environ['RADICAL_VERBOSE']              = 'INFO'
os.environ['RADICAL_PILOT_PROFILE']        = 'True'
os.environ['RADICAL_REPEX_SYNCEX_PROFILE'] = 'True'
os.environ['RADICAL_REPEX_RUN_PROFILE']    = 'True'

os.environ['RADICAL_PILOT_DBURL'] = \
           'mongodb://smush:key1209@ds147361.mlab.com:47361/db_repex_4'

RMQ_PORT = int(os.environ.get('RMQ_PORT', 32769))
SANDER   = '/home/scm177/mantel/AMBER/amber14/bin/sander'
SANDER   = 'sleep 3; echo'


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

    def __init__(self, size, max_wait, min_cycles, min_temp, max_temp,
                 timesteps, basename, executable, cores):

        self._size       = size
        self._max_wait   = max_wait
        self._min_cycles = min_cycles
        self._min_temp   = min_temp
        self._max_temp   = max_temp
        self._timesteps  = timesteps
        self._basename   = basename
        self._executable = executable
        self._cores      = cores

        self._log = ru.Logger('radical.repex.exc')

        # inintialize the entk app manager
        re.AppManager.__init__(self, autoterminate=False, port=RMQ_PORT) 
        self.resource_desc = {"resource" : 'local.localhost',
                              "walltime" : 30,
                              "cpus"     : 4}                                

        # this is ugly
        self._sbox      = '$Pipeline_untarPipe_Stage_untarStg_Task_untarTsk'
        self._cnt       = 0  # count exchanges
        self._replicas  = list()
        self._waitlist  = list()

        # create the required number of replicas
        for i in range(self._size):

            replica = Replica(check_ex  = self._check_exchange,
                            # check_res = self._after_exchange,
                              rid       = i,
                              sbox      = self._sbox,
                              cores     = self._cores, 
                              exe       = self._executable)

            self._replicas.append(replica)


    # --------------------------------------------------------------------------
    #
    def setup(self):

        self._log.debug('=== data staging')

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
            tar.add  ('mdin-%s-0' % replica.rid)
            os.remove('mdin-%s-0' % replica.rid)

        tar.close()

        # create a single pipeline with one stage to transfer the tarball
        task = re.Task()
        task.name              = 'untarTsk'
        task.executable        = 'python'
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
        '''

        # mark this replica for the next exchange
        self._waitlist.append(replica)

        self._log.debug('=== EX %s check exchange (%d >= %d?)',
                        replica.rid, len(self._waitlist), self._max_wait)


        if len(self._waitlist) < self._max_wait:

            # just suspend this replica and wait for the next
            self._log.debug('=== EX %s suspend', replica.rid)
            replica.suspend()

        else:
            # we are in for a wile ride!
            self._log.debug('=== EX %s exchange', replica.rid)

            task = re.Task()
            task.name       = 'extsk'
         ## task.executable = 'python'
            task.executable = 'echo'
            task.arguments  = ['t_ex_gibbs.py', len(self._waitlist)]

      ##    for replica in self._waitlist:
      ##        rid   = replica.rid
      ##        cycle = replica.cycle
      ##        task.link_input_data.append('%s/mdinfo-%s-%s' 
      ##                                   % (self._sbox, rid, cycle))
            stage = re.Stage()
            stage.add_tasks(task)
            stage.post_exec = self._after_exchange

            replica.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def _after_exchange(self):
        '''
        This is triggered after the exchange stage from above.  Resume all
        suspended replicas, and also add a new MD stage for those which did not
        reach end of cycles.
        '''

        self._log.debug('=== EX after exchange')


        for _replica in self._waitlist:

            if _replica.cycle <= self._min_cycles:
                # more work to do for this replica
                _replica.add_md_stage()

                self._log.debug('=== EX %s resume', _replica.rid)
                try:
                    _replica.resume()
                except:
                    self._log.debug('=== EX %s resume error ignored', _replica.rid)

        # reset waitlist, increase exchange counter
        self._waitlist = list()
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
    def __init__(self, check_ex, rid, sbox, cores, exe):

        self._check_ex  = check_ex   # is called when checking for exchange
      # self._check_res = check_res  # is called when exchange is done
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
     ## task.link_input_data = ['%s/inpcrd > inpcrd-%s-%s' % (sbox, rid, cycle),
     ##                          '%s/prmtop'               % (sbox),
     ##                          '%s/mdin-%s-%s > mdin'    % (sbox, rid, cycle)]
        task.arguments       = ['-O', 
                                '-i',   'mdin', 
                                '-p',   'prmtop', 
                                '-c',   'inpcrd-%s-%s'     % (      rid, cycle), 
                                '-o',   'out',
                                '-x',   'mdcrd',
                                '-r',   '%s/inpcrd-%s-%s'  % (sbox, rid, cycle),
                                '-inf', '%s/mdinfo-%s-%s'  % (sbox, rid, cycle)]
        task.executable      = exe
        task.cpu_reqs        = {'processes' : cores}
        task.pre_exec        = ['echo $SHARED']

        stage = re.Stage()
        stage.add_tasks(task)
        stage.post_exec = self.after_md

        self.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def after_md(self):
        '''
        after an md cycle, record its completion and check for exchange
        '''

        self._log.debug('=== %s after md', self.rid)

        self._cycle += 1
        self._check_ex(self)


  # # --------------------------------------------------------------------------
  # #
  # def after_ex(self):
  #     '''
  #     after an ex cycle, trigger replica resumption
  #     '''
  #     self._log.debug('=== %s after ex', self.rid)
  #     self._check_res(self)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':


    exchange = Exchange(size       = 2,
                        max_wait   = 2,
                        min_cycles = 3, 
                        min_temp   = 100,
                        max_temp   = 200,
                        timesteps  = 500,
                        basename   = 'ace-ala', 
                        executable = SANDER, 
                        cores      = 1)

    exchange.execute()       # run replicas and exchanges
    exchange.terminate()     # done


# ------------------------------------------------------------------------------

