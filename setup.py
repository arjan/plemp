#!/usr/bin/env python
# Copyright (c) 2010 Arjan Scherpenisse
# See LICENSE for details.

"""
Plemp installation script
"""

from setuptools import setup
from plemp import __version__

setup(
    name = "plemp",
    version = __version__,
    author = "Arjan Scherpenisse",
    author_email = "arjan@scherpenisse.net",
    url = "http://scherpenisse.net/plemp",
    description = "Simple commandline flickr upload tool",
    scripts = [
        "scripts/plemp"
        ],
    license="MIT/X",
    packages = ['plemp'],
    package_data={'plemp': ['*.ui']},

    long_description = """
Plemp is a commandline tool for uploading photos to flickr. It has a
gtk-based status window, and therefore is ideal to use from thirdparty
applications like Bibble.
    """,
      install_requires = [
      ],
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Communications",
        "Topic :: Utilities"
        ]
    )
