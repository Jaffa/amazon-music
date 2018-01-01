AmazonMusic
===========

_AmazonMusic_ is an open source Python 3 library, providing access to Amazon Music/Prime Music's streaming service. It enables new applications to be written that use Amazon's service.

This is similar to other projects for other streaming services. For example, for Spotify use [`librespot`](https://github.com/plietar/librespot) and [`python-librespot`](https://github.com/plietar/python-librespot/) - based on Spotify's [`libspotify`](https://developer.spotify.com/technologies/libspotify/). Unfortunately, Amazon [don't offer an Amazon Music SDK](https://forums.developer.amazon.com/questions/58421/amazon-music-api.html), and this seems to be the first attempt to reverse engineer one.

Example usage
-------------

```python
from amazonmusic import AmazonMusic
import os

am = AmazonMusic(credentials = ['foo@example.com', 'xyzzy'])

station = am.createStation('A2UW0MECRAWILL')
print('Playing station %s...' % (station.name))

for t in station.tracks():
  print("Playing %s by %s from %s [%s]..." % (t.name, t.artist, t.album, t.albumArtist))
  os.system("cvlc --play-and-exit '%s'" % (t.getUrl()))
```

_Note:_ hardcoding your Amazon credentials is a bad idea! `AmazonMusic` can be passed a lambda function that returns a two-element list. This will be called if a sign-in is necessary and can be used to prompt the user for their credentials. For example:

```python
from getpass import getpass

am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])
```

Features
--------

* Play album by ASIN
* Play station by ASIN
* Play playlist by ASIN
* Supports Amazon Music UK with Prime subscriptions

### Roadmap
Short term:

* Searching (in progress)
* Browse recommendations
* Browse stations
* Library access (e.g. saved albums, playlists etc.)

Medium term:

* Ensure full Amazon Music Unlimited subscriptions are supported
* Support other regions/territories (help needed!)
* Better handling of a captcha during authentication

Possible long term:

* Better examples (full Amazon Music client?)
* Manage library (e.g. create playlists)
* Play tracks without an external player (such as `cvlc`)

Never:

* Features that facilitate piracy (such as track downloading): the library is to allow streaming only

If you would like to contribute to development, or understand how the library - or Amazon Music - works, see [DEVELOPMENT](DEVELOPMENT.md) for more information.

Examples
--------

Several examples are included. To run them:

1. Enure your working directory contains the `amazonmusic.py` library
2. Set `PYTHONPATH` and run them in Python 3:

```sh
PYTHONPATH=. python3 examples/play-album.py
PYTHONPATH=. python3 examples/play-station.py
PYTHONPATH=. python3 examples/play-playlist.py
```

Default ASINs for albums, stations and playlists are defaulted within the examples, but alternatives can be provided as a command line argument. The `search.py` example can be used to find alternatives (although the raw JSON needs to be manually parsed at the moment):

```
PYTHONPATH=. python3 examples/search.py Adele 25
```

```javascript
[...]
      {
        "document": {
          "__type": "com.amazon.music.platform.model#CatalogAlbum",
          "artFull": {
            "URL": "https://m.media-amazon.com/images/I/A170tH1apiL._AA500.jpg",
            "__type": "com.amazon.music.platform.model#ArtURL",
            "artUrl": "https://m.media-amazon.com/images/I/A170tH1apiL._AA500.jpg"
          },
          "artistAsin": "B001EEJMYG",
          "artistName": "Adele",
          "asin": "B0170UQ0OC",
          "isMusicSubscription": "true",
          "originalReleaseDate": 1447977600.0,
          "primaryGenre": "Pop",
          "primeStatus": "PRIME",
          "title": "25",
          "trackCount": 11
        }
      },
```

```sh
PYTHONPATH=. python3 examples/play-album.py B0170UQ0OC
```

Background
----------

I have a long term plan to build an integrated smart home with voice assistant (possibly using the likes of [spaCy](https://spacy.io/), [Snowboy](https://snowboy.kitt.ai/), [openHAB](https://www.openhab.org/), [Mopidy](https://www.mopidy.com/) and [respeaker-avs](https://github.com/respeaker/avs)). As an Amazon Prime subscriber, I get access to Prime Music - which just about covers my streaming audio needs. Unfortunately, Alexa Voice Service [only allows people actively working with Amazon on commercial products](https://github.com/alexa-pi/AlexaPi/wiki/Q&A-(FAQ)#does-alexapi-support-amazon-music) under NDA to access Amazon Music.

Switching to Spotify will cost money. Commercialising the integrating smart home solution might be an even longer term plan, but I don't want to predicate access on that. Reverse engineering Amazon Music - or getting Amazon to provide an API - so that it can be added to projects like Mopidy seems like the best way forward.

License
-------
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this library except in compliance with the License.
You may obtain a copy of the License in the [`LICENSE`](LICENSE)
file.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Attribution to Andrew Flegg is welcome, but not required.
