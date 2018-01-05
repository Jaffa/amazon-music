#!/usr/bin/env python
#
# Show the contents of the user's library.
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

from amazonmusic import AmazonMusic
from getpass import getpass
try: input = raw_input
except NameError: pass

# -- Create a session...
#
am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])

# -- Display the user's library...
#
for a in am.listAlbums():
  print('[%s] "%s" by %s: %d tracks' % (a.id, a.name, a.artist, a.trackCount))
