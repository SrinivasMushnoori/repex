from repex import async_sliding_window as async 
from repex.async_sliding_window import Replica as Rep
import os, glob, shutil


def test_Exchange():
	exchange = async.Exchange(size          = 8,
                        exchange_size = 4,   # Exchange size is how big the exchange list needs to be to move to the exchange phase
                        window_size   = 8,   # Window size is the width of the sliding window
                        min_cycles    = 3, 
                        min_temp      = 300,
                        max_temp      = 320,
                        timesteps     = 500,
                        basename      = 'ace-ala', 
                        executable    = 'SANDER', 
                        cores         = 1)

	
	#assert exchange._replicas() == list()
	assert len(exchange._replicas) == 8

    #assign two replicas to waitlist
	exchange._waitlist = [exchange._replicas[0],exchange._replicas[2]]

	list_for_exchange = exchange._sliding_window(exchange._waitlist, 4, 8)
	assert type(list_for_exchange) == type(list())
	assert len(list_for_exchange) == 4  # This will, for now, return 1. This is because
	                                    # of a known issue that treats the exchange list
	                                    # as a local private list, where it should be 
	                                    # global.
	print ('yes')

def cleanup():
    for filename in glob.glob("re.session*"):
        shutil.rmtree(filename) 




test_Exchange()
cleanup()



