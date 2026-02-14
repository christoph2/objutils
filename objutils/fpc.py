#!/usr/bin/env python
"""Four Packed Code (FPC) object file format reader/writer.

This module handles the FPC format, a compact binary-to-ASCII encoding
that uses base-85 encoding (similar to ASCII85) to represent 32-bit values
as 5-character sequences.

Format specification:
- Each line starts with '$' prefix
- Data encoded as quintuples (5 chars each) using base-85
- Character set: ASCII 37-122 (excluding 42/'*')
- Each quintuple encodes a 32-bit value
- Records can be absolute (type 0), incremental (type 1), or relative (type 2)
- EOF record: 00000000 (decoded form)
- Uses LRC checksum with two's complement
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
import os
import re
from functools import partial
from typing import Any, BinaryIO

import objutils.hexfile as hexfile
import objutils.utils as utils
from objutils import checksums
from objutils.image import Image
from objutils.utils import create_string_buffer, slicer


DATA_ABS = 1
DATA_INC = 2
DATA_REL = 3
EOF = 4

PREFIX = "$"

MAPPING = dict(enumerate(chr(n) for n in range(37, 123) if n not in (42,)))
REV_MAPPING = {ord(value): key for key, value in MAPPING.items()}
NULLS = re.compile(r"\0*\s*!M\s*(.*)", re.DOTALL | re.M)
VALID_CHARS = re.compile(r"^\{}[{}]+$".format(PREFIX, re.escape("".join(MAPPING.values()))))

atoi16 = partial(int, base=16)


class Reader(hexfile.Reader):
    """FPC format reader.

    Decodes base-85 encoded FPC files to standard hex format,
    then uses the parent Reader to process the decoded data.
    """

    FORMAT_SPEC = (
        (DATA_ABS, "CCLL0000AAAAAAAADD"),
        (DATA_INC, "CCLL0001DD"),
        (DATA_REL, "CCLL0002AAAAAAAADD"),
        (EOF, "00000000"),
    )

    def decode(self, fp: BinaryIO) -> str:
        """Decode FPC base-85 encoding to hex format.

        Converts each quintuple (5 ASCII chars) to an 8-digit hex value.

        Args:
            fp: File pointer to read FPC data from

        Returns:
            Decoded hex string with newline-separated records

        Raises:
            FormatError: If line doesn't start with PREFIX or has invalid length
        """
        self.last_address = 0
        out_lines = []
        for line in fp.readlines():
            line = line.strip()
            startSym, line = line[0], line[1:]

            if startSym != PREFIX:
                self.error(f"Line must start with '{PREFIX}' prefix")

            if (len(line) % 5) != 0:
                self.error(f"Line length must be multiple of 5, got {len(line)}")

            values = []
            for quintuple in self.split_quintuples(line):
                value = self.convert_quintuple(quintuple)
                values.append(f"{value:08X}")
            out_lines.append("".join(values))
        return "\n".join(out_lines)

    def read(self, fp: BinaryIO) -> Image:
        """Read FPC file and convert to Image.

        Args:
            fp: File pointer to read from

        Returns:
            Image object containing decoded sections
        """
        return super().read(create_string_buffer(bytearray(self.decode(fp), "ascii")))

    def convert_quintuple(self, quintuple: str) -> int:
        """Convert 5-character base-85 quintuple to 32-bit integer.

        Args:
            quintuple: 5-character string from FPC character set

        Returns:
            32-bit integer value
        """
        res = 0
        for ch in quintuple:
            v = REV_MAPPING[bytearray((ch,))[0]]
            res = v + (res * 85)
        return res

    def split_quintuples(self, line: str) -> list[str]:
        """Split line into 5-character quintuples.

        Args:
            line: Input line (without prefix)

        Returns:
            List of 5-character strings
        """
        res = []
        for i in range(0, len(line), 5):
            res.append(line[i : i + 5])
        return res

    def check_line(self, line: Any, format_type: int) -> bool:
        """Validate line checksum and handle different record types.

        Args:
            line: Parsed line object with address, length, chunk, checksum
            format_type: Record type (DATA_ABS, DATA_INC, DATA_REL, or EOF)

        Returns:
            True if line is valid

        Raises:
            InvalidRecordChecksumError: If checksum validation fails
            FormatError: If format type is invalid or relative addressing used
        """
        if format_type == EOF:
            return True
        line.length -= 4
        if line.length != len(line.chunk):
            line.chunk = line.chunk[: line.length]
        if format_type == DATA_ABS:
            tmp = 0
            self.last_address = line.address + line.length
        elif format_type == DATA_INC:
            tmp = 1
            line.address = self.last_address
        elif format_type == DATA_REL:
            self.error("Relative addressing not supported")
            tmp = 2
        else:
            self.error(f"Invalid format type: {format_type}")
            tmp = 0
        checksum = checksums.lrc(
            utils.make_list(tmp, line.length + 4, utils.int_to_array(line.address), line.chunk),
            8,
            checksums.COMPLEMENT_TWOS,
        )
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()
        return True

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Check if line contains data.

        Args:
            line: Parsed line object
            format_type: Record type identifier

        Returns:
            True if line is a data record
        """
        return format_type in (DATA_ABS, DATA_INC, DATA_REL)

    def probe(self, fp: BinaryIO) -> bool:
        """Check if file is in FPC format.

        Args:
            fp: File pointer to probe

        Returns:
            True if file appears to be FPC format
        """
        for idx, line in enumerate(fp, 1):
            if not VALID_CHARS.match(line.decode()):
                fp.seek(0, os.SEEK_SET)
                return False
            if idx > 3:
                break
        fp.seek(0, os.SEEK_SET)
        return super().probe(create_string_buffer(bytearray(self.decode(fp), "ascii")))


