# dump a display of running and pending builds for the fedora 32 test slaves
#
# this assumes you have a builds-running.js & builds-pending.js on disk from
#  https://secure.pub.build.mozilla.org/builddata/buildjson/builds-running.js
#  https://secure.pub.build.mozilla.org/builddata/buildjson/builds-pending.js

import json
import time
import os
import re

# from buildapi/buildapi/model/util.py
RELEVENT_BUILDERS = {
    re.compile('^Rev3 Fedora 12 .+'),
    re.compile('jetpack-.*-fedora(?!64)'),
    re.compile('^b2g_.+(opt|debug) test.+',  re.IGNORECASE)
}

# from buildbot-configs/mozilla/master_common.py
# otherwise defaults to 2
BRANCH_PRIORITIES = {
    'mozilla-central': 3,
    'comm-central': 3,
    'mozilla-aurora': 3,
    'comm-aurora': 3,
    'mozilla-beta': 2,
    'comm-beta': 2,
    'mozilla-release': 0,
    'comm-release': 0,
    'mozilla-esr10': 1,
    'mozilla-esr17': 1,
    'mozilla-b2g18': 1,
    'mozilla-b2g18_v1_0_0': 1,
    'comm-esr10': 1,
    'comm-esr17': 1,
    'try': 4,
    'try-comm-central': 4,
    'alder': 5,
    'ash': 5,
    'birch': 5,
    'cedar': 5,
    'date': 5,
    'elm': 5,
    'fig': 5,
    'gum': 5,
    'holly': 5,
    'jamun': 5,
    'larch': 5,
    'maple': 5,
    'oak': 5,
    'pine': 5,
}

# neglecting this for now, in prod it's used to match on builder.name rather than the pretty name we get from buildapi
# otherwise defaults to 100
BUILDER_PRIORITIES = [
    (re.compile('b2g(-debug)?_test'), 50),
]

PRINT_FORMAT = "%s  %10s  %10s  %-20s  %-12s  %s"

def isRelevantBuilder(buildername):
    for pat in RELEVENT_BUILDERS:
       if pat.match(buildername):
           return True
    return False    

def sortkey(build):
    return build[2], build[0], -build[1], build[3]

def processBuilds(builds, priorities):
    result = []
    for p in priorities:
        for branch in priorities[p]:
            if branch in builds:
                b_br = builds[branch]
                for revision in b_br:
                    b_br_rev = b_br[revision]
                    for build in b_br_rev:
                        name = build['buildername']
                        if isRelevantBuilder(name):
                            start = now - build.get('start_time', now)
                            result.append((p, now - build['submitted_at'],
                                           start, branch, revision, name))
    return result


# force California times
os.environ['TZ'] = 'America/Pacific'
now = int(time.time())

# rejig the priorities by increasing priority order
priorities = {}
for k,v in BRANCH_PRIORITIES.iteritems():
    priorities.setdefault(v, []).append(k)

# load up the builds
pending_builds = json.load(open('builds-pending.js'))['pending']
running_builds = json.load(open('builds-running.js'))['running']

# default to priority 2 for any undefined branches
for branch in running_builds.keys() + pending_builds.keys():
  if branch not in BRANCH_PRIORITIES and branch not in priorities[2]:
     print "defaulting to priority 2 for branch %s" % branch
     priorities[2].append(branch)

# process build info
running = processBuilds(running_builds, priorities)
pending = processBuilds(pending_builds, priorities)


# sort + pretty print
print "\nBranch priorities:"
for p in priorities:
    priorities[p] = sorted(priorities[p])
    print p, ", ".join(priorities[p])

print "\nRunning builds   (as they started, then priority+wait sort)"
print PRINT_FORMAT % ('Pri.', 'Wait (s)', 'Run (s)', 'Branch',
                      'Revision', 'Builder name')
for r in sorted(running, key=sortkey):
    print PRINT_FORMAT % r

print "\nPending builds   (priority then wait sort)"
print PRINT_FORMAT % ('Pri.', 'Wait (s)', 'Run (s)', 'Branch',
                      'Revision', 'Builder name')
for p in sorted(pending, key=sortkey):
    print PRINT_FORMAT % p
