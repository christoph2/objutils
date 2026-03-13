#!/usr/bin/env python
"""RCA Cosmac hexadecimal object file format reader/writer.

This module handles the RCA Cosmac hex format, used with RCA 1802/1804/1805
microprocessors and COSMAC development systems.

Format specification:
- Four data record formats with optional address:
  1. !MAAAA DD - Full format with start symbol
  2. ?MAAAA DD - Alternate start symbol
  3. AAAA DD - Address only (no symbol)
  4. DD - Data only (address continues from previous)
- M: Memory identifier (single hex digit)
- AAAA: 16-bit address (hex)
- DD: Data bytes (hex, space-separated)
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from collections.abc import Sequence
from typing import Any

import objutils.hexfile as hexfile

# Record type identifiers
DATA0 = 1  # !MAAAA DD
DATA1 = 2  # ?MAAAA DD
DATA2 = 3  # AAAA DD
DATA3 = 4  # DD (address continues)


class Reader(hexfile.Reader):
    """RCA Cosmac format reader.

    Reads Cosmac hex files with memory identifier and flexible addressing.
    Supports four data formats including continuation records without address.
    """

    FORMAT_SPEC = (
        (DATA0, r"!MAAAA DD"),
        (DATA1, r"\?MAAAA DD"),
        (DATA2, r"AAAA DD"),
        (DATA3, r"DD"),
    )

    def __init__(self) -> None:
        """Initialize reader with address state tracking."""
        super().__init__()
        self.previous_address: int = 0
        self.previous_length: int = 0

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate Cosmac record.

        Args:
            line: Parsed line container
            format_type: Record type (DATA0-DATA3)

        Note:
            Cosmac format has no checksums, validation is minimal.
        """
        # Cosmac has no checksums - nothing to validate
        return None

    def probe(self, fp: Any, **kws: Any) -> bool:
        """Check if file matches RCA Cosmac format.

        Cosmac format is extremely flexible (!MAAAA DD, ?MAAAA DD, AAAA DD, DD),
        making it very prone to false positives. We check for the presence
        of start symbols (!M or ?M) to confirm.
        """
        MAX_SAMPLE_LINES = 10

        # Save position
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, Exception):
            pass

        try:
            for _ in range(MAX_SAMPLE_LINES):
                line = fp.readline()
                if not line:
                    break

                line_str = line.decode(errors="ignore") if isinstance(line, bytes) else line
                line_str = line_str.strip()
                if not line_str:
                    continue

                # Check for explicit start symbols (!M or ?M)
                if line_str.startswith(("!M", "?M")):
                    return True

            # If no symbols found, it's probably not Cosmac (or a very bare-bones version)
            return False
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, Exception):
                pass


class Writer(hexfile.Writer):
    """RCA Cosmac format writer.

    Writes Cosmac hex files with memory identifier and 16-bit addressing.
    """

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (16-bit)
            length: Data length in bytes (unused, inferred from row)
            row: Data bytes to encode

        Returns:
            Formatted Cosmac record: !MAAAA DD
        """
        # Use full format (!M) with explicit address
        line = f"!M{address:04X} {Writer.hex_bytes(row)}"
        return line
