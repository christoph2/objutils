#!/bin/env python

import os
from setuptools import setup, find_packages
from glob import glob
import sys

def packagez(base):
    return  ["{0!s}{1!s}{2!s}".format(base, os.path.sep, p) for p in find_packages(base)]

install_reqs = ['future', 'mako', 'six', 'construct']

if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 4):
    install_reqs.extend(['enum34', 'mock'])

setup(
    name = 'objutils',
    version = '0.9.0',
    provides = ['objutils'],
    description = "Objectfile library for Python",
    author = 'Christoph Schueler',
    author_email = 'cpu12.gems@googlemail.com',
    url = 'http://github.com/christoph2/objutils',
    packages = packagez('objutils'),
    install_requires = install_reqs,
    #entry_points = {
    #    'console_scripts': [
    #            'readelf.py = objutils.tools.readelf:main',
    #            'ticoff-dump = objutils.tools.ticoffdump:main'
    #    ],
    #},
    tests_require=["pytest", "pytest-runner"],
    test_suite="objutils.tests",
    #data_files = [
    #    ('objutils/tests/ELFFiles', glob('objutils/tests/ELFFiles*.*')),
    #],
    package_dir = {'tests': 'objutils/tests'},
    #package_data = {'tests': ['ELFFiles/*.*']},
    #include_package_data = True,
)

