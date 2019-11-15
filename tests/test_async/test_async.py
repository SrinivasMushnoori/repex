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


# ------------------------------------------------------------------------------
#
def test_select_replicas_1D():

    ensemble_size = 16
    ex_size = 4

    rlist=create_replica_list(ensemble_size)
    criteria =   {"exchange_size" : ex_size,
                  "select_alg"    : "1D",
                  "exchange_alg"  : "RANDOM"}

    
    assert len(rlist) == ensemble_size    

    #### Create multiple sets of inputs, and pass them to a single loop containing asserts. 

    def common_asserts(waitlist, replica, ex_list, new_wl):
        assert(isinstance(ex_list, list))
        if len(ex_list) > 0:
            assert(replica in ex_list)
            assert(len(ex_list) == 4)
        assert(len(new_wl) == len(waitlist) - len(ex_list))
        for r in new_wl:
            assert(r not in ex_list)
        for r in ex_list:
            assert(r not in new_wl)


    cases = 2
    # assign four replicas to waitlist
    # returns new_waitlist, exchange_list

    
    waitlists          = [[rlist[1], rlist[2], rlist[4], rlist[7]], 
                          [rlist[1], rlist[2], rlist[4]]]
    active_replicas    = [rlist[2],
                          rlist[2]]


    ########[waitlist, replica] = [[rlist[1], rlist[2], rlist[4], rlist[7]], rlist[2]]
    
    for i in range(cases):
        [ex_list,new_wl] = algorithms.select_replicas_1D(waitlists[i], criteria, active_replicas[i])    
        common_asserts(waitlists[i],active_replicas[i], ex_list, new_wl)

   

# ------------------------------------------------------------------------------
#
def cleanup():

    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    test_select_replicas_1D(ensemble_size, ex_size, active_replica, waitlist)
    cleanup()

# ------------------------------------------------------------------------------

