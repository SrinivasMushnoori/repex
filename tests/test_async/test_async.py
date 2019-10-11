#!/usr/bin/env python

import glob
import shutil

# from repex import async_repex as async 
from radical.repex import algorithms #import select_replicas_1D as rsa 


# ------------------------------------------------------------------------------

class Replica():

    def __init__(self, rid):
        self.rid=rid



# ------------------------------------------------------------------------------
#

def create_replica_list(ensemble_size):
    replica_list = []
    for i in range(ensemble_size):
        replica = Replica(i)
        replica_list.append(replica)
    return replica_list

# ------------------------------------------------------------------------------
#
def test_select_replicas_1D():
    ensemble_size = 16
    rlist=create_replica_list(ensemble_size)
    criteria =   {"exchange_size" : 4,
                  "window_size"   : 4,
                  "select_alg"    : "1D",
                  "exchange_alg"  : "RANDOM"}


    assert len(rlist) == 16
    waitlist = [rlist[1], rlist[2], rlist[4], rlist[7]]
    replica = rlist[2]
    [ex_list,new_wl] = algorithms.select_replicas_1D(waitlist, criteria, replica)
    # assign four replicas to waitlist
    # returns new_waitlist, exchange_list
  

    old_len = len(waitlist)
    

    assert(isinstance(ex_list, list))
    assert(len(ex_list) == 4)
    assert(len(new_wl) == old_len - len(ex_list))
    assert(replica in ex_list)

    for r in new_wl:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in new_wl)


    # assign three replicas to waitlist 
    # this should fail, but it fails for the wron reason?
    waitlist = [rlist[1], rlist[2], rlist[4]]
    replica = rlist[2]
    [ex_list,new_wl] = algorithms.select_replicas_1D(waitlist, criteria, replica) ### This test fails because the algorithm returns 
                                                                                  ### NoneType instead of an empty ex_list.
                                                                                  ### So clearly new_wl is not being generated either  

    assert(isinstance(ex_list, list))
    assert(len(ex_list) == 0)
    assert(len(new_wl) == old_len - len(ex_list))
    assert(replica in ex_list)

    for r in new_wl:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in new_wl)


    

# ------------------------------------------------------------------------------
#
def cleanup():

    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    test_select_replicas_1D()
    cleanup()


# ------------------------------------------------------------------------------

