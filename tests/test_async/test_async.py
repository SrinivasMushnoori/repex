#!/usr/bin/env python

import random
import pytest

from radical.repex import algorithms as rxa


# ------------------------------------------------------------------------------
#
class Replica():

    def __init__(self, rid):
        self.rid = rid


# ------------------------------------------------------------------------------
#

test_data = list()

for alg in [rxa.select_replicas_1D,
            rxa.select_replicas_test]:
    for en_size in [1, 2, 4, 8, 16, 32]:
        for wl_size in [1, 2, 4, 8, 16, 32]:
            if wl_size > en_size:
                continue
            

            for ex_size in [1, 2, 4, 8, 16, 32]:
                #if wl_size > ex_size:
                    #pytest.raises(ValueError)

            #ex_size = wl_size
                test_data.append([alg, en_size, wl_size, ex_size])


@pytest.mark.parametrize("alg, en_size, wl_size, ex_size", test_data)
def test_select_replicas (alg, en_size, wl_size, ex_size):

    # create a random waitlist out of the given replica list
    rlist    = [Replica(i) for i in range(en_size)]
    wlist    = random.sample(rlist, wl_size)
    criteria = {"exchange_size" : ex_size}

    # attempt to use each replica as active replica
    for ar in wlist:

        [ex_list, new_wl] = alg(wlist, criteria, ar)

        assert(isinstance(ex_list, list))
        assert(isinstance(new_wl,  list))

        if ex_list:
            if wl_size > ex_size:
                pytest.raises(ValueError)

            else:
                assert(ar in ex_list)
                assert(len(ex_list) == ex_size)

        else:
            assert(wlist == new_wl)

        assert(len(new_wl) == len(wlist) - len(ex_list))

        for r in new_wl : assert(r not in ex_list)
        for r in ex_list: assert(r not in new_wl)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    test_select_replicas()


# ------------------------------------------------------------------------------

