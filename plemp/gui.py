# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import gtk
import gobject
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib

from twisted.internet import reactor


class GUI (object):

    def __init__(self, uploader):
        self.uploader = uploader
        self.uploader.setProgressCallback(self.uploadCallback)

        builder = gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__), "plemp.ui"))
        for b in builder.get_objects():
            setattr(self, gtk.Buildable.get_name(b), b)
        builder.connect_signals(self)

        self.goButton.hide()
        if not self.uploader.photoset:
            self.window.set_size_request(320, 70)
            self.setBox.hide()
        else:
            self.window.set_size_request(320, 120)
            self.setEntry.set_sensitive(False)
            self.setEntry.child.set_text(self.uploader.photoset)

        self.status("Will upload %d files." % len(self.uploader.files))
        gobject.idle_add(self.initialize)


    def initialize(self):
        session_bus = dbus.SessionBus()
        try:
            o = session_bus.get_object("net.scherpenisse.Plemp", '/%s' % (self.uploader.profile or "default"))
            # This is the second copy, add the files to the other copy.
            for f in self.uploader.files:
                o.addFile(f)
            reactor.stop()
            return
        except dbus.DBusException: # No other copy running
            pass

        # setup dbus service
        self.remote = RemoteControl(self, session_bus, self.uploader.profile)

        d = self.uploader.initializeAPI(self.waitForAuthentication, self.authorizationError)

        def ok(r):
            self.window.show()

            if self.uploader.canStart() and not self.confirm:
                self.upload()
            else:
                if self.uploader.photoset == "ask":
                    self.setEntry.child.set_text("")
                self.setEntry.set_sensitive(True)
                self.setEntry.get_child().set_activates_default(True)
                self.setEntry.grab_focus()
                self.goButton.grab_default()
                self.goButton.show()
        d.addCallback(ok)



    def status(self, text):
        self.progressLabel.set_text(text)


    def waitForAuthentication(self, url):
        d = gtk.MessageDialog(self.window, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                       "You need to allow plemp to access your account at Flickr. Click the link below to do the authorization.\n\nClick OK when done authorizing.")
        link = gtk.LinkButton(url, "Authorize my account")
        link.show()
        d.vbox.pack_start(link)
        d.run()
        d.destroy()
        return True


    def authorizationError(self, f):
        d = gtk.MessageDialog(self.window, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                              "Authorization failed. Please retry.")
        d.run()
        d.destroy()
        reactor.stop()


        # d = self.uploader.flickr.photosets_getList(async=1)
        # def p(*a):
        #     print ">>", a
        # d.addCallback(p)


        # if self.uploader.photoset:
        #     for title in self.uploader.photosets.keys():
        #         self.setEntry.append_text(title)



    def upload(self):
        self.uploader.photoset = self.setEntry.child.get_text()
        self.setEntry.set_sensitive(False)
        self.goButton.hide()
        d = self.uploader.doUpload()
        d.addCallback(lambda _: reactor.stop())


    def uploadCallback(self, file, progress, uploaded, total):
        self.status("%s (%d of %d)" % (os.path.basename(file), uploaded, total))
        self.progressBar.set_fraction(progress)


    def on_goAction_activate(self, b):
        self.upload()


    def addFile(self, f):
        self.uploader.addFile(f)
        if not self.uploader.uploadStarted:
            self.status("Will upload %d files." % len(self.uploader.files))


    def on_window_key_press_event(self, w, e):
        if self.uploader.uploadStarted:
            return
        if e.keyval == gtk.keysyms.Escape:
            reactor.stop()



class RemoteControl(dbus.service.Object):
    def __init__(self, gui, session_bus, profile):
        self.gui = gui
        bus_name = dbus.service.BusName("net.scherpenisse.Plemp", bus=session_bus)
        dbus.service.Object.__init__(self, object_path='/%s' % (profile or "default"), bus_name=bus_name)

    @dbus.service.method('net.scherpenisse.Plemp.Uploader')
    def addFile(self, f):
        self.gui.addFile(str(f))
