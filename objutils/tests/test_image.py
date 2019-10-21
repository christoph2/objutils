#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
import io
import unittest
import sys

from objutils import loads, dumps
from objutils.section  import Section
from objutils.image  import Image, Builder
from objutils.utils import PYTHON_VERSION, create_string_buffer

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.b0 = Builder()
        self.b1 = Builder()

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


class Equality(BaseTest):

    def testEqualImagesShallCompareEqualCase1(self):
        self.b0.add_section("01234567890", 0x1000)
        self.b1.add_section("01234567890", 0x1000)
        self.assertTrue(self.b0.image == self.b1.image)

    def testEqualImagesShallCompareEqualCase2(self):
        self.b0.add_section("01234567890", 0x1000)
        self.b1.add_section("01234567890", 0x1000)
        self.assertFalse(self.b0.image != self.b1.image)


class TestCreateSections(BaseTest):

    SREC = b"S1131000000102030405060708090A0B0C0D0E0F64"

    def runSectionTestPass(self, data):
        self.b0.add_section(data, 0x1000)
        result = dumps('srec', self.b0.image)
        self.assertEqual(result, self.SREC)

    def runSectionTestFail(self, data):
        self.assertRaises(ValueError, self.b0.add_section, data, 0x1000)

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
        self.b0.add_section(data, 0x1000)
        data.extend([0x10, 0x20, 0x30, 0x40])
        result = dumps('srec', self.b0.image)
        self.assertEqual(result, self.SREC)

    def testEmptySectionProducesEmptiness(self):
        self.b0.add_section([], 0x1000)
        result = dumps('srec', self.b0.image)
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
        self.b0.add_section(range(16))
        data = self.b0.image
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
        self.b0.add_section(range(16), 0x1000)
        self.b0.add_section(range(16), 0x2000)
        self.b0.add_section(range(16), 0x3000)

    def testLenWorks(self):
        self.createImage()
        image = self.b0.image
        self.assertEqual(len(image), 3)

    def testSlicingWorks(self):
        self.createImage()
        image = self.b0.image
        section = image[1]
        self.assertTrue(isinstance(section, Section))

    def testIteration(self):
        self.createImage()
        image = self.b0.image
        for section in image:
            self.assertTrue(isinstance(section, Section))

    def testHexdumpWorksOnSlice(self):
        self.createImage()
        image = self.b0.image
        section = image[1]
        if PYTHON_VERSION.major == 3:
            buf = io.TextIOWrapper(create_string_buffer())
        else:
            buf = create_string_buffer()
        section.hexdump(buf)


if __name__ == '__main__':
    unittest.main()

