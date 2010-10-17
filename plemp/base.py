# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import flickrapi

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
                       'hidden': 0,
                       'content_type': 1}
        self.photoset = None
        self.exif = {}
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret, username=profile)


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


    def start(self):

        if not self.files:
            return 0

        (token, frob) = self.flickr.get_token_part_one('write')
        if not token:
            self.waitForAuthentication()
        try:
            self.flickr.get_token_part_two((token, frob))
        except:
            # Authorization error
            self.authorizationError()
            exit(1)

        if self.photoset:
            self.loadPhotoSets()

        self.uploadCallback(1, 0.0, False)

        photos = []
        numUploaded = 0
        for f in self.files:
            p = self.flickr.upload(f, lambda p, d: self.uploadCallback(self.files.index(f)+1, p, d), **self.upload)
            numUploaded += 1
            photos.append(p.find(".//photoid").text)

        if self.photoset:
            # check if set exists
            if self.photoset in self.photosets:
                set_id = self.photosets[self.photoset]
            elif self.photoset in self.photosets.values():
                set_id = self.photoset
            else:
                # create set
                rsp = self.flickr.photosets_create(title=self.photoset, primary_photo_id=photos[0])
                del photos[0] # already in set
                set_id = rsp.find(".//photoset").attrib["id"]
            for p in photos:
                try:
                    self.flickr.photosets_addPhoto(photoset_id=set_id, photo_id=p)
                except Exception, e:
                    print e
        return numUploaded


    def waitForAuthentication(self):
        raw_input("Press ENTER after you authorized this program")


    def authorizationError(self):
        print "Authorization error. Launch the program again to retry."


    def uploadCallback(self, filenum, progress, done):
        if not done:
            print "%d of %d - %3d%%" % (filenum, len(self.files), progress)
        else:
            print "OK!"


    def loadPhotoSets(self):
        setsxml = self.flickr.photosets_getList()
        self.photosets = {}
        for setxml in setsxml.findall(".//photoset"):
            self.photosets[setxml.find(".//title").text] = setxml.attrib["id"]
