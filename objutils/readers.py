#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2013 by Christoph Schueler <github.com/Christoph2,
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

# TODO: Reader interfac!!!

import os
import struct


class PlainBinaryReader(object):
    LITTLE_ENDIAN   = '<'
    BIG_ENDIAN      = '>'

    def __init__(self, image, endianess = "@"):
        self.image = image # StringIO.StringIO(image)
        self.endianess = endianess
        self.pos = 0

    def _getPos(self):
        return self.image.tell()

    def _setPos(self, pos):
        self.image.seek(pos, os.SEEK_SET)

    def nextByte(self):
        return self.u8()

    def value(self, conversionCode, size):
        res, = struct.unpack('%c%c' % (self.endianess, conversionCode, ), self.image.read(size))
        return res

    def u8(self):
        return self.value('B', 1)

    def u16(self):
        return self.value('H', 2)

    def u32(self):
        return self.value('L', 4)

    def u64(self):
        return self.value('Q', 8)

    def s8(self):
        return self.value('b', 1)

    def s16(self):
        return self.value('h', 2)

    def s32(self):
        return self.value('l', 4)

    def s64(self):
        return self.value('q', 8)

    def asciiz(self):
        result = []
        while True:
            ch = self.nextByte()
            if ch == 0:
                break
            else:
                result.append(ch)
        return ''.join(chr(c) for c in result)

    pos = property(_getPos, _setPos)




