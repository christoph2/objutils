#!/usr/bin/env python

__all__ = ["Reader", "Writer"]

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <github.com/Christoph2,
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

import operator
from collections.abc import Mapping, Sequence
from functools import partial
from typing import Any, Callable, Optional

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils
from objutils.checksums import COMPLEMENT_TWOS, lrc


# Record type identifiers
DATA = 0
EOF = 1
EXTENDED_SEGMENT_ADDRESS = 2
START_SEGMENT_ADDRESS = 3
EXTENDED_LINEAR_ADDRESS = 4
START_LINEAR_ADDRESS = 5


class Reader(hexfile.Reader):
    """Intel HEX format reader.

    Reads Intel HEX files with support for all record types including
    extended addressing modes for 20-bit and 32-bit address spaces.
    """

    FORMAT_SPEC = ((hexfile.TYPE_FROM_RECORD, ":LLAAAATTDDCC"),)

    def __init__(self) -> None:
        """Initialize reader with address calculation state."""
        super().__init__()
        self.segmentAddress: int = 0
        self._address_calculator: Callable[[int], int] = self._default_address_calculator

    def _default_address_calculator(self, x: int) -> int:
        """Default address calculator (identity function).

        Args:
            x: Input address

        Returns:
            Same address unchanged
        """
        return x

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate Intel HEX record checksum.

        Args:
            line: Parsed line container
            format_type: Record type

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If checksum doesn't match
        """
        # Verify length matches actual data
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

        # Verify checksum (two's complement LRC)
        checksum = checksums.lrc(
            utils.make_list(line.type, line.length, utils.int_to_array(line.address), line.chunk),
            8,
            checksums.COMPLEMENT_TWOS,
        )
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError(f"Checksum mismatch: expected {checksum:02X}, " f"got {line.checksum:02X}")

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if record contains data.

        Args:
            line: Parsed line container
            format_type: Record type

        Returns:
            True for DATA records, False otherwise
        """
        return line.type == DATA

    def calculate_extended_address(self, line: Any, shift_by: int, name: str) -> None:
        """Calculate extended address from segment/linear address record.

        Args:
            line: Parsed line container
            shift_by: Bit shift amount (4 for segment, 16 for linear)
            name: Address type name for logging ("Segment" or "Linear")
        """
        if len(line.chunk) == 2:
            # Extract 16-bit segment value
            segment = (line.chunk[0] << 8) | line.chunk[1]
            line.add_processing_instruction(("segment", segment))

            # Update address calculator to add segment base
            self._address_calculator = partial(operator.add, segment << shift_by)
            self.debug(f"EXTENDED_{name.upper()}_ADDRESS: {segment:#X}")
        else:
            self.error(f"Bad Extended {name} Address at line #{line.line_number}.")

    def special_processing(self, line: Any, format_type: int) -> None:
        """Process special Intel HEX record types.

        Args:
            line: Parsed line container
            format_type: Record type

        Note:
            Handles extended addressing, start addresses, and EOF records.
        """
        if line.type == DATA:
            # Apply extended address calculation
            line.address = self._address_calculator(line.address)

        elif line.type == EXTENDED_SEGMENT_ADDRESS:
            # Extended segment address (20-bit: segment << 4)
            self.calculate_extended_address(line, 4, "Segment")

        elif line.type == START_SEGMENT_ADDRESS:
            # Start segment address (CS:IP for x86)
            if len(line.chunk) == 4:
                cs = (line.chunk[0] << 8) | line.chunk[1]
                ip = (line.chunk[2] << 8) | line.chunk[3]
                line.add_processing_instruction(("cs", cs))
                line.add_processing_instruction(("ip", ip))
                self.debug(f"START_SEGMENT_ADDRESS: {hex(cs)}:{hex(ip)}")
            else:
                self.error(f"Bad Segment Address at line #{line.line_number}.")

        elif line.type == EXTENDED_LINEAR_ADDRESS:
            # Extended linear address (32-bit: segment << 16)
            self.calculate_extended_address(line, 16, "Linear")

        elif line.type == START_LINEAR_ADDRESS:
            # Start linear address (EIP for x86)
            if len(line.chunk) == 4:
                eip = (line.chunk[0] << 24) | (line.chunk[1] << 16) | (line.chunk[2] << 8) | line.chunk[3]
                line.add_processing_instruction(("eip", eip))
                self.debug(f"START_LINEAR_ADDRESS: {hex(eip)}")
            else:
                self.error(f"Bad Linear Address at line #{line.line_number}.")

        elif line.type == EOF:
            # End of file - nothing to process
            pass

        else:
            self.warn(f"Invalid record type [{line.type}] at line {line.line_number}")


class Writer(hexfile.Writer):
    """Intel HEX format writer.

    Writes Intel HEX files with automatic extended address record insertion
    for 32-bit address spaces.
    """

    MAX_ADDRESS_BITS = 32
    checksum = staticmethod(partial(lrc, width=8, comp=COMPLEMENT_TWOS))

    def pre_processing(self, image: hexfile.Image) -> None:
        """Initialize writer state before processing image.

        Args:
            image: Image object to write
        """
        self.previosAddress: Optional[int] = None  # Note: typo kept for compatibility
        self.start_address: int = 0

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose data record with automatic extended address handling.

        Args:
            address: Start address (32-bit)
            length: Data length in bytes
            row: Data bytes to encode

        Returns:
            Formatted Intel HEX record(s), possibly with extended address record
        """
        result = ""

        # Split address into segment and offset
        seg, offs = divmod(address, 0x10000)
        hi, lo = self.word_to_bytes(address)

        # Insert extended address record if segment changed
        if offs != self.previosAddress:
            if address > 0xFFFF:
                if address > 0xFFFFF:
                    # Extended linear address (32-bit mode)
                    segHi, segLo = self.word_to_bytes(seg)
                    result = f":02000004{seg:04X}{self.checksum([2, 4, segHi, segLo]):02X}\n"
                else:
                    # Extended segment address (20-bit mode)
                    seg = seg << 12
                    segHi, segLo = self.word_to_bytes(seg)
                    result = f":02000002{seg:04X}{self.checksum([2, 2, segHi, segLo]):02X}\n"

        # Use offset within segment
        address = offs

        # Calculate checksum for data record
        checksum = self.checksum([length, hi, lo] + list(row))

        # Track address for next call
        self.previosAddress = offs + length

        # Compose data record
        result += f":{length:02X}{address:04X}{DATA:02X}{Writer.hex_bytes(row)}{checksum:02X}"
        return result

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose EOF record.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            EOF record string
        """
        hi, lo = self.word_to_bytes(self.start_address)
        return f":00{self.start_address:04X}{EOF:02X}{self.checksum([hi, lo, EOF]):02X}\n"
