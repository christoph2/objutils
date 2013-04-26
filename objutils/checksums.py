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

COMPLEMENT_NONE = 0
COMPLEMENT_ONES = 1
COMPLEMENT_TWOS = 2

def lrc(data, width, comp = COMPLEMENT_NONE):
    """    Longitudinal redundancy check.
    """

    cs = sum(data) % (2 ** width)

    if comp == COMPLEMENT_NONE:
        pass
    elif comp == COMPLEMENT_ONES:
        cs ^= 0xff
    elif comp == COMPLEMENT_TWOS:
        cs = ((cs ^ 0xff) + 1) & ((2 ** width) - 1)

    return cs

