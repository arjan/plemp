# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import postr.flickrest
from plemp import progressclient as client


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


    # overruled because we need to add the progress callback.
    
    def upload(self, filename=None, imageData=None,
               title=None, desc=None, tags=None,
               is_public=None, is_family=None, is_friend=None,
               safety=None, search_hidden=None, async=None, progressCallback=None):
        # Sanity check the arguments
        if filename is None and imageData is None:
            raise ValueError("Need to pass either filename or imageData")
        if filename and imageData:
            raise ValueError("Cannot pass both filename and imageData")

        kwargs = {}
        if title:
            kwargs['title'] = title
        if desc:
            kwargs['description'] = desc
        if tags:
            kwargs['tags'] = tags
        if is_public is not None:
            kwargs['is_public'] = is_public and 1 or 0
        if is_family is not None:
            kwargs['is_family'] = is_family and 1 or 0
        if is_friend is not None:
            kwargs['is_friend'] = is_friend and 1 or 0
        if safety:
            kwargs['safety_level'] = safety
        if search_hidden is not None:
            kwargs['hidden'] = search_hidden and 2 or 1 # Why Flickr, why?
        if async:
            kwargs['async'] = async and 1
        self.__sign(kwargs)
        self.logger.info("Upload args %s" % kwargs)
        
        if imageData:
            kwargs['photo'] = imageData
        else:
            kwargs['photo'] = file(filename, "rb")

        (boundary, form) = self.__encodeForm(kwargs)
        headers= {
            "Content-Type": "multipart/form-data; boundary=%s" % boundary,
            "Content-Length": str(len(form))
            }

        self.logger.info("Calling upload")
        return client.getPage("http://api.flickr.com/services/upload/",
                              proxy=self.proxy, method="POST",
                              headers=headers, postdata=form,
                              progressCallback=progressCallback).addCallback(self.__cb, "upload")
