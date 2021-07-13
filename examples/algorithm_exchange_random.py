#!/usr/bin/env python3


# ------------------------------------------------------------------------------
#
def exchange_by_random(rid, cycle, ex_list, ex_data):
    '''
    We expect the following arguments:

      - ID of replica running this script
      - current cycle number
      - list of replica IDs in the exchange list
      - list of filename patterns (containing `%(rid)s`)

    We select random pairs of replicas from the replica list and pairwise
    exchange the file content of their `mdin` and `inpcrd` files
    '''

    import random
    random.shuffle(ex_list)

    while len(ex_list) >= 2:

        a = ex_list.pop()
        b = ex_list.pop()

        print('%s [%04d]: %s <-> %s' % (rid, cycle, a, b))

        for dname in ex_data:

            fa = dname % {'rid': a}
            fb = dname % {'rid': b}

            print(' %s <-> %s' % (fa, fb))

            with open(fa, 'r') as fin : data_a = fin.read()
            with open(fb, 'r') as fin : data_b = fin.read()
            with open(fa, 'w') as fout: fout.write(data_b)
            with open(fb, 'w') as fout: fout.write(data_a)


# ------------------------------------------------------------------------------

