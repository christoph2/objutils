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

from array import array
from operator import itemgetter
import reprlib
import objutils.hexdump as hexdump
from objutils.utils import PYTHON_VERSION


class Section(object):

    def __init__(self, address = 0, data = None):
        self.address = address
        if data is None:
            self.data = bytearray()
        else:
            self.data = bytearray(data) # bytearray seems to be the most appropriate canocical representation.
        self._length = len(self.data)
        if isinstance(data, array) and data.typecode != 'B':
            if PYTHON_VERSION.major == 3:
                data = array('B', data.tobytes())
            else:
                data = array('B', data.tostring())
        self.repr = reprlib.Repr()
        self.repr.maxstring = 64

    def __getitem__(self, key):
        if key == 0:
            return self.address
        elif key == 1:
            return self.length
        elif key == 2:
            return self.data
        else:
            raise IndexError()

    def __eq__(self, other):
        return self.address == other.address

    def __ne__(self, other):
        return self.address == other.address

    def __lt__(self, other):
        return self.address < other.address

    def __le__(a, b):
        return self.address <= other.address

    def __ge__(a, b):
        return self.address >= other.address

    def __gt__(a, b):
        return self.address > other.address

    def __repr__(self):
        return "Section(address = 0X{0:08X}, length = {1:d}, data = {2})".format(self.address, self.length, self.repr.repr(str(self.data)))

    def __len__(self):
        return self.length

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    def hexdump(self, fp):
        dumper = hexdump.CanonicalDumper(fp)  # TODO: cache dumpers.
        dumper.dumpData(self)


def joinSections(sections, orderSections = True):
    resultSections = []
    if orderSections:
        sections.sort(key = itemgetter(0))
    prevSection = Section()
    while sections:
        section = sections.pop(0)
        if section.address == prevSection.address + prevSection.length and resultSections:
            lastSegment = resultSections[-1]
            lastSegment.data.extend(section.data)
            lastSegment.length += section.length
        else:
            # Create a new Segment.
            resultSections.append(Section(section.address, section.data))
        prevSection = section
    if resultSections:
        return resultSections
    else:
        return []

