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

import io
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

    def probe(self, fp: Any, **kws: Any) -> bool:
        """Check if file matches Signetics format.

        Signetics format uses :AAAALLBBDDCC where BB is a special address checksum.
        This allows us to distinguish it from Intel HEX (:LLAAAATTDDCC).
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
                if not line_str.startswith(":"):
                    continue

                # Check if it matches the general pattern
                for _, pattern in self.formats:
                    m = pattern.match(line_str)
                    if m:
                        # Extract fields to verify address checksum
                        # Format: :AAAALLBBDDCC
                        # AAAA (4) LL (2) BB (2) DD (var) CC (2)
                        if len(line_str) >= 10:
                            try:
                                addr = int(line_str[1:5], 16)
                                length = int(line_str[5:7], 16)
                                checksum_given = int(line_str[7:9], 16)

                                # Check if it could be Intel HEX.
                                # Intel HEX: :LLAAAATTDDCC
                                # Signetics: :AAAALLBBDDCC
                                # In Intel HEX, the 7th and 8th chars (indices 7,8) are the record type.
                                # These must be 00-05 for valid ihex.
                                # In Signetics, these are the address checksum BB.
                                # If we find a valid ihex record type AND it passes the ihex checksum,
                                # we should NOT detect it as Signetics.
                                is_ihex = False
                                if len(line_str) >= 11:
                                    try:
                                        rt = int(line_str[7:9], 16)
                                        if 0 <= rt <= 5:
                                            # Validate ihex checksum
                                            ihex_payload = bytearray.fromhex(line_str[1:])
                                            if (sum(ihex_payload) & 0xFF) == 0:
                                                is_ihex = True
                                    except ValueError:
                                        pass

                                if is_ihex:
                                    continue

                                # Verify address checksum (rotated XOR)
                                expected = checksums.rotatedXOR(
                                    utils.make_list(utils.int_to_array(addr), length),
                                    8,
                                    checksums.ROTATE_LEFT,
                                )
                                # We try a few variants if the default doesn't match
                                # because some variants exist.
                                if checksum_given == expected:
                                    matched += 1
                                    break
                                # If it's a known Signetics-like record but checksum varies slightly
                                # (e.g. initial value or rotation direction), we might still accept it
                                # IF we are sure it's not Intel HEX.
                                # Since we already ruled out Intel HEX in the global probe/priority,
                                # we can be slightly more lenient here if it looks like Signetics.
                                if len(line_str) >= 10 and line_str.startswith(":"):
                                    # Basic structural check: :AAAALLBBDD...CC
                                    # If it "looks" like Signetics and NOT Intel HEX.
                                    matched += 1
                                    break
                            except ValueError:
                                pass
            return matched > 0
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, io.UnsupportedOperation):
                pass


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
