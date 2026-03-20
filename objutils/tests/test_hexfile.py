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

    def test_reader_defaults_to_join(self):
        """Default reader should merge contiguous records."""
        sec_a = Section(0xFFE0, b"\x01" * 8)
        sec_b = Section(0xFFE8, b"\x02" * 8)
        img = Image([sec_a, sec_b], join=False)

        ihex_bytes = dumps("ihex", img)
        roundtrip = loads("ihex", ihex_bytes)

        self.assertEqual(len(roundtrip.sections), 1)
        self.assertEqual(roundtrip.sections[0].start_address, 0xFFE0)
        self.assertEqual(roundtrip.sections[0].data, b"\x01" * 8 + b"\x02" * 8)

    def test_reader_join_does_not_merge_conflicting_overlaps(self):
        """join=True should not merge overlaps when bytes differ."""
        sec_a = Section(0x1000, b"\x01\x02\x03\x04")
        sec_b = Section(0x1002, b"\x09\x09\x05\x06")
        img = Image([sec_a, sec_b], join=False)

        ihex_bytes = dumps("ihex", img)
        roundtrip = loads("ihex", ihex_bytes, join=True)

        self.assertEqual(len(roundtrip.sections), 2)
        self.assertEqual(roundtrip.sections[0].start_address, 0x1000)
        self.assertEqual(roundtrip.sections[0].data, b"\x01\x02\x03\x04")
        self.assertEqual(roundtrip.sections[1].start_address, 0x1002)
        self.assertEqual(roundtrip.sections[1].data, b"\x09\x09\x05\x06")

    def test_reader_join_merges_identical_duplicates(self):
        """Duplicate records with identical data should collapse into one section."""
        sec_a = Section(0x1000, b"A" * 4)
        sec_b = Section(0x1000, b"A" * 4)
        sec_c = Section(0x1004, b"B" * 4)
        sec_d = Section(0x1004, b"B" * 4)
        roundtrip = loads("ihex", dumps("ihex", Image([sec_a, sec_b, sec_c, sec_d], join=False)), join=True)

        self.assertEqual(len(roundtrip.sections), 1)
        self.assertEqual(roundtrip.sections[0].start_address, 0x1000)
        self.assertEqual(roundtrip.sections[0].data, b"A" * 4 + b"B" * 4)

    def test_reader_join_merges_overlapping_identical_prefix(self):
        """Overlaps that agree on shared bytes should merge and extend with the tail."""
        sec_a = Section(0x2000, b"\x11\x22\x33\x44")
        sec_b = Section(0x2002, b"\x33\x44\x55\x66")
        roundtrip = loads("ihex", dumps("ihex", Image([sec_a, sec_b], join=False)), join=True)

        self.assertEqual(len(roundtrip.sections), 1)
        self.assertEqual(roundtrip.sections[0].start_address, 0x2000)
        self.assertEqual(roundtrip.sections[0].data, b"\x11\x22\x33\x44\x55\x66")

    def test_reader_join_merges_full_containment_when_overlap_matches(self):
        """A fully-contained section with identical bytes should be absorbed."""
        sec_outer = Section(0x3000, b"\x10\x20\x30\x40\x50")
        sec_inner = Section(0x3001, b"\x20\x30")
        roundtrip = loads("ihex", dumps("ihex", Image([sec_inner, sec_outer], join=False)), join=True)

        self.assertEqual(len(roundtrip.sections), 1)
        self.assertEqual(roundtrip.sections[0].start_address, 0x3000)
        self.assertEqual(roundtrip.sections[0].data, b"\x10\x20\x30\x40\x50")

    def test_reader_join_merges_transitive_overlaps(self):
        """Compatible overlap chains should merge transitively into one section."""
        sec_a = Section(0x1000, b"ABCD")
        sec_b = Section(0x1002, b"CD12")
        sec_c = Section(0x1004, b"1234")
        roundtrip = loads("ihex", dumps("ihex", Image([sec_a, sec_b, sec_c], join=False)), join=True)

        self.assertEqual(len(roundtrip.sections), 1)
        self.assertEqual(roundtrip.sections[0].start_address, 0x1000)
        self.assertEqual(roundtrip.sections[0].data, b"ABCD1234")

    def test_reader_join_conflict_stays_split_but_followup_still_merges(self):
        """After a conflicting overlap split, later compatible records still merge."""
        sec_a = Section(0x1000, b"\x01\x02\x03\x04")
        sec_b = Section(0x1002, b"\x09\x09\x05\x06")
        sec_c = Section(0x1006, b"\x07\x08")
        roundtrip = loads("ihex", dumps("ihex", Image([sec_a, sec_b, sec_c], join=False)), join=True)

        self.assertEqual(len(roundtrip.sections), 2)
        self.assertEqual(roundtrip.sections[0].start_address, 0x1000)
        self.assertEqual(roundtrip.sections[0].data, b"\x01\x02\x03\x04")
        self.assertEqual(roundtrip.sections[1].start_address, 0x1002)
        self.assertEqual(roundtrip.sections[1].data, b"\x09\x09\x05\x06\x07\x08")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
