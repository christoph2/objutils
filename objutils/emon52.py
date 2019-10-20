#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import objutils.hexfile as hexfile

DATA                        = 0
EOF                         = 1
EXTENDED_SEGMENT_ADDRESS    = 2
START_SEGMENT_ADDRESS       = 3
EXTENDED_LINEAR_ADDRESS     = 4
START_LINEAR_ADDRESS        = 5


class Codec(object):
    """

    """

    def __init__(self, file_like):
        self.file_like = file_like

    def readlines(self):
        for line in self.file_like.readlines():
            yield line

    def writelines(self, lines):
        for line in lines:
            self.file_like.write(line)


class Reader(hexfile.Reader):
    """

    """

    FORMAT_SPEC = (
        (hexfile.TYPE_FROM_RECORD, "LL AAAA:DD CCCC"),
    )
    DATA_SEPARATOR =  " "

    def check_line(self, line, format_type):
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        # todo: factor out checksum calculation from line!!!
        checksum = (sum(line.chunk) & 0xffff)
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line, format_type):
        return True


class Writer(hexfile.Writer):
    """

    """

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address, length, row):
        checksum = sum(row) % 65536
        return "{0:02X} {1:04X}:{2!s} {3:04X}".format(length, address, Writer.hex_bytes(row, spaced = True), checksum)
