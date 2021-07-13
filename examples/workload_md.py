#!/usr/bin/env python


# ------------------------------------------------------------------------------
#
def prepare_md(wl):
    '''
    Write replica config files according to the given configuration.  The
    resulting config files are stored in the directory <inputs>.  The directory
    is created by the script.  If it exists, it is the responsibility of the
    caller to ensure that no file name collisions occur - existing files will be
    overwritten!

    This method also prepares the <outputs> directory.
    '''

    import os
    import glob

    bname   = wl.prepare.basename
    inputs  = wl.data.inputs
    outputs = wl.data.outputs
    nreps   = wl.config.replicas
    nsteps  = wl.config.timesteps
    tmin    = wl.config.min_temp
    tmax    = wl.config.max_temp
    tstep   = (tmax - tmin) / nreps

    try           : os.makedirs(inputs)
    except OSError: pass

    try           : os.makedirs(outputs)
    except OSError: pass

    for fname in glob.glob('%s/*' % bname):
        if fname.endswith('/mdin'):
            continue
        os.system('cp -v %s %s/' % (fname, inputs))

    for i in range(nreps):

        temp = tmin + i * tstep

        with open('%s/mdin' % bname, 'r') as fin:
            tbuffer  = fin.read()
            tbuffer  = tbuffer.replace('@temperature@', str(temp))
            tbuffer  = tbuffer.replace('@timesteps@',   str(nsteps))

        fname = '%s/mdin.rep.%04d' % (inputs, i)
        with open(fname, 'w') as fout:
            fout.write(tbuffer)

        os.system('cp %s/inpcrd %s/inpcrd.rep.%04d' % (bname, inputs, i))

    # `inputs` should be staged as `shared_data`
    return inputs


# ------------------------------------------------------------------------------

