Development
===========

Overview
--------
The _AmazonMusic_ library works in two parts:

1. Authenticating through the Amazon login portal, and saving the cookies in a cookie jar (by default `~/.amazonmusic-cookies.dat`)
2. Accessing the JSON API, used by the Amazon Music web interface, to access stations, tracks etc.

It is important, particularly during (1), to appear to be a normal browser - paying particular attention to `Accept` and `Accept-Language` headers.

Once authenticated, web portal is loaded and a JSON object, `amznMusic.appConfig` is retrieved. This provides information that is necessary to send in subsequent JSON API calls - in particular, CSRF (Cross-Site Request Forgery) tokens; and device & customer IDs.

The JSON calls themselves are to various HTTP endpoints and in addition to HTTP headers including the CSRF tokens, include an `X-Amz-Target` header. This looks like a fully-qualified Java class name, corresponding to the target action.

Known Endpoints
---------------

URL  | Target | Description 
-----|--------|----------------
/EU/api/mpqs/voiceenabled/createQueue | com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.createQueue | Create a queue for a station (and other types of queuable item?)
/EU/api/muse/legacy/lookup | com.amazon.musicensembleservice.MusicEnsembleService.lookup | Look up the tracks for an album (and other types of defined list, such as a playlist?)
/EU/api/dmls/ | com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getRestrictedStreamingURL | Get the URL to stream a track
/EU/api/mpqs/voiceenabled/getNextTracks | com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.getNextTracks | Get the next page for a queue
/EU/api/search/v1_1/ | com.amazon.tenzing.v1_1.TenzingServiceExternalV1_1.search | Perform a search

The `AmazonMusic.call` method can be used to call these APIs and get responses. This is used throughout the library, and can also be used directly (although this is discouraged, since those features should be rolled into the API).

Analysis
--------

To identify new endpoints, and the request/response format, using a browser's development tools is easiest:

1. Open a private browsing window
2. Navigate to [https://music.amazon.co.uk/](https://music.amazon.co.uk/)
3. Open the web development tools in the browser (for example, pressing F12 in Firefox)
4. Open the _Network_ tab and filter it to XMLHttpRequest POSTs
5. Perform an action and inspect the calls made

Confirming the format of the endpoint URLs for other regions and territories would be very helpful!