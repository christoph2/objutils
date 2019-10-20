#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
from objutils import loads, dumps
from objutils.section import Section
from objutils.image import Builder
from objutils.utils import create_string_buffer, PYTHON_VERSION
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
            buf = io.TextIOWrapper(create_string_buffer())
        else:
            buf = create_string_buffer()
        b0 = Builder()
        b0.add_section("hello world!")
        b0.join_sections()
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

    def createImage(self, auto_sort = False, auto_join = False):
        builder = Builder(auto_sort = auto_sort, auto_join = auto_join)
        builder.add_section(range(16), 0x90)
        builder.add_section(range(16), 0x80)
        builder.add_section(range(16), 0x70)
        builder.add_section(range(16), 0x60)
        builder.add_section(range(16), 0x50)
        return [s.start_address for s in builder.image]

    def testBuilderPreservesOrder(self):
        self.assertEqual(self.createImage(auto_sort = False), [144, 128, 112, 96, 80])

    def testBuilderSortsSegments(self):
        self.assertEqual(self.createImage(auto_sort = True), [80, 96, 112, 128, 144])

    def testBuilderAutoJoinsSegments(self):
        self.assertEqual(self.createImage(auto_sort = True, auto_join = True), [80])

    def testBuilderCantJoinSegments(self):
        self.assertEqual(self.createImage(auto_sort = False, auto_join = True), [144, 128, 112, 96, 80])

if __name__ == '__main__':
    unittest.main()

