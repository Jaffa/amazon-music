"""
Browse Object class
"""


class BrowseObject(object):
    """
    Represents an individual browsable object in category hierarchy

    Key properties are:

    * `id` - Object ID
    * `name` - Object  name
    """
    def __init__(self, am, data):
        self.id = data.get( 'browseId' ) or data[ 'categoryId' ]
        self.name = data.get( 'browseName' ) or data[ 'title' ]

