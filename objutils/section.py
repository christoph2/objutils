#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2018 by Christoph Schueler <github.com/Christoph2,
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

import struct
import sys

from array import array
from operator import attrgetter
import reprlib
import objutils.hexdump as hexdump
from objutils.utils import PYTHON_VERSION


##
## todo: find/search methode(n) mit slice funktion!
## Basic patch-interface: (addr, datatype (endianess)) - readAs()/writeAs()
##

FORMATS = {
    "uint8": "B",
    "int8": "b",
    "uint16": "H",
    "int16": "h",
    "uint32": "I",
    "int32": "i",
    "uint64": "Q",
    "int64": "q",
    "float32": "f",
    "float64": "d",
}

BYTEORDER = {
    "le": "<",
    "be": ">",
}

class Section(object):

    def __init__(self, address = 0, data = None):
        self.startAddress = address
        if data is None:
            self.data = bytearray()
        else:
            self.data = bytearray(data) # bytearray seems to be the most appropriate canonical representation.
        self._length = len(self.data)
        if isinstance(data, array) and data.typecode != 'B':
            if PYTHON_VERSION.major == 3:
                data = array('B', data.tobytes())
            else:
                data = array('B', data.tostring())
        self.repr = reprlib.Repr()
        self.repr.maxstring = 64
        self.repr.maxother = 64

    def __eq__(self, other):
        return self.startAddress == self.startAddress

    def __ne__(self, other):
        return self.startAddress == self.startAddress

    def __lt__(self, other):
        return self.startAddress < self.startAddress

    def __le__(a, b):
        return self.startAddress <= self.startAddress

    def __ge__(a, b):
        return self.startAddress >= self.startAddress

    def __gt__(a, b):
        return self.startAddress > self.startAddress

    def __repr__(self):
        return "Section(address = 0X{0:08X}, length = {1:d}, data = {2})".format(
            self.startAddress,
            self.length,
            self.repr.repr(memoryview(self.data).tobytes())
        )

    def __len__(self):
        return self.length

    def __contains__(self, addr):
        return self.startAddress <= addr < (self.startAddress + self.length)

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    def hexdump(self, fp = sys.stdout):
        dumper = hexdump.CanonicalDumper(fp)
        dumper.dumpData(self)

    def _getformat(self, dtype):
        dtype = dtype.lower()
        fmt, bo = dtype.split("_")
        return "{}{}".format(BYTEORDER.get(bo), FORMATS.get(fmt))

    def readNumeric(self, addr, dtype):
        offset = addr - self.startAddress
        fmt = self._getformat(dtype)
        data = self.data[offset : offset + struct.calcsize(fmt)]
        return struct.unpack(fmt, data)[0]

    def writeNumeric(self, addr, value, dtype):
        offset = addr - self.startAddress
        fmt = self._getformat(dtype)
        self.data[offset : offset + struct.calcsize(fmt)] = struct.pack(fmt, value)

    def readString(self, addr, encoding = "latin1", length = -1):
        offset = addr - self.startAddress
        pos = self.data[offset : ].find(b'\x00')
        if pos == -1:
            raise RuntimeError("Unterminated String!!!")
        return self.data[offset : offset + pos].decode(encoding = encoding)

    def writeString(self, addr, value, encoding = "latin1"):
        offset = addr - self.startAddress
        if PYTHON_VERSION.major == 3:
            self.data[offset : offset +  len(value)] = bytes(value, encoding = encoding)
        else:
            self.data[offset : offset +  len(value)] = bytes(value)
        self.data[offset +  len(value)] = 0


def joinSections(sections, orderSections = True):
    resultSections = []
    if orderSections:
        sections.sort(key = attrgetter("startAddress"))
    prevSection = Section()
    while sections:
        section = sections.pop(0)
        if section.startAddress == prevSection.startAddress + prevSection.length and resultSections:
            lastSegment = resultSections[-1]
            lastSegment.data.extend(section.data)
            lastSegment.length += section.length
        else:
            # Create a new section.
            resultSections.append(Section(section.startAddress, section.data))
        prevSection = section
    if resultSections:
        return resultSections
    else:
        return []

