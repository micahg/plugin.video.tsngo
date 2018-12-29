#import requests.packages.urllib3.connectionpool as httplib
#httplib.HTTPConnection.debuglevel = 1
import requests, json, re, os
from ..utils import saveCookies, log
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from bs4 import BeautifulSoup

class OAuth:

    def __init__(self):
        self.CONFIG_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/init/urn:tsn:ca:idp:prod?responsemethod=redirect&format=jsonp&responsetarget=prod2https'
        self.SECOND_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/init/urn:{}:idp:prod?responsemethod=redirect&format=jsonp&responsetarget=prod2https'
        #self.SECOND_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/init/urn:shaw:ca:idp:prod?responsemethod=redirect&format=jsonp&responsetarget=prod2https'
        self.IDENTITY_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/identity/?format=jsonp&responsefield=aisresponse'
        self.USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        self.session = requests.Session()
        self.msos = {
            'shaw': 'shaw:ca',
            'rogers': 'rogers:com'
        }
        return

    def authorize(self, idp, username, password, callback = None):
        """
        Authorize with the idp
        @param idp the provider (eg: rogers)
        """
        result = self.start_oauth(idp, username, password)
        callback(66) if not callback == None else None
        saveCookies(self.session.cookies)
        callback(100) if not callback == None else None
        self.getIdentity()
        return result

    def start_oauth(self, idp, username, password):
        """
        Begin OAuth
        @param idp_str IDP URL string
        @param username The username
        @param password The password
        """
        regex_str = '<input.*? name="(.*?)".*? value="(.*?)".*?>'
        url_regex = '<form.*? action="(.*?)"'

        credentials = {}
        if not idp.lower() in self.msos.keys():
            log('Unsupported idp: "{}"'.format(idp))
            return False
        mso = self.msos[idp.lower()]

        if idp.lower() == 'rogers':
            credentials['UserName'] = username
            credentials['UserPassword'] = password
        elif idp.lower() == 'shaw':
            #credentials = credentials
            credentials['pf.username'] = username
            credentials['pf.pass'] = password
        elif idp.lower() == 'bell':
            credentials['USER'] = username
            credentials['PASSWORD'] = password
        elif idp.lower() == 'telus':
            credentials = credentials
        else:
            log('Unsupported idp: "{}"'.format(idp))
            return False

        headers = { 'User-Agent' : self.USER_AGENT}
        r = self.session.post(self.CONFIG_URL, headers = headers)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.CONFIG_URL, r.status_code), True)
            return None

        return self.standardAuthorize(self.SECOND_URL.format(mso), credentials)


    def standardAuthorize(self, url, credentials):
        post = False
        values = {}
        headers = { 'User-Agent' : self.USER_AGENT}
        while True:
            if not post:
                r = self.session.get(url, headers = headers)
            else:
                r = self.session.post(url, data = values, headers = headers)

            # if the request was not successful log an error and return false
            if not r.status_code == 200:
                log('{} returns status {}'.format(url, r.status_code), True)
                return False

            #print(r.content)

            # set URL to the previous url for relative form actions
            url = r.url
            html_doc = BeautifulSoup(r.content, 'html.parser')

            # I guess TSN ends on a page titled ais_response
            #if html_doc.find('title').string == 'ais_response':
            #    return True

            form = html_doc.find('form')
            if form == None:
                return True

            post = form.get('method').lower() == 'post'

            action = form.get('action')
            print('MICAH form is {}'.format(action))
            """
            This little bit is to work around telus using javascript to submit
            their logon form - annoying
            """
            if not action:
                for input in form.find_all('input'):
                    if input.get('name').lower() == 'authstate':
                        action = input.get('value')
                        action = action[action.find(':')+1:len(action)]
                        post = True

            if not action:
                log('Unable to determine redirect URL at {}'.format(r.url), True)
                return False

            # strip leading './' eg action="./authorize?blah=foo"
            if action[0:2] == './':
                action = action[2:len(action)]

            url_bits = urlparse(action)
            if not url_bits.netloc == '':
                # with a hostname, just use the whole url
                url = action
            elif url_bits.path[0] == '/':
                # no hostname but a path starting with / means append the path
                url_bits = urlparse(url)
                url = '{}://{}{}'.format(url_bits.scheme, url_bits.netloc,
                               action)
            else:
                # no hostname and path that doesn't start with / means append
                # the filename to the dirname of the prior url/path
                url_bits = urlparse(url)
                path = '{}/{}'.format(os.path.dirname(url_bits.path), action)
                url = '{}://{}{}'.format(url_bits.scheme, url_bits.netloc, path)

            if url == r.url:
                log('Directed to same login page. Authorizaiton likely failed')
                return True

            # reset the values
            values = {}
            for input in form.find_all('input'):

                ''' get the input name and value. If there is no value it might
                    be our credentials '''
                input_name = input.get('name')
                input_value = input.get('value')
                if input_value == '':
                    input_value = None
                #if not input_value == None and not input_name == None:
                if not input_value == None and not input_name == None:
                    values[input_name] = input_value
                elif input_name in credentials.keys():
                    values[input_name] = credentials[input_name]

        return False

    def getIdentity(self):
        """
        Make the identity call and save/return the json identity data
        """
        headers = { 'Referer': 'https://www.tsn.ca/live',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36' }
        r = self.session.get(self.IDENTITY_URL, headers=headers)

        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.IDENTITY_URL, r.status_code))
            return None

        return
