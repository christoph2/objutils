#!/bin/env python

import os
from setuptools import setup, find_packages
from glob import glob
import sys

with open(os.path.join('objutils', 'version.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[-1].strip().strip('"')
            break

install_reqs = ['future', 'mako', 'six', 'construct', 'attrs >= 19.3.0', 'sortedcontainers', 'SQLAlchemy']

if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 4):
    install_reqs.extend(['enum34', 'mock'])

with open("docs/README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name = 'objutils',
    version = version,
    provides = ['objutils'],
    description = "Objectfile library for Python",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author = 'Christoph Schueler',
    author_email = 'cpu12.gems@googlemail.com',
    url = 'http://github.com/christoph2/objutils',
    packages=find_packages(),
    #include_package_data=True,
    extras_require={
       "docs": [
           'sphinxcontrib-napoleon'
       ],
        "develop": [
            "bumpversion"
       ]
    } ,
    install_requires = install_reqs,
    entry_points = {
        'console_scripts': [
                'oj-elf-info = objutils.scripts.oj_elf_info:main',
                'oj-elf-syms = objutils.scripts.oj_elf_syms:main',
                'oj-hex-info = objutils.scripts.oj_hex_info:main',
                'oj-elf-arm-attrs = objutils.scripts.oj_elf_arm_attrs:main',
                'oj-elf-extract = objutils.scripts.oj_elf_extract:main',
    #            'ticoff-dump = objutils.tools.ticoffdump:main'
        ],
    },
    tests_require=["pytest", "pytest-runner"],
    test_suite="objutils.tests",
    #data_files = [
    #    ('objutils/tests/ELFFiles', glob('objutils/tests/ELFFiles*.*')),
    #],
    package_dir = {'tests': 'objutils/tests'},
    license='GPLv2',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords = [
        'hex files',
        'intel hex',
        's19',
        'srec',
        'srecords',
        'object files',
        'map files',
        'embedded',
        'microcontroller',
        'ECU',
        'shf',
        'rfc4194',
    ],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    #package_data = {'tests': ['ELFFiles/*.*']},
)

