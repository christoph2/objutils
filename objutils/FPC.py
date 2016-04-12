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
import operator
import re
import objutils.HexFile as HexFile
from objutils.utils import createStringBuffer, slicer
from objutils import checksums
import objutils.utils as utils

DATA_ABS    = 1
DATA_INC    = 2
DATA_REL    = 3
EOF         = 4

PREFIX      = '$'

MAPPING = dict(enumerate(chr(n) for n in range(37, 123) if not n in (42, )))

REV_MAPPING = dict([(value, key) for key, value in MAPPING.items()])
NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)

atoi16 = partial(int, base = 16)


class Reader(HexFile.Reader):

    FORMAT_SPEC = (
        (DATA_ABS,  "CCLL0000AAAAAAAADD"),
        (DATA_INC,  "CCLL0001DD"),
        (DATA_REL,  "CCLL0002AAAAAAAADD"),
        (EOF,       "00000000")
    )

    def read(self, fp):
        self.lastAddress = 0
        outLines = []
        for line in fp.readlines():
            line = line.strip()
            startSym, line = line[0], line[1:]

            if startSym != PREFIX:
                pass # todo: FormatError!!!

            if (len(line) % 5) != 0:
                pass # todo: FormatError!!!

            values = []
            for quintuple in self.splitQuintuples(line):
                value = self.convertQuintuple(quintuple)
                values.append("%08X" % value)
            outLines.append(''.join(values))
        return super(Reader, self).read(createStringBuffer('\n'.join(outLines)))

    def convertQuintuple(self, quintuple):
        res = 0         # reduce(lambda accu, x: (accu * 85) + x, value, 0)
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
        if formatType == EOF:
            return True
        line.length -= 4
        if line.length != len(line.chunk):
            line.chunk = line.chunk[ : line.length] # Cut padding.
        if formatType == DATA_ABS:
            tmp = 0
            self.lastAddress = line.address + line.length
        elif formatType == DATA_INC:
            tmp = 1
            line.address = self.lastAddress
        elif formatType == DATA_REL:
            self.error("relative adressing not supported.")
            tmp = 2
        else:
            self.error("Invalid format type: '{0}'".format(formatType))
            tmp = 0
        checksum = checksums.lrc(utils.makeList(tmp, line.length + 4, utils.intToArray(line.address), line.chunk), 8, checksums.COMPLEMENT_TWOS)
        if line.checksum != checksum:
            raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self, line, formatType):
        return formatType in (DATA_ABS, DATA_INC, DATA_REL)


class Writer(HexFile.Writer):

    MAX_ADDRESS_BITS = 16

    def composeRow(self, address, length, row):
        tmp = 0 # TODO: format type!?
        checksum = checksums.lrc(utils.makeList(tmp, length + 4, utils.intToArray(address), row), 8, checksums.COMPLEMENT_TWOS)
        if length < self.rowLength:
            lengthToPad = self.rowLength - length
            padding = [0] * (lengthToPad)
            row.extend(padding)
        line = "{0:02X}{1}0000{2:08X}{3}".format(checksum, length - 2, address, Writer.hexBytes(row))
        return line

    def composeFooter(self, meta):
        return "00000000"

    def postProcess(self, data):
        result = []
        for line in data.splitlines():
            if len(line) % 4:
                self.error("Size of line must be a multiple of 4.")
                continue
            res = []
            for item in slicer(line, 8, atoi16):
                item = self.convertQuintuple(item)
                res.append(item)
            result.append("{0}{1}".format(PREFIX, ''.join(res)))
        return '\n'.join(result)

    def convertQuintuple(self, value):
        result = []
        while value:
            result.append(MAPPING[value % 85])
            value /= 85
        if len(result) < 5:
            result.extend([MAPPING[0]] * (5 - len(result)))
        return ''.join(reversed(result))

"""
ZMQ-Base85:
----------
+------+------+------+------+------+------+------+------+
| 0x86 | 0x4F | 0xD2 | 0x6F | 0xB5 | 0x59 | 0xF7 | 0x5B |
+------+------+------+------+------+------+------+------+

   SHALL encode as the following 10 characters:
+---+---+---+---+---+---+---+---+---+---+
| H | e | l | l | o | W | o | r | l | d |
+---+---+---+---+---+---+---+---+---+---+

"""
