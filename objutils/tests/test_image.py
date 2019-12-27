#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
import io
import unittest
import sys

import pytest

from objutils import loads, dumps
from objutils.section import Section
from objutils.image import Image, InvalidAddressError
from objutils.utils import PYTHON_VERSION, create_string_buffer

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.b0 = Image()
        self.b1 = Image()

    def tearDown(self):
        del self.b0
        del self.b1


class TestImageConstructors(unittest.TestCase):

    def testEmpty(self):
        img = Image()
        self.assertEqual(img.sections, [])

    def testNone(self):
        img = Image(None)
        self.assertEqual(img.sections, [])

    def testSingle(self):
        sec0 = Section(data = "hello", start_address = 0x100)
        img = Image(sec0)
        self.assertEqual(len(img.sections), 1)

    def testTwo(self):
        sec0 = Section(data = "hello", start_address = 0x100)
        sec1 = Section(data = "world", start_address = 0x200)
        img = Image((sec0, sec1))
        self.assertEqual(len(img.sections), 2)

    def testFailOnUnsupportedType(self):
        self.assertRaises(TypeError, Image, 4711)

@pytest.fixture
def images(scope = "module"):
    img0 = Image()
    img1 = Image()
    yield img0, img1
    del img0
    del img1

def test_insert1(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    assert img0.sections[0].start_address == 0x100
    assert img0.sections[0].data == bytearray(b"0123456789")
    assert img0.sections[0].length == 10

def test_insert_overlapping1(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    with pytest.raises(InvalidAddressError):
        img0.insert_section(data = b"0123456789", start_address = 0x100)

def test_insert_overlapping2(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    with pytest.raises(InvalidAddressError):
        img0.insert_section(data = b"0123456789", start_address = 0x109)

def test_insert_overlapping3(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    img0.insert_section(data = b"0123456789", start_address = 0x10a)

def test_insert_overlapping3(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    with pytest.raises(InvalidAddressError):
        img0.insert_section(data = b"0123456789", start_address = 0x0f7)

def test_insert_overlapping4(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    img0.insert_section(data = b"0123456789", start_address = 0x0f6)

def test_insert_overlapping5(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    img0.insert_section(data = b"0123456789", start_address = 0x114)
    img0.insert_section(data = b"0123456789", start_address = 0x10a)

def test_update1(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    with pytest.raises(InvalidAddressError):
        img0.update_section(data = b"abcdefghij", address = 0x10a)

def test_update2(images):
    img0, _ = images
    img0.insert_section(data = b"0123456789", start_address = 0x100)
    img0.update_section(data = b"abcdefghij", address = 0x109)

"""


    b0.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == TEST1
"""
def test_sorting1(capsys):
    RES = """
Section #0000
-------------
00000010  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0001
-------------
00000020  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0002
-------------
00000030  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0003
-------------
00000040  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0004
-------------
00000050  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0005
-------------
00000060  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0006
-------------
00000070  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0007
-------------
00000080  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0008
-------------
00000090  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0009
-------------
00000100  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------
"""
    img = Image(join = True)
    img.insert_section(data = b"0123456789", start_address = 0x100)
    img.insert_section(data = b"0123456789", start_address = 0x090)
    img.insert_section(data = b"0123456789", start_address = 0x080)
    img.insert_section(data = b"0123456789", start_address = 0x070)
    img.insert_section(data = b"0123456789", start_address = 0x060)
    img.insert_section(data = b"0123456789", start_address = 0x050)
    img.insert_section(data = b"0123456789", start_address = 0x040)
    img.insert_section(data = b"0123456789", start_address = 0x030)
    img.insert_section(data = b"0123456789", start_address = 0x020)
    img.insert_section(data = b"0123456789", start_address = 0x010)
    img.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == RES

def test_sorting2(capsys):
    RES = """
Section #0000
-------------
00000010  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0001
-------------
00000020  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0002
-------------
00000030  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0003
-------------
00000040  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0004
-------------
00000050  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0005
-------------
00000060  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0006
-------------
00000070  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0007
-------------
00000080  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0008
-------------
00000090  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------

Section #0009
-------------
00000100  30 31 32 33 34 35 36 37 38 39                    |0123456789      |
---------------
       10 bytes
---------------
"""
    img = Image(join = False)
    img.insert_section(data = b"0123456789", start_address = 0x100)
    img.insert_section(data = b"0123456789", start_address = 0x090)
    img.insert_section(data = b"0123456789", start_address = 0x080)
    img.insert_section(data = b"0123456789", start_address = 0x070)
    img.insert_section(data = b"0123456789", start_address = 0x060)
    img.insert_section(data = b"0123456789", start_address = 0x050)
    img.insert_section(data = b"0123456789", start_address = 0x040)
    img.insert_section(data = b"0123456789", start_address = 0x030)
    img.insert_section(data = b"0123456789", start_address = 0x020)
    img.insert_section(data = b"0123456789", start_address = 0x010)
    img.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == RES

@pytest.mark.skip
def test_sorting7(capsys):
    RES = """
Section #0000
-------------
00000000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
---------------
       16 bytes
---------------

Section #0001
-------------
00000010  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
---------------
       16 bytes
---------------

Section #0002
-------------
00000020  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
---------------
       16 bytes
---------------

Section #0003
-------------
00000030  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
---------------
       16 bytes
---------------
"""
    img = Image(join = False)
    img.insert_section(data = range(16), start_address = 0x030)
    img.insert_section(data = range(16), start_address = 0x020)
    img.insert_section(data = range(16), start_address = 0x010)
    img.insert_section(data = range(16), start_address = 0x000)
    img.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == RES

def test_sorting8(capsys):
    RES = """
Section #0000
-------------
00000000  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
          *
00000030  00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f  |................|
---------------
       64 bytes
---------------
"""
    img = Image(join = True)
    img.insert_section(data = range(16), start_address = 0x030)
    img.insert_section(data = range(16), start_address = 0x020)
    img.insert_section(data = range(16), start_address = 0x010)
    img.insert_section(data = range(16), start_address = 0x000)
    img.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == RES

@pytest.mark.skip
def test_get_section1():
    img = Image(join = False)
    img.insert_section(data = range(16), start_address = 0x030)
    img.insert_section(data = range(16), start_address = 0x020)
    img.insert_section(data = range(16), start_address = 0x010)
    img.insert_section(data = range(16), start_address = 0x000)
    sec = img.get_section(0x33)
    assert sec.start_address == 0x30
    sec = img.get_section(0x22)
    assert sec.start_address == 0x20
    sec = img.get_section(0x11)
    assert sec.start_address == 0x10
    sec = img.get_section(0x02)
    assert sec.start_address == 0x00

def test_get_section2():
    img = Image(join = True)
    img.insert_section(data = range(16), start_address = 0x030)
    img.insert_section(data = range(16), start_address = 0x020)
    img.insert_section(data = range(16), start_address = 0x010)
    img.insert_section(data = range(16), start_address = 0x000)
    sec = img.get_section(0x33)
    assert sec.start_address == 0x00
    assert len(sec) == 64


@pytest.mark.parametrize("join,", [False, True])
def test_get_section_raises(join):
    img = Image(join = join)
    img.insert_section(data = range(10), start_address = 0x030)
    img.insert_section(data = range(10), start_address = 0x020)
    img.insert_section(data = range(10), start_address = 0x010)
    img.insert_section(data = range(10), start_address = 0x000)
    with pytest.raises(InvalidAddressError):
        sec = img.get_section(0x3a)
    with pytest.raises(InvalidAddressError):
        sec = img.get_section(0x2b)
    with pytest.raises(InvalidAddressError):
        sec = img.get_section(0x1c)
    with pytest.raises(InvalidAddressError):
        sec = img.get_section(0x0d)


class Equality(BaseTest):

    def testEqualImagesShallCompareEqualCase1(self):
        self.b0.insert_section("01234567890", 0x1000)
        self.b1.insert_section("01234567890", 0x1000)
        self.assertTrue(self.b0 == self.b1)

    def testEqualImagesShallCompareEqualCase2(self):
        self.b0.insert_section("01234567890", 0x1000)
        self.b1.insert_section("01234567890", 0x1000)
        self.assertFalse(self.b0 != self.b1)


class TestCreateSections(BaseTest):

    SREC = b"S1131000000102030405060708090A0B0C0D0E0F64"

    def runSectionTestPass(self, data):
        self.b0.insert_section(data, 0x1000)
        result = dumps('srec', self.b0)
        self.assertEqual(result, self.SREC)

    def runSectionTestFail(self, data):
        self.assertRaises(ValueError, self.b0.insert_section, data, 0x1000)

    def testCreateSectionFromStringWorks(self):
        self.runSectionTestPass('\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f')

    def testCreateSectionFromListOfBytesWorks(self):
        self.runSectionTestPass([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f])

    def testCreateSectionFromListOfWordsFails(self):
        self.runSectionTestFail([0x0001, 0x0203, 0x0405, 0x0607, 0x0809, 0x0a0b, 0x0c0d, 0x0e0f])

    def testCreateSectionFromRangeWorks(self):
        self.runSectionTestPass(range(16))

    def testEnsureSectionHasCopySemantics(self):
        data = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f]
        self.b0.insert_section(data, 0x1000)
        data.extend([0x10, 0x20, 0x30, 0x40])
        result = dumps('srec', self.b0)
        self.assertEqual(result, self.SREC)

    def testEmptySectionProducesEmptiness(self):
        self.b0.insert_section([], 0x1000)
        result = dumps('srec', self.b0)
        self.assertEqual(result, b'')

    def testCreateSectionFromBytesWorks(self):
        if PYTHON_VERSION.major == 3:
            self.runSectionTestPass(bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f]))
        else:
            pass    # Unfortunately, this test-case isn't supported by Python 2.x

    def testCreateSectionFromByteArrayWorks(self):
        self.runSectionTestPass(bytearray([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f]))

    def testCreateSectionFromArrayBWorks(self):
        self.runSectionTestPass(array('B', [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f]))

    def testOmittedAddressYieldsToZero(self):
        self.b0.insert_section(range(16))
        data = self.b0
        self.assertEqual(data[0].start_address, 0X00000000)

    #def testCreateSectionFromArrayHWorks(self):
    #    if sys.byteorder == 'little':
    #        self.runSectionTestPass(array('H', [0x0100, 0x0302, 0x0504, 0x0706, 0x0908, 0x0b0a, 0x0d0c, 0x0f0e]))
    #    else:
    #        self.runSectionTestPass(array('H', [0x0001, 0x0203, 0x0405, 0x0607, 0x0809, 0x0a0b, 0x0c0d, 0x0e0f]))

    #def testCreateSectionFromUnicodeFails(self):
    #    self.runSectionTestPass('\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f')

class TestImageSlices(BaseTest):

    def createImage(self):
        self.b0.insert_section(range(16), 0x1000)
        self.b0.insert_section(range(16), 0x2000)
        self.b0.insert_section(range(16), 0x3000)

    def testLenWorks(self):
        self.createImage()
        image = self.b0
        self.assertEqual(len(image), 3)

    def testSlicingWorks(self):
        self.createImage()
        image = self.b0
        section = image[1]
        self.assertTrue(isinstance(section, Section))

    def testIteration(self):
        self.createImage()
        image = self.b0
        for section in image:
            self.assertTrue(isinstance(section, Section))

    def testHexdumpWorksOnSlice(self):
        self.createImage()
        image = self.b0
        section = image[1]
        if PYTHON_VERSION.major == 3:
            buf = io.TextIOWrapper(create_string_buffer())
        else:
            buf = create_string_buffer()
        section.hexdump(buf)


if __name__ == '__main__':
    unittest.main()

