#!/usr/bin/env python

import glob
import shutil

# from repex import async_repex as async 
from repex import dummy_exchange as async 


# ------------------------------------------------------------------------------
#
def set_waitlist(exchange, rids):

    exchange._waitlist = list()
    for rid in rids:
        exchange._waitlist.append(exchange._replicas[rid])


# ------------------------------------------------------------------------------
#
def test_ReplicaExchange():

    # exchange_size:  how big the exchange list needs to be
    #                 to move to the exchange phase
    # window_size:    the width of the sliding window
    exchange = async.ReplicaExchange(ensemble_size = 16,
                                     exchange_size = 4,
                                     window_size   = 8,
                                     md_cycles     = 3,
                                   # min_temp      = 300,
                                   # max_temp      = 320,
                                   # timesteps     = 500,
                                   # basename      = 'ace-ala', 
                                   # executable    = 'SANDER', 
                                   # cores         = 1
                                    )
    assert len(exchange._replicas) == 16


    # assign seven replicas to waitlist
    set_waitlist(exchange, [0, 2, 4, 5, 12, 13, 15])

    old_len = len(exchange._waitlist)
    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[0])

    assert(isinstance(ex_list, list))
    assert(len(ex_list) == 4)
    assert(len(exchange._waitlist) == old_len - len(ex_list))
    assert(exchange._replicas[0] in ex_list)

    for r in exchange._waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in exchange._waitlist)


    # assign seven replicas to waitlist with ending replicas
    # fulfilling the criteria
    set_waitlist(exchange, [0, 4, 14, 12, 13, 15])

    old_len = len(exchange._waitlist)
    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[12])

    assert(isinstance(ex_list, list))
    assert(len(ex_list) == 4)
    assert(len(exchange._waitlist) == old_len - len(ex_list))  
    assert(exchange._replicas[12] in ex_list)

    for r in exchange._waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in exchange._waitlist)


    # assign eight replicas to waitlist with two sets of
    # replicas fulfilling the criteria
    set_waitlist(exchange, [0, 2, 3, 4, 14, 12, 13, 15])

    old_len = len(exchange._waitlist)
    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[2])

    assert(isinstance(ex_list, list))
    assert([r.rid for r in ex_list] == [0, 2, 3, 4])
    assert(len(ex_list) == 4)
    assert(len(exchange._waitlist) == old_len - len(ex_list))  

    for r in exchange._waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in exchange._waitlist)

    old_len = len(exchange._waitlist)
    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[12])

    assert(isinstance(ex_list, list))
    assert([r.rid for r in ex_list] == [12, 13, 14, 15]) 
    assert(len(ex_list) == 4)
    assert(len(exchange._waitlist) == old_len - len(ex_list)) 

    for r in exchange._waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in exchange._waitlist)


    # assign four replicas to waitlist
    set_waitlist(exchange, [0, 2, 4, 5])

    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[0])

    assert(isinstance(ex_list, list))
    assert(len(ex_list) == 4)
    assert(len(exchange._waitlist)) == 0

    for r in exchange._waitlist:
        assert(r not in ex_list)

    for r in ex_list:
        assert(r not in exchange._waitlist)


  # assign three replicas to waitlist

    set_waitlist(exchange, [0, 2, 1])

    ex_list = exchange._find_exchange_list(4, 8, exchange._replicas[0])

    assert((ex_list) is None)


  # assign two replicas to waitlist

    set_waitlist(exchange, [0, 2])

    ex_list = exchange._find_exchange_list(4, 4, exchange._replicas[0])

    assert((ex_list) is None)

  # assign 8 replicas to waitlist

    set_waitlist(exchange, [0, 1, 2, 3, 4, 6, 7, 8, 9])

    ex_list = exchange._find_exchange_list(4, 4, exchange._replicas[4])
    ex_list_ids = [rep.rid for rep in ex_list]

    assert((ex_list_ids) == [1,2,3,4])


# ------------------------------------------------------------------------------
#
def cleanup():

    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    test_ReplicaExchange()
    cleanup()


# ------------------------------------------------------------------------------

