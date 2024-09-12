#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils


DATA = 1
EOF = 2


class Reader(hexfile.Reader):
    FORMAT_SPEC = (
        (DATA, "/AAAALLBBDDCC"),
        (EOF, "/AAAA00BB"),
    )

    def check_line(self, line, format_type):
        if format_type == DATA:
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            address_checksum = checksums.nibble_sum(utils.make_list(utils.int_to_array(line.address), line.length))
            if line.addrChecksum != address_checksum:
                raise hexfile.InvalidRecordChecksumError()
            checksum = checksums.nibble_sum(line.chunk)
            if line.checksum != checksum:
                raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line, format_type):
        return format_type == DATA


class Writer(hexfile.Writer):
    MAX_ADDRESS_BITS = 16

    def compose_footer(self, meta):
        return "/{:04X}00{:02X}".format(
            self.last_address,
            checksums.nibble_sum(utils.int_to_array(self.last_address)),
        )

    def compose_row(self, address, length, row):
        address_checksum = checksums.nibble_sum(utils.make_list(utils.int_to_array(address), length))

        data_checksum = checksums.nibble_sum(row)
        line = f"/{address:04X}{length:02X}{address_checksum:02X}{Writer.hex_bytes(row)!s}{data_checksum:02X}"
        self.last_address = address + length
        return line
