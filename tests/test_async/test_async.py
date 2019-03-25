#!/usr/bin/env python

import glob
import shutil

from repex import async_sliding_window as async 


def test_Exchange():
    # exchange_size:  how big the exchange list needs to be
    #                 to move to the exchange phase
    # window_size:    the width of the sliding window
    exchange = async.Exchange(size          = 8,
                              exchange_size = 4,
                              window_size   = 8,
                              min_cycles    = 3, 
                              min_temp      = 300,
                              max_temp      = 320,
                              timesteps     = 500,
                              basename      = 'ace-ala', 
                              executable    = 'SANDER', 
                              cores         = 1)


  # assert exchange._replicas() == list()
    assert len(exchange._replicas) == 8

  # assign two replicas to waitlist
    exchange._waitlist = [exchange._replicas[0],exchange._replicas[2]]

    list_for_exchange = exchange._sliding_window(exchange._waitlist, 4, 8)
    assert isinstance(list_for_exchange, list)
    # This will, for now, return 1. This is because of a known issue that treats
    # the exchange list as a local private list, where it should be global.
    assert(len(list_for_exchange) == 4), 'list: %s' % list_for_exchange

    print ('yes')


def cleanup():
    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 


if __name__ == '__main__':

    test_Exchange()
    cleanup()



