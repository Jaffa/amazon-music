#!/usr/bin/env python
#
# Play an Amazon Music playlist.
#
# Copyright (c) 2018 by Andrew Flegg.
#
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

from amazonmusic.amazonmusic import AmazonMusic
from getpass import getpass
import os, sys
try: input = raw_input
except NameError: pass

# -- Create a session...
#
am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])

# -- Play a station...
#
asin = sys.argv[1] if len(sys.argv) == 2 else 'B01MRIAAFE'
playlist = am.get_playlists(asin)
print('Art: %s\nPlaying playlist %s (%d/5)...' % (playlist.coverUrl, playlist.name, playlist.rating))

for t in playlist.tracks:
  print("Playing %s by %s from %s [%s]..." % (t.name, t.artist, t.album, t.albumArtist))
  #os.system("cvlc --play-and-exit '%s'" % (t.stream_url))
  print(t.stream_url)
  print('-------------------------')
