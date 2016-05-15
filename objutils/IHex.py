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

from functools import partial
import operator
import objutils.hexfile as hexfile
from objutils.checksums import lrc, COMPLEMENT_TWOS
import objutils.utils as utils
import objutils.checksums as checksums

DATA                        = 0
EOF                         = 1
EXTENDED_SEGMENT_ADDRESS    = 2
START_SEGMENT_ADDRESS       = 3
EXTENDED_LINEAR_ADDRESS     = 4
START_LINEAR_ADDRESS        = 5


class Reader(hexfile.Reader):
    FORMAT_SPEC = (
        (hexfile.TYPE_FROM_RECORD, ":LLAAAATTDDCC"),
        )

    def __init__(self):
        super(Reader,self).__init__()
        self.segmentAddress=0

    def checkLine(self, line, formatType):
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        checksum = checksums.lrc(utils.makeList(line.type, line.length, utils.intToArray(line.address), line.chunk), 8, checksums.COMPLEMENT_TWOS)
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        if line.type == DATA:
            return True
        else:
            return False

    def calculateExtendedAddress(self, line, shiftBy, name):
            if len(line.chunk) == 2:
                segment = ((line.chunk[0]) << 8) | (line.chunk[1])
                line.addPI(('segment', segment))
                self._addressCalculator = partial(operator.add, segment << shiftBy)
                self.debug("EXTENDED_{0}_ADDRESS: {1:#X}".format(name.upper(), segment))
            else:
                self.error("Bad Extended {0} Address at line #{1}.".format(name, line.lineNumber))

    def specialProcessing(self, line, formatType):
        if line.type == DATA:
            line.address = self._addressCalculator(line.address)
        elif line.type == EXTENDED_SEGMENT_ADDRESS:
            self.calculateExtendedAddress(line, 4, "Segment")
        elif line.type == START_SEGMENT_ADDRESS:
            if len(line.chunk) == 4:
                cs = ((line.chunk[0]) << 8) | (line.chunk[1])
                ip = ((line.chunk[2]) << 8) | (line.chunk[3])
                line.addPI(('cs', cs))
                line.addPI(('ip', ip))
                self.debug("START_SEGMENT_ADDRESS: {0}:{1}".format(hex(cs), hex(ip)))
            else:
                self.error("Bad Segment Address at line %{0:u}.".format(line.lineNumber))
        elif line.type == EXTENDED_LINEAR_ADDRESS:
            self.calculateExtendedAddress(line, 16, "Linear")
        elif line.type == START_LINEAR_ADDRESS:
            if len(line.chunk) == 4:
                eip = ((line.chunk[0]) << 24) | ((line.chunk[1]) << 16) | ((line.chunk[2]) << 8) | (line.chunk[3])
                line.addPI(('eip', eip))
                self.debug("START_LINEAR_ADDRESS: {0}".format(hex(eip)))
            else:
                self.error("Bad Linear Address at line #%u." % line.lineNumber)
        elif line.type == EOF:
            pass
        else:
            self.warn("Invalid record type [{0:u}] at line {1:u}".format(line.type, line.lineNumber))

    _addressCalculator = utils.identity


class Writer(hexfile.Writer):
    MAX_ADDRESS_BITS = 32
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

