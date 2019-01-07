"""
amazonmusic
----
Reversed engineered Python API for amazon music.
"""

__version__ = '0.1'
VERSION = __version__

AMAZON_MUSIC = 'https://music.amazon.com'
AMAZON_SIGNIN = '/ap/signin'
AMAZON_FORCE_SIGNIN = '/gp/dmusic/cloudplayer/forceSignIn'
COOKIE_TARGET = '_AmazonMusic-targetUrl'  # Placeholder cookie to store target server in
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'

# Overrides for realm -> region, if the first two characters can't be used,
# based on digitalMusicPlayer
REGION_MAP = {
    'USAmazon': 'NA',
    'EUAmazon': 'EU',
    'FEAmazon': 'FE'
}
