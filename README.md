Plemp
=====

A small, no-frills tool for uploading photos to Flickr.

Usage
-----

    plemp *.jpg

Uploads all jpeg files from current directory to flickr.

    plemp --photoset="A new set" -n *.jpg 

The same, but without a graphical interface. Puts the files in the set "A new set".

    plemp ---photoset=ask *.jpg

Shows the plemp window with the photoset box highlighted so you can type the title for the photoset, or select an existing set from your account from the dropdown.
Installation:

Installation
------------

In Ubuntu:

    sudo add-apt-repository ppa:arjan-scherpenisse/plemp
    sudo apt-get update
    sudo apt-get install plemp

Or else:

    sudo easy_install plemp


Download source code
--------------------

 * http://github.com/arjan/plemp
 * git clone http://arjan@github.com/arjan/plemp.git
