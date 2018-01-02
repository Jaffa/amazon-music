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

Changes to `AmazonMusic` must be tested in both Python 2 and Python 3.

Known Endpoints
---------------

URL  | Target | Description 
-----|--------|----------------
/EU/api/mpqs/voiceenabled/createQueue | com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.createQueue | Create a queue for a station
/EU/api/muse/legacy/lookup | com.amazon.musicensembleservice.MusicEnsembleService.lookup | Look up the tracks for an album or playlist
/EU/api/dmls/ | com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getRestrictedStreamingURL | Get the URL to stream a track
/EU/api/mpqs/voiceenabled/getNextTracks | com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.getNextTracks | Get the next page for a queue
/EU/api/search/v1_1/ | com.amazon.tenzing.v1_1.TenzingServiceExternalV1_1.search | Perform a search
/EU/api/muse/legacy/getBrowseRecommendations | com.amazon.musicensembleservice.MusicEnsembleService.getBrowseRecommendations | Browse recommendations

The `AmazonMusic.call` method can be used to call these APIs and get responses. This is used throughout the library, and can also be used directly (although this is discouraged, since those features should be rolled into the API).

### Searching

A number of search models exist:

Model | Parameters | Description
------|------------|--------------------
BooleanQuery | must<Query>, must_not<Query>, should<Query> | Allows building of composite queries
ExistsQuery | fieldName | The field exists and has a non-null value
MatchQuery | fieldName, matchType, query | The given field matches `query`. By default, `fieldName` and `matchType` must be defaulted to values that mean "all fields"
MultiMatchQuery | fieldNames<String>, multiMatchType, query | Unknown
RangeQuery | fieldName, gt, gte, lt, lte | The given field matches the constraints
StringQuery | query | Unknown
TermQuery | fieldName, term | The given field has the exact value

Unfortunately, although `trackCount` is a parameter on the `Album` object, I can't make the following filter for albums work; nor can I get it returned from  the Tenzing service as a result field:

```javascript
"__type": "com.amazon.music.search.model#RangeQuery",
"fieldName": "trackCount",
"gte": "4"
```

Analysis
--------

To identify new endpoints, and the request/response format, using a browser's development tools is easiest:

1. Navigate to [https://music.amazon.co.uk/](https://music.amazon.co.uk/)
2. Open the web development tools in the browser (for example, pressing F12 in Firefox)
3. Open the _Network_ tab and filter it to XMLHttpRequest POSTs
4. Perform an action and inspect the calls made

Confirming the format of the endpoint URLs for other regions and territories would be very helpful!

If working on `AmazonMusic.__init__`, and so the authentication mechanism, working in a private-browsing window is best, as no other Amazon cookies will obfuscate and confuse.

Amazon Music Unlimited vs. Prime Music
--------------------------------------

There are probably differences in the requests & responses between Music Unlimited subscribers and Prime members. At the moment, these haven't been identified, but candidates are:

### Initialisation
In `appConfig` there are a number of possibly interesting values:

* `featureController.noSubscription`: empty for me, as a Prime subscriber.
* `featureController.subscription`: `1` for me, as a Prime subscriber.
* `userData.unlimitedMusic`: `0` for me, as a Prime subscriber
* `userData.hawkfireAccess`: `0` for me, as a Prime subscriber, but (looking at `isPrimeOnlyCustomer()` in `digitalMusicWebPlayer.js`) this looks to be the codename for Music Unlimited, and so will be `1` in Music Unlimited.

### Searching

When searching the catalogue, one of the constraints is `primeStatus = PRIME`:

```javascript
  "query": {
    "__type": "com.amazon.music.search.model#BooleanQuery",
    "must": [
      {
        "__type": "com.amazon.music.search.model#MatchQuery",
        "query": "Adele 25"
      },
      {
        "__type": "com.amazon.music.search.model#TermQuery",
        "fieldName": "primeStatus",
        "term": "PRIME"
      }
    ]
  },
```

Looking at a de-minified version of `digitalMusicWebPlayer.js` suggests that the alternative for Music Unlimited would be `isMusicSubscription == true`.

