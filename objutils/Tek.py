#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2015 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import objutils.HexFile as HexFile
import objutils.utils as utils
import objutils.checksums as checksums

from objutils.registry import register

DATA    = 1
EOF     = 2

class Reader(HexFile.Reader):

    FORMAT_SPEC = (
        (DATA,  "/AAAALLBBDDCC"),
        (EOF,   "/AAAA00BB"),
    )

    def checkLine(self, line, formatType):
        if formatType == DATA:
            if line.length != len(line.chunk):
                raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            addrChecksum = 0
            addressChecksum = checksums.nibbleSum(utils.makeList(utils.intToArray(line.address), line.length))
            if line.addrChecksum != addressChecksum:
                raise HexFile.InvalidRecordChecksumError()
            checksum = checksums.nibbleSum(line.chunk)
            if line.checksum != checksum:
                raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        return formatType == DATA


class Writer(HexFile.Writer):

    MAX_ADDRESS_BITS = 16

    def composeRow(self, address, length, row):
        addressChecksum = checksums.nibbleSum(utils.makeList(utils.intToArray(address), length))

        dataChecksum = checksums.nibbleSum(row)
        line = "/%04X%02X%02X%s%02X" % (address, length, addressChecksum, Writer.hexBytes(row), dataChecksum)
        return line

#    def composeFooter(self, meta):
#        return ";00"

register('tek', Reader, Writer)

