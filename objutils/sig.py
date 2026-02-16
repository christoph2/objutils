#!/usr/bin/env python
"""Signetics hexadecimal object file format reader/writer.

This module handles the Signetics hex format, used by Signetics
microcontrollers and development systems.

Format specification:
- Data records: :AAAALLBBDDCC
  - AAAA: 16-bit address (hex)
  - LL: Length/byte count (hex)
  - BB: Address checksum (rotated XOR)
  - DD: Data bytes (hex)
  - CC: Data checksum (rotated XOR)
- EOF record: :AAAA00
  - AAAA: Last address
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

from collections.abc import Mapping, Sequence
from typing import Any, Optional

import objutils.checksums as checksums
from objutils import hexfile, utils


# Record type identifiers
DATA = 1
EOF = 2


class Reader(hexfile.Reader):
    """Signetics format reader.

    Reads Signetics hex files with address and data checksums based on
    rotated XOR algorithm.
    """

    FORMAT_SPEC = ((DATA, ":AAAALLBBDDCC"), (EOF, ":00"))

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate Signetics record checksums.

        Args:
            line: Parsed line container with attributes: address, length,
                addrChecksum, chunk (data), checksum
            format_type: Record type (DATA or EOF)

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If address or data checksum invalid
        """
        if format_type == DATA:
            # Verify length matches actual data
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

            # Verify address checksum (rotated XOR of address + length)
            address_checksum = checksums.rotatedXOR(
                utils.make_list(utils.int_to_array(line.address), line.length),
                8,
                checksums.ROTATE_LEFT,
            )
            if line.addrChecksum != address_checksum:
                raise hexfile.InvalidRecordChecksumError(
                    f"Address checksum mismatch: expected {address_checksum:02X}, " f"got {line.addrChecksum:02X}"
                )

            # Verify data checksum (rotated XOR of data bytes)
            data_checksum = checksums.rotatedXOR(line.chunk, 8, checksums.ROTATE_LEFT)
            if line.checksum != data_checksum:
                raise hexfile.InvalidRecordChecksumError(
                    f"Data checksum mismatch: expected {data_checksum:02X}, " f"got {line.checksum:02X}"
                )

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
    """Signetics format writer.

    Writes Signetics hex files with 16-bit addressing and rotated XOR checksums.
    """

    MAX_ADDRESS_BITS = 16

    def __init__(self) -> None:
        """Initialize writer with state tracking."""
        super().__init__()
        self.last_address: int = 0

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record.

        Args:
            address: Start address (16-bit)
            length: Data length in bytes
            row: Data bytes to encode

        Returns:
            Formatted Signetics record: :AAAALLBBDDCC
        """
        # Address checksum: rotated XOR of address + length
        address_checksum = checksums.rotatedXOR(
            utils.make_list(utils.int_to_array(address), length),
            8,
            checksums.ROTATE_LEFT,
        )

        # Data checksum: rotated XOR of all data bytes
        data_checksum = checksums.rotatedXOR(row, 8, checksums.ROTATE_LEFT)

        line = f":{address:04X}{length:02X}{address_checksum:02X}{Writer.hex_bytes(row)}{data_checksum:02X}"

        # Track last address for footer generation
        self.last_address = address + length

        return line

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose EOF record with last address.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            EOF record string in format :AAAA00
        """
        return f":{self.last_address:04X}00"
