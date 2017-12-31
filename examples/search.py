#!/usr/bin/env python3
#
# Search Amazon Music for a given query, and show the results.
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
import sys
import json

#import requests
#import logging
#import http.client as http_client
#http_client.HTTPConnection.debuglevel = 1
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

# -- Create a session...
#
am = AmazonMusic(credentials = lambda: [input('Email: '), getpass('Amazon password: ')])

# -- Check syntax...
if len(sys.argv) < 2:
  print("syntax: search.py <terms...>")
  sys.exit(1)

# -- Search for the command line argument and show the results...
#
results = am.search(' '.join(sys.argv[1:]))
print(json.dumps(results, sort_keys=True, indent=2))