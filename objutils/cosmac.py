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

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data and update address tracking.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            True for all DATA record types, False for meta records
        """
        if format_type == DATA3:
            # Continuation record - check for start symbols
            if line.junk in ("!M", "?M"):  # Start symbol, not data
                return False

            # Address continues from previous record
            line.address = self.previous_address + self.previous_length
            self.previous_address = line.address
            self.previous_length = len(line.chunk)
        else:
            # Explicit address record - update tracking
            if hasattr(line, "chunk"):
                length = len(line.chunk)
            else:
                length = 0
            self.previous_address = line.address
            self.previous_length = length

        return format_type in (DATA0, DATA1, DATA2, DATA3)


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
