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

from amazonmusic.amazonmusic import AmazonMusic
from getpass import getpass
try: input = raw_input
except NameError: pass

# -- Create a session...
#
am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])

# -- Display the user's library...
#

count= 0
print( '--- ALBUMS ---' )  
for a in am.my_albums:
  print('[%s] "%s" by %s: %d tracks' % (a.id, a.name, a.artist, a.trackCount))
  count+= 1
print( '--- Total %d ---' % count )  

count= 0
print( '--- ARTISTS ---' )  
for a in am.my_artists:
  count+= 1
  print('[%s] "%s": %d tracks' % (a.id, a.name, a.trackCount))
print( '--- Total %d ---' % count )  

count= 0
print( '--- OWN PLAYLISTS ---' )  
for a in am.my_own_playlists:
  count+= 1
  print('[%s] "%s": %d tracks' % (a.id, a.name, a.trackCount))
print( '--- Total %d ---' % count )  

count= 0
print( '--- FOLLOWED PLAYLISTS ---' )  
for p in am.my_followed_playlists:
  count+= 1
  print('[%s] "%s": %d tracks' % (p.id, p.name, p.trackCount))
    
print( '--- Total %d ---' % count )  

count= 0
print( '--- SONGS ---' )  
for p in am.my_songs:
  count+= 1
  print('[%s] "%s" by %s' % (p.id, p.name, p.artist))
    
print( '--- Total %d ---' % count )  

count= 0
print( '--- GENRES ---' )  
for p in am.my_genres:
  count+= 1
  print('[%s] "%s"' % (p.id, p.name))
    
print( '--- Total %d ---' % count )  

count= 0
print( '--- RECOMMENDED ---' )  
for p in am.recommended():
  count+= 1
  print('  %s' % p[ 'type' ])
  for item in p[ 'items' ]:
    print('    [%s] "%s"' % (item.id, item.name))
    
