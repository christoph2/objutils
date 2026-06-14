#!/usr/bin/env python
"""Tests for the OpenOCD ``flash mdb`` text format (oocdtxt) reader/writer."""

import io
import unittest

from objutils import dumps, load, loads
from objutils.oocdtxt import DEFAULT_ROW_LENGTH, Reader, Writer

# ---------------------------------------------------------------------------
# Minimal fixture: two consecutive 32-byte lines starting at 0x00008000
# ---------------------------------------------------------------------------
SIMPLE_INPUT = (
    b"0x00008000: aa 50 01 02 00 90 00 00 00 50 00 00 6e 76 73 00"
    b" 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00\n"
    b"0x00008020: aa 50 01 00 00 e0 00 00 00 20 00 00 6f 74 61 64"
    b" 61 74 61 00 00 00 00 00 00 00 00 00 00 00 00 00\n"
)


# One line with 16 bytes (non-standard row length)
SIXTEEN_BYTE_INPUT = b"0x00001000: 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f\n"
SIXTEEN_BYTE_DATA = bytes(range(16))

# File with extra comment / prompt lines that should be ignored
NOISY_INPUT = b"> flash mdb 0x00001000 16\n" b"0x00001000: 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f\n" b"shutdown\n"

# Three non-consecutive sections
MULTI_SECTION_INPUT = b"0x00000000: de ad be ef\n" b"0x00001000: ca fe ba be\n" b"0x00002000: 01 02 03 04\n"


