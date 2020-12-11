#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
import io
import unittest
import sys

import pytest

from objutils import dumps
from objutils.section import Section
from objutils.image import Image
from objutils.exceptions import InvalidAddressError
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
        self.assertEqual(len(image), 48)

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

def test_read_write_datatypes_require_suffix():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "uint8")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "int8")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "uint16")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "int16")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "uint32")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "int32")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "uint64")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "int64")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "float32")
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "float64")

def test_invalid_read_write_datatype_raises():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    with pytest.raises(TypeError):
        img.read_numeric(0x1000, "foobar_le")

def test_read_write():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write(0x1000, b'hello')
    assert img.read(0x1000, 5) == b"hello"

def test_write_boundary_case1():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    img.write(0x1000, b'hello')

def test_write_boundary_case2():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write(0x1001, b'hello')

def test_write_boundary_case3():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write(0x0fff, b'hello')

def test_read_boundary_case1():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    assert img.read(0x1000, 5) == b"\x00\x00\x00\x00\x00"

def test_read_boundary_case2():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read(0x1001, 5)

def test_read_boundary_case3():
    img = Image(Section(data = bytearray(5), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read(0x0fff, 5)

def test_read_write_uint8():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 0x55, "uint8_be")
    assert img.read_numeric(0x1000, "uint8_be") == 0x55
    img.write_numeric(0x1000, 0x55, "uint8_le")
    assert img.read_numeric(0x1000, "uint8_le") == 0x55

def test_read_write_int8():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, -20, "int8_be")
    assert img.read_numeric(0x1000, "int8_be") == -20
    img.write_numeric(0x1000, -20, "int8_le")
    assert img.read_numeric(0x1000, "int8_le") == -20

def test_read_write_uint16():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 0x5555, "uint16_be")
    assert img.read_numeric(0x1000, "uint16_be") == 0x5555
    img.write_numeric(0x1000, 0x5555, "uint16_le")
    assert img.read_numeric(0x1000, "uint16_le") == 0x5555

def test_read_write_int16():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, -2000, "int16_be")
    assert img.read_numeric(0x1000, "int16_be") == -2000
    img.write_numeric(0x1000, -2000, "int16_le")
    assert img.read_numeric(0x1000, "int16_le") == -2000

def test_read_write_uint32():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 0x55555555, "uint32_be")
    assert img.read_numeric(0x1000, "uint32_be") == 0x55555555
    img.write_numeric(0x1000, 0x55555555, "uint32_le")
    assert img.read_numeric(0x1000, "uint32_le") == 0x55555555

def test_read_write_int32():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, -20000000, "int32_be")
    assert img.read_numeric(0x1000, "int32_be") == -20000000
    img.write_numeric(0x1000, -20000000, "int32_le")
    assert img.read_numeric(0x1000, "int32_le") == -20000000

def test_read_write_uint64():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 0x5555555555555555, "uint64_be")
    assert img.read_numeric(0x1000, "uint64_be") == 0x5555555555555555
    img.write_numeric(0x1000, 0x5555555555555555, "uint64_le")
    assert img.read_numeric(0x1000, "uint64_le") == 0x5555555555555555

def test_read_write_int64():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, -200000000000, "int64_be")
    assert img.read_numeric(0x1000, "int64_be") == -200000000000
    img.write_numeric(0x1000, -200000000000, "int64_le")
    assert img.read_numeric(0x1000, "int64_le") == -200000000000

def test_read_write_float32():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 1234.5678, "float32_be")
    assert img.read_numeric(0x1000, "float32_be") == 1234.5677490234375
    img.write_numeric(0x1000, 1234.5678, "float32_le")
    assert img.read_numeric(0x1000, "float32_le") == 1234.5677490234375

def test_read_write_float64():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric(0x1000, 1234.5678, "float64_be")
    assert img.read_numeric(0x1000, "float64_be") == 1234.5678
    img.write_numeric(0x1000, 1234.5678, "float64_le")
    assert img.read_numeric(0x1000, "float64_le") == 1234.5678

def test_read_write_string():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_string(0x1000, 'hello')
    assert img.read_string(0x1000) == "hello"

def test_read_write_string_length():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_string(0x1000, 'hello world!!!')
    assert img.read_string(0x1000, length = 5) == "hello"

def test_read_unterminated_string_raises():
    img = Image(Section(data = bytearray(b"\x0a" * 32), start_address = 0x1000))
    img.write(0x1000, b'hello')
    with pytest.raises(TypeError):
        data = img.read_string(0x1000)
##
def test_write_array_data_must_be_iterable():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    with pytest.raises(TypeError):
        img.write_numeric_array(0x1000, 0x55, "uint8_be")

def test_write_uint8_array_boundary_case1():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")
    assert img[0].length == 10

