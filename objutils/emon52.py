#!/usr/bin/env python
"""Elektor EMON52 hexadecimal object file format reader/writer.

This module handles the EMON52 hex format used by the Elektor
Electronics EMON52 8052 development system.

Format specification:
- Data records: LL AAAA:DD CCCC
  - LL: Length/byte count (hex)
  - AAAA: 16-bit address (hex)
  - DD: Data bytes (hex, space-separated)
  - CCCC: 16-bit checksum (sum of data bytes, mod 65536)
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
from typing import Any, BinaryIO

import objutils.hexfile as hexfile


# Record type identifiers (Intel HEX compatible)
DATA = 0
EOF = 1
EXTENDED_SEGMENT_ADDRESS = 2
START_SEGMENT_ADDRESS = 3
EXTENDED_LINEAR_ADDRESS = 4
START_LINEAR_ADDRESS = 5


class Codec:
    """Simple codec wrapper for file I/O.

    Provides pass-through readlines/writelines methods.
    """

    def __init__(self, file_like: BinaryIO) -> None:
        """Initialize codec with file object.

        Args:
            file_like: Binary file-like object
        """
        self.file_like = file_like

    def readlines(self):
        """Read all lines from file.

        Yields:
            Lines from the file
        """
        yield from self.file_like.readlines()

    def writelines(self, lines):
        """Write lines to file.

        Args:
            lines: Iterable of lines to write
        """
        for line in lines:
            self.file_like.write(line)


class Reader(hexfile.Reader):
    """EMON52 format reader.

    Reads EMON52 hex files with 16-bit checksums (sum of data bytes).
    """

    FORMAT_SPEC = ((hexfile.TYPE_FROM_RECORD, "LL AAAA:DD CCCC"),)
    DATA_SEPARATOR = " "

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate EMON52 record checksum.

        Args:
            line: Parsed line container with length, chunk, checksum
            format_type: Record type

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If checksum doesn't match
        """
        # Verify length matches actual data
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

        # Verify checksum (16-bit sum of data bytes)
        checksum = sum(line.chunk) & 0xFFFF
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError(f"Checksum mismatch: expected {checksum:04X}, " f"got {line.checksum:04X}")

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            Always True (all records contain data in EMON52 format)
        """
        return True


class Writer(hexfile.Writer):
    """EMON52 format writer.

    Writes EMON52 hex files with 16-bit addressing and 16-bit checksums.
    """

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (16-bit)
            length: Data length in bytes
            row: Data bytes to encode

        Returns:
            Formatted EMON52 record: LL AAAA:DD CCCC
        """
        # Calculate checksum (16-bit sum of data bytes)
        checksum = sum(row) % 65536

        return f"{length:02X} {address:04X}:{Writer.hex_bytes(row, spaced=True)} {checksum:04X}"
