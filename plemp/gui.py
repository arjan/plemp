# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import gtk
import gobject


class GUI (object):

    def __init__(self, uploader):
        self.uploader = uploader

        builder = gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__), "plemp.ui"))
        for b in builder.get_objects():
            setattr(self, gtk.Buildable.get_name(b), b)
        builder.connect_signals(self)

        self.uploader.waitForAuthentication = self.waitForAuthentication
        self.uploader.authorizationError = self.authorizationError
        self.uploader.uploadCallback = self.uploadCallback

        self.goButton.hide()
        if not self.uploader.photoset:
            self.window.set_size_request(320, 70)
            self.setBox.hide()
        else:
            self.window.set_size_request(320, 120)
            self.setEntry.set_sensitive(False)
            self.setEntry.set_text(self.uploader.photoset)

        self.window.show()
        gobject.idle_add(self.checkStart)


    def waitForAuthentication(self):
        d = gtk.MessageDialog(self.window, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                              "You need to allow plemp to access your account at Flickr. A webpage has been opened for you to do the authorization.\n\nClick OK when done.")
        d.run()
        d.destroy()


    def authorizationError(self):
        d = gtk.MessageDialog(self.window, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                              "Authorization failed. Please retry.")
        d.run()
        d.destroy()


    def uploadCallback(self, filenum, progress, done):
        total = len(self.uploader.files)
        if done and filenum == total:
            self.progressLabel.set_text("Done!")
            self.progressBar.set_fraction(1.)
            gobject.idle_add(gtk.main_quit)
        else:
            self.progressLabel.set_text("Uploading file %d of %d" % (filenum, total))
            self.progressBar.set_fraction((100*(filenum-1)+progress)/(total*100.))

        self.window.queue_draw()
        self.window.get_window().process_updates(True)


    def checkStart(self):
        self.window.queue_draw()
        self.window.get_window().process_updates(True)

        if self.uploader.canStart():
            self.uploader.start()
        else:
            print "Need more info.."
            if self.uploader.photoset == "ask":
                self.setEntry.set_text("")
            self.setEntry.set_sensitive(True)
            self.setEntry.grab_focus()
            self.goButton.grab_default()
            self.goButton.show()


    def on_goAction_activate(self, b):
        self.uploader.photoset = self.setEntry.get_text()
        self.setEntry.set_sensitive(False)
        self.goButton.hide()
        self.uploader.start()

