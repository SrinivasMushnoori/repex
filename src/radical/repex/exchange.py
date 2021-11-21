
import copy

import time
import inspect

import radical.entk  as re
import radical.utils as ru

from   .algorithms import selection_algs, exchange_algs, prepare_algs
from   .algorithms import exchange_alg_prefix
from   .replica    import Replica
from   .utils      import last_task


# ------------------------------------------------------------------------------
#
class Exchange(re.AppManager):

    _t_0    = time.time()
    _glyphs = {re.states.INITIAL:    '+',
               re.states.SCHEDULING: '|',
               re.states.SUSPENDED:  '-',
               re.states.DONE:       ' ',
               re.states.FAILED:     '!',
               re.states.CANCELED:   'X'}


    # --------------------------------------------------------------------------
    #
    def __init__(self, workload, resource, replicas=None):

        self._uid  = ru.generate_id('rx')
        self._prof = ru.Profiler('radical.repex')
        self._prof.prof('create', uid=self._uid)

        self._workload = ru.Config(cfg=workload)
        self._resource = ru.Config(cfg=resource)
        self._replicas = replicas

        # the replicas need to be aware about pre_exec directives
        self._workload.pre_exec = self._resource.pre_exec

        assert(self._workload.config.replicas or self._replicas)
        assert(self._workload.config.cycles)

        self._cycles   = self._workload.config.cycles
        self._waitlist = list()

        if self._replicas:
            self._workload.config.replicas = len(self._replicas)
        else:
            self._replicas = [Replica(workload=self._workload)
                                for _ in range(self._workload.config.replicas)]

        self._pre_alg  = prepare_algs  .get(self._workload.prepare.algorithm)
        self._sel_alg  = selection_algs.get(self._workload.selection.algorithm)
        self._exc_alg  = exchange_algs .get(self._workload.exchange.algorithm)

        # if the configured algorithms are not known (not hard-coded in RX),
        # then assume they point to user specified files and load them
        if not self._pre_alg:
            filename, funcname = self._workload.prepare.algorithm.split(':')
            syms = ru.import_file(filename)
            self._pre_alg = syms['functions'][funcname]

        if not self._sel_alg:
            filename, funcname = self._workload.selection.algorithm.split(':')
            syms = ru.import_file(filename)
            self._sel_alg = syms['functions'][funcname]

        if not self._exc_alg:
            filename, funcname = self._workload.exchange.algorithm.split(':')
            syms = ru.import_file(filename)
            self._exc_alg = syms['functions'][funcname]

        assert(self._pre_alg),  'preparation algorithm missing'
        assert(self._sel_alg),  'selection algorithm missing'
        assert(self._exc_alg),  'exchange algorithm missing'

        rmq_host = str(self._resource.get('rmq_host', 'localhost'))
        rmq_port = int(self._resource.get('rmq_port', '5672'))
        rmq_user = str(self._resource.get('rmq_user','guest'))
        rmq_pass = str(self._resource.get('rmq_pass','guest'))
        re.AppManager.__init__(self, autoterminate=True,
                                     hostname=rmq_host, port=rmq_port,
                                     username=rmq_user, password=rmq_pass)

        for r in self._replicas:
            r._initialize(check_ex=self._check_exchange,
                          check_res=self._check_resume,
                          sid=self.sid, prof=self._prof)

        self._lock = ru.Lock(name='rx')

        rd = copy.deepcopy(self._resource)
        if 'rmq_host' in rd: del(rd['rmq_host'])
        if 'rmq_port' in rd: del(rd['rmq_port'])
        if 'pre_exec' in rd: del(rd['pre_exec'])

        self.resource_desc = rd

        self._log  = ru.Logger('radical.repex')
        self._dout = open('dump.log', 'a')
        self._dump(msg='startup')

        # run the replica pipelines
        self.workflow = set(self._replicas)


    # --------------------------------------------------------------------------
    #
    def run(self):
        '''
        run the replica exchange pipelines, and after all is done, fetch the
        requested output data
        '''

        # run the preparator, set resulting data as `shared_data`, and begin to
        # work
        fnames = ru.as_list(self._pre_alg(self._workload))

        if self._workload.data.inputs not in fnames:
            fnames.append(self._workload.data.inputs)

        # write exchange algorithm to disk (once), and then stage with every
        # exchange task
        self._ex_alg_file = 'exchange_algorithm.py'
        with open('%s/%s' % (self._workload.data.inputs, self._ex_alg_file),
                  'w') as fout:
            fout.write(exchange_alg_prefix % (inspect.getsource(self._exc_alg),
                                              self._exc_alg.__name__))

        self.shared_data = fnames
        re.AppManager.run(self)


    # --------------------------------------------------------------------------
    #
    def _dump(self, msg=None, special=None, glyph=None ):

        if not self._dout:
            return

        if not msg:
            msg = ''

        if not self._dout:
            return

        self._dout.write(' | %7.2f |' % (time.time() - self._t_0))
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
        if self._dout:
            self._dout.close()
            self._dout = None

        # we are done!
        re.AppManager.terminate(self)


    # --------------------------------------------------------------------------
    #
    def _check_exchange(self, replica):

        # method races when concurrently triggered by multpiple replicas
        with self._lock:

            self._waitlist.append(replica)

            ex_list   = None
            new_wlist = None

            # invoke the user defined selection algorithm
            try:
                ex_list, new_wlist = self._sel_alg(
                        waitlist=self._waitlist,
                        criteria=self._workload.selection,
                        replica=replica)
                self._log.debug('sel: %4d -> %4d + %4d = %4d',
                        len(self._waitlist), len(ex_list), len(new_wlist),
                        len(ex_list) + len(new_wlist))
            except Exception as e:
                self._log.exception('selection algorithm failed: %s' % e)

            # check if the user found something to exchange
            if not ex_list:
                # nothing to do, suspend this replica and wait until we get more
                # candidates and can try again
                self._log.debug('%5s %s no  - suspend',
                                replica.rid, replica._uid)
                replica.suspend()
                self._dump()

                # waiting for more replicas only makes sense if any others are
                # still in `SCHEDULING` state
                states = dict()
                for r in self._replicas:
                    if r.state not in states: states[r.state] = 1
                    else                    : states[r.state] += 1
                self._log.debug('=== %s', ['%s=%s' % (k, v) for k, v in states.items()])

                if states.get(re.states.SCHEDULING):
                    # some more replicas are active - wait for those to complete
                    # the exchange list
                    return

                # did not find any active replics, thus the exchange list will
                # never grow and a new exchange will never happen - terminate
                self._log.warn('=== terminating due to lack of active replicas')
                raise RuntimeError('terminating due to lack of active replicas')

            # Seems we got an exchange list - check it: exchange list and
            # new wait list must be proper partitions of the original waitlist:
            #   - make sure no replica is lost
            #   - make sure that replicas are not in both lists
            assert(new_wlist is not None)
            missing = len(self._waitlist) - len(ex_list) - len(new_wlist)
            if missing:
                raise ValueError('%d replicas went missing' % missing)

            for r in self._waitlist:
                if r not in ex_list and r not in new_wlist:
                    raise ValueError('replica %s (%s) missing'
                                    % r, r.properties)

            if replica not in ex_list:
                raise ValueError('active replica (%s) not in exchange list %s)'
                                % (replica.rid, [r.rid for r in ex_list]))

            # lists are valid - use them
            self._waitlist = new_wlist

            self._log.debug('%5s %s yes - exchange', replica.rid, replica._uid)
            msg = " > %s: %s" % (replica.rid, [r.rid for r in ex_list])
            self._dump(msg=msg, special=ex_list, glyph='v')

            # we have a set of exchange candidates.  The current replica is
            # tasked to host the exchange task.
            replica.add_ex_stage(ex_list, self._ex_alg_file, self.sid)


    # --------------------------------------------------------------------------
    #
    def _check_resume(self, replica):

        self._dump()
        self._log.debug('%5s %s check resume', replica.rid, replica._uid)

        resumed = list()  # list of resumed replica IDs

        msg = " < %s: %s" % (replica.rid,
                             [r.rid for r in replica.exchange_list])
        self._dump(msg=msg, special=replica.exchange_list, glyph='^')

        exchange = last_task(replica)

        # after a successfull exchange we revive all participating replicas.
        # For those replicas which did not yet reach min cycles, add an md
        # stage, all others we let die and add a new md stage for them.
        for _replica in replica.exchange_list:

            if _replica.cycle <= self._cycles:
                last = bool(_replica.cycle == self._cycles)
                _replica.add_md_stage(exchanged_from=exchange,
                                      sid=self.sid, last=last)

            # Make sure we don't resume the current replica
            if replica.rid != _replica.rid:

                self._log.debug('%5s %s resume', _replica.rid, replica._uid)
                if _replica.state == re.states.SUSPENDED:
                    _replica.resume()
                resumed.append(_replica.uid)

        return resumed


# ------------------------------------------------------------------------------

