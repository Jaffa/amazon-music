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

import sys
from amazonmusic.amazonmusic import AmazonMusic
from getpass import getpass
try: input = raw_input
except NameError: pass

# -- Create a session...
#
am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])

# -- Check if parent is given
#
if len( sys.argv )== 1:
  print( 'Usage: browse-library <CATEGORY> [parent]\n  <CATEGORY>::= MOODS_AND_ACTIVITIES | GENRES | STATIONS' )
elif len( sys.argv )> 1:
  # Get category playlists to browse (MOODS_AND_ACTIVITIES|GENRES)
  count= 0
  print( '--- %s ---' % sys.argv[ 1 ] )  
  if sys.argv[ 1 ] in ( 'MOODS_AND_ACTIVITIES','GENRES' ):
    for c in am.get_category_playlists( sys.argv[ 1 ], ( len( sys.argv )== 3 and sys.argv[ 2 ] ) ):
      print('[%s] %s' % (c.id, c.name))
      count+= 1
  elif sys.argv[ 1 ] in ( 'STATIONS' ):
    for c in am.get_stations( len( sys.argv )== 3 and sys.argv[ 2 ] ):
      print('[%s] %s' % (c.id, c.name))
      count+= 1
  else:
    print( '  !!Unknown category" %s' % sys.argv[ 1 ] )
    
  print( '--- Total %d ---' % count )  
  
