#!/usr/bin/env python

import os
import sys

import radical.utils as ru


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    '''
    usage   : %s <config> <path>
    synopsis:
        Write replica config files according to the given configuration.
        The resulting config files are stored in the directory <path>.  The
        directory is created by the script.  If it exists, it is the
        responsibility of the caller to ensure that no file name collisions
        occur - existing files will be overwritten!
    ''' % sys.argv[0]

    # check what workload the replicas should run
    if len(sys.argv) != 3:
        print 'Usage: %s <config> <path>' % sys.argv[0]
        sys.exit(1)

    wl   = ru.read_json(sys.argv[1])
    path = sys.argv[2]

    try:
        os.makedirs(path)
    except OSError:
        pass

    nreps  = wl['replicas']
    nsteps = wl['timesteps']
    bname  = wl['basename']
    tmin   = wl['min_temp']
    tmax   = wl['max_temp']
    tstep  = (tmax - tmin) / nreps

    for i in range(nreps):

        print 'create inputs for replica %d' % i

        temp = tmin + i * tstep

        with open('%s/mdin' % bname, 'r') as fin:
            tbuffer  = fin.read()
            tbuffer  = tbuffer.replace('@temperature@', str(temp))
            tbuffer  = tbuffer.replace('@timesteps@',   str(nsteps))

        fname = '%s/mdin-%d' % (path, i)
        print 'writing %s' % fname
        with open(fname, 'w') as fout:
            fout.write(tbuffer)

        os.system('cp %s/inpcrd %s/inpcrd-%d' % (bname, bname, i))


# ------------------------------------------------------------------------------

