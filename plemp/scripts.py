# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

import gtk

from optparse import OptionParser

from plemp import __version__
from plemp.base import Uploader


def main():
    parser = OptionParser(description="Utility to upload photos to Flickr, with graphical feedback.")
    parser.add_option("-p", "--profile", help="Profile name, for connecting multiple Flickr accounts", default=None, action='store')
    parser.add_option("", "--photoset", help="Upload to set ('ask' means interactive prompt)", default=None, action='store')
    parser.add_option("", "--collection", help="Upload to collection ('ask' means interactive prompt)", default=None, action='store')
    parser.add_option("-n", "--no-gui", help="Upload to collection ('ask' means interactive prompt)", action='store_true')
    parser.add_option("-c", "--confirm", help="Dont start uploading immediately, only after clicking the button.", action='store_true')

    parser.add_option("", "--content-type", help="Content type; 1 for Photo, 2 for Screenshot, or 3 for Other.", action='store')
    parser.add_option("", "--hidden", help="Hide; set to 1 to keep the photo in global search results, 2 to hide from public searches.", action='store')
    parser.add_option("-a", "--access", help="Access (public,private,family; comma separated)", action='store')
    parser.add_option("-v", "--version", help="Get version info.", action='store_true')

    (options, filenames) = parser.parse_args()

    if options.version:
        print "plemp", __version__
        print
        exit()

    uploader = Uploader(options.profile)
    uploader.photoset = options.photoset

    for opt in ['hidden', 'content_type']:
        uploader.setUploadOption(opt, getattr(options, opt))

    if options.access:
        access = [s.strip() for s in options.access.split(",")]
        if "public" not in access:
            uploader.setUploadOption('is_public', 0)
            for k in access:
                try:
                    uploader.setUploadOption('is_'+k, 1)
                except:
                    print "Invalid access option: " + k
                    exit(1)
        else:
            # public picture (the default)
            pass

    for f in filenames:
        uploader.addFile(f)

    if options.no_gui:
        uploader.initializeAPI()
        n = uploader.start()
        print "%d file(s) uploaded." % n
    else:
        if not uploader.files:
            exit()

        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)

        from plemp.gui import GUI
        gui = GUI(uploader)
        gui.confirm = options.confirm

        gtk.main()

