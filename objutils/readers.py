#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

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


import os
import struct


class PlainBinaryReader:
    LITTLE_ENDIAN = "<"
    BIG_ENDIAN = ">"

    def __init__(self, image, byte_order_prefix="@"):
        self.image = image
        self.image.seek(0, os.SEEK_END)
        self._size = self.image.tell()
        self.image.seek(0, os.SEEK_SET)
        self.byte_order_prefix = byte_order_prefix
        self.pos = 0

    def _get_pos(self):
        return self.image.tell()

    def _set_pos(self, pos):
        self.image.seek(pos, os.SEEK_SET)

    def _get_size(self):
        return self._size

    def reset(self):
        self.pos = 0

    def next_byte(self):
        return self.u8()

    def value(self, conversion_code, size):
        (res,) = struct.unpack(
            "%c%c"
            % (
                self.byte_order_prefix,
                conversion_code,
            ),
            self.image.read(size),
        )
        return res

    def u8(self):
        return self.value("B", 1)

    def u16(self):
        return self.value("H", 2)

    def u32(self):
        return self.value("L", 4)

    def u64(self):
        return self.value("Q", 8)

    def s8(self):
        return self.value("b", 1)

    def s16(self):
        return self.value("h", 2)

    def s32(self):
        return self.value("l", 4)

    def s64(self):
        return self.value("q", 8)

    def uleb(self):
        result = 0
        shift = 0
        while True:
            bval = self.next_byte()
            result |= (bval & 0x7F) << shift
            if bval & 0x80 == 0:
                break
            shift += 7
        return result

    def sleb(self):
        result = 0
        shift = 0
        idx = 0
        while True:
            bval = self.next_byte()
            result |= (bval & 0x7F) << shift
            shift += 7
            idx += 1
            if bval & 0x80 == 0:
                break
        if (shift < 32) or (bval & 0x40) == 0x40:
            mask = -(1 << (idx * 7))
            result |= mask
        return result

    def asciiz(self):
        result = []
        while True:
            ch = self.next_byte()
            if ch == 0:
                break
            else:
                result.append(ch)
        return "".join(chr(c) for c in result)

    pos = property(_get_pos, _set_pos)
    size = property(_get_size)