def test_write_uint8_array_boundary_case2():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    img.write_numeric_array(0x1005, [1, 2, 3, 4, 5], "uint8_be")
    assert img[0].length == 10

def test_write_uint8_array_boundary_case3():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric_array(0x1006, [1, 2, 3, 4, 5], "uint8_be")

def test_write_uint8_array_boundary_case4():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric_array(0x0fff, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")

def test_read_uint8_array_boundary_case1():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    assert img.read_numeric_array(0x1000, 10, "uint8_be") == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

def test_read_uint8_array_boundary_case2():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    assert img.read_numeric_array(0x1005, 5, "uint8_be") == (0, 0, 0, 0, 0)

def test_read_uint8_array_boundary_case3():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric_array(0x1006, 5, "uint8_be") == (0, 0, 0, 0, 0)

def test_read_uint8_array_boundary_case4():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric_array(0x0fff, 5, "uint8_be") == (0, 0, 0, 0, 0)

def test_read_write_uint8_array():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "uint8_be") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_le")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "uint8_le") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

def test_read_write_int8_array():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int8_be")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "int8_be") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int8_le")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "int8_le") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)

def test_read_write_uint16_array():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint16_be")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "uint16_be") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint16_le")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "uint16_le") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

def test_read_write_int16_array():
    img = Image(Section(data = bytearray(32), start_address = 0x1000))
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int16_be")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "int16_be") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int16_le")
    assert img[0].length == 32
    assert img.read_numeric_array(0x1000, 10, "int16_le") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)

def test_read_write_uint32_array():
    img = Image(Section(data = bytearray(64), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint32_be")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "uint32_be") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint32_le")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "uint32_le") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

def test_read_write_int32_array():
    img = Image(Section(data = bytearray(64), start_address = 0x1000))
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int32_be")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "int32_be") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int32_le")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "int32_le") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)

def test_read_write_uint64_array():
    img = Image(Section(data = bytearray(128), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint64_be")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "uint64_be") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint64_le")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "uint64_le") == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

def test_read_write_int64_array():
    img = Image(Section(data = bytearray(128), start_address = 0x1000))
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int64_be")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "int64_be") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)
    img.write_numeric_array(0x1000, [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10], "int64_le")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "int64_le") == (-1, -2, -3, -4, -5, -6, -7, -8, -9, -10)

def test_read_write_float32_array():
    img = Image(Section(data = bytearray(64), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], "float32_be")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "float32_be") == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0)
    img.write_numeric_array(0x1000, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], "float32_le")
    assert img[0].length == 64
    assert img.read_numeric_array(0x1000, 10, "float32_le") == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0)

def test_read_write_float64_array():
    img = Image(Section(data = bytearray(128), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], "float64_be")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "float64_be") == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0)
    img.write_numeric_array(0x1000, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], "float64_le")
    assert img[0].length == 128
    assert img.read_numeric_array(0x1000, 10, "float64_le") == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0)

#
def test_write_uint8_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "uint8_le")

def test_write_uint16_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "uint16_le")

def test_write_uint32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "uint32_le")

def test_write_uint64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "uint64_le")

def test_write_int8_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "int8_le")

def test_write_int16_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "int16_le")

def test_write_int32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "int32_le")

def test_write_int64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 0xff, "int64_le")

def test_write_float32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 3.14159, "float32_le")

def test_write_float64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric(0x0fff, 3.14159, "float64_le")

def test_read_uint8_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "uint8_le")

def test_read_uint16_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "uint16_le")

def test_read_uint32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "uint32_le")

def test_read_uint64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "uint64_le")

def test_read_int8_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "int8_le")

def test_read_int16_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "int16_le")

def test_read_int32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "int32_le")

def test_read_int64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "int64_le")

def test_read_float32_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "float32_le")

def test_read_float64_negative_offset():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric(0x0fff, "float64_le")

def test_read_uint8_array_boundary_case1():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    assert img.read_numeric_array(0x1000, 10, "uint8_be") == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

def test_read_uint8_array_boundary_case2():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric_array(0x1001, 10, "uint8_be") == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

def test_read_uint8_array_boundary_case3():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.read_numeric_array(0x0fff, 10, "uint8_be") == (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

def test_write_uint8_array_boundary_case1():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    img.write_numeric_array(0x1000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")

def test_write_uint8_array_boundary_case2():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric_array(0x1001, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")

def test_write_uint8_array_boundary_case3():
    img = Image(Section(data = bytearray(10), start_address = 0x1000))
    with pytest.raises(InvalidAddressError):
        img.write_numeric_array(0x0fff, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "uint8_be")

if __name__ == '__main__':
    unittest.main()

