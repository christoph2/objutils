#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.1"

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

import math
import sys


isprintable = lambda ch: 0x1F < ch

def unpack(*args):
    return args

class Dumper(object):

    def __init__(self, fout = sys.stdout, numAddressBits = 32):
        self._fout = fout
        self._rolloverMask = 2 ** numAddressBits
        self._nibbles = numAddressBits >> 2
        self._addressMask = "%%0%ux " % self._nibbles
        self.previousRow = bytearray()
        self.elided = False

    def dumpRow(self, row):
        pass

    def dumpData(self, section, offset = 0):
        end = section.length
        lineCount = math.ceil(len(section.data) / self.LINE_LENGTH)
        startPos = 0
        lineNum = 0
        endPos = self.LINE_LENGTH
        while endPos < end:
            lineNum += 1
            row = section.data[startPos : endPos]
            if row == self.previousRow:
                if not self.elided:
                    print "          *"
                    self.elided = True
            else:
                self.dumpRow(row, startPos + section.address)
                self.elided = False
            startPos = endPos
            endPos = endPos + self.LINE_LENGTH
            self.previousRow = row
        row = section.data[startPos : endPos]
        self.dumpRow(row, startPos + section.address)


class CanonicalDumper(Dumper):
    LINE_LENGTH = 0x10

    def printHexBytes(self, row):
        row = list(row)
        filler = list([0x20] * (self.LINE_LENGTH - len(row)))
        print('|{0}|'.format(('%s' * self.LINE_LENGTH) % unpack(*[isprintable(x) and chr(x) or '.' for x in row + filler] )))

    def dumpRow(self, row, startAddr):
        startPos = 0
        print(self._addressMask % ((startPos + startAddr) % self._rolloverMask)),
        print('%02x ' * len(row) % unpack(*row)),
        if len(row) == 0:
            print
        if len(row) < self.LINE_LENGTH:
            spaces = "   " * (self.LINE_LENGTH - len(row))
            print(spaces[ 1: ]),
        self.printHexBytes(row)


class OneByteOctalDumper(Dumper):

    def dumpRow(self, row, startAddr):
        startPos = 0
        print(self._addressMask % ((startPos + startAddr) % self._rolloverMask)),
        print('%03o ' * len(row) % unpack(*row))

class TwoByteOctalDumper(Dumper): pass

class OneByteCharDumper(Dumper): pass

class TwoByteDecimalDumper(Dumper): pass

class TwoByteHexDumper(Dumper): pass

class FormattedDumper(Dumper): pass

