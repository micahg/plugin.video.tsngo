import os, requests.utils, pickle
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict

def getCookieFile():

    try:
        import xbmc, xbmcaddon
        base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    except:
        base = os.getcwd()

    return os.path.join(base, 'cookies')


def saveCookies(session_cookies):
    """
    Write cookies to the cookie file
    @param session_cookies the session.cookies object to save
    """
    with open(getCookieFile(), 'wb') as f:
        pickle.dump(session_cookies, f)
        f.close()


def loadCookies():
    """
    Load cookies from the cookie file into a session.cookies object
    @return a session.cookies object
    """
    try:
        with open(getCookieFile(), 'rb') as f:
            cookies = pickle.load(f)
            f.close()
            return cookies
    except IOError as err:
        log('Unable to load cookies: {}'.format(err), True)

    return None


def log(msg, error = False):
    """
    Log an error
    @param msg The error to log
    @param error error severity indicator
    """
    try:
        import xbmc
        full_msg = "plugin.video.tsngo: {0}".format(msg)
        xbmc.log(full_msg, level=xbmc.LOGERROR if error else xbmc.LOGINFO)
    except:
        print(msg)
