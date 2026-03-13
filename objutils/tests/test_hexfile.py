#!/usr/bin/env python
import unittest

from objutils import hexfile, loads, dumps, Section
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

    def test_reader_join_flag_preserves_sections(self):
        """Ensure Reader join flag keeps original section boundaries."""
        sec_a = Section(0xFFE0, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        sec_b = Section(0xFFE8, b"\x11\x12\x13\x14\x15\x16\x17\x18")
        img = Image([sec_a, sec_b], join=False)

        ihex_bytes = dumps("ihex", img)
        roundtrip = loads("ihex", ihex_bytes, join=False)

        self.assertEqual(len(roundtrip.sections), 2)
        self.assertEqual(roundtrip.sections[0].start_address, 0xFFE0)
        self.assertEqual(roundtrip.sections[0].data, sec_a.data)
        self.assertEqual(roundtrip.sections[1].start_address, 0xFFE8)
        self.assertEqual(roundtrip.sections[1].data, sec_b.data)

    def test_reader_defaults_to_no_join(self):
        """Default reader should preserve sections without merging."""
        sec_a = Section(0xFFE0, b"\x01" * 8)
        sec_b = Section(0xFFE8, b"\x02" * 8)
        img = Image([sec_a, sec_b], join=False)

        ihex_bytes = dumps("ihex", img)
        roundtrip = loads("ihex", ihex_bytes)

        self.assertEqual(len(roundtrip.sections), 2)
        self.assertEqual(roundtrip.sections[0].length, 8)
        self.assertEqual(roundtrip.sections[1].length, 8)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
