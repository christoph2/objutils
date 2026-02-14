#!/usr/bin/env python
"""Extended Tektronix hexadecimal object file format reader/writer.

This module handles the Extended Tektronix hex format, an extension
of the standard Tektronix format with 24-bit addressing and symbol support.

Format specification:
- Data records: %LL6CCAAAAADD
  - LL: Length field (2 * (data_length + 5) in hex)
  - 6: Record type identifier  
  - CC: Checksum (nibble sum)
  - AAAAAA: 24-bit address (hex)
  - DD: Data bytes (hex)
- Symbol records: %LL3CCU
  - LL: Length field
  - 3: Symbol type identifier
  - CC: Checksum
  - U: Symbol string (name + address)
- EOF records: %LL8CCAAAAADD
  - 8: EOF type identifier
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

import re
from collections.abc import Sequence
from typing import Any

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils

# Record type identifiers
DATA = 1
SYMBOL = 2
EOF = 3


class Reader(hexfile.Reader):
    """Extended Tektronix format reader.

    Reads Extended Tektronix hex files with 24-bit addressing,
    symbol records, and nibble sum checksums.
    """

    # Allow alphanumeric chars, space, percent, and whitespace (for symbols)
    VALID_CHARS = re.compile(r"^[a-zA-Z0-9_ %\n\r]*$")

    FORMAT_SPEC = (
        (DATA, "%LL6CCAAAAADD"),
        (SYMBOL, "%LL3CCU"),
        (EOF, "%LL8CCAAAAADD"),
    )

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate Extended Tektronix record checksums.

        Args:
            line: Parsed line container
            format_type: Record type (DATA, SYMBOL, or EOF)

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If checksum doesn't match
        """
        if format_type == DATA:
            # Decode length: LL = 2 * (data_length + 5)
            line.length = (line.length // 2) - 5

            # Verify length matches actual data
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError(
                    "Byte count doesn't match length of actual data."
                )

            # Verify checksum (nibble sum of address + length + data)
            checksum = checksums.nibble_sum(
                utils.make_list(
                    utils.int_to_array(line.address),
                    6,
                    ((line.length + 5) * 2),
                    line.chunk,
                )
            )
            if line.checksum != checksum:
                raise hexfile.InvalidRecordChecksumError(
                    f"Checksum mismatch: expected {checksum:02X}, "
                    f"got {line.checksum:02X}"
                )

        elif format_type == SYMBOL:
            # Symbol record: extract address from end of symbol string
            checksum = checksums.nibble_sum(
                utils.make_list(3, ((line.length + 5) * 2), [ord(b) for b in line.chunk])
            )

            # Symbol format: "NAME1234" where 1234 is hex address
            chunk = line.chunk.strip()
            address = int(chunk[-4:], 16)
            line.address = address

            # Note: Checksum validation disabled for symbols (often wrong in files)
            # if line.checksum != checksum:
            #     raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            True for DATA records, False for SYMBOL/EOF
        """
        return format_type == DATA

    def parseData(self, line: Any, format_type: int) -> bool:
        """Determine if line should be parsed as data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            False for SYMBOL records, True otherwise
        """
        return format_type != SYMBOL


class Writer(hexfile.Writer):
    """Extended Tektronix format writer.

    Writes Extended Tektronix hex files with 24-bit addressing
    and nibble sum checksums.
    """

    MAX_ADDRESS_BITS = 24

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (24-bit)
            length: Data length in bytes
            row: Data bytes to encode

        Returns:
            Formatted Extended Tektronix record: %LL6CCAAAAADD
        """
        # Calculate checksum (nibble sum of address + length + data)
        checksum = checksums.nibble_sum(
            utils.make_list(utils.int_to_array(address), 6, ((length + 5) * 2), row)
        )

        # Length field: 2 * (data_length + 5)
        line = f"%{(length + 5) * 2:02X}6{checksum:02X}{address:06X}{Writer.hex_bytes(row)}"
        return line
