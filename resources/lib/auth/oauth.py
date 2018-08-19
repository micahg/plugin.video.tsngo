#import httplib as http_client
#http_client.HTTPConnection.debuglevel = 1
import requests, json, re, os
from ..utils import saveCookies, log
from urlparse import urlparse
from bs4 import BeautifulSoup

class OAuth:

    def __init__(self):
        self.CONFIG_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/init/urn:tsn:ca:idp:prod?responsemethod=redirect&format=jsonp&responsetarget=prod2https'
        self.SECOND_URL = 'https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/init/urn:rogers:com:idp:prod?responsemethod=redirect&format=jsonp&responsetarget=prod2https'
        self.session = requests.Session()
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
        if idp.lower() == 'rogers':
            credentials['UserName'] = username
            credentials['UserPassword'] = password
        elif idp.lower() == 'bell':
            credentials['USER'] = username
            credentials['PASSWORD'] = password
        elif idp.lower() == 'telus':
            credentials = credentials
        else:
            log('Unsupported idp: "{}"'.format(idp))
            return False

        r = self.session.post(self.CONFIG_URL)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.CONFIG_URL, r.status_code), True)
            return None

        return self.standardAuthorize(self.SECOND_URL, credentials)


    def standardAuthorize(self, url, credentials):

        post = False
        values = {}
        while True:
            if not post:
                r = self.session.get(url)
            else:
                r = self.session.post(url, data = values)

            # if the request was not successful log an error and return false
            if not r.status_code == 200:
                log('{} returns status {}'.format(url, r.status_code), True)
                return False

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
            """
            This little bit is to work around telus using javascript to submit
            their logon form - annoying 
            """
            if not action:
                print r.content
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
                return False

            # reset the values
            values = {}
            for input in form.find_all('input'):

                ''' get the input name and value. If there is no value it might
                    be our credentials ''' 
                input_name = input.get('name')
                input_value = input.get('value')
                if not input_value == None and not input_name == None:
                    values[input_name] = input_value
                elif input_name in credentials.keys():
                    values[input_name] = credentials[input_name]

        return False
