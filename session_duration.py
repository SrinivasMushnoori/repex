#!/usr/bin/env python

import os
import sys
import glob
import pprint
import radical.utils as ru
import radical.pilot as rp
import radical.analytics as ra

__copyright__ = 'Copyright 2013-2016, http://radical.rutgers.edu'
__license__   = 'MIT'

"""
Radical Analytics method ra.Session.duration(). Adapted from RADICAL Analytics.
"""

# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    if len(sys.argv) != 2:
        print "\n\tusage: %s <dir>\n" % sys.argv[0]
        sys.exit(1)

    src = sys.argv[1]

    # find json file in dir, and derive session id
    json_files = glob.glob('%s/*.json' % src)

    if len(json_files) < 1: raise ValueError('%s contains no json file!' % src)
    if len(json_files) > 1: raise ValueError('%s contains more than one json file!' % src)

    json_file = json_files[0]
    json      = ru.read_json(json_file)
    sid       = os.path.basename(json_file)[:-5]

    print 'sid: %s' % sid

    session = ra.Session(sid, 'radical.pilot', src=src)

    # A formatting helper before starting...
    def ppheader(message):
        separator = '\n' + 78 * '-' + '\n'
        print separator + message + separator

    # and here we go. Once we filter our session object so to keep only the
    # relevent entities (as seen in example 03), we are ready to perform our
    # analyses :) Currently, RADICAL-Analytics supports two types of analysis:
    # duration and concurrency. This examples shows how to use the RA API to
    # performan duration analysis, using both states and events.
    #
    # First we look at the state model of our session. We saw how to print it
    # out in example 00:
    ppheader("state models")
    pprint.pprint(session.describe('state_model'))

    # Let's say that we want to see for how long all the pilot(s) we use have
    # been active. Looking at the state model of the entity of type 'pilot' and
    # to the documentation of RADICAL-Pilot, we know that a pilot is active
    # between the state 'ACTIVE' and one of the three final states 'DONE',
    # 'CANCELED', 'FAILED' of all the entities of RP.
    ppheader("Time spent by the pilots being active")
    pilots = session.filter(etype='pilot', inplace=False)
    durations = pilots.duration([rp.PMGR_ACTIVE, rp.FINAL])
    pprint.pprint(durations)

    # Now, we want to do the same for the all the entities of type 'unit':
    ppheader("Time spent by the units being active")
    units = session.filter(etype='unit', inplace=False)
    duration_active = units.duration([rp.AGENT_EXECUTING, rp.FINAL])
    pprint.pprint(duration_active)

    conc = units.concurrency(state=[rp.AGENT_EXECUTING,
                                    rp.AGENT_STAGING_OUTPUT_PENDING],
                                    sampling=2.0)
    pprint.pprint(conc)

    # The careful reader will have noticed that the previous duration includes
    # the time spent by the units to execute and to stage data out. We can
    # separate the two by using the state 'AGENT_STAGING_OUTPUT_PENDING',
    # instead of the final states:
    ppheader("Time spent by the units executing their kernel")
    units = session.filter(etype='unit', inplace=False)
    duration_exec = units.duration([rp.AGENT_EXECUTING, rp.AGENT_STAGING_OUTPUT_PENDING])
    pprint.pprint(duration_exec)

    # We calculate the time spent doing staging out by all entities of type
    # 'unit' with 'AGENT_STAGING_OUTPUT_PENDING' and the final states:
    ppheader("Time spent by the units performing staging out")
    units = session.filter(etype='unit', state=rp.DONE, inplace=False)
    duration_sout = units.duration([rp.AGENT_STAGING_OUTPUT_PENDING, rp.FINAL])
    pprint.pprint(duration_sout)

    # we print the timestamps for the units for when they entered certain states
    ppheader("Timestamps for state transitions")
    print '[rp.AGENT_STAGING_OUTPUT_PENDING]:'
    pprint.pprint(units.timestamps(state=[rp.AGENT_STAGING_OUTPUT_PENDING]))
    print 'rp.AGENT_EXECUTING'
    pprint.pprint(units.timestamps(state=rp.AGENT_EXECUTING))
    print '[rp.AGENT_EXECUTING, rp.AGENT_STAGING_OUTPUT_PENDING]'
    pprint.pprint(units.timestamps(state=[rp.AGENT_EXECUTING, rp.AGENT_STAGING_OUTPUT_PENDING]))

    print """ The very careful reader may have noticed that the sum of the time
    spent by the units to execute their kernel and performing staging out may be
    greater than the time spent by the units being active. This is explained by
    the potential overlapping between the time spent executing the kernell and
    that spent staging out. This overlapping is accounted for when calculating
    the time spent by the units being active."""

    ppheader("Ovelapping between executing and staging")
    overlap = (duration_exec + duration_sout) - duration_active
    print overlap

    sys.exit(0)
