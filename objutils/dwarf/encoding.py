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

import math
import unittest

def numberOfBits(value):
    return int(math.ceil(math.log(abs(value), 2)))

def encodeULEB(value):
    if value < 0:
        raise ValueError('value must be non-negative.')
    result = []
    while True:
        bval = value & 0x7f
        value >>= 7
        if value != 0:
            bval |= 0x80
        result.append(bval)
        if value == 0:
            break
    return result


def encodeSLEB(value):
 result = []
 more = 1
 size = 32
 while more:
     bval = value & 0x7f
     value >>= 7
     if ((value == 0 and (bval & 0x40) == 0x00)) or ((value == -1 and (bval & 0x40) == 0x40)):
         more = 0
     else:
         bval |= 0x80
     result.append(bval)
 return result


def decodeSLEB(values):
 result = 0
 shift = 0
 size = 32

 for bval in values:
     result |= ((bval & 0x7f) << shift)
     shift += 7
     if bval & 0x80 == 0:
         break
 if (shift < 32) or (bval & 0x40) == 0x40:
     mask = - (1 << (len(values) * 7))
     result |= mask
 return result


def decodeULEB(values):
 result = 0
 shift = 0
 for bval in values:
     result |= ((bval & 0x7f) << shift)
     if bval & 0x80 == 0:
         break
     shift += 7
 return result


##
##  Unittests.
##

class testEncodeULEB(unittest.TestCase):
    values = [2, 127, 128, 129, 130, 12857]
    results = [[2], [127], [128, 1], [129, 1], [130, 1], [185, 100]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encodeULEB(value), result)

    def testExceptionOnNegativeNumber(self):
        self.assertRaises(ValueError, encodeULEB, -1)


class testEncodeSLEB(unittest.TestCase):
    values = [-2, -127, -128, -129, -130, -12857]
    results = [[126], [129, 127], [128, 127], [255, 126], [254, 126], [199, 155, 127]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encodeSLEB(value), result)


class testDecodeULEB(unittest.TestCase):
    values = [[2], [127], [128, 1], [129, 1], [130, 1], [185, 100]]
    results = [2, 127, 128, 129, 130, 12857]

    def testDecoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(decodeULEB(value), result)


class testDecodeSLEB(unittest.TestCase):
    values = [[126], [129, 127], [128, 127], [255, 126], [254, 126], [199, 155, 127]]
    results = [-2, -127, -128, -129, -130, -12857]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(decodeSLEB(value), result)


def sint(value, nbytes):
    mask = 2 ** ((nbytes * 8) - 1)
    if value >=mask:
        return (~value) + 1
    else:
        return value

print sint(-144, 2)

def main():
    unittest.main()

if __name__ == '__main__':
    main()

