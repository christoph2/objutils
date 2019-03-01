#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import json
import os

import objutils.elf as Elf
import objutils.elf.defs as defs
import objutils.utils as utils

from objutils.elf.visual.readelf import ReadElf

def _basePath():
    import objutils as ot
    return ot.__path__[0]

BASE_PATH = _basePath()
PATH_TO_TEST_FILES = os.path.abspath(os.path.join(BASE_PATH, 'tests/'))

import unittest

class TestHeader(unittest.TestCase):

    def testFirst(self):
        headerStuff = json.load(open(os.path.join(PATH_TO_TEST_FILES, "elfHeaders.json")))
        log = open("results.txt", "w")

        for fname in headerStuff.keys():
           try:
               print("ELFFiles/{0}".format(fname))
               reader = ReadElf(os.path.join(PATH_TO_TEST_FILES, "ELFFiles/{0}".format(fname)))
               header0 = reader.renderHeader()
               header1 = headerStuff[fname]
               self.assertEqual(header0, header1)
               log.write(header0)
               log.write("*****\n")
               log.write(header1)
           except Exception as e:
                print("\t*** Something wrent wrong: '{0}'".format(str(e)))
        log.close()

    def testFileHeader(self):
        readElf = ReadElf(os.path.join(PATH_TO_TEST_FILES, 'ELFFiles/testfile23'))
        header = readElf.renderHeader()
        #self.assertEqual(header, R0)

    #def testProgramHeaders(self):
    #    readElf = ReadElf(os.path.join(PATH_TO_TEST_FILES, 'test-core.exec'))
    #
    #    header = renderTemplate(PROGRAM_HEADER_TMPL, ns)
    #    print(header)

def main():
    #unittest.main()
    pass

#"""
import difflib
from pprint import pprint

headerStuff = json.load(open(os.path.join(PATH_TO_TEST_FILES, "elfHeaders.json")))
reader = ReadElf(os.path.join(PATH_TO_TEST_FILES, "ELFFiles/aarch64_super_stripped.elf"))
header0 = headerStuff['aarch64_super_stripped.elf']
header1 = reader.renderHeader()
pprint(list(difflib.unified_diff(header0, header1)))
#pprint(list(difflib.ndiff(header0, header1)))
print("-" * 80)
print(header0)
print("-" * 80)
print(header1)
print("-" * 80)
print(header0 == header1)
#"""

if __name__ == '__main__':
    main()

