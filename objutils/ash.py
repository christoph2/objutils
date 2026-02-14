#!/usr/bin/env python
"""ASCII Space Hex (ASH) format reader/writer.

This module handles the ASH format, a simple ASCII hex format with
STX/ETX framing and flexible separators.

Format specification:
- STX (0x02) marks start of data
- ETX (0x03) marks end of data
- Address lines: $A followed by hex address and separator (comma or period)
- Data: Hex bytes separated by space, %, comma, or apostrophe
- Optional checksum: $$XXXX after ETX (16-bit LRC)
- Flexible word sizes (2-4 hex digits per value)

Example:
    <STX> $A1000.
    12 34 56 78
    <ETX>$$ABCD,
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
from functools import partial
from typing import Any

import objutils.hexfile as hexfile
from objutils.checksums import lrc


STX = "\x02"
ETX = "\x03"

DATA = re.compile(
    r"(?:.*?\02)(?P<chunks>.*)(?:\03)\s*(?:\$\$(?P<checksum>[0-9a-zA-Z]{2,4})[,.])?",
    re.DOTALL | re.MULTILINE,
)
ADDRESS = re.compile(r"\$A(?P<value>[0-9a-zA-Z]{2,8})[,.]\s*")
LINE_SPLIITER = re.compile(r"[ %,']")

checksum = partial(lrc, width=16)


class Reader(hexfile.ASCIIHexReader):
    """ASCII Space Hex format reader.

    Parses ASH files with STX/ETX framing and $A address markers.
    Supports multiple separator characters and optional checksums.
    """

    VALID_CHARS = re.compile(r"^[a-fA-F0-9 %,\'\$\x02\x03\n\r]*$")

    def __init__(
        self,
        address_pattern: str = r"^(?:(?P<stx>[\x02])\s+)?\$A(?P<address>[0-9a-zA-Z]{2,8})[,.]\s*$",
        data_pattern: str = r"^(?:[0-9a-zA-Z]{{2,4}}[{0}]?)*\s*$",
        etx_pattern: str = r"^q.*$",
    ) -> None:
        """Initialize ASH reader.

        Args:
            address_pattern: Regex for address lines with $A prefix
            data_pattern: Regex for data lines (supports 2-4 hex digits)
            etx_pattern: Regex for end-of-transmission marker
        """
        super().__init__(address_pattern, data_pattern, etx_pattern, separators=", %'")


class Writer(hexfile.ASCIIHexWriter):
    """ASCII Space Hex format writer.

    Generates ASH files with STX/ETX framing and optional checksums.
    """

    MAX_ADDRESS_BITS = 16
    ADDRESS_DESIGNATOR = "$A"

    def __init__(self, address_designator: str = "$A") -> None:
        """Initialize ASH writer.

        Args:
            address_designator: Prefix for address lines (default: "$A")
        """
        super().__init__()
        self.address_designator = address_designator
        self.separator = " "
        self.previous_address: int | None = None

    def compose_row(self, address: int, length: int, row: list[int]) -> str:
        """Compose data row with optional address line.

        Args:
            address: Start address for this row
            length: Number of data bytes
            row: List of data bytes

        Returns:
            Formatted row string, potentially with address line prefix
        """
        prepend_address = True if address != self.previous_address else False
        self.previous_address = address + length
        if prepend_address:
            line = "{}\n{}".format(
                f"{self.address_designator}{address:04X},",
                f"{self.separator}".join([f"{x:02X}" for x in row]),
            )
        else:
            line = " ".join([f"{x:02X}" for x in row])
        self.row_callout(address, length, row)
        return line

    def compose_header(self, meta: dict[str, Any]) -> str:
        """Compose file header with STX.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            Header string with STX marker
        """
        self.checksum = 0
        self.previous_address = None
        line = f"{STX} "
        return line

    def compose_footer(self, meta: dict[str, Any]) -> str:
        """Compose file footer with ETX and checksum.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            Footer string with ETX and 16-bit checksum
        """
        line = f"{ETX}$${self.checksum % 65536:04X},"
        return line

    def row_callout(self, address: int, length: int, row: list[int]) -> None:
        """Update running checksum with row data.

        Args:
            address: Row start address
            length: Number of bytes in row
            row: Data bytes
        """
        self.checksum += checksum(row)
