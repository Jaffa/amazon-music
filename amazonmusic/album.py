"""
Album class
"""
from .track import Track

class Album(object):
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
    * `tracks` - Iterable generator for the `Tracks` that make up this station.
    """

    def __init__(self, am, data):
        """
        Internal use only.

        :param am: AmazonMusic object, used to make API calls.
        :param data: JSON data structure for the album, from Amazon Music.
            Supports both `muse` and `cirrus` formats.
        """
        self._am = am
        self.json = data
        if 'metadata' in data:
            self.trackCount = data['numTracks']
            data = data['metadata']
            self.json = data
            self.id = data.get('albumAsin') or data['asin']
            self.coverUrl = data.get('albumCoverImageFull', data.get('albumCoverImageMedium'))
            self.name = data['albumName']
            self.artist = data['albumArtistName']
            self.genre = data['primaryGenre']
            self.rating = None
            self.releaseDate = None
        else:
            self.id = data['asin']
            self.coverUrl = data.get('image') or data['albumArtImageUrl']
            self.name = data.get('title') or data['albumName']
            self.artist = data['artist']['name'] if 'artist' in data  else data['artistName']
            self.genre = 'productDetails' in data and data['productDetails'].get('primaryGenreName')
            self.rating = data['reviews']['average'] if 'reviews' in data else -1
            self.trackCount = data.get('trackCount') or data['totalNumberOfTracks']
            self.releaseDate = data['originalReleaseDate'] / 1000

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
