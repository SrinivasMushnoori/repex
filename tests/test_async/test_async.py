#!/usr/bin/env python

import glob
import shutil

# from repex import async_repex as async 
from repex import dummy_exchange as async 

def test_ReplicaExchange():
    #exchange_size:  how big the exchange list needs to be
    #                to move to the exchange phase
    #window_size:    the width of the sliding window
    replicaexchange = async.ReplicaExchange(ensemble_size = 16,
                             exchange_size = 4,
                             window_size   = 8,
                             md_cycles    = 3, )
                             #min_temp      = 300,
                             #max_temp      = 320,
                             #timesteps     = 500,
                             #basename      = 'ace-ala', 
                             #executable    = 'SANDER', 
                             #cores         = 1)


    assert len(replicaexchange._replicas) == 16
    
  # assign seven replicas to waitlist
    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2], replicaexchange._replicas[4],replicaexchange._replicas[5],replicaexchange._replicas[12],replicaexchange._replicas[13],replicaexchange._replicas[15]]
    old_replica_waitlist_length = len(replicaexchange._waitlist)
    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[0])
    assert isinstance(list_for_exchange, list)
    print [r.rid for r in list_for_exchange] 
    assert(len(list_for_exchange) == 4) #, 'list: %s' % list_for_exchange
    assert(len(replicaexchange._waitlist)==old_replica_waitlist_length-len(list_for_exchange))
    assert(replicaexchange._replicas[0] in list_for_exchange)
    for r in replicaexchange._waitlist:
        assert(r not in list_for_exchange)
    for r in list_for_exchange:
        assert(r not in replicaexchange._waitlist)

  # assign seven replicas to waitlist with ending replicas fulfilling the criteria
    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2], replicaexchange._replicas[4],replicaexchange._replicas[14],replicaexchange._replicas[12],replicaexchange._replicas[13],replicaexchange._replicas[15]]
    old_replica_waitlist_length = len(replicaexchange._waitlist)
    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[12])
    assert isinstance(list_for_exchange, list)
    print [r.rid for r in list_for_exchange] 
    assert(len(list_for_exchange) == 4) #, 'list: %s' % list_for_exchange
    assert(len(replicaexchange._waitlist)==old_replica_waitlist_length-len(list_for_exchange))  
    assert(replicaexchange._replicas[12] in list_for_exchange)
    for r in replicaexchange._waitlist:
        assert(r not in list_for_exchange)
    for r in list_for_exchange:
        assert(r not in replicaexchange._waitlist)


  # assign eight replicas to waitlist with two sets of replicas fulfilling the criteria
    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2],replicaexchange._replicas[3], replicaexchange._replicas[4],replicaexchange._replicas[14],replicaexchange._replicas[12],replicaexchange._replicas[13],replicaexchange._replicas[15]]
    old_replica_waitlist_length = len(replicaexchange._waitlist)
    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[2])
    assert isinstance(list_for_exchange, list)
    assert([r.rid for r in list_for_exchange] ==[0,2,3,4])
    assert(len(list_for_exchange) == 4) #, 'list: %s' % list_for_exchange
    assert(len(replicaexchange._waitlist)==old_replica_waitlist_length-len(list_for_exchange))  
    for r in replicaexchange._waitlist:
        assert(r not in list_for_exchange)
    for r in list_for_exchange:
        assert(r not in replicaexchange._waitlist)

    old_replica_waitlist_length = len(replicaexchange._waitlist)
    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[12])
    assert isinstance(list_for_exchange, list)
    assert([r.rid for r in list_for_exchange] ==[12,13,14,15]) 
    assert(len(list_for_exchange) == 4) #, 'list: %s' % list_for_exchange
    assert(len(replicaexchange._waitlist)==old_replica_waitlist_length-len(list_for_exchange)) 
    for r in replicaexchange._waitlist:
        assert(r not in list_for_exchange)
    for r in list_for_exchange:
        assert(r not in replicaexchange._waitlist)

  # assign four replicas to waitlist
    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2], replicaexchange._replicas[4],replicaexchange._replicas[5]]
    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[0])
    assert isinstance(list_for_exchange, list)
    assert(len(list_for_exchange) == 4) #, 'list: %s' % list_for_exchange
    assert(len(replicaexchange._waitlist)) == 0
    for r in replicaexchange._waitlist:
        assert(r not in list_for_exchange)
    for r in list_for_exchange:
        assert(r not in replicaexchange._waitlist)

  # assign three replicas to waitlist

    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2],replicaexchange._replicas[1]]

    list_for_exchange = replicaexchange._find_exchange_list(4, 8, replicaexchange._replicas[0])

    assert(list_for_exchange) == None #, 'list: %s' % list_for_exchange

  # assign two replicas to waitlist

    replicaexchange._waitlist = [replicaexchange._replicas[0],replicaexchange._replicas[2]]

    list_for_exchange = replicaexchange._find_exchange_list(4, 4, replicaexchange._replicas[0])

    assert(list_for_exchange) == None #, 'list: %s' % list_for_exchange

    

def cleanup():
    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 


if __name__ == '__main__':

    test_Exchange()

    cleanup()