class Writer(hexfile.Writer):
    """FPC format writer.

    Encodes hex data to FPC base-85 format with '$' prefix.
    """

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address: int, length: int, row: list[int]) -> str:
        """Compose a data row in internal hex format.

        Args:
            address: Start address for this row
            length: Number of data bytes
            row: List of data bytes

        Returns:
            Hex-encoded row string (before base-85 encoding)
        """
        tmp = 0
        checksum = checksums.lrc(
            utils.make_list(tmp, length + 4, utils.int_to_array(address), row),
            8,
            checksums.COMPLEMENT_TWOS,
        )
        if length < self.row_length:
            lengthToPad = self.row_length - length
            padding = [0] * lengthToPad
            row.extend(padding)
        line = f"{checksum:02X}{length - 2}0000{address:08X}{Writer.hex_bytes(row)}"
        return line

    def compose_footer(self, meta: dict[str, Any]) -> str:
        """Compose EOF record.

        Args:
            meta: Metadata dictionary (unused)

        Returns:
            EOF marker in hex format
        """
        return "00000000"

    def post_processing(self, data: bytes) -> bytes:
        """Convert hex format to FPC base-85 encoding.

        Args:
            data: Hex-encoded data bytes

        Returns:
            FPC-encoded data with '$' prefixes

        Raises:
            FormatError: If line length is not a multiple of 4
        """
        result = []
        for line in data.splitlines():
            if len(line) % 4:
                self.error("Size of line must be a multiple of 4")
                continue
            res = []
            for item in slicer(line, 8, atoi16):
                item = self.convert_quintuple(item)
                res.append(item)
            result.append(f"{PREFIX}{''.join(res)}")
        return bytes("\n".join(result), "ascii")

    def convert_quintuple(self, value: int) -> str:
        """Convert 32-bit integer to 5-character base-85 quintuple.

        Args:
            value: Integer value to encode (0-2^32)

        Returns:
            5-character string from FPC character set
        """
        result = []
        while value:
            result.append(MAPPING[value % 85])
            value //= 85
        if len(result) < 5:
            result.extend([MAPPING[0]] * (5 - len(result)))
        return "".join(reversed(result))
