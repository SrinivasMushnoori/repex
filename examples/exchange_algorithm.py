#!/usr/bin/env python3


# ------------------------------------------------------------------------------
#
def exchange_by_random(waitlist, criteria):
    '''
    This method will select a number of replicas to exchange
    arguments: the number of replicas to exchange, and the cycle (?).
    '''

    import random

    def select(wl):
        idx = random.randint(1, len(wl)) - 1
        val = wl[idx]
        del(wl[idx])
        return val

    n_pairs   = criteria.get('n_pairs', 1)
    exchanges = list()
    while len(exchanges) < n_pairs and len(waitlist) >= 2:
        r1 = select(waitlist)
        r2 = select(waitlist)
        exchanges.append([r1, r2])

    return exchanges, waitlist


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    import sys
    import pprint

    import radical.utils as ru

    syms = ru.import_file(__file__)
    func = syms['functions']['exchange_by_random']

    waitlist = list(range(int(sys.argv[1])))
    criteria = {'n_pairs' : 3}
    el, wl = func(waitlist, criteria)

    pprint.pprint(el)
    pprint.pprint(wl)


# ------------------------------------------------------------------------------

