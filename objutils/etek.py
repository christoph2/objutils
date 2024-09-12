#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils


DATA = 1
SYMBOL = 2
EOF = 3


class Reader(hexfile.Reader):
    VALID_CHARS = re.compile(r"^[a-zA-Z0-9_ %\n\r]*$")  # We need to consider symbol information.

    FORMAT_SPEC = (
        (DATA, "%LL6CCAAAAADD"),
        (SYMBOL, "%LL3CCU"),
        (EOF, "%LL8CCAAAAADD"),
    )

    def check_line(self, line, format_type):
        if format_type == DATA:
            line.length = (line.length / 2) - 5
            checksum = checksums.nibble_sum(
                utils.make_list(
                    utils.int_to_array(line.address),
                    6,
                    ((line.length + 5) * 2),
                    line.chunk,
                )
            )
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            if line.checksum != checksum:
                raise hexfile.InvalidRecordChecksumError()
        elif format_type == SYMBOL:
            checksum = checksums.nibble_sum(utils.make_list(3, ((line.length + 5) * 2), [ord(b) for b in line.chunk]))
            chunk = line.chunk.strip()
            address = int(chunk[-4:], 16)
            line.address = address
            # if line.checksum!=checksum:
            #    raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line, format_type):
        return format_type == DATA

    def parseData(self, line, format_type):
        return format_type != SYMBOL


class Writer(hexfile.Writer):
    MAX_ADDRESS_BITS = 24

    def compose_row(self, address, length, row):
        checksum = checksums.nibble_sum(utils.make_list(utils.int_to_array(address), 6, ((length + 5) * 2), row))

        line = f"%{(length + 5) * 2:02X}6{checksum:02X}{address:04X}{Writer.hex_bytes(row)!s}"
        return line
