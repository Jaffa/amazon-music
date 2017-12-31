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
* Supports Amazon Music UK

### Roadmap
Short term:

* Searching
* Library access (e.g. saved albums, playlists etc.)

Medium term:

* Support other regions/territories (help needed!)
* Better handling of a captcha during authentication

Possible long term:

* Manage library (e.g. create playlists)
* Play tracks without an external player (such as `cvlc`)

Never:

* Features that facilitate piracy (such as track downloading): the library is to allow streaming only

If you would like to contribute to development, or understand how the library - or Amazon Music - works, see [DEVELOPMENT](DEVELOPMENT.md) for more information.

Examples
--------
Two examples are included. To run them:

1. Enure your working directory contains the `amazonmusic.py` library
2. Set `PYTHONPATH` and run them in Python 3:

```sh
PYTHONPATH=. python3 examples/play-album.py
PYTHONPATH=. python3 examples/play-station.py
```

Both the album ASIN and station ASIN to be played are hardcoded within the examples, but can be changed (finding a new ASIN is left as an exercise for the reader at this point!)

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
