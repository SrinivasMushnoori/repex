
import radical.utils as ru


# ------------------------------------------------------------------------------
#
def select_replicas_1D(waitlist, criteria, replica):
    '''
    replica selection algorithm: out of the list of eligible replicas, select
    those which should be part of an exchange step.

    Arguments:

      - waitlist: a list of replica objects which are eligible for exchange
      - criteria: dictionary of selection criteria to control the algorthm's
    '''

    try:
        print '================================================='
        print 'criteria: %s' % criteria
        print 'waitlist: %s' % [r.rid for r in waitlist]

        # get required parameters
        ex_size = criteria['exchange_size']

        # check if size of wait list suffices
        if len(waitlist) < ex_size:

            # not enough replicas to attempt exchange
            print '-------------------------------------------------'
            return

        # we have enough replicas!  Remove all as echange candidates from the
        # waitlist and return them!
        exchange_list = list()
        for r in waitlist:
            exchange_list.append(r)

        # empty the waitlist to start collecting new candidates
        new_waitlist = list()

        print 'exchange: %s' % [r.rid for r in exchange_list]
        print 'new wait: %s' % [r.rid for r in new_waitlist]
        print '================================================='

        return exchange_list, new_waitlist


    except Exception as e:

        print 'replica selection failed: %s' % e
        ru.print_exception_trace()

        # on failure, return the unchanged waitlist and an empty selection
        return [], waitlist


# ------------------------------------------------------------------------------

