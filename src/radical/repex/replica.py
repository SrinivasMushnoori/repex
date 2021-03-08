
import copy

import radical.utils as ru
import radical.entk  as re

from .utils import expand_ln, last_task


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
    def __init__(self, workload, properties=None):

        self._workload  = workload
        self._check_ex  = None
        self._check_res = None

        if not properties:
            properties  = dict()

        self._rid       = ru.generate_id('rep.%(counter)04d', ru.ID_CUSTOM)

        self._props     = properties
        self._cycle     = -1    # increased when adding md stage
        self._ex_list   = None  # list of replicas used in exchange step

        re.Pipeline.__init__(self)
        self.name = 'p.%s' % self.rid
        self._log = ru.Logger('radical.repex')


    # --------------------------------------------------------------------------
    #
    def _initialize(self, check_ex, check_res, sid):
        '''
        This method should only be called by the Exchange class upon
        initialization.
        '''

        self._check_ex  = check_ex
        self._check_res = check_res

        # add an initial md stage
        self.add_md_stage(sid=sid)


    # --------------------------------------------------------------------------
    #
    @property
    def rid(self):        return self._rid

    @property
    def cycle(self):      return self._cycle

    @property
    def properties(self): return self._props

    # --------------------------------------------------------------------------
    #
    @property
    def exchange_list(self):

        return self._ex_list


    # --------------------------------------------------------------------------
    #
    def add_md_stage(self, exchanged_from=None, sid=None, last=False):

        self._cycle += 1
        self._log.debug('%5s %s add md', self.rid, self._uid)

      # task = re.Task(from_dict=self._workload['md'])
      # task.name = 'mdtsk-%s-%s' % (self.rid, self.cycle)
        env  = {'REPEX_RID'   : str(self.rid),
                'REPEX_CYCLE' : str(self.cycle),
               }
        # TODO: filter out custom keys from that dict
        td   = ru.expand_env(copy.deepcopy(self._workload['md']), env=env)
        sandbox = '%s.%04d.md' % (self.rid, self.cycle)
        link_inputs = list()

        # link initial data
        link_inputs += expand_ln(self._workload.md.inputs,
                     'pilot:///%s' % self._workload.data.inputs,
                     'unit:///',
                     self.rid, self.cycle)

        if self._cycle == 0:
            # link initial data
            link_inputs += expand_ln(self._workload.md.inputs_0,
                         'pilot:///%s' % self._workload.data.inputs,
                         'unit:///',
                         self.rid, self.cycle)
        else:
            # get data from previous task
            t = last_task(self)
            if exchanged_from:
                self._log.debug('Exchange from %s', exchanged_from.name)
                link_inputs += expand_ln(self._workload.md.ex_2_md,
                        'pilot:///%s' % (exchanged_from.sandbox),
                        'unit:///',
                        self.rid, self.cycle)
            else:
                # FIXME: this apparently can't happen
                link_inputs += expand_ln(self._workload.md.md_2_md,
                         'resource:///%s' % (t.sandbox),
                         'unit:///',
                         self.rid, self.cycle)

        copy_outputs = expand_ln(self._workload.md.outputs,
                         'unit:///',
                         'client:///%s' % self._workload.data.outputs,
                         self.rid, self.cycle)

        if last:
            copy_outputs += expand_ln(self._workload.md.outputs_n,
                         'unit:///',
                         'client:///%s' % self._workload.data.outputs,
                         self.rid, self.cycle)

        for i, descr in enumerate(ru.as_list(td['description'])):
            task = re.Task()
            
            for k,v in descr.items():
                setattr(task, k, v)

            if self._workload.pre_exec:
                if task.pre_exec: task.pre_exec.extend  (self._workload.pre_exec)
                else            : task.pre_exec.extend = self._workload.pre_exec

            task.name = '%s.%04d.%04d.md' % (self.rid, self.cycle, i)
            task.sandbox = sandbox
            stage = re.Stage()
            if i == 0:
                task.link_input_data = link_inputs
            elif i == len(td['description']) - 1:
                task.download_output_data = copy_outputs
                stage.post_exec = self.check_exchange
            self._log.debug('%5s add md: %s', self.rid, task.name)

            stage.add_tasks(task)
            self.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def check_exchange(self):
        '''
        after an md cycle, record its completion and check for exchange
        '''

        self._log.debug('%5s check_exchange %s', self.rid, self._uid)
        self._check_ex(self)


    # --------------------------------------------------------------------------
    #
    def add_ex_stage(self, exchange_list, ex_alg, sid):

        self._log.debug('%5s add ex: %s', self.rid,
                        [r.rid for r in exchange_list])
        self._ex_list = exchange_list

        task = re.Task()
        task.executable = 'python3'
        task.arguments  = [ex_alg, '-r', self.rid, '-c', self.cycle] \
                        + ['-e'] + [r.rid for r in exchange_list] \
                        + ['-d'] + [d for d in self._workload.exchange.ex_data]

        if self._workload.pre_exec:
            task.pre_exec = self._workload.pre_exec

        # link alg
        link_inputs = ['pilot:///%s/%s' % (self._workload.data.inputs, ex_alg)]

        # link exchange data
        for r in exchange_list:

            t = last_task(r)
            self._log.debug('Exchage: %s, Task Name: %s Sandbox %s', r.name, t.name, t.sandbox)
            link_inputs += expand_ln(self._workload.exchange.md_2_ex,
                                     # FIXME: how to get absolute task sbox?
                                     #        rep.0000.0000:/// ...
                                     #        i.e., use task ID as schema
                                     'pilot:///%s' % t.sandbox,
                                     'unit:///',
                                     r.rid, r.cycle)

        task.link_input_data   = link_inputs

        task.name    = '%s.%04d.ex' % (self.rid, self.cycle)
        task.sandbox = '%s.%04d.ex' % (self.rid, self.cycle)
        
        self._log.debug('%5s added ex: %s, input data: %s', self.rid, task.name, task.link_input_data)

        stage = re.Stage()
        stage.add_tasks(task)
        stage.post_exec = self.check_resume

        self.add_stages(stage)


    # --------------------------------------------------------------------------
    #
    def check_resume(self):
        '''
        after an ex cycle, trigger replica resumption
        '''
        self._log.debug('%5s check_resume %s', self.rid, self._uid)
        return self._check_res(self)


# ------------------------------------------------------------------------------