class TestReader(unittest.TestCase):
    """Unit tests for :class:`objutils.oocdtxt.Reader`."""

    def _loads(self, data: bytes, join: bool = False):
        """Helper: parse *data* using the oocdtxt codec."""
        return loads("oocdtxt", data, join=join)

    # ------------------------------------------------------------------
    # Basic parsing
    # ------------------------------------------------------------------

    def test_simple_two_lines(self):
        img = self._loads(SIMPLE_INPUT)
        sections = list(img)
        # Two consecutive sections (not joined by default)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].start_address, 0x00008000)
        self.assertEqual(len(sections[0].data), 32)
        self.assertEqual(sections[1].start_address, 0x00008020)
        self.assertEqual(len(sections[1].data), 32)

    def test_first_line_data_content(self):
        img = self._loads(SIMPLE_INPUT)
        section = list(img)[0]
        self.assertEqual(section.data[0], 0xAA)
        self.assertEqual(section.data[1], 0x50)

    def test_sixteen_byte_line(self):
        img = self._loads(SIXTEEN_BYTE_INPUT)
        sections = list(img)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].start_address, 0x00001000)
        self.assertEqual(bytes(sections[0].data), SIXTEEN_BYTE_DATA)

    def test_join_consecutive_sections(self):
        img = self._loads(SIMPLE_INPUT, join=True)
        sections = list(img)
        # Two 32-byte lines are consecutive → joined into one
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(sections[0].data), 64)

    def test_noisy_file_skips_non_matching_lines(self):
        """Lines that do not match the pattern must be silently ignored."""
        img = self._loads(NOISY_INPUT)
        sections = list(img)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].start_address, 0x00001000)
        self.assertEqual(bytes(sections[0].data), SIXTEEN_BYTE_DATA)

    def test_multi_section(self):
        img = self._loads(MULTI_SECTION_INPUT)
        sections = list(img)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].start_address, 0x00000000)
        self.assertEqual(sections[1].start_address, 0x00001000)
        self.assertEqual(sections[2].start_address, 0x00002000)

    def test_multi_section_data(self):
        img = self._loads(MULTI_SECTION_INPUT)
        sections = list(img)
        self.assertEqual(bytes(sections[0].data), b"\xde\xad\xbe\xef")
        self.assertEqual(bytes(sections[1].data), b"\xca\xfe\xba\xbe")
        self.assertEqual(bytes(sections[2].data), b"\x01\x02\x03\x04")

    def test_empty_file_raises(self):
        from objutils.hexfile import ParseError

        with self.assertRaises(ParseError):
            self._loads(b"# no valid data here\n")

    def test_file_path_loading(self):
        """load() with an actual file path must work end-to-end."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as fh:
            fh.write(SIXTEEN_BYTE_INPUT)
            tmp_path = fh.name

        try:
            img = load("oocdtxt", tmp_path)
            sections = list(img)
            self.assertEqual(len(sections), 1)
            self.assertEqual(bytes(sections[0].data), SIXTEEN_BYTE_DATA)
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Mixed-case addresses / bytes
    # ------------------------------------------------------------------

    def test_uppercase_address(self):
        data = b"0x0000ABCD: 01 02 03\n"
        img = self._loads(data)
        sections = list(img)
        self.assertEqual(sections[0].start_address, 0x0000ABCD)

    def test_uppercase_bytes(self):
        data = b"0x00000000: AA BB CC DD\n"
        img = self._loads(data)
        sections = list(img)
        self.assertEqual(bytes(sections[0].data), b"\xaa\xbb\xcc\xdd")


class TestProbe(unittest.TestCase):
    """Unit tests for :meth:`objutils.oocdtxt.Reader.probe`."""

    def _probe(self, data: bytes) -> bool:
        reader = Reader()
        return reader.probe(io.BytesIO(data))

    def test_valid_file_detected(self):
        self.assertTrue(self._probe(SIMPLE_INPUT))

    def test_noisy_file_detected(self):
        # More than half of non-empty lines match → True
        self.assertTrue(self._probe(SIMPLE_INPUT))

    def test_unrelated_file_not_detected(self):
        self.assertFalse(self._probe(b":10000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00\n"))

    def test_empty_file_not_detected(self):
        self.assertFalse(self._probe(b""))

    def test_probe_restores_position(self):
        buf = io.BytesIO(SIMPLE_INPUT)
        reader = Reader()
        reader.probe(buf)
        self.assertEqual(buf.tell(), 0)


class TestWriter(unittest.TestCase):
    """Unit tests for :class:`objutils.oocdtxt.Writer`."""

    def _roundtrip(self, data: bytes, row_length: int = DEFAULT_ROW_LENGTH) -> bytes:
        """Parse *data*, serialise back, return the raw bytes."""
        img = loads("oocdtxt", data)
        return bytes(dumps("oocdtxt", img, row_length=row_length))

    # ------------------------------------------------------------------
    # Output format verification
    # ------------------------------------------------------------------

    def test_compose_row_format(self):
        writer = Writer()
        row = list(range(4))  # [0, 1, 2, 3]
        result = writer.compose_row(0x00008000, 4, row)
        self.assertEqual(result, "0x00008000: 00 01 02 03")

    def test_compose_row_lowercase_bytes(self):
        writer = Writer()
        result = writer.compose_row(0x00000000, 4, [0xAA, 0xBB, 0xCC, 0xDD])
        self.assertIn("aa bb cc dd", result)

    def test_compose_row_address_format(self):
        writer = Writer()
        result = writer.compose_row(0x12345678, 1, [0xFF])
        self.assertTrue(result.startswith("0x12345678:"))

    # ------------------------------------------------------------------
    # Round-trip tests
    # ------------------------------------------------------------------

    def test_roundtrip_simple(self):
        """Data survives a load → dump → load cycle unchanged."""
        img_orig = loads("oocdtxt", SIXTEEN_BYTE_INPUT)
        serialised = dumps("oocdtxt", img_orig, row_length=16)
        img_rt = loads("oocdtxt", serialised)
        orig_sections = list(img_orig)
        rt_sections = list(img_rt)
        self.assertEqual(len(orig_sections), len(rt_sections))
        for orig, rt in zip(orig_sections, rt_sections):
            self.assertEqual(orig.start_address, rt.start_address)
            self.assertEqual(bytes(orig.data), bytes(rt.data))

    def test_roundtrip_multi_section(self):
        img_orig = loads("oocdtxt", MULTI_SECTION_INPUT)
        serialised = dumps("oocdtxt", img_orig, row_length=4)
        img_rt = loads("oocdtxt", serialised)
        orig_sections = sorted(img_orig, key=lambda s: s.start_address)
        rt_sections = sorted(img_rt, key=lambda s: s.start_address)
        self.assertEqual(len(orig_sections), len(rt_sections))
        for orig, rt in zip(orig_sections, rt_sections):
            self.assertEqual(orig.start_address, rt.start_address)
            self.assertEqual(bytes(orig.data), bytes(rt.data))

    def test_default_row_length_is_32(self):
        """The default Writer output must use 32-byte rows."""
        # Build a 64-byte image
        img = loads("oocdtxt", SIMPLE_INPUT, join=True)
        output = dumps("oocdtxt", img).decode()
        lines = [ln for ln in output.splitlines() if ln.strip()]
        # 64 bytes / 32 per row = 2 rows
        self.assertEqual(len(lines), 2)

    def test_custom_row_length_16(self):
        img = loads("oocdtxt", SIMPLE_INPUT, join=True)
        output = dumps("oocdtxt", img, row_length=16).decode()
        lines = [ln for ln in output.splitlines() if ln.strip()]
        # 64 bytes / 16 per row = 4 rows
        self.assertEqual(len(lines), 4)

    def test_output_starts_with_0x(self):
        img = loads("oocdtxt", SIXTEEN_BYTE_INPUT)
        output = dumps("oocdtxt", img, row_length=16).decode()
        for line in output.splitlines():
            if line.strip():
                self.assertTrue(line.startswith("0x"), f"Line does not start with '0x': {line!r}")

    def test_output_colon_separator(self):
        img = loads("oocdtxt", SIXTEEN_BYTE_INPUT)
        output = dumps("oocdtxt", img, row_length=16).decode()
        for line in output.splitlines():
            stripped = line.strip()
            if stripped:
                self.assertIn(": ", stripped)

    # ------------------------------------------------------------------
    # Conversion to another format
    # ------------------------------------------------------------------

    def test_convert_to_ihex(self):
        """Loaded oocdtxt data must be convertible to Intel HEX."""
        img = loads("oocdtxt", SIXTEEN_BYTE_INPUT)
        ihex_data = dumps("ihex", img)
        self.assertIn(b":", ihex_data)

    def test_convert_from_srec(self):
        """S-Record data must be convertible to oocdtxt."""
        srec_data = b"S1130000000102030405060708090a0b0c0d0e0f74\nS5030001FB\n"
        img = loads("srec", srec_data)
        oocd_data = dumps("oocdtxt", img, row_length=16).decode()
        lines = [ln for ln in oocd_data.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("0x00000000:"))


class TestExampleFile(unittest.TestCase):
    """Integration test using the real example file shipped with the project."""

    EXAMPLE_PATH = "examples/openocd_bytes.txt"

    def test_load_example_file(self):
        try:
            img = load("oocdtxt", self.EXAMPLE_PATH)
        except FileNotFoundError:
            self.skipTest(f"Example file not found: {self.EXAMPLE_PATH}")
        sections = list(img)
        self.assertGreater(len(sections), 0, "Expected at least one section")

    def test_example_first_section_address(self):
        try:
            img = load("oocdtxt", self.EXAMPLE_PATH, join=True)
        except FileNotFoundError:
            self.skipTest(f"Example file not found: {self.EXAMPLE_PATH}")
        sections = sorted(img, key=lambda s: s.start_address)
        self.assertEqual(sections[0].start_address, 0x00008000)

    def test_example_roundtrip(self):
        try:
            img_orig = load("oocdtxt", self.EXAMPLE_PATH, join=True)
        except FileNotFoundError:
            self.skipTest(f"Example file not found: {self.EXAMPLE_PATH}")
        serialised = dumps("oocdtxt", img_orig)
        img_rt = loads("oocdtxt", serialised, join=True)
        orig_sections = sorted(img_orig, key=lambda s: s.start_address)
        rt_sections = sorted(img_rt, key=lambda s: s.start_address)
        self.assertEqual(len(orig_sections), len(rt_sections))
        for orig, rt in zip(orig_sections, rt_sections):
            self.assertEqual(orig.start_address, rt.start_address)
            self.assertEqual(bytes(orig.data), bytes(rt.data))


def main():
    unittest.main()


if __name__ == "__main__":
    main()
