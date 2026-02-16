#!/usr/bin/env python
"""MOS Technology hexadecimal object file format reader/writer.

This module handles the MOS Technology hex format, used with
6502-family microprocessors (6502, 6510, 65C02, etc.).

Format specification:
- Data records: ;LLAAAADDCCCC
  - LL: Length/byte count (hex)
  - AAAA: 16-bit address (hex)
  - DD: Data bytes (hex)
  - CCCC: 16-bit LRC checksum (no complement)
- EOF record: ;00
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

from collections.abc import Mapping, Sequence
from typing import Any, Optional

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils


# Record type identifiers
DATA = 1
EOF = 2


class Reader(hexfile.Reader):
    """MOS Technology format reader.

    Reads MOS Technology hex files with 16-bit LRC checksums.
    """

    FORMAT_SPEC = ((DATA, ";LLAAAADDCCCC"), (EOF, ";00"))

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate MOS Technology record checksum.

        Args:
            line: Parsed line container
            format_type: Record type (DATA or EOF)

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If checksum doesn't match
        """
        if format_type == DATA:
            # Verify length matches actual data
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

            # Verify checksum (16-bit LRC of address + length + data)
            checksum = checksums.lrc(
                utils.make_list(utils.int_to_array(line.address), line.length, line.chunk),
                16,
                checksums.COMPLEMENT_NONE,
            )
            if line.checksum != checksum:
                raise hexfile.InvalidRecordChecksumError(f"Checksum mismatch: expected {checksum:04X}, " f"got {line.checksum:04X}")

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            True for DATA records, False for EOF
        """
        return format_type == DATA


class Writer(hexfile.Writer):
    """MOS Technology format writer.

    Writes MOS Technology hex files with 16-bit addressing and LRC checksums.
    """

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (16-bit)
            length: Data length in bytes
            row: Data bytes to encode

        Returns:
            Formatted MOS Technology record: ;LLAAAADDCCCC
        """
        # Calculate checksum (16-bit LRC of address + length + data)
        checksum = checksums.lrc(
            utils.make_list(utils.int_to_array(address), length, row),
            16,
            checksums.COMPLEMENT_NONE,
        )

        line = f";{length:02X}{address:04X}{Writer.hex_bytes(row)}{checksum:04X}"
        return line

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose EOF record.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            EOF record string: ;00
        """
        return ";00"
