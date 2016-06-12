#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import objutils.checksums as checksums
import objutils.utils as utils


DATA    = 1
SYMBOL  = 2
EOF     = 3


class Reader(hexfile.Reader):

    VALID_CHARS = re.compile(r"^[a-zA-Z0-9_ %\n\r]*$")    # We need to consider symbol information.

    FORMAT_SPEC = (
        (DATA,      "%LL6CCAAAAADD"),
        (SYMBOL,    "%LL3CCU"),
        (EOF,      "%LL8CCAAAAADD"),
    )

    def checkLine(self, line, formatType):
        if formatType == DATA:
            line.length = (line.length / 2) - 5
            checksum = checksums.nibbleSum(utils.makeList(utils.intToArray(line.address), 6, ((line.length + 5) * 2), line.chunk))
            if line.length != len(line.chunk):
                raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            if line.checksum!=checksum:
                raise hexfile.InvalidRecordChecksumError()
        elif formatType == SYMBOL:
            checksum = checksums.nibbleSum(utils.makeList(3, ((line.length + 5) * 2), [ord(b) for b in line.chunk]))
            chunk = line.chunk.strip()
            address = int(chunk[-4 : ], 16)
            line.address = address
            #if line.checksum!=checksum:
            #    raise hexfile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        return formatType == DATA

    def parseData(self, line, formatType):
        return formatType != SYMBOL

class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 24

    def composeRow(self, address, length, row):
        checksum = checksums.nibbleSum(utils.makeList(utils.intToArray(address), 6, ((length + 5) * 2), row))

        line = "%{0:02X}6{1:02X}{2:04X}{3!s}".format((length + 5) * 2, checksum, address, Writer.hexBytes(row) )
        return line

