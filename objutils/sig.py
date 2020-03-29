#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from objutils import hexfile
from objutils import utils
import objutils.checksums as checksums

DATA = 1
EOF = 2


class Reader(hexfile.Reader):

    FORMAT_SPEC = (
        (DATA, ":AAAALLBBDDCC"),
        (EOF, ":00")
    )

    def check_line(self, line, format_type):
        if format_type == DATA:
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            address_checksum = checksums.rotatedXOR(utils.make_list(utils.int_to_array(line.address), line.length), 8, checksums.ROTATE_LEFT)
            if line.addrChecksum != address_checksum:
                raise hexfile.InvalidRecordChecksumError()
            data_checksum = checksums.rotatedXOR(line.chunk, 8, checksums.ROTATE_LEFT)
            if line.checksum != data_checksum:
                raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self,line,format_type):
        return format_type == DATA

class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address, length, row):
        address_checksum = checksums.rotatedXOR(utils.make_list(utils.int_to_array(address), length), 8, checksums.ROTATE_LEFT)
        data_checksum = checksums.rotatedXOR(row, 8, checksums.ROTATE_LEFT)
        line = ":{0:04X}{1:02X}{2:02X}{3}{4:02X}".format(address, length, address_checksum, Writer.hex_bytes(row), data_checksum)
        self.last_address = address + length
        return line

    def compose_footer(self, meta):
      return ":{0:04X}00".format(self.last_address)
