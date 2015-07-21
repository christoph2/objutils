#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2015 by Christoph Schueler <github.com/Christoph2,
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

from functools import partial
import operator
import objutils.HexFile as HexFile
from objutils.checksums import lrc, COMPLEMENT_TWOS
from objutils.utils import identity

from objutils.registry import register

DATA                        = 0
EOF                         = 1
EXTENDED_SEGMENT_ADDRESS    = 2
START_SEGMENT_ADDRESS       = 3
EXTENDED_LINEAR_ADDRESS     = 4
START_LINEAR_ADDRESS        = 5


class Reader(HexFile.Reader):
    FORMAT_SPEC = (
        (HexFile.TYPE_FROM_RECORD, ":LLAAAATTDDCC"),
        )

    def __init__(self):
        super(Reader,self).__init__()
        self.segmentAddress=0

    def checkLine(self, line, formatType):
        if line.length != len(line.chunk):
            raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        # todo: factor out checksum calculation from line!!!
        checksum = (~(sum([line.type, line.length, (line.address & 0xff00) >> 8, line.address & 0xff])+ sum(line.chunk)) + 1) & 0xff
        if line.checksum != checksum:
            raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        if line.type == DATA:
            return True
        else:
            return False

    def specialProcessing(self, line, formatType):
        if line.type == DATA:
            line.address = self._addressCalculator(line.address)
            #line.addPI(('address', line.address))
        elif line.type == EXTENDED_SEGMENT_ADDRESS:
            seg = ((line.chunk[0]) << 8) | (line.chunk[1])
            line.addPI(('segment', seg))
            self._addressCalculator = partial(operator.add, seg << 4)
            print "EXTENDED_SEGMENT_ADDRESS: ", hex(seg)
        elif line.type == START_SEGMENT_ADDRESS:
            cs = ((line.chunk[0]) << 8) | (line.chunk[1])
            ip = ((line.chunk[2]) << 8) | (line.chunk[3])
            line.addPI(('cs', cs))
            line.addPI(('ip', ip))
            print "START_SEGMENT_ADDRESS: %s:%s" % (hex(cs), hex(ip))
        elif line.type == EXTENDED_LINEAR_ADDRESS:
            seg = ((line.chunk[0]) << 8) | (line.chunk[1])
            line.addPI(('segment', seg))
            self._addressCalculator = partial(operator.add, seg << 16)
            print "EXTENDED_LINEAR_ADDRESS: ", hex(seg)
        elif line.type == START_LINEAR_ADDRESS:
            eip = ((line.chunk[0]) << 24) | ((line.chunk[1]) << 16) | ((line.chunk[2]) << 8) | (line.chunk[3])
            line.addPI(('eip', eip))
            print "START_LINEAR_ADDRESS: ", hex(eip)
        elif line.type == EOF:
            print "/// EOF"
        else:
            print "???"

    _addressCalculator = identity


":10010000214601360121470136007EFE09D2190140"
":10010000214601360121470136007EFE09D2190140"

": 10 0100  00      21 46 01 36 01 21 47 01 36 00 7E FE 09 D2 19 01      40"

class Writer(HexFile.Writer):
    checksum = partial(lrc, width = 8, comp = COMPLEMENT_TWOS)

    def writeHeader(self):
        pass

    def writeFooter(self, checksum):
        pass

    def writeBlock(self, block):
        pass

    def writeLine(self, type_, address, data):
        length = len(data)
        h, l = self.wordToBytes((address))
        checksum = self.checksum(list((length, h, l)) + list(data))
        ## buildLine()
        line = ""
        for b in data:
            line += "%02X" % b

        self.outFile.write(":%02X%04X%02X%s%02X" % (length, address, type_, line, checksum))

register('ihex', Reader, Writer)

