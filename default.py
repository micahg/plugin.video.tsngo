from resources.lib.tsngo import *
from resources.lib.auth.oauth import OAuth
from resources.lib.utils import log
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse
import inputstreamhelper

getSetting = xbmcaddon.Addon().getSetting
getString = xbmcaddon.Addon().getLocalizedString

def getAuthCredentials():
    """
    Get the authorization credentials
    """
    username = getSetting("username")
    if len(username) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    password = getSetting("password")
    if len(password) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    mso = getSetting("mso")

    return { 'u' : username, 'p' : password, 'm' : mso }


def authorize(tsn):
    creds = getAuthCredentials()
    oa = OAuth()
    oa.authorize(creds['m'], creds['u'], creds['p'])
    return


def channelMenu(stream):
    """
    @param stream A stream object, containing a desc, img and id
    """
    for stream in streams:
        item = xbmcgui.ListItem(stream['desc'])
        item.setIconImage(stream['img'])
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(stream),
                                    listitem=item,
                                    isFolder=True)
    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return


def playMpd(url, desc):
    inputstream_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not inputstream_helper.check_inputstream():
        # TODO pop-up an error
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-CA%2Cen-GB%3Bq%3D0.9%2Cen-US%3Bq%3D0.8%2Cen%3Bq%3D0.7',
        'Host': 'pe-fa-lp01a.9c9media.com',
        'Origin': 'https://www.tsn.ca',
        'Referer': 'https://www.tsn.ca/live',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'content-type': '',
        'Accept-Charset': ''
    };
    header_str = '&'.join(["{}={}".format(k, v) for k, v in headers.items()])
    lic_srv = 'https://license.9c9media.ca/widevine|{}|R{{SSM}}|'.format(header_str)

    labels = {'TVShowTitle': desc}
    li = xbmcgui.ListItem(desc)
    li.setInfo(type="Video", infoLabels=labels)
    li.setMimeType('application/dash+xml')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.license_key', lic_srv)
    #li.setProperty('inputstream.adaptive.license_key', 'https://license.9c9media.ca/widevine||R{SSM}|')
    p = xbmc.Player()
    p.play(url, li)


def playChannel(tsn, id, desc, img, reauth=False):
    """
    Play the indicated channel
    """
    log('MICAH playing {} {}'.format(id, desc), True)
    content_id = tsn.getMpdInfoURL(id)
    log('MICAH {} -> {}'.format(id, content_id), True)
    mpd_info = tsn.getMpdInfo(id, content_id)
    log('MICAH MPD info: {}'.format(mpd_info), True)

    authz = tsn.getMpdAuthz(mpd_info)
    log('MICAH Authz = "{}"'.format(authz), True)

    if reauth:
        # TODO popup error
        log('Reauthorization failed', True)
        return

    if not tsn.checkMpdAuthz(authz):
        log("Attempting authorization", True)
        authorize(tsn)
        playChannel(tsn, id, desc, img, True)
        return

    log('Authorized! Getting MPD URL...', True)

    mpd_url = tsn.getMpdUrl(id, content_id, authz)
    log('MICAH MPD URL is "{}"'.format(mpd_url), True)

    playMpd(mpd_url, desc)


"""
Parse the plugin url
"""
tsn = TsnGo()
if len(sys.argv[2]) == 0:

    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    #authorize(tsn)

    streams = tsn.getStreams()
    channelMenu(streams)
else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if not 'id' in values:
        log('ERROR: Unable to get id', True)
        # TODO pop up dialog
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
        playChannel(tsn, values['id'][0], values['desc'][0], values['img'][0])
