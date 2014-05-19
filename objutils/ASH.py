#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2014 by Christoph Schueler <github.com/Christoph2,
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

##
##  ASCII hex-space format.
##

import cStringIO
from functools import partial
import re
import sys
from objutils.Segment import Segment, joinSegments
from objutils.Image import Image
from objutils.checksums import lrc, COMPLEMENT_NONE

STX = '\x02'
ETX = '\x03'


ASCII_HEX = """ $A0000,
7F D2 43 A6 7F F3 43 A6 3F C0 00 3F 3B DE 70 0C
3B E0 00 01 93 FE 00 00 7F FA 02 A6 93 FE 00 04
7F FB 02 A6 93 FE 00 08 7F D2 42 A6 7F F3 42 A6
48 00 1F 04 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
$ACF00,
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
$$0FF0,"""


DATA = re.compile(r'(?:.*?\02)(?P<chunks>.*)(?:\03)\s*(?:\$\$(?P<checksum>[0-9a-zA-Z]{2,4}),)?', re.DOTALL | re.MULTILINE)

ADDRESS = re.compile(r'\$A(?P<value>[0-9a-zA-Z]{2,8}),\s*')

checksum = partial(lrc, width = 16)

class Reader(object):
    def __init__(self, inFile, dataSeparator = ' '):
        self.inFile = inFile
        self.dataSeparator = dataSeparator

    def read(self):
        lines = self.inFile.read()
        ma = DATA.match(lines)

        chunks = ma.groupdict()['chunks'].strip()

        segments = []
        lines = []
        address = 0
        previousAddress = 0

        for line in chunks.splitlines():
            print "***%s***" % line
            ma = ADDRESS.match(line)
            if ma:
                address = int(ma.groupdict()['value'], 16)
                print "ADDRESS: %u" % address
                if lines:
                    print "APPEND"
                    segments.append((previousAddress, lines))
                else:
                    print "*** No Lines!!!"
                previousAddress = address
                lines = []
            else:
                lines.append(line)

        if lines:
            segments.append((address, lines))

        chunks = []
        for address, segment in segments:
            print "Start-Address: %04X" % address
            for line in segment:
                chunk = bytearray(self._getByte(line))
                print "*** BA: '%s'***" % chunk

                chunks.append(Segment(address, len(chunk), chunk))
                address += len(chunk)

        return Image(joinSegments(chunks))

    def _getByte(self, chunk):
        for line in chunk.splitlines():
            for b in line.split():
                yield chr(int(b, 16))


class Writer(object):
    def __init__(self, outFile, bytesPerRow = 16):
        self.outFile = outFile
        self.bytesPerRow = bytesPerRow

    def write(self, image): # TODO: Make Template Pattern!!!
        checksum = 0
        self.writeHeader()
        for segment in image.segments:
            self.outFile.write("$A%04X," %segment.address)
            for idx, b in enumerate(segment.data):
                if (idx % self.bytesPerRow) == 0:
                    self.outFile.write("\n")

                self.outFile.write("%02X " % b)
                checksum += b
            self.outFile.write("\n")
        ## TODO: Newline in case of odd byte count.
        self.writeFooter(checksum)

    def updateChecksum(self, value):
        pass

    def writeHeader(self):
        self.outFile.write("%c " % STX)

    def writeFooter(self, checksum):
        self.outFile.write("%c$$%04X," % (ETX, (checksum % 65536)))

    def writeBlock(self, block):
        pass



S19 = """S321000000007FD243A67FF343A63FC0003F3BDE700C3BE0000193FE00007FFA02A6A8
S3210000001C93FE00047FFB02A693FE00087FD242A67FF342A648001F040000000074
S3210000003800000000000000000000000000000000000000000000000000000000A6
S32100000054000000000000000000000000000000000000000000000000000000008A"""


def main():
    inf = cStringIO.StringIO(ASCII_HEX)
    hr = Reader(inf)
    data = hr.read()
    print data
    wr = Writer(sys.stdout)
    wr.write(data)

if __name__ == '__main__':
    main()

