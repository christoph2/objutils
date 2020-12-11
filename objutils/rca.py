#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <github.com/Christoph2,
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

import re
import objutils.hexfile as hexfile

DATA    = 1
EOF     = 2

NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)


class Reader(hexfile.Reader):

    #data = re.sub('\0*$', ';\n:0000', NULLS.match(inFile.read()).group(1), 1)  # FIXME!!!
    FORMAT_SPEC = (
        (DATA, "AAAA DD;"),
        (EOF, ":0000")
    )

    def check_line(self, line, format_type):
        if format_type == DATA:
            line.length = len(line.chunk)

    def is_data_line(self, line, format_type):
        return format_type == DATA


class Writer(hexfile.Writer):
    SEPARATOR = "{0!s}\x0d\x0a".format(('\x00' * 48))
    MAX_ADDRESS_BITS = 16

    def compose_row(self, address, length, row):
        return "{0:04X} {1!s};".format(address, Writer.hex_bytes(row))

    def compose_header(self, meta):
        return "{0!s}!M".format(Writer.SEPARATOR)

    def compose_footer(self, meta):
        return "{0!s}".format(Writer.SEPARATOR)
