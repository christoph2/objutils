#!/usr/bin/env python
"""RCA hexadecimal object file format reader/writer.

This module handles the RCA hex format, used with RCA
microprocessors and development systems.

Format specification:
- Data records: AAAA DD;
  - AAAA: 16-bit address (hex)
  - DD: Data bytes (hex, space-separated)
  - Ends with semicolon
- EOF record: :0000
- Header: 48 null bytes + CRLF + !M
- Footer: 48 null bytes + CRLF
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

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

import io
import re
from collections.abc import Mapping, Sequence
from typing import Any, Optional

import objutils.hexfile as hexfile

# Record type identifiers
DATA = 1
EOF = 2

# Regex to match header (null bytes + !M marker)
NULLS = re.compile(r"\0*\s*!M\s*(.*)", re.DOTALL | re.M)


class Reader(hexfile.Reader):
    """RCA format reader.

    Reads RCA hex files with special header/footer formatting.
    """

    FORMAT_SPEC = ((DATA, "AAAA DD;"), (EOF, ":0000"))

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate RCA record.

        Args:
            line: Parsed line container
            format_type: Record type (DATA or EOF)

        Note:
            For DATA records, sets line.length from actual data length.
        """
        if format_type == DATA:
            # RCA format doesn't have explicit length field
            line.length = len(line.chunk)

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            True for DATA records, False for EOF
        """
        return format_type == DATA

    def probe(self, fp: Any, **kws: Any) -> bool:
        """Check if file matches RCA format.

        RCA format uses !M marker in header and AAAA DD; records.
        """
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, io.UnsupportedOperation):
            pass

        try:
            # Peek first 100 bytes for !M marker
            data = fp.read(100)
            if b"!M" in data:
                return True

            # If no header, check for AAAA DD; records
            if not data:
                return False

            data_str = data.decode(errors="ignore")
            # Pattern: 4 hex digits, space, at least one hex byte, semicolon
            if re.search(r"[0-9A-F]{4}\s+[0-9A-F]{2}\s*;", data_str):
                return True
            return False
        except Exception:
            return False
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, io.UnsupportedOperation):
                pass


class Writer(hexfile.Writer):
    """RCA format writer.

    Writes RCA hex files with special header/footer formatting
    (48 null bytes + CRLF).
    """

    SEPARATOR = "\x00" * 48 + "\x0d\x0a"
    MAX_ADDRESS_BITS = 16

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (16-bit)
            length: Data length in bytes (unused)
            row: Data bytes to encode

        Returns:
            Formatted RCA record: AAAA DD;
        """
        return f"{address:04X} {Writer.hex_bytes(row)};"

    def compose_header(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose header with separator and marker.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            Header string with null bytes + !M marker
        """
        return f"{Writer.SEPARATOR}!M"

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose footer with separator.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            Footer string with null bytes
        """
        return Writer.SEPARATOR
