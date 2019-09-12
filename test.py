#!/usr/bin/python

#import httplib as http_client
#http.client.HTTPConnection.debuglevel = 1

import sys, os
from optparse import OptionParser
from resources.lib.tsngo import *
from resources.lib.auth.oauth import OAuth
from resources.lib.schedule import *

# parse the options
parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option('-i', '--id', type='int', dest='id',
                  help="Channel ID")
parser.add_option('-m', '--mso', type='string', dest='mso', default=None,
                  help="Multi-system operator (eg: Rogers)")
parser.add_option('-s', '--schedule', action='store_true', dest='schedule')
(options, args) = parser.parse_args()


if options.user != None and options.password != None:
    if options.mso == None:
        print('Please specify MSO')
        parser.print_help()
        sys.exit(1)
    oa = OAuth()
    if not oa.authorize(options.mso, options.user, options.password):
        print('Authorization failed')
        sys.exit(1)
    else:
        print('Authorization succeeded')
        sys.exit(0)

tsn = TsnGo()
#tsn.getIdentity()
if not options.id == None:

    content_id = tsn.getMpdInfoURL(options.id)
    print('{} -> {}'.format(options.id, content_id))

    mpd_info = tsn.getMpdInfo(options.id, content_id)
    print('MPD info: {}'.format(mpd_info))

    authz = tsn.getMpdAuthz(mpd_info)
    print('Authz = "{}"'.format(authz))

    if not tsn.checkMpdAuthz(authz):
        print('Unable to get MPD URL')
        sys.exit(1)

    print('Authorized! Getting MPD URL...')

    mpd_url = tsn.getMpdUrl(options.id, content_id, authz)
    print('MPD URL is "{}"'.format(mpd_url))
else:
    streams = tsn.getStreams()
    for stream in streams:
        item = Schedule.getCurrentProgram(stream['desc'])
        if options.schedule:
            print('\tstream: {}\n\titem: {}'.format(stream, item))
        title = item['Title'] if 'Title' in item else ''
        print('{}) {} - {}'.format(stream['id'], stream['desc'], title))
