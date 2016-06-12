#!/bin/env/python

from distutils.core import setup, Extension
import os
from setuptools import find_packages
from glob import glob

def packagez(base):
    return  ["{0!s}{1!s}{2!s}".format(base, os.path.sep, p) for p in find_packages(base)]

from distutils.core import setup,Extension
from setuptools import find_packages,setup

setup(
    name = 'objutils',
    version = '0.9.0',
    provides = ['objutils'],
    description = "Objectfile library for Python",
    author = 'Christoph Schueler',
    author_email = 'cpu12.gems@googlemail.com',
    url = 'http://github.com/christoph2/objutils',
    packages = packagez('objutils'),
    install_requires = ['enum34', 'future'],
    entry_points = {
	'console_scripts': [
		'readelf.py = objutils.tools.readelf:main',
        ],
    },
    test_suite = "objutils.tests"
)

