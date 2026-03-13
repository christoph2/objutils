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

import io
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

    def probe(self, fp: Any, **kws: Any) -> bool:
        """Check if file matches MOS Technology format.

        MOS Technology format uses ;LLAAAADDCCCC.
        """
        MAX_SAMPLE_LINES = 5

        # Save position
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, io.UnsupportedOperation):
            pass

        try:
            matched = 0
            for _ in range(MAX_SAMPLE_LINES):
                line = fp.readline()
                if not line:
                    break

                line_str = line.decode(errors="ignore") if isinstance(line, bytes) else line
                line_str = line_str.strip()
                if not line_str.startswith(";"):
                    continue

                # Check if it matches the general pattern
                for _, pattern in self.formats:
                    m = pattern.match(line_str)
                    if m:
                        # For Mostec, we check if the checksum matches (16-bit LRC)
                        # Format: ;LLAAAADDCCCC
                        # LL (2) AAAA (4) DD (var) CCCC (4)
                        if len(line_str) >= 11:
                            try:
                                length = int(line_str[1:3], 16)
                                addr = int(line_str[3:7], 16)
                                data_hex = line_str[7:-4]
                                checksum_given = int(line_str[-4:], 16)

                                if len(data_hex) == length * 2:
                                    data = bytearray.fromhex(data_hex)
                                    expected = checksums.lrc(
                                        utils.make_list(utils.int_to_array(addr), length, data),
                                        16,
                                        checksums.COMPLEMENT_NONE,
                                    )
                                    if checksum_given == expected:
                                        matched += 1
                                        break
                            except ValueError:
                                pass
                        elif line_str == ";00":
                            matched += 1
                            break
            return matched > 0
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, io.UnsupportedOperation):
                pass


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
