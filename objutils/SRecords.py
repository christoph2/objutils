#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2012 by Christoph Schueler <github.com/Christoph2,
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

import HexFile
import cStringIO
import re

S0=1
S1=2
S2=3
S3=4
S5=5
S7=6
S8=7
S9=8
SYM=9

FORMATS=(
    (S0,"S0LLAAAADDCC"),
    (S1,"S1LLAAAADDCC"),
    (S2,"S2LLAAAAAADDCC"),
    (S3,"S3LLAAAAAAAADDCC"),
    (S5,"S5LLAAAACC"),
    (S7,"S7LLAAAAAAAACC"),
    (S8,"S8LLAAAAAACC"),
    (S9,"S9LLAAAACC"),
)

BIAS = {
    S0 : 3,
    S1 : 3,
    S2 : 4,
    S3 : 5,
    S5 : 2,
    S7 : 5,
    S8 : 4,
    S9 : 3
}

SYMBOLTABLE = re.compile(r"(^\$\$\s+(?P<modulename>\S*)(?P<symbols>.*?)\$\$)",re.MULTILINE|re.DOTALL)
SYMBOL = re.compile(r'\s+(?P<symbol>.*?)\s+\$(?P<value>.+)',re.MULTILINE|re.DOTALL)

class Reader(HexFile.Reader):
    def __init__(self, inFile, dataSep=None):
        data = inFile.read()
        ## todo: extract Symbols and wipe them out.

        symbolTables = SYMBOLTABLE.findall(data)
        if symbolTables:
            self._stripSymbols(symbolTables)
        records = SYMBOLTABLE.sub('', data).strip()
        inf = cStringIO.StringIO(records)
        super(Reader, self).__init__(FORMATS, inf, dataSep)

    def checkLine(self, line, formatType):
        # todo: Fkt.!!!
        if formatType in (S0, S1, S5, S9):
            checkSumOfAddress=((line.address & 0xff00) >> 8) + (line.address & 0xff)
        elif formatType in (S2, S8):
            checkSumOfAddress = ((line.address & 0xff0000)>>16) + ((line.address & 0xff00) >> 8) + \
                (line.address & 0xff)
        elif formatType in (S3, S7):
            checkSumOfAddress=(((line.address & 0xff000000) >> 24)+((line.address & 0xff0000) >> 16) + \
                ((line.address & 0xff00) >>8 )+(line.address & 0xff))
        else:
            raise TypeError("Invalid format type '%s'." % formatType)
        if hasattr(line, 'chunk'):
            checksum = (~(sum([line.length,checkSumOfAddress]) + sum(line.chunk))) & 0xff
        else:
            checksum = (~(sum([line.length,checkSumOfAddress]))) & 0xff
        if line.checksum != checksum:
            raise HexFile.InvalidRecordChecksumError()
        line.length-=BIAS[formatType]   # calculate actual data length.
        if line.length and (line.length != len(line.chunk)):
            raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

    def isDataLine(self, line, formatType):
        return formatType in (S1, S2, S3)

    def specialProcessing(self, line, formatType):
        if formatType == S0:
            pass
        elif formatType == S5:
            pass
        elif formatType == S7:
            startAddress = line.address
            print "32-Bit Start-Address: ", hex(startAddress)
        elif formatType == S8:
            startAddress = line.address
            print "24-Bit Start-Address: ", hex(startAddress)
        elif formatType == S9:
            startAddress=line.address
            print "16-Bit Start-Address: ", hex(startAddress)

    def _stripSymbols(self, symbolTables):
        self.symbols=[]
        for _, moduleName, symbolTable in symbolTables:
            sb = []
            for symbol in symbolTable.splitlines():
                ma = SYMBOL.match(symbol)
                if ma:
                    #print ma.groupdict()
                    gd = ma.groupdict()
                    sb.append((gd['symbol'], int(gd['value'], 16)))
            self.symbols.append(sb)
        print self.symbols

