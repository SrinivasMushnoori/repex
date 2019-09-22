#!/usr/bin/env python

import random


# ------------------------------------------------------------------------------
#
def create_list(repnum=100, t_min=100, t_max=200):
    '''
    This helper method will create a list of replicas waiting for an exchange.
    The returned list consists of tuples [replic_uid, temperature], like this:

      [['replica.075',  111],
       ['replica.056',  184],
       ['replica.057',  156],
       ['replica.082',  187],
       ['replica.068',  122],
       ['replica.029',  172]]

    repnum:  number of replicas
    t_min :  minimal temperatire
    t_max :  maximal temperature
    '''

    ret    = list()
    for n in range(repnum):

        uid  = 'replica.%03d' % n
        temp = random.randint(t_min, t_max)

        ret.append([uid, temp])

    # sort entries by temperature.
    return sorted(ret, key=lambda x: x[1])


# ------------------------------------------------------------------------------
# 
def get_ranges(replica_list, temp_range, min_replicas):
    '''
    Find all sublists in the replica list where at least `min_replicas` are
    within the given temperature range.  The method also returns a new replica
    list which has all replicas found in interesting temperatre ranges removed

    Example:  

      replica_list = [['replica.075',  111],
                      ['replica.057',  156],
                      ['replica.082',  157],
                      ['replica.056',  163],
                      ['replica.068',  183],
                      ['replica.029',  184]]

      new_list, ranges = get_populated_ranges(replica_list, 10, 2)

      replica_list = [['replica.075',  111]]

      ranges       = [[['replica.056',  156],
                       ['replica.056',  157],
                       ['replica.057',  163]], 

                      [['replica.068',  183],
                       ['replica.029',  184]]]
    '''

    ranges           = list()
    new_replica_list = list()  # new replica list to return
    last_range       = None    # avoid rechecking replicas


    # scan through the list and determine start temp for the tange
    for replica in replica_list:

        # ignore this replica if it was part of the last range
        if last_range and replica[0] in last_range:
            continue

        t_start = replica[1]
        t_end   = t_start + temp_range

        # find replicas in list within that temperature range
        temp_list =  [t for t in replica_list
                        if (t[1] >= t_start and t[1] <= t_end)]

        # is that list long enough to be interesting?
        if len(temp_list) < min_replicas:

            # no - put the start replica in the new replica list
            new_replica_list.append(replica)

        else:
            # yes - store range for return
            ranges.append(temp_list)

            # create a list of replicia IDs to check 
            # against to avoid duplication
            last_range = [r[0] for r in temp_list]

    return new_replica_list, ranges


# ------------------------------------------------------------------------------
#
import pprint

replicas = create_list(20)
print 'origin list'
pprint.pprint(replicas)
print

replicas, ranges = get_ranges(replicas, 10, 3)

print 'remaining list'
pprint.pprint(replicas)
print

print 'temp ranges'
for r in ranges:
    pprint.pprint(r)
    print



