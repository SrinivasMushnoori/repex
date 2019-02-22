from repex import async_sliding_window as async 

def test_Exchange():
	exchange = Exchange(size          = 4,
                        exchange_size = 2,   # Exchange size is how big the exchange list needs to be to move to the exchange phase
                        window_size   = 4,   # Window size is the width of the sliding window
                        min_cycles    = 3, 
                        min_temp      = 300,
                        max_temp      = 320,
                        timesteps     = 500,
                        basename      = 'ace-ala', 
                        executable    = SANDER, 
                        cores         = 1)

	
	assert exchange.replicas == list()
	assert len(exchange.replicas) == 4

    #assign two replicas to waitlist
	exchange.waitlist = [exchange.replicas[0],exchange.replicas[2]]
	exchange._sliding_window()




