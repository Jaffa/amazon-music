"""
Track class
"""
import json


class Track(object):
    """
    Represents an individual track on Amazon Music. This will be returned from
    one of the other calls and cannot be created directly.

    Key properties are:

    * `name` - Track name
    * `artist` - Track artist
    * `album` - Album containing the track
    * `albumArtist` - Primary artist for the album
    * `coverUrl` - URL containing cover art for the track/album.
    * `streamUrl` - URL of M3U playlist allowing the track to be streamed.
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the track, from Amazon Music.
                     Supported data structures are from `mpqs` and `muse`.
        """
        self._am = am
        self._url = None

        self.json = data
        self.id = data.get('asin') or data['identifier']
        self.name = data.get('name') or data['title']
        self.artist = data.get('artistName') or data['artist']['name']
        self.album = data.get('albumName') or data['album'].get('name')\
                or data['album'].get('title')
        self.albumArtist = data['albumArtistName'] if 'albumArtistName' in data else None
        self.coverUrl = None
        self.purchased = 'orderId' in data

        if 'artUrlMap' in data:
            self.coverUrl = data['artUrlMap'].get('FULL', data['artUrlMap'].get('LARGE'))
        elif 'album' in data and 'image' in data['album']:
            self.coverUrl = data['album']['image']
        elif 'albumCoverImageFull' in data:
            self.coverUrl = data['albumCoverImageFull']

        if 'identifierType' in data:
            self.identifierType = data['identifierType']
            self.identifier = data['identifier']
        else:
            self.identifierType = 'ASIN'
            self.identifier = data['asin']

        self.duration = data.get('durationInSeconds') or data.get('duration')\
                or data['durationSeconds']

    @property
    def stream_url(self):
        """
        Return the URL for an M3U playlist for the track, allowing it to be streamed.
        The playlist seems to consist of individual chunks of the song, in ~10s segments,
        so a player capable of playing playlists seamless is required, such as VLC.
        """
        if self._url is None:
            stream_json = self._am.call(
                'dmls/',
                'com.amazon.digitalmusiclocator.DigitalMusicLocatorServiceExternal.getRestrictedStreamingURL',
                {
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
            if 'statusCode' in stream_json and\
                    stream_json['statusCode'] == 'MAX_CONCURRENCY_REACHED':
                raise Exception(stream_json['statusCode'])

            try:
                self._url = stream_json['contentResponse']['urlList'][0]
            except KeyError as e:
                data = json.dumps(stream_json, sort_keys=True)
                e.args = ('{} not found in {}'.format(e.args[0], data),)
                raise
        return self._url
