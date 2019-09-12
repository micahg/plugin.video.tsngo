#import requests.packages.urllib3.connectionpool as httplib
#httplib.HTTPConnection.debuglevel = 1
import requests, json, re, urllib
try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus
from .utils import saveCookies, loadCookies, log

class TsnGo:

    def __init__(self):
        self.STREAMS_URL = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/collections/83/contents?$include=[Authentication,Media.Name,images]'
        self.STREAM_DETAILS_FMT = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/{}?$include=[ContentPackages,Authentication]'
        self.MPD_DETAILS_FMT = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/{}/contentpackages/{}?$include=[HasClosedCaptions,Stacks.ManifestHost.mpd]'
        self.MPD_AUTH_FMT = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/identity/resourceAccess/{}?format=jsonp&responsefield=authz{}&callback=authz{}'
        self.MPD_AUTH_RESP_REGEX_FMT = 'authz{}\((.*)\)'
        self.MPD_FMT = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/{}/contentpackages/{}/manifest.mpd?az={}'
        self.MPD_REF_FMT = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/{}/contentpackages/{}/manifest.mpd?az={}&action=reference'
        self.WIDEVINE_URL = 'https://license.9c9media.ca/widevine'
        self.session = requests.Session()

    def refreshCookies(self):
        """
        Set the session cookies to the saved session cookies, so long as the
        saved cookies are valid
        """
        session_cookies = loadCookies()
        if not session_cookies == None:
            self.session.cookies = session_cookies


    def getStreams(self):
        """
        Get the stream list
        @return A list of streams, each with an id, desc and img
        """
        self.refreshCookies()
        r = self.session.get(self.STREAMS_URL)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        streams = []
        items = json.loads(r.content)['Items']
        for item in items:
            stream = {
                'id': item['Id'],
                'desc': item['Name']
            }
            if 'Images' in item and len(item['Images']) > 0:
                stream['img'] = item['Images'][0]['Url']
            else:
                stream['img'] = None
            streams.append(stream)
        return streams


    def getMpdInfoURL(self, id):
        """
        Get the mpd info url for the stream
        @param id The stream ID (according to getSTreams)
        @return the content id.
        """
        self.refreshCookies()
        url = self.STREAM_DETAILS_FMT.format(id)
        r = self.session.get(url)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        item = json.loads(r.content)

        return item['ContentPackages'][0]['Id']


    def getMpdInfo(self, id, content_id):
        """
        Get the content package ID for the stream
        @param id The stream ID (according to getSTreams)
        @return the content id.
        """
        self.refreshCookies()
        url = self.MPD_DETAILS_FMT.format(id, content_id)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        item = json.loads(r.content)

        return {
            'auth_type': item['Constraints']['Security']['Type'],
            'auth_res': item['Constraints']['Authentication']['Resources'][0]['ResourceCode'],
            'host': item['ManifestHost']
        }

    def getMpdAuthz(self, mpd_info):
        self.refreshCookies()
        # Why the fuck are we using TSN2?!?!?!?!
        auth_res = mpd_info['auth_res']
        url = self.MPD_AUTH_FMT.format(auth_res, auth_res, auth_res)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        regex_fmt = self.MPD_AUTH_RESP_REGEX_FMT.format(auth_res)
        stuff = re.search(regex_fmt, r.content.decode('utf-8'))
        if not stuff:
            log('ERROR: Unable to parse MPD AI response "{}"'.format(r.content), True)
            return { 'status': 'unknown' }

        return stuff.group(1)


    def checkMpdAuthz(self, authz):
        self.refreshCookies()
        auth = json.loads(authz)
        if not 'authorization' in auth:
            log('ERROR: No authorization element in AI response "{}"'.format(auth), True)
            return False

        if not auth['authorization'] == True:
            log('ERROR: AI response had authorization value of "{}" ({})'.format(auth['authorization'], authz), True)
            return False

        return True

    def getMpdUrl(self, id, content_id, authz):
        self.refreshCookies()
        #url = self.MPD_REF_FMT.format(id, content_id, urllib.quote_plus(authz))
        url = self.MPD_REF_FMT.format(id, content_id, quote_plus(authz))
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)
        return r.content
