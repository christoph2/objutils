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

from functools import partial
import re
from objutils.checksums import lrc, COMPLEMENT_ONES
from objutils.utils import makeList
import objutils.hexfile as hexfile
import objutils.utils as utils

S0  = 1
S1  = 2
S2  = 3
S3  = 4
S5  = 5
S7  = 6
S8  = 7
S9  = 8
SYM = 9

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

class Reader(hexfile.Reader):
    FORMAT_SPEC = (
        (S0, "S0LLAAAADDCC"),
        (S1, "S1LLAAAADDCC"),
        (S2, "S2LLAAAAAADDCC"),
        (S3, "S3LLAAAAAAAADDCC"),
        (S5, "S5LLAAAACC"),
        (S7, "S7LLAAAAAAAACC"),
        (S8, "S8LLAAAAAACC"),
        (S9, "S9LLAAAACC"),
    )

    def load(self, fp, **kws):
        data = self.read(fp)


        ## todo: extract Symbols and wipe them out.
        """
        symbolTables = SYMBOLTABLE.findall(data)
        if symbolTables:
            self._stripSymbols(symbolTables)
        records = SYMBOLTABLE.sub('', data).strip()
        """

        return data

    def checkLine(self, line, formatType):
        # todo: Fkt.!!!
        if formatType in (S0, S1, S5, S9):
            checkSumOfAddress = ((line.address & 0xff00) >> 8) + (line.address & 0xff)
        elif formatType in (S2, S8):
            checkSumOfAddress = ((line.address & 0xff0000) >> 16) + ((line.address & 0xff00) >> 8) + (line.address & 0xff)
        elif formatType in (S3, S7):
            checkSumOfAddress = (((line.address & 0xff000000) >> 24)+((line.address & 0xff0000) >> 16) +
                ((line.address & 0xff00) >>8 )+(line.address & 0xff)
            )
        else:
            raise TypeError("Invalid format type '%s'." % formatType)
        if hasattr(line, 'chunk'):
            checksum = (~(sum([line.length,checkSumOfAddress]) + sum(line.chunk))) & 0xff
        else:
            checksum = (~(sum([line.length,checkSumOfAddress]))) & 0xff
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()
        line.length -= BIAS[formatType]   # calculate actual data length.
        if hasattr(line, 'chunk') and line.length and (line.length != len(line.chunk)):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

    def isDataLine(self, line, formatType):
        return formatType in (S1, S2, S3)

    def specialProcessing(self, line, formatType):
        if formatType == S0:
            #print "S0: [%s]" % line.chunk
            pass
        elif formatType == S5:
            #print "S5: [%s]" % line.chunk
            startAddress = line.address
        elif formatType == S7:
            startAddress = line.address
            #print "Startaddress[S7]: %u" % startAddress
            #print "32-Bit Start-Address: ", hex(startAddress)
        elif formatType == S8:
            startAddress = line.address
            #print "Startaddress[S8]: %u" % startAddress
            #print "24-Bit Start-Address: ", hex(startAddress)
        elif formatType == S9:
            startAddress = line.address
            #print "Startaddress[S9]: %u" % startAddress
            #print "16-Bit Start-Address: ", hex(startAddress)

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
        #print self.symbols


class Writer(hexfile.Writer):
    recordType = None
    s5record = False
    startAddress = None

    MAX_ADDRESS_BITS = 32

    checksum = partial(lrc, width = 8, comp = COMPLEMENT_ONES)

    def preProcessing(self, image):
        if self.recordType is None:
            lastSegment = sorted(image.sections, key = lambda s: s.address)[-1]
            highestAddress = lastSegment.address + lastSegment.length
            if highestAddress <= 0x000000ffff:
                self.recordType = 1
            elif highestAddress <= 0x00ffffff:
                self.recordType = 2
            elif highestAddress <= 0xffffffff:
                self.recordType = 3
        self.addressMask = "%%0%uX" % ((self.recordType + 1) * 2, )
        self.offset = self.recordType + 2


    def srecord(self, recordType, length, address, data = None):
        if data is None:
            data = []
        length += self.offset
        addressBytes = utils.intToArray(address)
        checksum = self.checksum(makeList(addressBytes, length, data))
        mask = "S%%u%%02X%s%%s%%02X" % self.addressMask
        return mask % (recordType, length, address, Writer.hexBytes(data), checksum)

    def composeRow(self, address, length, row):
        self.recordCount += 1
        return self.srecord(self.recordType, length, address, row)

    def composeHeader(self, meta):
        self.recordCount = 0
        result = []
        if S0 in meta:  # Usually only one S0 record, but be tolerant.
            for meta in meta[S0]:
                result.append(self.srecord(0, len(meta.chunk), meta.address, meta.chunk))
        return '\n'.join(result)

    def composeFooter(self, meta):
        result = []
        if self.s5record:
            result.append(self.srecord(5, 0, self.recordCount))
        if not self.startAddress is None:
            if self.recordType == 1:    # 16bit.
                if S9 in meta:
                    s9 = meta[S9][0]
                    result.append(self.srecord(9, 0, s9.address))
                else:
                    result.append(self.srecord(9, 0, self.startAddress))
            elif self.recordType == 2:  # 24bit.
                if S8 in meta:
                    s8 = meta[S8][0]
                    result.append(self.srecord(8, 0, s8.address))
                else:
                    result.append(self.srecord(8, 0, self.startAddress))
            elif self.recordType == 3:  # 32bit.
                if S7 in meta:
                    s7 = meta[S7][0]
                    result.append(self.srecord(7, 0, s7.address))
                else:
                    result.append(self.srecord(7, 0, self.startAddress))
        return '\n'.join(result)
