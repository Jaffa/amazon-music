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
import os
import requests
import re
import types
# internal package imports
from . import *
from .track import Track
from .album import Album
from .artist import Artist
from .playlist import *
from .browse_object import BrowseObject
from .genre import Genre
from .station import Station

try:
    from http.cookiejar import MozillaCookieJar, LWPCookieJar, Cookie
except ImportError:
    # noinspection PyUnresolvedReferences
    from cookielib import MozillaCookieJar, LWPCookieJar, Cookie


class AmazonMusic:
    """
    Allows interaction with the Amazon Music service through a programmatic
    interface.

    Usage::

      >>> from amazonmusic import AmazonMusic
      >>> from getpass import getpass
      >>> am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])
    """

    def __init__(self, cookies=None, credentials=None):
        """
        Constructs and returns an :class:`AmazonMusic <AmazonMusic>`. This
        will use a cookie jar stored, by default, in the home directory.

        :param credentials: Two-element array of username/password or lambda that will return such.
        :param cookies: (optional) File path to be used for the cookie jar.
        """

        local_dir = os.path.dirname(os.path.realpath(__file__))
        def _cookie_path(extension):
           return cookies or '{}/.amazonmusic-cookies.{}'.format(os.environ.get('HOME',
                                                                   os.environ.get('LOCALAPPDATA',
                                                                   local_dir)),
                                                                 extension)
        cookie_path = _cookie_path('dat')
        self.session = requests.Session()
        if os.path.isfile(cookie_path):
            self.session.cookies = LWPCookieJar(cookie_path)
            self.session.cookies.load()
        else:
            cookie_path = _cookie_path('moz.dat')
            self.session.cookies = MozillaCookieJar(cookie_path)
            if os.path.isfile(cookie_path):
                self.session.cookies.load()

        target_cookie = next((c for c in self.session.cookies if c.name == COOKIE_TARGET), None)
        if target_cookie is None:
            target_cookie = Cookie(1, COOKIE_TARGET, AMAZON_MUSIC, '0', False, ':invalid', True, ':invalid', '', False,
                                   True, 2147483647, False, 'Used to store target music URL',
                                   'https://github.com/Jaffa/amazon-music/', {})

        # -- Fetch the homepage, authenticating if necessary...
        #
        self.__c = credentials
        r = self.session.get(target_cookie.value, headers=self._http_headers(None))
        self.session.cookies.save()
        os.chmod(cookie_path, 0o600)

        app_config = None
        while app_config is None:
            while r.history and any(h.status_code == 302 and AMAZON_SIGNIN in h.headers['Location'] for h in r.history):
                r = self._authenticate(r)

            # -- Parse out the JSON config object...
            #
            for line in r.iter_lines(decode_unicode=True):
                if 'amznMusic.appConfig = ' in line:
                    app_config = json.loads(re.sub(r'^[^{]*', '', re.sub(r';$', '', line)))
                    break

            if app_config is None:
                raise Exception("Unable to find appConfig in {}".format(r.content))

            if app_config['isRecognizedCustomer'] == 0:
                r = self.session.get(AMAZON_MUSIC + AMAZON_FORCE_SIGNIN, headers=self._http_headers(r))
                app_config = None
        self.__c = None

        # -- Store session variables...
        #
        self.deviceId = app_config['deviceId']
        self.csrfToken = app_config['CSRFTokenConfig']['csrf_token']
        self.csrfTs = app_config['CSRFTokenConfig']['csrf_ts']
        self.csrfRnd = app_config['CSRFTokenConfig']['csrf_rnd']
        self.customerId = app_config['customerId']
        self.deviceType = app_config['deviceType']
        self.territory = app_config['musicTerritory']
        self.locale = app_config['i18n']['locale']
        self.region = REGION_MAP.get(app_config['realm'], app_config['realm'][:2])
        self.url = 'https://' + app_config['serverInfo']['returnUrlServer']

        target_cookie.value = self.url
        self.session.cookies.set_cookie(target_cookie)
        self.session.cookies.save()

    def _authenticate(self, r):
        """
        Handles the sign-in process with Amazon's login page.

        :param r: The response object pointing to the Amazon signin page.
        """
        if isinstance(self.__c, types.FunctionType):
            self.__c = self.__c()

        if not isinstance(self.__c, list) or len(self.__c) != 2:
            raise Exception("Invalid self.__c: expected list of two elements, but got " + type(self.__c))

        r = self._post(r, {"email": self.__c[0], "password": self.__c[1]})
        soup = BeautifulSoup(r.content, "html.parser")
        tag = soup.select('audio#audio-captcha source')
        if tag is not None and len(tag) > 0:
            raise Exception("Unable to handle captcha: {}".format(tag))

        self.session.cookies.save()
        return r

    def _post(self, r, data):
        """
        Assuming an HTML form, copy over any hidden fields and submit it with the extra data.

        :param r: The response object pointing to the Amazon signin page.
        """
        soup = BeautifulSoup(r.content, "html.parser")
        query = {}
        for field in soup.form.find_all("input"):
            if field.get("type") == "hidden":
                query[field.get("name")] = field.get("value")

        query.update(data)
        r = self.session.post(soup.form.get("action"),
                              headers = self._http_headers(r),
                              data = query)
        return r

    def _http_headers(self, r):
        """
        Given a given response, return the set of HTTP headers to use for the next request.

        :param r: The current page.
        """
        return {
            'User-Agent': USER_AGENT,
            'Referer': r.history[0].headers['Location'] if r and len(r.history) > 0 else '',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en-GB;q=0.7,chrome://global/locale/intl.properties;q=0.3'
        }

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
        if target is None:  # Legacy cirrus API
            query_data = query
        else:
            query_headers['X-Amz-Target'] = target
            query_headers['Content-Type'] = 'application/json'
            query_headers['Content-Encoding'] = 'amz-1.0'
            query_data = json.dumps(query)

        r = self.session.post('{}/{}/api/{}'.format(self.url, self.region, endpoint), headers=query_headers,
                              data=query_data)
        self.session.cookies.save()
        return r.json()

    def create_station(self, station_id):
        """
        Create a station that can be played.

        :param station_id: Station ID, for example `A2UW0MECRAWILL`.
        """
        data = self.call('mpqs/voiceenabled/createQueue',
                         'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueServiceExternal'
                         'VoiceEnabledClient.createQueue',
                         {
                             'identifier': station_id, 'identifierType': 'STATION_KEY',
                             'customerInfo': {
                                 'deviceId': self.deviceId,
                                 'deviceType': self.deviceType,
                                 'musicTerritory': self.territory,
                                 'customerId': self.customerId
                             }
                         }
        )
        # Augment station key to data, because it is not included in the results of this API call
        data['stationKey'] = station_id
        return Station(self, data)

    def get_album(self, album_id):
        """
        Get an album that can be played.

        :param albumId: Album ID, for example `B00J9AEZ7G`.
        """
        return Album(
            self,
            self.call(
                'muse/legacy/lookup',
                'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
                {
                    'asins': [album_id],
                    'features': [
                        'popularity',
                        'expandTracklist',
                        'trackLibraryAvailability',
                        'collectionLibraryAvailability'
                    ],
                    'requestedContent': 'MUSIC_SUBSCRIPTION',
                    'deviceId': self.deviceId,
                    'deviceType': self.deviceType,
                    'musicTerritory': self.territory,
                    'customerId': self.customerId
                }
            )['albumList'][0]
        )

    def get_track(self, track_id):
        """
        Get a track by it's asin

        :param track_id: acin of the track
        :return: a Track object containing track information
        """
        # Using search as bridge (or hack) to get track information
        search_result = self.search(track_id, library_only=False, tracks=True, albums=False, playlists=False, artists=False, stations=False)
        # TODO error handling on not found
        track_data = [record[1]['hits'][0]['document'] for record in search_result if record[0] == 'catalog_tracks' ][0]
        return Track(self, track_data)


    @property
    def my_albums(self):
        """
        Return albums that are in the library. Amazon considers all albums,
        however this filters the list to albums with only four or more items.
        """
        query = {
            'Operation': 'searchLibrary',
            'ContentType': 'JSON',
            'searchReturnType': 'ALBUMS',
            'searchCriteria.member.1.attributeName': 'status',
            'searchCriteria.member.1.comparisonType': 'EQUALS',
            'searchCriteria.member.1.attributeValue': 'AVAILABLE',
            'searchCriteria.member.2.attributeName': 'trackStatus',
            'searchCriteria.member.2.comparisonType': 'IS_NULL',
            'searchCriteria.member.2.attributeValue': None,
            'albumArtUrlsSizeList.member.1': 'FULL',
            'selectedColumns.member.1': 'albumArtistName',
            'selectedColumns.member.2': 'albumName',
            'selectedColumns.member.3': 'artistName',
            'selectedColumns.member.4': 'objectId',
            'selectedColumns.member.5': 'primaryGenre',
            'selectedColumns.member.6': 'sortAlbumArtistName',
            'selectedColumns.member.7': 'sortAlbumName',
            'selectedColumns.member.8': 'sortArtistName',
            'selectedColumns.member.9': 'albumCoverImageFull',
            'selectedColumns.member.10': 'albumAsin',
            'selectedColumns.member.11': 'artistAsin',
            'selectedColumns.member.12': 'gracenoteId',
            'sortCriteriaList': None,
            'maxResults': 100,
            'nextResultsToken': None,
            'caller': 'getAllDataByMetaType',
            'sortCriteriaList.member.1.sortColumn': 'sortAlbumName',
            'sortCriteriaList.member.1.sortType': 'ASC',
            'customerInfo.customerId': self.customerId,
            'customerInfo.deviceId': self.deviceId,
            'customerInfo.deviceType': self.deviceType,
        }

        data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
        results = []
        results.extend(data['searchReturnItemList'])
        while results:
            r = results.pop(0)
            # if r['numTracks'] >= 4 and r['metadata'].get('primeStatus') == 'PRIME':  # DB: Amazon music ignores this status and shows all artists. 
            yield Album(self, r)

            if not results and data['nextResultsToken']:
                query['nextResultsToken'] = data['nextResultsToken']
                data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
                results.extend(data['searchReturnItemList'])

    @property
    def my_artists(self):
        """
        Return artists that are in the library. 
        """
        query = {
            'Operation': 'searchLibrary',
            'ContentType': 'JSON',
            'searchReturnType': 'ARTISTS',
            'searchCriteria.member.1.attributeName': 'status',
            'searchCriteria.member.1.comparisonType': 'EQUALS',
            'searchCriteria.member.1.attributeValue': 'AVAILABLE',
            'searchCriteria.member.2.attributeName': 'trackStatus',
            'searchCriteria.member.2.comparisonType': 'IS_NULL',
            'searchCriteria.member.2.attributeValue': None,
            'selectedColumns.member.1': 'albumArtistName',
            'selectedColumns.member.2': 'albumName',
            'selectedColumns.member.3': 'artistName',
            'selectedColumns.member.4': 'objectId',
            'selectedColumns.member.5': 'primaryGenre',
            'selectedColumns.member.6': 'sortAlbumArtistName',
            'selectedColumns.member.7': 'sortAlbumName',
            'selectedColumns.member.8': 'sortArtistName',
            'selectedColumns.member.9': 'albumCoverImageFull',
            'selectedColumns.member.10': 'albumAsin',
            'selectedColumns.member.11': 'artistAsin',
            'selectedColumns.member.12': 'gracenoteId',
            'selectedColumns.member.13': 'physicalOrderId',
            'albumArtUrlsSizeList.member.1': 'FULL',
            'sortCriteriaList': None,
            'maxResults': 100,
            'caller': 'getAllDataByMetaType',
            'sortCriteriaList.member.1.sortColumn': 'sortArtistName',
            'sortCriteriaList.member.1.sortType': 'ASC',
            'customerInfo.customerId': self.customerId,
            'customerInfo.deviceId': self.deviceId,
            'customerInfo.deviceType': self.deviceType,
        }

        data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
        results = []
        results.extend(data['searchReturnItemList'])
        while results:
            r = results.pop(0)
            
            # if r['metadata'].get('primeStatus') == 'PRIME':  # DB: Amazon music ignores this status and shows all artists. 
            yield Artist(self, r)

            if not results and data['nextResultsToken']:
                query['nextResultsToken'] = data['nextResultsToken']
                data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
                results.extend(data['searchReturnItemList'])
    
    @property
    def my_genres(self):
        """
        Return artists that are in the library. 
        """
        query = {
            'Operation': 'searchLibrary',
            'ContentType': 'JSON',
            'searchReturnType': 'GENRES',
            'searchCriteria.member.1.attributeName': 'status',
            'searchCriteria.member.1.comparisonType': 'EQUALS',
            'searchCriteria.member.1.attributeValue': 'AVAILABLE',
            'searchCriteria.member.2.attributeName': 'trackStatus',
            'searchCriteria.member.2.comparisonType': 'IS_NULL',
            'searchCriteria.member.2.attributeValue': None,
            'albumArtUrlsSizeList.member.1': 'MEDIUM',
            'selectedColumns.member.1': 'objectId',
            'selectedColumns.member.2': 'primaryGenre',
            'albumArtUrlsSizeList.member.1': 'FULL',
            'sortCriteriaList': None,
            'maxResults': 100,
            'caller': 'getAllDataByMetaType',
            'sortCriteriaList.member.1.sortColumn': 'primaryGenre',
            'sortCriteriaList.member.1.sortType': 'ASC',
            'customerInfo.customerId': self.customerId,
            'customerInfo.deviceId': self.deviceId,
            'customerInfo.deviceType': self.deviceType,
        }

        data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
        results = []
        results.extend(data['searchReturnItemList'])
        while results:
            r = results.pop(0)
            
            # if r['metadata'].get('primeStatus') == 'PRIME':  # DB: Amazon music ignores this status and shows all artists. 
            yield Genre(self, r)

            if not results and data['nextResultsToken']:
                query['nextResultsToken'] = data['nextResultsToken']
                data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
                results.extend(data['searchReturnItemList'])
    
    @property
    def my_own_playlists(self):
        """
        Return own (user's only) playlists that are in the library. 
        """
        query = {
            'entryOfffset': 0,
            'musicTerritory': self.region,
            'pageSize': 100,
            'customerId': self.customerId,
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
        }

        data = self.call('playlists/', 'com.amazon.musicplaylist.model.MusicPlaylistService.getOwnedPlaylistsInLibrary', query)
        results = []
        results.extend(data['playlists'])
        while results:
            r = results.pop(0)
            yield OwnPlaylist(self, r)

    @property
    def my_followed_playlists(self):
        """
        Return own (user's only) playlists that are in the library. 
        """
        query = {
            'entryOfffset': 0,
            'musicTerritory': self.region,
            'pageSize': 100,
            'customerId': self.customerId,
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
            'optIntoSharedPlaylists': 'true',
        }

        data = self.call('playlists/', 'com.amazon.musicplaylist.model.MusicPlaylistService.getFollowedPlaylistsInLibrary', query)
        results = []
        results.extend(data['playlists'])
        while results:
            r = results.pop(0)
            yield FollowedPlaylist(self, r)

    @property
    def my_songs(self):
        """
        Return tracks/songs been stored in My Music
        """
        query = {
            'Operation': 'searchLibrary',
            'ContentType': 'JSON',
            'searchReturnType': 'TRACKS',
            'searchCriteria.member.1.attributeName': 'status',
            'searchCriteria.member.1.comparisonType': 'EQUALS',
            'searchCriteria.member.1.attributeValue': 'AVAILABLE',
            'searchCriteria.member.2.attributeName': 'assetType',
            'searchCriteria.member.2.comparisonType': 'EQUALS',
            'searchCriteria.member.2.attributeValue': 'AUDIO',
            'selectedColumns.member.1': 'albumArtistName',
            'selectedColumns.member.2': 'albumName',
            'selectedColumns.member.3': 'artistName',
            'selectedColumns.member.4': 'assetType',
            'selectedColumns.member.5': 'duration',
            'selectedColumns.member.6': 'objectId',
            'selectedColumns.member.7': 'sortAlbumArtistName',
            'selectedColumns.member.8': 'sortAlbumName',
            'selectedColumns.member.9': 'sortArtistName',
            'selectedColumns.member.9': 'albumCoverImageFull',
            'selectedColumns.member.10': 'title',
            'selectedColumns.member.11': 'status',
            'selectedColumns.member.12': 'trackStatus',
            'selectedColumns.member.13': 'extension',
            'selectedColumns.member.14': 'asin',
            'selectedColumns.member.15': 'primeStatus',
            'selectedColumns.member.16': 'albumCoverImageLarge',
            'selectedColumns.member.17': 'albumCoverImageMedium',
            'selectedColumns.member.18': 'albumCoverImageSmall',
            'selectedColumns.member.19': 'albumCoverImageFull',
            'selectedColumns.member.20': 'isMusicSubscription',
            'albumArtUrlsRedirects': 'false',
            'distinctOnly': 'false',
            'countOnly': 'false',
            'maxResults': 500,
            'caller': 'getServerSongs',
            'sortCriteriaList.member.1.sortColumn': 'sortTitle',
            'sortCriteriaList.member.1.sortType': 'ASC',
            'customerInfo.customerId': self.customerId,
            'customerInfo.deviceId': self.deviceId,
            'customerInfo.deviceType': self.deviceType,
        }

        data = self.call('cirrus/', None, query)['searchLibraryResponse']['searchLibraryResult']
        results = []
        results.extend(data['searchReturnItemList'])
        while results:
            r = results.pop(0)
            yield Track(self, r[ 'metadata' ])
            
    def _get_playlists_by_parent(self, parent, rank_type ):
        """
        Return playlists based on parent category and rank_type
        """
        query = {
            'musicTerritory':   'US',
            'customerId':       self.customerId,
            'deviceId':         self.deviceId,
            'deviceType':       self.deviceType,
            'lang':             self.locale,
            'requestedContent': 'PRIME',
            'maxCount':         24, 
            'rankType':         rank_type,
            'types':            ["playlist"],
            'features':         ["playlistLibraryAvailability", "ownership"],
            'browseId':         parent,
            'nextTokenMap':     {'playlist': ''},
        }

        data = self.call('muse/getTopMusicEntities', 'com.amazon.musicensembleservice.MusicEnsembleService.getTopMusicEntities', query)
        results = []
        results.extend(data['playlistList'])
        while results:
            r = results.pop(0)
            yield Playlist(self, r)

    def get_category_playlists(self, category, parent= None ):
        """
        Return playlists based on category and allow dig deeper when parent ID is known
        """
        query = {
            'musicTerritory': self.territory,
            'customerId': self.customerId,
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
            'lang': self.locale,
            'requestedContent': 'PRIME',
        }

        data = self.call('muse/browseHierarchyV2', 'com.amazon.musicensembleservice.MusicEnsembleService.browseHierarchyV2', query)
        results = []
        results.extend(data['browseHierarchy'])
        while results:
            r = results.pop(0)
            if r[ 'type' ]== category:
              # Check if we have nesting
              if parent:
                # Find our parent and browse into it
                yield self._get_playlists_by_parent( parent, 'popularity-rank' )
              else:
                for b in r[ 'browseObjects' ]:
                  yield BrowseObject(self, b)
    
    def get_playlists(self, album_id):
        """
        Get a playlist that can be played.

        :param album_id: Playlist ID, for example `B075QGZDZ3`.
        """
        return Playlist(
            self,
            self.call(
                'muse/legacy/lookup',
                'com.amazon.musicensembleservice.MusicEnsembleService.lookup',
                {
                    'asins': [album_id],
                    'features': [
                        'popularity',
                        'expandTracklist',
                        'trackLibraryAvailability',
                        'collectionLibraryAvailability'
                    ],
                    'requestedContent': 'MUSIC_SUBSCRIPTION',
                    'deviceId': self.deviceId,
                    'deviceType': self.deviceType,
                    'musicTerritory': self.territory,
                    'customerId': self.customerId
                }
            )['playlistList'][0]
        )

    def search(self, query, library_only=False, tracks=True, albums=True, playlists=True, artists=True, stations=True):
        """
        Search Amazon Music for the given query, and return matching results
        (playlists, albums, tracks and artists).

        This is still a work-in-progress, and at the moment the raw Amazon Music
        native data structure is returned.

        :param query: Query.
        :param library_only (optional) Limit to the user's library only, rather than the library + Amazon Music.
               Defaults to false.
        :param tracks: (optional) Include tracks in the results, defaults to true.
        :param albums: (optional) Include albums in the results, defaults to true.
        :param playlists: (optional) Include playlists in the results, defaults to true.
        :param artists: (optional) Include artists in the results, defaults to true.
        :param stations: (optional) Include stations in the results, defaults to true - only makes sense if
               `library_only` is false.
        """
        query_obj = {
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
            'musicTerritory': self.territory,
            'customerId': self.customerId,
            'languageLocale': self.locale,
            'requestContext': {'customerInitiated': True},
            'query': {},
            'resultSpecs': []
        }

        # -- Set up the search object...
        #
        if library_only:
            def _set_q(q):
                query_obj['query'] = q
        else:
            query_obj['query'] = {
                '__type': 'com.amazon.music.search.model#BooleanQuery',
                'must': [{}],
                'should': [{
                    '__type': 'com.amazon.music.search.model#TermQuery',
                    'fieldName': 'primeStatus',
                    'term': 'PRIME'
                }]
            }

            def _set_q(q):
                query_obj['query']['must'][0] = q

        # -- Set up the query...
        #
        if query is None:
            _set_q({
                '__type': 'com.amazon.music.search.model#ExistsQuery',
                'fieldName': 'asin'
            })
        else:
            _set_q({
                '__type': 'com.amazon.music.search.model#MatchQuery',
                'query': query
            })

        def _add_result_spec(**kwargs):
            for type_ in kwargs:
                if kwargs[type_]:
                    def result_spec(n):
                        return {
                            'label': '{}s'.format(n),  # Before it was %ss, is {}s right?
                            'documentSpecs': [{
                                'type': n,
                                'fields': [
                                    '__DEFAULT',
                                    'artFull',
                                    'fileExtension',
                                    'isMusicSubscription',
                                    'primeStatus'
                                ]
                            }],
                            'maxResults': 30
                        }
                    if type_ != 'station':
                        query_obj['resultSpecs'].append(result_spec('library_{}'.format(type_)))
                    if not library_only:
                        query_obj['resultSpecs'].append(result_spec('catalog_{}'.format(type_)))

        _add_result_spec(
            track=tracks,
            album=albums,
            playlist=playlists,
            artist=artists,
            station=stations
        )

        # TODO Convert into a better data structure
        # TODO There seems to be a paging token
        return list(map(
            lambda r: [r['label'], r],
            self.call('search/v1_1/', 'com.amazon.tenzing.v1_1.TenzingServiceExternalV1_1.search', query_obj)['results']
        ))
    
    def recommended(self):
        """
        Return all recommended categories for logged user(playlists,albums,songs,stations)
        """
        query = {
            'customerId': self.customerId,
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
            'lang': self.locale,
            'maxResultsPerWidget': 24,
            'minResultsPerWidget': 5,
            'musicTerritory': self.territory,
            'requestedContent': 'PRIME',
        }
        data = self.call('muse/legacy/getBrowseRecommendations/', 'com.amazon.musicensembleservice.MusicEnsembleService.getBrowseRecommendations', query)
        results = []
        results.extend(data['recommendations'])
        while results:
            r = results.pop(0)
            if r['recommendationType'] == 'PLAYLIST':
                yield {'type': r['recommendationType'], 'items': [FollowedPlaylist(self, playlist) for playlist in r['playlists']]}
            if r['recommendationType'] == 'ALBUM':
                yield {'type': r['recommendationType'], 'items': [Album(self, album) for album in r['albums']]}
            if r['recommendationType'] == 'TRACK':
                yield {'type': r['recommendationType'], 'items': [Track(self, track) for track in r['tracks']]}
            if r['recommendationType'] == 'STATION':
                yield {'type': r['recommendationType'], 'items': [Station(self, station) for station in r['stations']]}
        
    def get_stations(self, parent=None):
        """
        Return all recommended stations
        """
        query = {
            'customerId': self.customerId,
            'deviceId': self.deviceId,
            'deviceType': self.deviceType,
            'lang': self.locale,
            'musicTerritory': self.territory,
            'requestedContent': 'PRIME',
        }
        data = self.call('muse/stations/getStationSections', 'com.amazon.musicensembleservice.MusicEnsembleService.getStationSections', query)
        categories= data[ 'categories' ]
        if parent:
          # Retrieve all stations
          stations= data[ 'stations' ]
        
        for category in categories:
            c = categories[ category ]
            if parent:
              if c[ 'categoryId' ]== parent:
                for station in c[ 'stationMapIds' ]:
                  yield Station( self, stations[ station ] )
            else:
              yield BrowseObject( self, c )
              
