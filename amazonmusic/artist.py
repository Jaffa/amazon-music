"""
Artist class
"""
from .track import Track


class Artist(object):
    """
    Represents a streamable, playable artist. This should be created with
    `AmazonMusic.getArtist`.

    Key properties are:

    * `id` - ID of the artist (Amazon ASIN)
    * `name` - Artist name.
    * `coverUrl` - URL containing cover art for the artist.
    * `genre` - Genre of the album.
    * `rating` - Average review score (out of 5).
    * `trackCount` - Number of tracks.
    * `releaseDate` - UNIX timestamp of the original release date.
    * `tracks` - Iterable generator for the `Tracks` that make up this station.
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the artist, from Amazon Music.
            Supports `cirrus` formats for now
        """
        self._am = am
        self.json = data
        if 'metadata' in data:
            self.trackCount = data['numTracks']
            self.json = data['metadata']
            data = self.json
            self.id = data['albumArtistAsin']
            self.coverUrl = data.get('albumCoverImageFull', data.get('albumCoverImageMedium'))
            self.name = data['artistName']
            self.genre = data['albumPrimaryGenre']
            self.rating = None
            self.releaseDate = None
        else:
            self.id = 'MUSE NOT SUPPORTED'
            self.coverUrl = 'MUSE NOT SUPPORTED'
            self.name = 'MUSE NOT SUPPORTED'
            self.genre = 'MUSE NOT SUPPORTED'
            self.rating = 'MUSE NOT SUPPORTED'
            self.trackCount = 'MUSE NOT SUPPORTED'
            self.releaseDate = 'MUSE NOT SUPPORTED'

    @property
    def tracks(self):
        """
        Provide the list for the `Tracks` that make up this album.
        """
        # If we've only got a summary, load the full data
        if 'tracks' not in self.json:
            album = self._am.get_album(self.id)
            self.__init__(self._am, album.json)

        return [Track(self._am, track) for track in self.json['tracks']]
