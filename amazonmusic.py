"""
This module implements an API for interacting with Amazon Music.

:copyright: 2018 Andrew Flegg
:license: Licensed under the Apache License, see LICENSE.
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bs4 import BeautifulSoup
import json
import urllib
import os
import requests
import re
import types
from http.cookiejar import LWPCookieJar

AMAZON_MUSIC='https://music.amazon.co.uk'
AMAZON_SIGNIN='https://www.amazon.co.uk/ap/signin'
USER_AGENT='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'

class AmazonMusic:
  """
    Allows interaction with the Amazon Music service through a programmatic
    interface.

    Usage::

      >>> from amazonmusic import AmazonMusic
      >>> from getpass import getpass
      >>> am = AmazonMusic(credentials = lambda: [input('Email: '),
                                                  getpass('Amazon password: ')])
  """

  def __init__(self, cookies=None, credentials=None):
    """
      Constructs and returns an :class:`AmazonMusic <AmazonMusic>`. This
      will use a cookie jar stored, by default, in the home directory.

      :param credentials: Two-element array of username/password or lambda that will return such.
      :param cookies: (optional) Filepath to be used for the cookie jar.
    """

    cookiepath = cookies or '%s/.amazonmusic-cookies.dat' % (os.environ['HOME'])
    self.session = requests.Session()
    self.session.cookies = LWPCookieJar(cookiepath)
    if os.path.isfile(cookiepath):
      self.session.cookies.load()

    # -- Fetch the homepage, authenticating if necessary...
    #
    r = self.session.get(AMAZON_MUSIC, headers = {'User-Agent': USER_AGENT})
    self.session.cookies.save()
    os.chmod(cookiepath, 0o600)

    if r.history and r.history[0].status_code == 302 and AMAZON_SIGNIN in r.history[0].headers['Location']:
      r = self._authenticate(credentials, r)

    # -- Parse out the JSON config object...
    #
    appConfig = None
    for line in r.iter_lines(decode_unicode=True):
      if 'amznMusic.appConfig = ' in line:
        appConfig = json.loads(re.sub(r'^[^\{]*', '',
                               re.sub(r';$', '', line)))
        break
    
    if appConfig is None:
      raise Exception("Unable to find appConfig")

    # -- Store session variables...
    #
    self.deviceId=appConfig['deviceId']
    self.csrfToken=appConfig['CSRFTokenConfig']['csrf_token']
    self.csrfTs=appConfig['CSRFTokenConfig']['csrf_ts']
    self.csrfRnd=appConfig['CSRFTokenConfig']['csrf_rnd']
    self.customerId=appConfig['customerId']
    self.deviceType=appConfig['deviceType']
    self.territory=appConfig['musicTerritory']
    self.locale=appConfig['i18n']['locale']
    self.region=appConfig['realm'][:2]


  def _authenticate(self, credentials, r):
    """
      Handles the sign-in process with Amazon's login page.

      :param credentials: Provider of credential information.
      :param r: The response object from the attempt to access `AMAZON_MUSIC` homepage.
    """

    if type(credentials) == types.FunctionType:
      credentials = credentials()

    if not isinstance(credentials, list) or len(credentials) != 2:
      raise Exception("Invalid credentials: expected list of two elements, but got " + type(credentials))

    soup = BeautifulSoup(r.content, "html.parser")
    query = { "email": credentials[0], "password": credentials[1] }
  
    for field in soup.form.find_all("input"):
      if field.get("type") == "hidden":
        query[field.get("name")] = field.get("value")
      #else:
        #print("skipping %s of type %s with value %s" % (field.get("name"), field.get("type"), field.get("value")))
  
    r = self.session.post(soup.form.get("action"), headers = {
          'User-Agent': USER_AGENT,
            'Referer': r.history[0].headers['Location'],
            'Upgrade-Insecure-Requests': 1,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en-GB;q=0.7,chrome://global/locale/intl.properties;q=0.3'
          },
          data = query)
    self.session.cookies.save()
    return r


  def call(self, endpoint, target, query):
    """
      Make a call against an endpoint and return the JSON response.

      :param endpoint: The URL endpoint of the request.
      :param target: The (Java?) class of the API to invoke.
      :param query: The JSON request.
    """
    query_headers = {
      'User-Agent': USER_AGENT,
      'csrf-token': self.csrfToken,
      'csrf-rnd': self.csrfRnd,
      'csrf-ts': self.csrfTs,
      'X-Requested-With': 'XMLHttpRequest'
    }
    if target is None: # Legacy cirrus API
      query_data = query
    else:
      query_headers['X-Amz-Target'] = target
      query_headers['Content-Type'] = 'application/json'
      query_headers['Content-Encoding'] = 'amz-1.0'
      query_data = json.dumps(query)

    r = self.session.post('%s/%s/api/%s' % (AMAZON_MUSIC, self.region, endpoint), headers = query_headers, data = query_data)
    self.session.cookies.save()
    return r.json()


  def createStation(self, stationId):
    """
      Create a station that can be played.

      :param stationId: Station ID, for example `A2UW0MECRAWILL`.
    """
    return Station(
      self, stationId,
      self.call('mpqs/voiceenabled/createQueue',
                     'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.createQueue',
                     {'identifier': stationId, 'identifierType': 'STATION_KEY',
                      'customerInfo': {
                        'deviceId': self.deviceId,
                        'deviceType': self.deviceType,
                        'musicTerritory': self.territory,
                        'customerId': self.customerId
                      }
                     }))


  def getAlbum(self, albumId):
    """
      Get an album that can be played.

      :param albumId: Album ID, for example `B00J9AEZ7G`.
    """
    return Album(
      self,
      self.call('muse/legacy/lookup',
                'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
                {
                  'asins': [ albumId ],
                  'features': [ 'popularity', 'expandTracklist', 'trackLibraryAvailability', 'collectionLibraryAvailability' ],
                  'requestedContent': 'MUSIC_SUBSCRIPTION',
                  'deviceId': self.deviceId,
                  'deviceType': self.deviceType,
                  'musicTerritory': self.territory,
                  'customerId': self.customerId 
                })['albumList'][0])


  def listAlbums(self):
    """
      Return albums that are in the library. Amazon considers all albums,
      however this filters the list to albums with only four or more items.
    """
    return list(
        map(
          lambda r: Album(self, r),
          filter(
            lambda f: f['trackCount'] >= 4,
            self.call('muse/legacy/lookup',
                  'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
                  {
                    'asins': list(map(
                        lambda h: h['document']['asin'],
                        self.search(None, library_only=True, tracks=False, albums=True,
                                          playlists=False, artists=False, stations=False)[0]['hits']
                      )),
                    'features': [ 'popularity', 'expandTracklist', 'trackLibraryAvailability', 'collectionLibraryAvailability' ],
                    'requestedContent': 'MUSIC_SUBSCRIPTION',
                    'deviceId': self.deviceId,
                    'deviceType': self.deviceType,
                    'musicTerritory': self.territory,
                    'customerId': self.customerId 
                  })['albumList']
          )
        )
      )


  def getPlaylist(self, albumId):
    """
      Get a playlist that can be played.

      :param playlistId: Playlist ID, for example `B075QGZDZ3`.
    """
    return Playlist(
      self,
      self.call('muse/legacy/lookup',
                'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
                {
                  'asins': [ albumId ],
                  'features': [ 'popularity', 'expandTracklist', 'trackLibraryAvailability', 'collectionLibraryAvailability' ],
                  'requestedContent': 'MUSIC_SUBSCRIPTION',
                  'deviceId': self.deviceId,
                  'deviceType': self.deviceType,
                  'musicTerritory': self.territory,
                  'customerId': self.customerId 
                })['playlistList'][0])


  def search(self, query, library_only=False, tracks=True, albums=True, playlists=True, artists=True, stations=True):
    """
      Search Amazon Music for the given query, and return matching results
      (playlists, albums, tracks and artists).

      This is still a work-in-progress, and at the moment the raw Amazon Music
      native data structure is returned.

      :param query: Query.
      :param library_only (optional) Limit to the user's library only, rather than the library + Amazon Music. Defaults to false.
      :param tracks: (optional) Include tracks in the results, defaults to true.
      :param albums: (optional) Include albums in the results, defaults to true.
      :param playlists: (optional) Include playlists in the results, defaults to true.
      :param artists: (optional) Include artists in the results, defaults to true.
      :param stations: (optional) Include stations in the results, defaults to true - only makes sense if `library_only` is false.
    """

    results = []
    query_base = lambda: {
      'deviceId': self.deviceId,
      'deviceType': self.deviceType,
      'musicTerritory': self.territory,
      'customerId': self.customerId,
      'languageLocale': self.locale,
      'requestContext': { 'customerInitiated': True },
      'query': {},
      'resultSpecs': []
    }

    # -- Search the library...
    #
    query_library = query_base()
    if query is None:
      query_library['query'] = {
        '__type': 'com.amazon.music.search.model#ExistsQuery',
        'fieldName': 'asin'
      }
    else:
      query_library['query'] = {
        '__type': 'com.amazon.music.search.model#MatchQuery',
        'query': query
      }

    resultSpec = lambda n: {
        'label': '%ss' % (n),
        'documentSpecs': [{
          'type': n,
          'fields': ['__DEFAULT', 'artFull', 'fileExtension', 'isMusicSubscription', 'primeStatus']
        }],
        'maxResults': 30
    }

    if tracks:
      query_library['resultSpecs'].append(resultSpec('library_track'))
    if albums:
      query_library['resultSpecs'].append(resultSpec('library_album'))
    if playlists:
      query_library['resultSpecs'].append(resultSpec('library_playlist'))
    if artists:
      query_library['resultSpecs'].append(resultSpec('library_artist'))

    results.extend(self.call('search/v1_1/', 'com.amazon.tenzing.v1_1.TenzingServiceExternalV1_1.search', query_library)['results'])

    # -- Search Amazon...
    #
    if not library_only:
      query_amazon = query_base()
      query_amazon['query']['__type'] = 'com.amazon.music.search.model#BooleanQuery'
      query_amazon['query']['must'] = [
        {
          '__type': 'com.amazon.music.search.model#MatchQuery',
          'query': query
        },
        {
          '__type': 'com.amazon.music.search.model#TermQuery',
          'fieldName': 'primeStatus',
          'term': 'PRIME'
        }
      ]

      if tracks:
        query_amazon['resultSpecs'].append(resultSpec('catalog_track'))
      if albums:
        query_amazon['resultSpecs'].append(resultSpec('catalog_album'))
      if playlists:
        query_amazon['resultSpecs'].append(resultSpec('catalog_playlist'))
      if artists:
        query_amazon['resultSpecs'].append(resultSpec('catalog_artist'))
      if stations:
        query_amazon['resultSpecs'].append(resultSpec('catalog_station'))

      results.extend(self.call('search/v1_1/', 'com.amazon.tenzing.v1_1.TenzingServiceExternalV1_1.search', query_amazon)['results'])

    ### TODO Convert into a better data structure
    ### TODO There seems to be a paging token
    return results


class Station:
  """
    Represents a streamable, unending station. This should be created with
    `AmazonMusic.createStation`.

    Key properties are:

      * `id` - ID of the station (Amazon ASIN)
      * `name` - Name of the station.
      * `coverUrl` - URL containing cover art for the station.
  """

  def __init__(self, am, asin, json):
    """
      Internal use only.

      :param am: AmazonMusic object, used to make API calls.
      :param asin: Station ASIN.
      :param json: JSON data structure for the station, from Amazon Music.
    """
    self._am = am
    self.id = asin
    self.json = json
    self.coverUrl = json['queue']['queueMetadata']['imageUrlMap']['FULL']
    self.name = json['queue']['queueMetadata']['title']
    self._pageToken = json['queue']['pageToken']


  def tracks(self):
    """
      Provides an iterable generator for the `Tracks` that make up this
      station.
    """
    tracks = []
    tracks.extend(self.json['trackMetadataList'])
    while tracks:
      yield Track(self._am, tracks.pop(0))
    
      if not tracks:
        print("[DEBUG] Running out of tracks - loading more")
        data = self._am.call('mpqs/voiceenabled/getNextTracks',
                             'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternalVoiceEnabledClient.getNextTracks',
                             { 'pageToken': self._pageToken,
                               'numberOfTracks': 10,
                               'customerInfo': {
                                 'deviceId': self._am.deviceId,
                                 'deviceType': self._am.deviceType,
                                 'musicTerritory': self._am.territory,
                                 'customerId': self._am.customerId
                               }
                             })
        self._pageToken = data['nextPageToken']
        tracks.extend(data['trackMetadataList'])


class Album:
  """
    Represents a streamable, playable album. This should be created with
    `AmazonMusic.getAlbum`.

    Key properties are:

      * `id` - ID of the album (Amazon ASIN)
      * `name` - Album name.
      * `artist` - Album artist name.
      * `coverUrl` - URL containing cover art for the album.
      * `genre` - Genre of the album.
      * `rating` - Average review score (out of 5).
      * `trackCount` - Number of tracks.
      * `releaseDate` - UNIX timestamp of the original release date.

  """

  def __init__(self, am, json):
    """
      Internal use only.

      :param am: AmazonMusic object, used to make API calls.
      :param json: JSON data structure for the album, from Amazon Music.
    """
    self._am = am
    self.json = json
    self.id = json['asin']
    self.coverUrl = json['image']
    self.name = json['title']
    self.artist = json['artist']['name']
    self.genre = json['productDetails'].get('primaryGenreName')
    self.rating = json['reviews']['average']
    self.trackCount = json['trackCount']
    self.releaseDate = json['originalReleaseDate'] / 1000


  def tracks(self):
    """
      Provide the list for the `Tracks` that make up this album.
    """
    return list(map(lambda t: Track(self._am, t), self.json['tracks']))


class Playlist:
  """
    Represents a streamable, playable playlist. This should be created with
    `AmazonMusic.getPlaylist`.

    Key properties are:

      * `id` - ID of the album (Amazon ASIN)
      * `name` - Album name.
      * `coverUrl` - URL containing cover art for the album.
      * `genre` - Genre of the album.
      * `rating` - Average review score (out of 5).
      * `trackCount` - Number of tracks.
  """

  def __init__(self, am, json):
    """
      Internal use only.

      :param am: AmazonMusic object, used to make API calls.
      :param json: JSON data structure for the album, from Amazon Music.
    """
    self._am = am
    self.json = json
    self.id = json['asin']
    self.coverUrl = json['image']
    self.name = json['title']
    self.genre = json['primaryGenre']
    self.rating = json['reviews']['average']
    self.trackCount = json['trackCount']


  def tracks(self):
    """
      Provide the list for the `Tracks` that make up this album.
    """
    return list(map(lambda t: Track(self._am, t), self.json['tracks']))


class Track:
  """
    Represents an individual track on Amazon Music. This will be returned from
    one of the other calls and cannot be created directly.

    Key properties are:

      * `name` - Track name
      * `artist` - Track artist
      * `album` - Album containing the track
      * `albumArtist` - Primary artist for the album
      * `coverUrl` - URL containing cover art for the track/album.

    Key method is:

      * `getUrl()` - Returns an M3U playlist allowing the track to be streamed.
  """

  def __init__(self, am, data):
    """
      Internal use only.

      :param am: AmazonMusic object, used to make API calls.
      :param data: JSON data structure for the track, from Amazon Music. 
                   Supported data structures are from `mpqs` and `muse`.
    """
    try:
      self._am = am
      self._url = None

      self.json = data
      self.name = data.get('name') or data['title']
      self.artist = data.get('artistName') or data['artist']['name']
      self.album = data['album'].get('name') or data['album'].get('title')
      self.albumArtist = data['album'].get('artistName') or data['album'].get('albumArtistName', self.artist)

      self.coverUrl = None
      if 'artUrlMap' in data:
        self.coverUrl = data['artUrlMap'].get('FULL', data['artUrlMap'].get('LARGE'))
      elif 'image' in data['album']:
        self.coverUrl = data['album']['image']

      if 'identifierType' in data:
        self.identifierType = data['identifierType']
        self.identifier = data['identifier']
      else:
        self.identifierType = 'ASIN'
        self.identifier = data['asin']

      self.duration = data.get('durationInSeconds', data.get('duration'))
    except KeyError as e:
      e.args = ('%s not found in %s' % (e.args[0], json.dumps(data, sort_keys = True)), )
      raise


  def getUrl(self):
    """
      Return the URL for an M3U playlist for the track, allowing it to be streamed.
      The playlist seems to consist of individual chunks of the song, in ~10s segments,
      so a player capable of playing playlists seamless is required, such as VLC.
    """
    if self._url is None:
      stream_json=self._am.call('dmls/', 'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getRestrictedStreamingURL', {
        'customerId': self._am.customerId,
        'deviceToken': {
          'deviceTypeId': self._am.deviceType,
          'deviceId': self._am.deviceId,
        },
        'appMetadata': {
          'https': 'true'
        },
        'clientMetadata': {
          'clientId': 'WebCP',
        },
        'contentId': {
          'identifier': self.identifier,
          'identifierType': self.identifierType,
          'bitRate': 'HIGH',
          'contentDuration': self.duration
        }
        })
      if 'statusCode' in stream_json and stream_json['statusCode'] == 'MAX_CONCURRENCY_REACHED':
        raise Exception(stream_json['statusCode'])

      self._url = stream_json['contentResponse']['urlList'][0]

    return self._url
