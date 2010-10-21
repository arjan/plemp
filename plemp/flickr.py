# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import postr.flickrest


class Flickr (postr.flickrest.Flickr):
    """
    Extends the postr.flickrest.Flickr class to support multiple profiles.
    """

    def __init__(self, api_key, secret, profile=None, perms="read"):
        postr.flickrest.Flickr.__init__(self, api_key, secret, perms)
        self.profile = profile

    def __getTokenFile(self):
        """Get the filename that contains the authentication token for the API key"""
        if not self.profile:
            authFile = "auth.xml"
        else:
            authFile = "auth-%s.xml" % self.profile
        return os.path.expanduser(os.path.join("~", ".flickr", self.api_key, authFile))
