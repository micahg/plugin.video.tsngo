#!/usr/bin/python
import sys, os
from optparse import OptionParser
from resources.lib.tsngo import *
from resources.lib.auth.oauth import OAuth

# parse the options
parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option('-i', '--id', type='int', dest='id',
                  help="Channel ID")
parser.add_option('-m', '--mso', type='string', dest='mso', default='Rogers',
                  help="Multi-system operator (eg: Rogers)")
(options, args) = parser.parse_args()


if options.user != None and options.password != None:
    oa = OAuth()
    oa.authorize(u'rogers', options.user, options.password)

tsn = TsnGo()
if not options.id == None:

    content_id = tsn.getMpdInfoURL(options.id)
    print '{} -> {}'.format(options.id, content_id)

    mpd_info = tsn.getMpdInfo(options.id, content_id)
    print 'MPD info: {}'.format(mpd_info)

    authz = tsn.getMpdAuthz(mpd_info)
    print 'Authz = "{}"'.format(authz)

    if not tsn.checkMpdAuthz(authz):
        print 'Unable to get MPD URL'
        sys.exit(1)

    print 'Authorized! Getting MPD URL...'

    mpd_url = tsn.getMpdUrl(options.id, content_id, authz)
    print 'MPD URL is "{}"'.format(mpd_url)
    """
    print 'Auth status: {}'.format(auth)
    if auth['status'] == 'auth':
        print auth['url']
    elif auth['status'] == 'no_auth':
        print "Authorization required"
    else:
        print "Unknown error"
    """
else:  
    streams = tsn.getStreams()
    for stream in streams:
        print '{}) {}'.format(stream['id'], stream['desc'])