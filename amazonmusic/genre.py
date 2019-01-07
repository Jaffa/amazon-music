"""
Genre class
"""


class Genre(object):
    """
    Represents a genre for MyMusic
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
            data = data['metadata']
            self.json = data
            self.id = data['objectId']
            self.coverUrl = data.get('albumCoverImageFull', data.get('albumCoverImageMedium'))
            self.name = data['primaryGenre']
        else:
            self.id = 'MUSE NOT SUPPORTED'
            self.coverUrl = 'MUSE NOT SUPPORTED'
            self.name = 'MUSE NOT SUPPORTED'
            self.trackCount = 'MUSE NOT SUPPORTED'

