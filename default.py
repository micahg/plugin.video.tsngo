from resources.lib.tsngo import *
from resources.lib.schedule import *
from resources.lib.auth.oauth import OAuth
from resources.lib.utils import log, getCookieFile
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse
import inputstreamhelper

getString = xbmcaddon.Addon().getLocalizedString

# handle logout before using argv[1] as the 
if sys.argv[1] == 'logout':
    log('Logging out... {}'.format(sys.argv[1]), True)
    xbmcaddon.Addon().setSetting('authorized', str(False))
    xbmcgui.Dialog().notification(getString(30056), getString(30061))
    sys.exit(0)

addon_handle = int(sys.argv[1])

def getAuthCredentials():
    """
    Get the authorization credentials
    """
    username = xbmcaddon.Addon().getSetting("username")
    if len(username) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(addon_handle, False)
        return None

    password = xbmcaddon.Addon().getSetting("password")
    if len(password) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(addon_handle, False)
        return None

    mso = xbmcaddon.Addon().getSetting("mso")

    return { 'u' : username, 'p' : password, 'm' : mso }


def authorize(tsn):

    # create a progress dialog
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30052))

    creds = getAuthCredentials()
    oa = OAuth()
    result = oa.authorize(creds['m'], creds['u'], creds['p'], prog.update)
    log('Authorization returned {}'.format(result), True)
    xbmcaddon.Addon().setSetting('authorized', str(result)) 
    prog.close()
    return


def channelMenu(tsn):
    """
    @param stream A stream object, containing a desc, img and id
    """
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30058), getString(30059))

    streams = tsn.getStreams()
    num_streams = len(streams)
    stream_num = 0
    for stream in streams:
        channel = stream['desc']
        info = Schedule.getCurrentProgram(channel)
        stream_num += 1
        pct = (float(stream_num) / float(num_streams)) * 100
        prog.update(int(pct), getString(30060).format(channel))

        # sort out the title before creating the item
        labels = {'title': channel, 'mediatype': 'video'}
        labels['title'] += ' - {}'.format(info['Title']) if 'Title' in info else ''

        item = xbmcgui.ListItem(labels['title'])

        # use the default image but if nicer images are available use them
        img_url = stream['img'] if 'img' in stream else None
        if 'Images' in info:
            for image in info['Images']:
                if image['Type'] == 'thumbnail':
                    img_url = image['Url']

        # if an image is found use it
        if not img_url == None:
            item.setArt({ 'thumb': img_url, 'poster': img_url })

        labels['PlotOutline'] = info['Desc'] if 'Desc' in info else None
        labels['Plot'] = info['Desc'] if 'Desc' in info else None

        item.setInfo('Video', labels)
        item.setProperty('IsPlayable', 'true')

        # add the info labels to the stream details
        stream['labels'] = labels

        path = sys.argv[0] + "?" + urllib.urlencode(stream)
        xbmcplugin.addDirectoryItem(addon_handle, path, item, False)
    # signal the end of the directory
    xbmcplugin.endOfDirectory(addon_handle)
    prog.close()
    return


def playMpd(url, labels):
    inputstream_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not inputstream_helper.check_inputstream():
        # TODO pop-up an error
        xbmcplugin.endOfDirectory(addon_handle)
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

    li = xbmcgui.ListItem(path=url)
    li.setInfo('video', infoLabels=labels)
    li.setMimeType('application/dash+xml')
    li.setProperty('inputstreamaddon', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    li.setProperty('inputstream.adaptive.license_key', lic_srv)
    li.setProperty('IsPlayable', 'true')
    return xbmcplugin.setResolvedUrl(addon_handle, True, li)


def playChannel(tsn, id, desc, img, labels):
    """
    Play the indicated channel
    """
    prog = xbmcgui.DialogProgress()
    prog.create(getString(30053))
    content_id = tsn.getMpdInfoURL(id)
    prog.update(25)
    mpd_info = tsn.getMpdInfo(id, content_id)
    prog.update(50)
    authz = tsn.getMpdAuthz(mpd_info)
    prog.update(75)

    if not tsn.checkMpdAuthz(authz):
        prog.close()
        xbmcaddon.Addon().setSetting('authorized', str(False))
        xbmcgui.Dialog().ok(getString(30054), getString(30055))
        return

    mpd_url = tsn.getMpdUrl(id, content_id, authz)
    prog.update(100)

    playMpd(mpd_url, labels)

"""
Parse the plugin url
"""
xbmcplugin.setContent(addon_handle, 'videos')
tsn = TsnGo()
if len(sys.argv[2]) == 0:

    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    if not xbmcaddon.Addon().getSettingBool('authorized'):
        authorize(tsn)

    if xbmcaddon.Addon().getSettingBool('authorized'):
        channelMenu(tsn)
    else:
        xbmcgui.Dialog().ok(getString(30054), getString(30055))
        xbmcplugin.endOfDirectory(addon_handle, False)
        xbmcaddon.Addon().setSetting('authorized', str(False))

else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if not 'id' in values:
        log('ERROR: Unable to get id', True)
        xbmcplugin.endOfDirectory(addon_handle, False)
    else:
        playChannel(tsn, values['id'][0], values['desc'][0], values['img'][0],
                    values['labels'][0])
