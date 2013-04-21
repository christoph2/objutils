#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2013 by Christoph Schueler <github.com/Christoph2,
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

import objutils.HexFile as HexFile
import cStringIO

DATA    = 1
SYMBOL  = 2
EOF     = 3

FORMATS=(
    (DATA,      "%LL6CCAAAADD"),
    (SYMBOL,    "%LL3CCU"),
    (EOF,       "/AAAA00BB"),
)

class Reader(HexFile.Reader):
    def __init__(self,  inFile):
        super(Reader,self).__init__(FORMATS, inFile)

    def nibbleSum(self, accu, b):
        hn = (b & 0xf0) >> 4
        ln = b & 0x0f
        s = hn + ln
        return accu + s

    def checkLine(self, line, formatType):
        if formatType == DATA:
            line.length = (line.length - 10) / 2
            if line.length != len(line.chunk):
                raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            ns = 0
            for b in [(line.address & 0xff00) >> 8, line.address & 0xff, line.length]:
                ns = self.nibbleSum(ns, b)
            for b in line.chunk:
                ns = self.nibbleSum(ns, b)
            checksum = ( ~ (sum(line.chunk)) + line.length + (line.address >> 8) + (line.address & 0xff) ) & 0xff
        elif formatType == SYMBOL:
            chunk = line.chunk
            print chunk
            '''
            if line.checksum!=checksum:
                raise HexFile.InvalidRecordChecksumError()
            '''

    def isDataLine(self, line, formatType):
        return formatType == DATA

    def parseData(self, line, formatType):
        return formatType != SYMBOL

