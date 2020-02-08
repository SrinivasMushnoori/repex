#!/usr/bin/env python3


# ------------------------------------------------------------------------------
#
def exchange_by_random(rid, cycle, ex_list, dn_list):
    '''
    We expect the following arguments:

      - ID of replica running this script
      - current cycle number
      - list of replica IDs in the exchange list
      - list of file basenames to exchange on

    We select random pairs of replicas from the replica list and pairwise
    exchange the file content of their `dn_list`.
    '''

    import random
    random.shuffle(ex_list)
    while len(ex_list) >= 2:

        a = ex_list.pop()
        b = ex_list.pop()

        print('%s [%04d]: %s <-> %s' % (rid, cycle, a, b))

        for dn in dn_list:
            fa = 'repex.%s.%s' % (a, dn)
            fb = 'repex.%s.%s' % (b, dn)

            print(' %s <-> %s' % (fa, fb))

            with open(fa, 'r') as fin : data_a = fin.read()
            with open(fb, 'r') as fin : data_b = fin.read()
            with open(fa, 'w') as fout: fout.write(data_b)
            with open(fb, 'w') as fout: fout.write(data_a)


# ------------------------------------------------------------------------------

