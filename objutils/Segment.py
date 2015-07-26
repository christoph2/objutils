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

from operator import itemgetter

class Segment(object):
    def __init__(self, address = 0, length = 0, data = bytearray()):
        self.address = address
        self.length = length
        self.data = data

    def __getitem__(self, key):
        if key == 0:
            return self.address
        elif key == 1:
            return self.length
        elif key == 2:
            return self.data
        else:
            raise IndexError()

    def __repr__(self):
        return "Segment (address: '0X%08X' length: '%d')" % (self.address, self.length)


def joinSegments(segments):
    resultSegments = []
    segments.sort(key = itemgetter(0))
    prevSegment = Segment()
    while segments:
        segment = segments.pop(0)
        if segment.address == prevSegment.address + prevSegment.length and resultSegments:
            resultSegments[-1].data.extend(segment.data)
            resultSegments[-1].length += segment.length
        else:
            # Create a new Segment.
            resultSegments.append(Segment(segment.address, segment.length, segment.data))
        prevSegment = segment
    lastSeg = resultSegments[-1]
    return resultSegments

