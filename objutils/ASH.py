#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2015 by Christoph Schueler <cpu12.gems@googlemail.com>

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
##  ASCII Space Hex format.
##

from functools import partial
import re
import sys
import objutils.HexFile as HexFile
from objutils.Segment import Segment, joinSegments
from objutils.Image import Image
from objutils.checksums import lrc, COMPLEMENT_NONE
from objutils.utils import PYTHON_VERSION
from objutils.registry import register

STX = '\x02'
ETX = '\x03'

DATA = re.compile(r'(?:.*?\02)(?P<chunks>.*)(?:\03)\s*(?:\$\$(?P<checksum>[0-9a-zA-Z]{2,4})[,.])?', re.DOTALL | re.MULTILINE)
ADDRESS = re.compile(r'\$A(?P<value>[0-9a-zA-Z]{2,8})[,.]\s*')
LINE_SPLIITER = re.compile(r"[ %,']")

checksum = partial(lrc, width = 16)


class Reader(HexFile.Reader):

    def __init__(self):
        pass

    def read(self, fp):
        if PYTHON_VERSION.major == 3:
            lines = fp.read().decode()
        else:
            lines = fp.read()
        segments = []
        address = 0
        previousAddress = 0
        resultLines = []
        for line in lines.splitlines():
            match = ADDRESS.match(line)
            if match:
                address = int(match.groupdict()['value'], 16)
                if resultLines:
                    segments.append((previousAddress, resultLines))
                previousAddress = address
                resultLines = []
            else:
                if not line.startswith('q'):
                    resultLines.append(line)

        if resultLines:
            segments.append((address, resultLines))

        chunks = []
        for address, segment in segments:
            for line in segment:
                chunk = bytearray(self._getByte(line))
                chunks.append(Segment(address, chunk))
                address += len(chunk)

        return Image(joinSegments(chunks))

    def _getByte(self, chunk):
        for line in chunk.splitlines():
            for ch in LINE_SPLIITER.split(line):
                yield chr(int(ch, 16))


class Writer(HexFile.Writer):

    MAX_ADDRESS_BITS = 16

    def composeRow(self, address, length, row):
        prependAddress =  True if address != self.previousAddress else False
        self.previousAddress = (address + length)
        self.checksum += checksum(row)
        if prependAddress:
            line = "{0}\n{1}".format("$A{0:04X},".format(address), " ".join(["{0:02X}".format(x) for x in row]))
        else:
            line = " ".join(["{0:02X}".format(x) for x in row])
        return line

    def composeHeader(self, meta):
        self.checksum = 0
        self.previousAddress = None
        line ="{0} ".format(STX)
        return line

    def composeFooter(self, meta):
        line = "{0}$${1:04X},".format(ETX, self.checksum % 65536)
        return line

register('ash', Reader, Writer)

