"""
Station class
"""
from .track import Track


class Station(object):
    """
    Represents a streamable, unending station. This should be created with
    `AmazonMusic.createStation`.

    Key properties are:

    * `id` - ID of the station (Amazon ASIN)
    * `name` - Name of the station.
    * `coverUrl` - URL containing cover art for the station.
    * `tracks` - Iterable generator for the `Tracks` that make up this station.
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the station, from Amazon Music.
        """
        self._am = am
        self.id = data['stationKey']
        self.json = data
        self.coverUrl = data['queue']['queueMetadata']['imageUrlMap']['FULL']\
                if 'queue' in data else data['stationImageUrl']
        self.name = data['queue']['queueMetadata']['title']\
                if 'queue' in data else data['stationTitle']
        self._pageToken = ('queue' in data and data['queue']['pageToken'])\
                or ('seed' in data and data['seed']['seedId'])

    @property
    def tracks(self):
        """
        Provides an iterable generator for the `Tracks` that make up this station.
        """
        tracks = []
        tracks.extend(self.json['trackMetadataList'])
        while tracks:
            yield Track(self._am, tracks.pop(0))

            if not tracks:
                data = self._am.call(
                    'mpqs/voiceenabled/getNextTracks',
                    'com.amazon.musicplayqueueservice.model.client.external.voiceenabled.MusicPlayQueueService'
                    'ExternalVoiceEnabledClient.getNextTracks',
                    {
                        'pageToken': self._pageToken,
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
