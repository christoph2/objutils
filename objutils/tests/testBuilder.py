#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
from objutils import loads, dumps
from objutils.section import Section
from objutils.image import Builder
from objutils.utils import createStringBuffer, PYTHON_VERSION
import unittest

TEST1 = """
Section #0000
-------------
00000000  68 65 6c 6c 6f 20 77 6f 72 6c 64 21              |hello world!    |
---------------
       12 bytes
---------------
"""

class TestBasicFunctionality(unittest.TestCase):

    def testBasic(self):
        if PYTHON_VERSION.major == 3:
            buf = io.TextIOWrapper(createStringBuffer())
        else:
            buf = createStringBuffer()
        b0 = Builder()
        b0.addSegment("hello world!")
        b0.joinSections()
        b0.hexdump(buf)
        buf.seek(0, os.SEEK_SET)
        self.assertEqual(buf.read(), TEST1)

    def testFailIfSectionsAreNotIterateble(self):
        self.assertRaises(TypeError, Builder, 4711)

    def testFailIfSectionIsNotValid(self):
        self.assertRaises(TypeError, Builder, ["abc"])

    def testValidSections(self):
        builder = Builder([Section(0x1000, range(128))])


    def testFailIfSectionsAreNotIterateble2(self):
        builder = Builder([])
        print(builder.image)

class TestBuilderParameters(unittest.TestCase):

    def createImage(self, autoSort = False, autoJoin = False):
        builder = Builder(autoSort = autoSort, autoJoin = autoJoin)
        builder.addSegment(range(16), 0x90)
        builder.addSegment(range(16), 0x80)
        builder.addSegment(range(16), 0x70)
        builder.addSegment(range(16), 0x60)
        builder.addSegment(range(16), 0x50)
        return [s.startAddress for s in builder.image]

    def testBuilderPreservesOrder(self):
        self.assertEqual(self.createImage(autoSort = False), [144, 128, 112, 96, 80])

    def testBuilderSortsSegments(self):
        self.assertEqual(self.createImage(autoSort = True), [80, 96, 112, 128, 144])

    def testBuilderAutoJoinsSegments(self):
        self.assertEqual(self.createImage(autoSort = True, autoJoin = True), [80])

    def testBuilderCantJoinSegments(self):
        self.assertEqual(self.createImage(autoSort = False, autoJoin = True), [144, 128, 112, 96, 80])

if __name__ == '__main__':
    unittest.main()

