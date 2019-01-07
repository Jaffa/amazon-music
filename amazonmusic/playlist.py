"""
Playlist classes
"""
from .track import Track


class Playlist(object):
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
    * `tracks` - Iterable generator for the `Tracks` that make up this station.
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the album, from Amazon Music.
        """
        self._am = am
        self.json = data
        self.id = data['asin']
        self.coverUrl = data['image']
        self.name = data['title']
        self.genre = data['primaryGenre']
        self.rating = data['reviews']['average']
        self.trackCount = data['trackCount']

    @property
    def tracks(self):
        """
        Provide the list for the `Tracks` that make up this album.
        """
        return [Track(self._am, track) for track in self.json['tracks']]


class FollowedPlaylist(object):
    """
    Represents followed playlist created by the third party.

    Key properties are:

    * `id` - ID of the playlist
    * `name` - Playlist name.
    * 'description' - description of the playlist
    * `coverUrl` - URL containing cover art for the album.
    * `trackCount` - Number of tracks.
    * `created` - Creation date
    * `durationSecs` - Duration of the playlist in secs
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the album, from Amazon Music.
        """
        self._am = am
        self.json = data
        self.id = data['asin']
        self.coverUrl = ('bannerImage' in data and data['bannerImage']['url'])\
            or ('fourSquareImage' in data and data['fourSquareImage']['url'])\
            or data['albumArtImageUrl']
        self.name = data['title']
        self.description = data['description']
        self.trackCount = data.get('totalTrackCount') or data['trackCount']
        self.created = data.get('createdDate')
        self.durationSecs = data.get('durationSeconds') or data['duration']


class OwnPlaylist(object):
    """
    Represents an owned playlist. This can be created with `AmazonMusic.getPlaylist`.

    Key properties are:

    * `id` - ID of the playlist
    * `name` - Playlist name.
    * `coverUrl` - URL containing cover art for the album.
    * `trackCount` - Number of tracks.
    * `created` - Creation date
    * `durationSecs` - Duration of the playlist in secs
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the album, from Amazon Music.
        """
        self._am = am
        self.json = data
        self.id = data['playlistId']
        self.coverUrl = data['fourSquareImage']['url']
        self.name = data['title']
        self.trackCount = data['totalTrackCount']
        self.created = data['createdDate']
        self.durationSecs = data['durationSeconds']
