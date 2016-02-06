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

import operator
import re
import objutils.HexFile as HexFile

DATA_ABS    = 1
DATA_INC    = 2
DATA_REL    = 3
EOF         = 4


FORMATS=(
    (DATA_ABS,  "CCLL0000AAAAAAAADD"),
    (DATA_INC,  "CCLL0001DD"),
    (DATA_REL,  "CCLL0002AAAAAAAADD"),
    (EOF,       "00000000")
)

NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)

def cs32(val):  # todo: universelle Funktion (in 'HexFile') !!!
    result = []
    for i in range(4):
        offs = 32 - (8 * (i + 1))
        result.append( (val & (0xff << offs)) >> offs)
    return reduce(operator.add, result)


class Reader(HexFile.Reader):
    def __init__(self, inFile, dataSep = None):
        self.lastAddress = 0
        outLines = []
        for inLine in inFile.readlines():
            inLine = inLine.strip()
            startSym, inLine = inLine[0], inLine[1:]

            if startSym != '$':
                pass # todo: FormatError!!!

            if (len(inLine) % 5) != 0:
                pass # todo: FormatError!!!

            values = []
            for quintuple in self.splitQuintuples(inLine):
                value = self.convertQuintuple(quintuple)
                values.append("%08X" % value)
            outLines.append(''.join(values))
        super(Reader, self).__init__(FORMATS, StringIO.StringIO('\n'.join(outLines)) , dataSep)

    def convertQuintuple(self, quintuple):
        res = 0
        for ch  in quintuple:
            v = REV_MAPPING[ch]
            res = v + (res * 85)
        return res

    def splitQuintuples(self, line):
        res = []
        for i in range(0, len(line), 5):
            res.append(line[i : i + 5])
        return res

    def checkLine(self, line, formatType):
        checksum = line.length
        line.length = len(line.chunk)
        if formatType == DATA_ABS:
            checksum += 0
            self.lastAddress = line.address + line.length
        elif formatType == DATA_INC:
            checksum += 1
            line.address = self.lastAddress
        elif formatType == DATA_REL:
            self.error("relative adressing not supported.")
            checksum += 2
        checksum += cs32(line.address)
        checksum += reduce(operator.add, line.chunk)
        checksum = (~checksum + 1) & 0xff
        if line.checksum != checksum:
            raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        return formatType in (DATA_ABS, DATA_INC, DATA_REL)

