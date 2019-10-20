#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import functools

COMPLEMENT_NONE = 0
COMPLEMENT_ONES = 1
COMPLEMENT_TWOS = 2

def lrc(data, width, comp = COMPLEMENT_NONE):
    """Longitudinal redundancy check.
    """

    mask = (2 ** width)

    cs = sum(data) % mask

    if comp == COMPLEMENT_NONE:
        pass
    elif comp == COMPLEMENT_ONES:
        cs ^= (mask - 1)
    elif comp == COMPLEMENT_TWOS:
        cs = ((cs ^ (mask - 1)) + 1) % mask

    return cs


def rolb(value):
    """Rotate byte left.
    """
    value &= 0xff
    carry = (value & 0x80) == 0x80
    value = (value << 1) & 0xff
    value |= 1 if carry else 0
    return value

def rorb(value):
    """Rotate byte right.
    """
    value &= 0xff
    carry = (value & 0x01) == 0x01
    value = value >> 1
    value |= 0x80 if carry else 0
    return value

def xor(frame, invert = True):
    return functools.reduce(operator.xor, frame, 0xff if invert else 0x00)

ROTATE_LEFT = rolb
ROTATE_RIGHT = rorb

def rotatedXOR(values, width, rotator):
    """Rotated XOR cipher.
    """
    cs = 0
    for value in values:
        cs ^= value
        cs = rotator(cs)
    return cs  % (2 ** width)

def nibble_sum(data):
    result = 0
    for d in data:
        hn = (d & 0xf0) >> 4
        ln = d & 0x0f
        result +=  hn + ln
    return result % 256

