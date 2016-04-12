#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <github.com/Christoph2,
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
import objutils.HexFile as HexFile
import objutils.utils as utils
from objutils.registry import register

DATA    = 1
EOF     = 2



NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)


class Reader(HexFile.Reader):

    #data = re.sub('\0*$', ';\n:0000', NULLS.match(inFile.read()).group(1), 1)  # FIXME!!!
    FORMAT_SPEC = (
        (DATA, "AAAA DD;"),
        (EOF, ":0000")
    )

    def checkLine(self, line, formatType):
        if formatType == DATA:
            line.length = len(line.chunk)

    def isDataLine(self, line, formatType):
        return formatType == DATA


class Writer(HexFile.Writer):
    SEPARATOR = "%s\x0d\x0a" % ('\x00' * 48)
    MAX_ADDRESS_BITS = 16

    def composeRow(self, address, length, row):
        return "%04X %s;" % (address, Writer.hexBytes(row))

    def composeHeader(self, meta):
        return "%s!M" % Writer.SEPARATOR

    def composeFooter(self, meta):
        return "%s" % Writer.SEPARATOR

