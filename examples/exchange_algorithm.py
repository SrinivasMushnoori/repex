#!/usr/bin/env python

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



import sys

rid     = None
cycle   = None
ex_list = list()
dn_list = list()

arg_mode = None
for arg in sys.argv[1:]:
    if   arg == '-r': arg_mode = 'rid'
    elif arg == '-c': arg_mode = 'cycle'
    elif arg == '-e': arg_mode = 'ex_list'
    elif arg == '-d': arg_mode = 'dn_list'
    else:
        if   arg_mode == 'rid'    : rid   = arg
        elif arg_mode == 'cycle'  : cycle = int(arg)
        elif arg_mode == 'ex_list': ex_list.append(arg)
        elif arg_mode == 'dn_list': dn_list.append(arg)



exchange_by_random(rid, cycle, ex_list, dn_list)

