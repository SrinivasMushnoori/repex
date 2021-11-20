#!/usr/bin/env python3

import random


# ------------------------------------------------------------------------------
#
def select_by_random(waitlist, criteria, replica):
    '''
    once `criteria['window_size']` replicas are waiting, a random subset smaller
    to equal of that size is selected for exchange.
    '''


    # check if size of wait list suffices
    if len(waitlist) < criteria.exchange_size:
        return [], waitlist

    # we have enough replicas.  Consider all to be exchange candidates and
    # select a subset (try until the active replica is included)
    while True:
        ret = random.sample(waitlist, criteria.exchange_size)
        if replica in ret:
            break

    # the new exchange list is the waitlist minus selected replicas
    return ret, [r for r in waitlist if r not in ret]


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    import sys
    import pprint

    import radical.utils as ru

    syms = ru.import_file(__file__)
    func = syms['functions']['select_by_random']

    size     = int(sys.argv[1])
    waitlist = list(range(size))
    criteria = {'exchange_size': int(size / 4)}
    el, wl = func(waitlist, criteria, 0)

    pprint.pprint(criteria)
    pprint.pprint(waitlist)
    pprint.pprint(el)
    pprint.pprint(wl)


# ------------------------------------------------------------------------------

