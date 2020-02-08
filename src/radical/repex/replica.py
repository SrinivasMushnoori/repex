
import copy

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
            self._rid   = ru.generate_id('rep.%(counter)06d', ru.ID_CUSTOM)

        self._props     = properties
        self._cycle     = -1    # increased when adding md stage
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

        self._cycle += 1
        self._log.debug('%5s %s add md', self.rid, self._uid)

      # task = re.Task(from_dict=self._workload['md'])
      # task.name = 'mdtsk-%s-%s' % (self.rid, self.cycle)
        env  = {'REPEX_RID'   : str(self.rid),
                'REPEX_CYCLE' : str(self.cycle),
               }
        td   = ru.expand_env(copy.deepcopy(self._workload['md']), env=env)
        task = re.Task()

        if 'link_output_data' in td:
            new_lod = list()
            for s in td['link_output_data']:
                new_lod.append(s % {'rid': self.rid, 'cycle': self.cycle})
            td['link_output_data'] = new_lod

        for k,v in td.items():
            setattr(task, k, v)

      # rid   = self.rid
      # cycle = self.cycle
      # for ed in ex_data:
      #     to_link.append('pilot:///%s.%04d.md/%s > repex.%s.%s'
      #                   %  (rid, cycle, ed, rid, ed))
      #
      # task.upload_input_data = [ex_alg]
      # task.link_input_data   = to_link

        task.name    = '%s.%04d.md' % (self.rid, self.cycle)
        task.sandbox = '%s.%04d.md' % (self.rid, self.cycle)

        import pprint
        self._log.debug('=== add_md_stage: %s', pprint.pformat(task.to_dict()))


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

        self._log.debug('%5s check_exchange %s', self.rid, self._uid)
        self._check_ex(self)


    # --------------------------------------------------------------------------
    #
    def add_ex_stage(self, exchange_list, ex_alg, ex_data):

        self._log.debug('%5s add ex: %s', self.rid, [r.rid for r
                                                           in  exchange_list])
        self._ex_list = exchange_list

        task = re.Task()
        task.executable        = 'python3'
        task.arguments         = [ex_alg, '-r', self.rid, '-c', self.cycle] \
                               + ['-e'] + [r.rid for r in exchange_list] \
                               + ['-d'] + ex_data
        to_link = list()
        for r in exchange_list:
            rid   = r.rid
            cycle = r.cycle
            for ed in ex_data:
                to_link.append('pilot:///repex.%s.%04d.%s > repex.%s.%s'
                              %  (rid, cycle, ed, rid, ed))

        task.upload_input_data = [ex_alg]
        task.link_input_data   = to_link

        task.name    = '%s.%04d.ex' % (self.rid, self.cycle)
        task.sandbox = '%s.%04d.ex' % (self.rid, self.cycle)

        self._log.debug('%5s add ex: %s', self.rid, task.name)
        import pprint
        self._log.debug('=== add_ex_stage: %s', pprint.pformat(task.to_dict()))

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

