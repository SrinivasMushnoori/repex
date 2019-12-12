#!/usr/bin/env python

import radical.repex as re


# ------------------------------------------------------------------------------
#
class Replica(object):
    def __init__(self, rid):
        self.rid = rid


# ------------------------------------------------------------------------------
#
def test_selection_alg():

    criteria = {'exchange_size' : 3}
    waitlist = [Replica(rid) for rid in [0, 2, 4, 5, 12, 13, 15]]
    replica  = waitlist[0]
    old_len  = len(waitlist)

    ex_list, new_waitlist = re.select_replicas_1D(waitlist, criteria, replica)

    print([r.rid for r in ex_list])
    print([r.rid for r in new_waitlist])

    assert(isinstance(ex_list, list))
    assert([r.rid for r in ex_list] == [0, 2, 3, 4])
    assert(len(ex_list) == 4)
    assert(len(waitlist) == old_len - len(ex_list))

    for r in waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in waitlist)



# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    test_selection_alg()


# ------------------------------------------------------------------------------

