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
    numUploaded = 0
    numUploading = 0
    uploadStarted = False
    currentFile = None

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
            return self.connected(state)
        return self.flickr.authenticate_1().addCallback(auth_1)


    def connected(self, state):
        """ We are connected. """
        return state


    def setProgressCallback(self, cb):
        self.progressCallback = cb


    def addFile(self, file):
        if not os.path.exists(file):
            raise OSError, "File does not exist."
        self.files.append(file)
        if self.uploadStarted:
            self.progressCallback(self.currentFile, self.getProgress(), self.numUploaded+1, self.numTotal)


    def setUploadOption(self, opt, value):
        if not opt in self.upload:
            raise ValueError("Invalid upload option: " + opt)
        self.upload[opt] = value


    def canStart(self):
        if self.photoset == 'ask':
            return False
        return True


    def uploadSingle(self, f):
        self.currentFile = f

        self.progressCallback(self.currentFile, self.getProgress(), self.numUploaded+1, self.numTotal)

        def progress(client, p):
            self.progressCallback(self.currentFile, max(0.0, min(1.0, self.getProgress()+p/float(self.numTotal))), self.numUploaded+1, self.numTotal)

        d = self.flickr.upload(filename=self.currentFile, progressCallback=progress, **self.upload)

        def incr(r):
            self.numUploading -= 1
            self.numUploaded += 1
        d.addCallback(incr)

        return d


    def doUpload(self):
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
            d.addCallback(lambda r: self.uploadSingle(f))

        def checkForMore(_):
            if self.files:
                return self.doUpload()
            return None
        d.addCallback(checkForMore)

        # set to 100%
        d.addCallback(lambda _: self.progressCallback(self.currentFile, self.getProgress(), self.numUploaded, self.numTotal))

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
