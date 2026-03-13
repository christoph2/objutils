#!/usr/bin/env python
"""Texas Instruments TI-TXT hexadecimal object file format reader/writer.

This module handles the TI-TXT format, a simple ASCII hex format used
by Texas Instruments development tools for MSP430 and other MCUs.

Format specification:
- Address lines: @XXXX where XXXX is hex address
- Data lines: Space-separated hex bytes (2-4 hex digits each)
- EOF marker: 'q'
- No checksums
- Clean, minimalist format

Example:
    @1000
    12 34 56 78
    @2000
    AA BB CC DD
    q
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

from typing import Any

import objutils.hexfile as hexfile


class Reader(hexfile.ASCIIHexReader):
    """TI-TXT format reader.

    Parses TI-TXT files with @ address markers and 'q' terminator.
    Supports space-separated hex data without checksums.
    """

    def __init__(
        self,
        address_pattern: str = r"^@(?P<address>[0-9a-zA-Z]{2,8})\s*$",
        data_pattern: str = r"^(?:[0-9a-zA-Z]{{2,4}}[{0}]?)*\s*$",
        etx_pattern: str = r"^q.*$",
    ) -> None:
        """Initialize TI-TXT reader.

        Args:
            address_pattern: Regex for address lines with @ prefix
            data_pattern: Regex for data lines (supports 2-4 hex digits)
            etx_pattern: Regex for 'q' terminator
        """
        super().__init__(address_pattern, data_pattern, etx_pattern)

    def probe(self, fp: Any, **kws: Any) -> bool:
        """Check if file matches TI-TXT format.

        TI-TXT uses @ address markers and 'q' terminator.
        """
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, Exception):
            pass

        try:
            matched_at = False
            matched_q = False
            lines_checked = 0
            while lines_checked < 50:
                line = fp.readline()
                if not line:
                    break
                line_str = line.decode(errors="ignore") if isinstance(line, bytes) else line
                line_str = line_str.strip()
                if not line_str:
                    continue
                lines_checked += 1
                if line_str.startswith("@"):
                    matched_at = True
                if line_str == "q":
                    matched_q = True
                if matched_at and matched_q:
                    return True
            # For TI-TXT, @ marker is quite characteristic if it's near the start
            return matched_at and lines_checked < 10
        except Exception:
            return False
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, Exception):
                pass


class Writer(hexfile.ASCIIHexWriter):
    """TI-TXT format writer.

    Generates TI-TXT files with @ address markers and 'q' terminator.
    """

    def __init__(self, address_designator: str = "@") -> None:
        """Initialize TI-TXT writer.

        Args:
            address_designator: Prefix for address lines (default: "@")
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
                f"{self.address_designator}{address:04X}",
                f"{self.separator}".join([f"{x:02X}" for x in row]),
            )
        else:
            line = " ".join([f"{x:02X}" for x in row])
        return line

    def compose_footer(self, meta: dict[str, Any]) -> str:
        """Compose file footer with 'q' terminator.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            Footer string "q"
        """
        return "q"
