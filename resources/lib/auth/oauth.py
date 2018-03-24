import requests, json, re
from ..utils import saveCookies, log

class OAuth:

    def __init__(self):
        self.CONFIG_URL = 'http://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:3/init/'
        self.START_URL = self.CONFIG_URL + '{}?responsemethod=redirect&responsetarget=prod&lang=en'
        self.session = requests.Session()
        return

    def authorize(self, idp, username, password):
        """
        Authorize with the idp
        @param idp the provider (eg: rogers)
        """
        idp_str = self.map_idp(idp);
        log('{} -> {}'.format(idp, idp_str), True)
        result = self.start_oauth(idp_str, username, password)
        saveCookies(self.session.cookies)
        return result

    def map_idp(self, idp_name):
        """
        Get the IDP strign by name
        @param idp_name The IDP name (eg: Rogers)
        """
        # fetch the auth config
        r = self.session.post(self.CONFIG_URL)
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(self.CONFIG_URL, r.status_code), True)
            return None

        # load the json and get the list of idps
        js = json.loads(r.text)
        if not 'possible_idps' in js:
            log("ERROR: no idps available", True)
            return None


        # find the requested idp_name
        idp_str = None
        for idp_key in js['possible_idps'].keys():
            name_key = js['possible_idps'][idp_key]['name']
            if name_key.lower() == idp_name.lower():
                idp_str = idp_key
                break

        # error if the idp_name is not found
        if idp_str == None:
            log('ERROR: unable to match idp_name with name "{}"'.format(idp_name), True)
            return None

        return idp_str


    def start_oauth(self, idp_str, username, password):
        """
        Begin OAuth
        @param idp_str IDP URL string
        @param username The username
        @param password The password
        """
        regex_str = '<input.*? name="(.*?)".*? id="(.*?)".*? value="(.*?)".*?>'
        url_regex = '<form.*? action="(.*?)".*?>'

        url = self.START_URL.format(idp_str)
        r = self.session.get(url)
        
        if not r.status_code == 200:
            log('ERROR: {} returns status of {}'.format(url, r.status_code), True)
            return False 

        result = r.text
        values = {}
        while True:
            stuff = re.search(regex_str, result, re.MULTILINE)
            if not stuff:
                break
            result = result[stuff.end(3):-1]
            values[stuff.group(2)] = stuff.group(3)

        values['UserName'] = username
        values['UserPassword'] = password
        values['Login'] = 'Sign in'
        next_url =  r.url

        q = self.session.post(next_url, data = values)
        if not q.status_code == 200:
            log('ERROR: {} returns status of {}'.format(next_url, r.status_code), True)
            return False

        return True
