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

import operator

from objutils.Segment import Segment

## TODO: diff interface!

## Adress-space constants.
AS_16   = 0
AS_24   = 1
AS_32   = 2
AS_64   = 3

class Image(object):
    def __init__(self, segments, meta = {}, valid = False):
        self.segments = segments
        self.meta = meta
        self.valid = valid

    def __repr__(self):
        result = []
        for segment in self.segments:
            result.append(repr(segment))
        return '\n'.join(result)

    def __len__(self):
        return len(self.segments)

    def __iter__(self):
        return iter(self.segments)

    def next(self):
        for segment in self.segments:
            yield segment

    def __eq__(self, other):
        if len(self.segments) == len(other.segments):
            return all([operator.eq(l,r) for l, r in zip(self.segments, other.segments)])
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def hexdump(self):
        for idx, section in enumerate(self.segments):
            print("\nSection #{0:04d}".format(idx))
            print("-" * 13)
            section.hexdump()


class Builder(object):

    def __init__(self, segments = []):
        self._segments = segments
        self.address = 0

    def addSegment(self, data, address =None, dontJoin = False):
        # If Address omitted, create continuos  address space.
        if isinstance(data, str):
            data = [ord(x) for x in data] # array.array('B',data)
        self._segments.append(Segment(address, data))

    def addMetaData(self, metaData):
        pass

    def joinSegments(self):
        pass

    def orderSegments(self):
        pass

    def hexdump(self):
        self.image.hexdump()

    @property
    def image(self):
        return Image(self._segments)

