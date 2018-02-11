import requests, json, re, urllib
from utils import saveCookies, loadCookies, log

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

        # load the cookies from any previou session into the current session
        self.session = requests.Session()
        session_cookies = loadCookies()
        if not session_cookies == None: 
            self.session.cookies = session_cookies 

    def getStreams(self):
        """
        Get the stream list
        @return A list of streams, each with an id, desc and img
        """
        r = self.session.get(self.STREAMS_URL)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies)

        streams = []
        items = json.loads(r.text)['Items']
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
        r = self.session.get(self.STREAM_DETAILS_FMT.format(id))

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None
        saveCookies(self.session.cookies) 

        item = json.loads(r.text)

        return item['ContentPackages'][0]['Id']


    def getMpdInfo(self, id, content_id):
        """
        Get the content package ID for the stream
        @param id The stream ID (according to getSTreams)
        @return the content id.
        """
        url = self.MPD_DETAILS_FMT.format(id, content_id)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None 
        saveCookies(self.session.cookies)

        item = json.loads(r.text)

        return {
            'auth_type': item['Constraints']['Security']['Type'],
            'auth_res': item['Constraints']['Authentication']['Resources'][0]['ResourceCode'],
            'host': item['ManifestHost']
        }

    def getMpdAuthz(self, mpd_info):
        auth_res = mpd_info['auth_res']
        url = self.MPD_AUTH_FMT.format(auth_res, auth_res, auth_res)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None 
        saveCookies(self.session.cookies)

        regex_fmt = self.MPD_AUTH_RESP_REGEX_FMT.format(auth_res)
        stuff = re.search(regex_fmt, r.text)
        if not stuff:
            log('ERROR: Unable to parse MPD AI response "{}"'.format(r.text), True)
            return { 'status': 'unknown' }

        return stuff.group(1)


    def checkMpdAuthz(self, authz):
        auth = json.loads(authz)
        if not 'authorization' in auth:
            log('ERROR: No authorization element in AI response "{}"'.format(r.text), True)
            return False

        if not auth['authorization'] == True:
            log('ERROR: AI response had authorization value of "{}" ({})'.format(auth['authorization'], r.text), True)
            return False

        return True

    def getMpdUrl(self, id, content_id, authz):
        url = self.MPD_REF_FMT.format(id, content_id, urllib.quote_plus(authz))
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None 
        saveCookies(self.session.cookies)
        return r.text

    """
    def getMpdUrl(self, id, content_id, mpd_info):
        auth_res = mpd_info['auth_res']
        regex_fmt = self.MPD_AUTH_RESP_REGEX_FMT.format(auth_res)
        url = self.MPD_AUTH_FMT.format(auth_res, auth_res, auth_res)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None 
        saveCookies(self.session.cookies)

        stuff = re.search(regex_fmt, r.text)
        if not stuff:
            log('ERROR: Unable to parse MPD AI response "{}"'.format(r.text), True)
            return { 'status': 'unknown' }

        js_str = stuff.group(1)
        auth = json.loads(js_str)
        if not 'authorization' in auth:
            log('ERROR: No authorization element in AI response "{}"'.format(r.text), True)
            return { 'status': 'no_auth' }

        if not auth['authorization'] == True:
            log('ERROR: AI response had authorization value of "{}" ({})'.format(auth['authorization'], r.text), True)
            return { 'status': 'no_auth'}

        return {
            'status': 'auth',
            'url': self.MPD_FMT.format(id, content_id, urllib.quote_plus(js_str))
        }

    def getMpdRefUrl(self, id, content_id, mpd_info):
        auth_res = mpd_info['auth_res']
        regex_fmt = self.MPD_AUTH_RESP_REGEX_FMT.format(auth_res)
        url = self.MPD_AUTH_FMT.format(auth_res, auth_res, auth_res)
        r = self.session.get(url)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return None 
        saveCookies(self.session.cookies)

        stuff = re.search(regex_fmt, r.text)
        if not stuff:
            log('ERROR: Unable to parse MPD AI response "{}"'.format(r.text), True)
            return { 'status': 'unknown' }
        MPD_REF_FMT
    """