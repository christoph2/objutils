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

import objutils.hexfile as hexfile
import objutils.utils as utils
import objutils.checksums as checksums

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
    previousAddress = 0
    previousLength = 0

    def checkLine(self, line, formatType):
        return True

    def isDataLine(self, line, formatType):
        if formatType == DATA3:
            if line.junk in ("!M", "?M"):   # Startsymbol, address ommited.
                return False
            line.address = self.previousAddress + self.previousLength
            self.previousAddress = line.address
            self.previousLength = len(line.chunk)
        else:
            if hasattr(line, 'chunk'):
                length = len(line.chunk)
            else:
                length = 0
            self.previousAddress = line.address
            self.previousLength = length
        return formatType in (DATA0, DATA1, DATA2, DATA3)


class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 16

    def composeRow(self, address, length, row):
        line = "!M{0:04X} {1}".format(address, Writer.hexBytes(row))
        return line

