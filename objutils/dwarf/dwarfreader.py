#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """/
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

from objutils.readers import PlainBinaryReader
from objutils.utils import createStringBuffer


class DwarfReader(PlainBinaryReader):

    def __init__(self, image, imageReader, byteOrderPrefix):
        super(DwarfReader, self).__init__(createStringBuffer(image), byteOrderPrefix)
        self.wordSize = None
        self.imageReader = imageReader

    def uleb(self):
        result = 0
        shift = 0
        while True:
            bval = self.nextByte()
            result |= ((bval & 0x7f) << shift)
            if bval & 0x80 == 0:
                break
            shift += 7
        return result

    def sleb(self):
        result = 0
        shift = 0
        idx =0
        while True:
            bval = self.nextByte()
            result |= ((bval & 0x7f) << shift)
            shift += 7
            idx += 1
            if bval & 0x80 == 0:
                break
        if (shift < 32) or (bval & 0x40) == 0x40:
            mask = - (1 << (idx * 7))
            result |= mask
        return result

    def asciiz(self):
        result = []
        while True:
            bval = self.nextByte()
            if bval == 0:
                break
            result.append(bval)
        return ''.join(chr(x) for x in result)

    def _block(self, size):
        _BLOCK_SIZE_READER = {1: self.u8, 2: self.u16, 4: self.u32, -1: self.uleb}
        return [self.u8() for _ in range(_BLOCK_SIZE_READER[size]())]

    def block1(self):
        return self._block(1)

    def block2(self):
        return self._block(2)

    def block4(self):
        return self._block(4)

    def block(self):
        return self._block(-1)

    def addr(self):
        if self.wordSize == 1:
            return self.u8()
        elif self.wordSize == 2:
            return self.u16()
        elif self.wordSize == 4:
            return self.u32()
        elif self.wordSize == 8:
            return self.u64()
        else:
            return self.u32()        # TODO: Error handling!

    def strp(self):
        section = self.imageReader.sections['.debug_str'].image
        offset = self.u32()

        result = [] # TODO: Refactor (s. asciiz)!
        idx = 0
        while True:
            try:
                bval = section[offset + idx]
            except IndexError as e: # TODO: Genau analysieren!!!
                print e
                break
            if bval == '\0':
                break
            idx += 1
            result.append(bval)
        rstr = ''.join(x for x in result)

        return rstr

