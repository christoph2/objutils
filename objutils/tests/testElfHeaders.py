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
PATH_TO_TEST_FILES = os.path.abspath(os.path.join(BASE_PATH, 'tests/ELFFiles'))

import unittest

class TestHeader(unittest.TestCase):

    def testFirst(self):
       headerStuff = json.load(file("./elfHeaders.json"))
       for fname in headerStuff.keys():
           print(fname)

    def testFileHeader(self):
        readElf = ReadElf(os.path.join(PATH_TO_TEST_FILES, 'testfile23'))
        header = readElf.renderHeader()
        #self.assertEqual(header, R0)

    #def testProgramHeaders(self):
    #    readElf = ReadElf(os.path.join(PATH_TO_TEST_FILES, 'test-core.exec'))
    #
    #    header = renderTemplate(PROGRAM_HEADER_TMPL, ns)
    #    print(header)

def main():
    unittest.main()

if __name__ == '__main__':
    main()

