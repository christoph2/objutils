#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from objutils.image import Image
from objutils.utils import create_string_buffer, PYTHON_VERSION
import os
import io

TEST1 = """
Section #0000
-------------
00001000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00001010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00001020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00001030  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  |0123456789:;<=>?|
---------------
       64 bytes
---------------
"""

TEST2 = """
Section #0000
-------------
00001000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00001010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00001020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00001030  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  |0123456789:;<=>?|
---------------
       64 bytes
---------------

Section #0001
-------------
00002000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00002010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00002020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00002030  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  |0123456789:;<=>?|
---------------
       64 bytes
---------------
"""

TEST3 = """
Section #0000
-------------
00001000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00001010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00001020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00001030  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  |0123456789:;<=>?|
00001040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
          *
00001240  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00001250  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00001260  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00001270  30 31 32 33 34 35 36 37 38 39 3a 3b 3c 3d 3e 3f  |0123456789:;<=>?|
---------------
      640 bytes
---------------
"""

TEST4 = """
Section #0000
-------------
00001000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
00001010  10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f  |................|
00001020  20 21 22 23 24 25 26 27 28 29 2a 2b 2c 2d 2e 2f  | !"#$%&'()*+,-./|
00001030  30 31 32 33 34                                   |01234           |
---------------
       53 bytes
---------------
"""

TEST5 = """
Section #0000
-------------
00001000                                                   |                |
---------------
        0 bytes
---------------
"""


class BaseTest(unittest.TestCase):

    def setUp(self):
        if PYTHON_VERSION.major == 3:
            self.buf = io.TextIOWrapper(create_string_buffer())
        else:
            self.buf = create_string_buffer()
        #self.stdout = sys.stdout
        #sys.stdout = self.buf
        self.image = Image()

    def tearDown(self):
        #sys.stdout = self.stdout
        del self.buf
        del self.image

    def getBuffer(self):
        self.buf.seek(0, os.SEEK_SET)
        return self.buf.read()


class TestHexdumper(BaseTest):

    def testDumpContinuousRange(self):
        self.image.insert_section(range(64), 0x1000)
        self.image.join_sections()
        self.image.hexdump(self.buf)
        self.assertEqual(self.getBuffer(), TEST1)

    def testDumpDiscontinuousRange(self):
        self.image.insert_section(range(64), 0x1000)
        self.image.insert_section(range(64), 0x2000)
        self.image.join_sections()
        self.image.hexdump(self.buf)
        self.assertEqual(self.getBuffer(), TEST2)

    def testDumpZeroBytesInBetween(self):
        self.image.insert_section(range(64), 0x1000)
        self.image.insert_section([0] * 512)
        self.image.insert_section(range(64))
        self.image.join_sections()
        self.image.hexdump(self.buf)
        self.assertEqual(self.getBuffer(), TEST3)

    def testDumpOddSizedRow(self):
        self.image.insert_section(range(53), 0x1000)
        self.image.join_sections()
        self.image.hexdump(self.buf)
        self.assertEqual(self.getBuffer(), TEST4)

    def testDumpEmptyRow(self):
        self.image.insert_section(range(0), 0x1000)
        self.image.join_sections()
        self.image.hexdump(self.buf)
        self.assertEqual(self.getBuffer(), TEST5)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

