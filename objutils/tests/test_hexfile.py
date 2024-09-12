#!/usr/bin/env python
import unittest

from objutils import hexfile, loads
from objutils.image import Image


class TestHexfile(unittest.TestCase):
    def setUp(self):
        self.image = Image()

    def tearDown(self):
        del self.image

    def testAddSectionAliasWorks(self):
        self.image.insert_section(range(64), 0x1000)
        # Ok, if no exception gets raised.

    def testRaisesInvalidChecksumError(self):
        self.assertRaises(
            hexfile.InvalidRecordChecksumError,
            loads,
            "srec",
            b"S110000048656C6C6F2C20776F726C6421AA",
        )

    def testRaisesError(self):
        #        self.assertRaises(hexfile.InvalidRecordChecksumError, loads, "srec", b'S110000048656C6C6F20776F726C642166')
        pass


def main():
    unittest.main()


if __name__ == "__main__":
    main()
