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

DATA0    = 1
DATA1    = 2
DATA2    = 3
DATA3    = 4


class Reader(hexfile.Reader):

    FORMAT_SPEC = (
        (DATA0,  "!MAAAA DD"),
        (DATA1,  "\?MAAAA DD"),
        (DATA2,  "AAAA DD"),
        (DATA3,  "DD"),
    )
    previous_address = 0
    previous_length = 0

    def check_line(self, line, format_type):
        return True

    def is_data_line(self, line, format_type):
        if format_type == DATA3:
            if line.junk in ("!M", "?M"):   # Startsymbol, address ommited.
                return False
            line.address = self.previous_address + self.previous_length
            self.previous_address = line.address
            self.previous_length = len(line.chunk)
        else:
            if hasattr(line, 'chunk'):
                length = len(line.chunk)
            else:
                length = 0
            self.previous_address = line.address
            self.previous_length = length
        return format_type in (DATA0, DATA1, DATA2, DATA3)


class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address, length, row):
        line = "!M{0:04X} {1}".format(address, Writer.hex_bytes(row))
        return line
