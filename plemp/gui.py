# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import os
import gtk
import gobject
import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
	import dbus.glib


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

        self.status("Will upload %d files." % len(self.uploader.files))
        gobject.idle_add(self.checkStart)
        self.started = False


    def status(self, text):
        self.progressLabel.set_text(text)


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


    def uploadCallback(self, filenum, total, progress, done):
        if done and filenum == total and total > 0:
            self.status("Done!")
            self.progressBar.set_fraction(1.)
            gobject.timeout_add(200, self.upload) # check for more files
        else:
            self.status("Uploading file %d of %d" % (filenum, total))
            self.progressBar.set_fraction((100*(filenum-1)+progress)/(total*100.))

        self.window.queue_draw()
        self.window.get_window().process_updates(True)


    def checkStart(self):

        session_bus = dbus.SessionBus()
        try:
            o = session_bus.get_object("net.scherpenisse.Plemp", '/')
            # This is the second copy, add the files to the other copy.
            for f in self.uploader.files:
                o.addFile(f)
            gtk.main_quit()
            return
        except dbus.DBusException, e: # No other copy running
            print e

        # setup dbus service
        self.remote = RemoteControl(self, session_bus, self.uploader.profile)
        self.window.show()

        self.window.queue_draw()
        self.window.get_window().process_updates(True)

        if self.uploader.canStart() and not self.confirm:
            self.upload()
        else:
            if self.uploader.photoset == "ask":
                self.setEntry.set_text("")
            self.setEntry.set_sensitive(True)
            self.setEntry.grab_focus()
            self.goButton.grab_default()
            self.goButton.show()


    def upload(self):
        self.started = True
        if not self.uploader.files:
            gtk.main_quit()
        self.uploader.start()
            

    def on_goAction_activate(self, b):
        self.uploader.photoset = self.setEntry.get_text()
        self.setEntry.set_sensitive(False)
        self.goButton.hide()
        self.upload()


    def addFile(self, f):
        self.uploader.addFile(f)
        self.status("Will upload %d files." % len(self.uploader.files))


    def on_window_key_press_event(self, w, e):
        if self.started:
            return
        if e.keyval == gtk.keysyms.Escape:
            gtk.main_quit()



class RemoteControl(dbus.service.Object):
    def __init__(self, gui, session_bus, profile):
        self.gui = gui
        bus_name = dbus.service.BusName("net.scherpenisse.Plemp", bus=session_bus)
        dbus.service.Object.__init__(self, object_path='/', bus_name=bus_name)

    @dbus.service.method('net.scherpenisse.Plemp.Uploader')
    def addFile(self, f):
        self.gui.addFile(str(f))
