
import random

import radical.entk  as re
import radical.utils as ru


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
    def __init__(self, workload, properties):

        self._workload  = workload
        self._check_ex  = None
        self._check_res = None

        if 'rid' in properties:
            self._rid   = properties['rid']
        else:
            self._rid   = ru.generate_id('replica..%(counter)06d', ru.ID_CUSTOM)

        self._props     = properties
        self._cycle     = 0     # initial cycle
        self._ex_list   = None  # list of replicas used in exchange step

        re.Pipeline.__init__(self)
        self.name = 'p_%s' % self.rid
        self._log = ru.Logger('radical.repex')


    # --------------------------------------------------------------------------
    #
    def _initialize(self, check_ex, check_res):
        '''
        This method should only be called by the Exchange class upon
        initialization.
        '''

        self._check_ex  = check_ex
        self._check_res = check_res

        # add an initial md stage
        self.add_md_stage()


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
    def add_md_stage(self):

        self._log.debug('=== %s add md', self.rid)

        task = re.Task(from_dict=self._workload['md'])
      # task.name = 'mdtsk-%s-%s' % (self.rid, self.cycle)

        stage = re.Stage()
        stage.add_tasks(task)
        stage.post_exec = self.check_exchange

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
    def add_ex_stage(self, exchange_list, ex_alg):

        self._log.debug('=== %s add ex: %s', self.rid,
                                             [r.rid for r in exchange_list])
        self._ex_list = exchange_list

        task = re.Task(from_dict=self._workload['ex'])
        task.arguments         = [ex_alg, len(exchange_list), self._cycle]
        task.upload_input_data = [ex_alg]

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
        self._log.debug('=== check resume %s', self.rid)
        return self._check_res(self)


# ------------------------------------------------------------------------------

