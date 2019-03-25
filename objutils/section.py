#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <github.com/Christoph2,
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
from copy import copy
from operator import attrgetter
import re
import reprlib

import attr

import objutils.hexdump as hexdump
from objutils.utils import PYTHON_VERSION


##
## todo: find/search methode(n) mit slice funktion!
## Basic patch-interface: (addr (plus ext!), datatype (endianess)) - readAs()/writeAs()
## API to change startAddress (but not length!) /w check for overlapps.
## split (for some reason) contingous regions into separate segments (splitAt [addresses], splitInto [n pieces]) inplace or new object.
## cut/copy/paste/delete

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


def filler(ch, n):
    """
    :param ch: fill char
    :type ch: int between 0 and 255
    :param int n: repetition count
    :return: bytearray
    """
    if not isinstance(ch, int):
        raise TypeError("ch must be of type int")
    if not (0 <= ch < 256):
        raise ValueError("ch must be between 0 and 255")
    if not isinstance(n, int):
        raise TypeError("n must be of type int")
    if n < 1:
        raise ValueError("n must be >= 1")
    return bytearray([ch] * n)


def _data_converter(data):
    if isinstance(data, bytearray):
        pass    # no conversion needed.
    elif isinstance(data, int):
        raise ValueError("single int not permitted")
    elif isinstance(data, str):
        if PYTHON_VERSION.major == 3 :
            data = bytearray(data, encoding = "ascii")
        else:
            data = bytearray(data)
    elif isinstance(data, array) and data.typecode != 'B':
        if PYTHON_VERSION.major == 3:
            data = bytearray(data.tobytes())
        else:
            data = bytearray(data.tostring())
    elif isinstance(data, Section):
        data = copy(data.data)    # just copy data from other section.
    else:
        try:
            data = bytearray(data)
        except Exception:
            raise ValueError("cannot convert '{}' to bytearray()".format(data))
    return data


@attr.s(repr = False, cmp = True)
class Section(object):
    """

    """
    startAddress = attr.ib(type = int, cmp = True, default = 0)
    data = attr.ib(default = bytearray(), converter = _data_converter, cmp = True)
    length = attr.ib(init = False, cmp = True)

    @length.default
    def __init_length__(self):
        return len(self.data)

    def __attrs_post_init__(self):
        self.repr = reprlib.Repr()
        self.repr.maxstring = 64
        self.repr.maxother = 64

    def __iter__(self):
        yield self

    def hexdump(self, fp = sys.stdout):
        dumper = hexdump.CanonicalDumper(fp)
        dumper.dumpData(self)

    def tobytes(self):
        if PYTHON_VERSION.major == 3:
            return  array('B', self.data).tobytes()
        else:
            return  array('B', self.data).tostring()

    def tolist(self):
        return  array('B', self.data).tolist()

    def _getformat(self, dtype):
        dtype = dtype.lower()
        fmt, bo = dtype.split("_")
        return "{}{}".format(BYTEORDER.get(bo), FORMATS.get(fmt))

    def read(self, addr, length):
        offset = addr - self.startAddress
        data = self.data[offset : offset + length]
        return Section(addr, data)

    def write(self, addr, length, data):
        offset = addr - self.startAddress
        self.data[offset : offset + length] = data

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

    def find(self, expr, addr = -1):
        for item in re.finditer(bytes(expr), self.data):
            yield (self.startAddress + item.start(), item.end()- item.start())

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

