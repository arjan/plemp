# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os

from twisted.internet import defer

from plemp.flickr import Flickr
from plemp import api_key, api_secret


class Uploader (object):
    """
    The uploader performs the actual uploading.
    """

    def __init__(self, profile=None):
        self.files = []
        self.upload = {'is_public': 1,
                       'is_family': 0,
                       'is_friend': 0,
                       'search_hidden': 0}
        self.photoset = None
        self.exif = {}
        self.flickr = Flickr(api_key, api_secret, profile=profile, perms='write')
        self.profile = profile
        self.photosets = None


    def initializeAPI(self, authCallback, errback=None):
        """
        Initialize the Flickr API and perform the initial authorization, if needed.
        """
        def auth_1(state):
            if state is not None:
                # we need to authenticate. This works synchronously!
                if authCallback(state['url']):
                    return self.flickr.authenticate_2(state).addCallbacks(self.connected, errback)
            self.connected(True)
            return state
        return self.flickr.authenticate_1().addCallback(auth_1)


    def connected(self, c):
        """ We are connected. """
        self.numUploaded = 0
        self.numUploading = 0
        self.uploadStarted = False


    def addFile(self, file):
        if not os.path.exists(file):
            raise OSError, "File does not exist."
        self.files.append(file)


    def setUploadOption(self, opt, value):
        if not opt in self.upload:
            raise ValueError("Invalid upload option: " + opt)
        self.upload[opt] = value


    def canStart(self):
        if self.photoset == 'ask':
            return False
        return True


    def uploadSingle(self, f, callback):
        callback(f, self.getProgress(), self.numUploaded, self.numTotal)
        d = self.flickr.upload(filename=f, **self.upload)
        def incr(data):
            self.numUploading -= 1
            self.numUploaded += 1
            return data
        d.addCallback(incr)
        d.addCallback(lambda _: callback(f, self.getProgress(), self.numTotal))
        return d


    def doUpload(self, progressCallback):
        """
        Upload the files in the current queue. When done, it checks
        for more files and continues to upload those as well.
        """
        self.uploadStarted = True

        files = self.files[:]
        self.numUploading = len(self.files)
        self.files = []

        d = defer.succeed(True)
        for f in files:
            d.addCallback(lambda r: self.uploadSingle(f, progressCallback))

        def checkForMore(_):
            if self.files:
                return self.doUpload()
            return None
        d.addCallback(checkForMore)

        return d


    @property
    def numTotal(self):
        return self.numUploaded + self.numUploading + len(self.files)


    def getProgress(self):
        if not self.uploadStarted:
            return 0.
        return self.numUploaded / float(self.numTotal)


    def loadPhotoSets(self):
        setsxml = self.flickr.photosets_getList()
        self.photosets = {}
        for setxml in setsxml.findall(".//photoset"):
            self.photosets[setxml.find(".//title").text] = setxml.attrib["id"]
