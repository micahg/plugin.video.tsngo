# TSN Go Kodi Addon

The TSN Go Kodi addon -- play TSN live streams with your TSN Go (or Cable
provider) account. Uses inputstream.adaptive to play the video.

**NOTE**: This addon will probably die a quick and painless death. Unlike
Sportsnet, TSN doesn't really have an API -- its more of a Rube Goldberg style
series of calls that somehow result in video playback. Compatibility with any
external platform (let alone their own player) doesn't seem like much of a
priority for them and in all likelihood, the burden of maintenance will be too
high. Don't get too attached!

## What Works

* Some streams
  * after it fails the first time... this can be fixed
  * some streams don't play -- needs further investigation

## TODO
* Fix spinner on top of dialogs

## New API?

* https://idp.securetve.com/rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/identity/?format=jsonp&responsefield=aisresponse (line 19583)
  * gives back jsigblock (nonce, signature)
* https://webapps.9c9media.com/config/vidi-player/v1/tsn/autoplay-off.json
  * player configuration
  * seems to have the widevine stuff as well as other junk... might save a constant (eg: https://license.9c9media.ca/widevine)
  * player error constants
* https://webapps.9c9media.com/config/vidi-chromecast/v2/tsn/web-prod.json
  * seems similar to player configuraiton
  * contains 59cb81261a926ddc6abcc287cd8e3d6fbc119f77... conviva?
* https://users.9c9media.com/Accounts/Login (line 43881)
  * POST with data from jsig_block
  * returns access_token
* https://users.9c9media.com/Accounts/Login (line 47172 - second time)
  * POST that return access_token, same as before -- hopefully we can just ignore it
* https://users.9c9media.com/v3/Devices/Current
  * OPTIONS... 200 response
* https://users.9c9media.com/v3/Devices/Current
  * GET with auth token from Login
  * returns null...
* https://59cb81261a926ddc6abcc287cd8e3d6fbc119f77.cws.conviva.com/0/wsg (line 86857)
  * WTF IS THIS?
* https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/69585?%24include=%5BId%2CName%2CDesc%2CShortDesc%2CType%2COwner%2CMedia%2CSeason%2CEpisode%2CGenres%2CImages%2CContentPackages%2CAuthentication%2CPeople%2COmniture%2C+revShare%5D&%24lang=en
  * gives back id 
* https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/contents/69585/contentpackages/23535?%24include=%5BHasClosedCaptions%2CStacks.ManifestHost.mpd%5D

The failing call is /rest/1.0/urn:bellmedia:com:sp:tsn:prod:1/identity/resourceAccess/TSN?format=jsonp&responsefield=authzTSN&callback=authzTSN...