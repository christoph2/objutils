#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2017 by Christoph Schueler <github.com/Christoph2,
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

from construct.core import Construct, ConstructError
from construct.core import Adapter, Struct, singleton
import six

class ULEBError(ConstructError): pass
class SLEBError(ConstructError): pass

@singleton
class ULEB(Construct):

    def __init__(self, *args):
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super(self.__class__, self).__init__()

    def _parse(self, stream, context, path = None):
        result = 0
        shift = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise ULEBError(str(e))
            result |= ((bval & 0x7f) << shift)
            if bval & 0x80 == 0:
                break
            shift += 7
        return result


    def _build(self, value, stream, context, path):
        assert value is not None
        if value < 0:
            raise ULEBError('value must be non-negative.')
        result = []
        while True:
            bval = value & 0x7f
            value >>= 7
            if value != 0:
                bval |= 0x80
            result.append(bval)
            if value == 0:
                break
        stream.write(bytes(result))


@singleton
class SLEB(Construct):

    def __init__(self, *args):
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super(self.__class__, self).__init__()

    def _parse(self, stream, context, path = None):
        result = 0
        shift = 0
        size = 32
        idx = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise SLEBError(str(e))
            result |= ((bval & 0x7f) << shift)
            shift += 7
            idx += 1
            if bval & 0x80 == 0:
                break
        if (shift < 32) or (bval & 0x40) == 0x40:
            mask = - (1 << (idx * 7))
            result |= mask
        return result

    def _build(self, value, stream, context, path):
        assert value is not None
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
        stream.write(bytes(result))


