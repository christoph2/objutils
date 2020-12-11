#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <github.com/Christoph2,
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

import struct

from construct.core import Construct, ConstructError, Bytes, CString
from construct.core import singleton
from construct import Int16ul, Int32ul, Int64ul, Int8ul
from construct import Int16ub, Int32ub, Int64ub

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
            super().__init__()

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

@singleton
class One(Construct):

    def __init__(self, *args):
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super().__init__()

    def _parse(self, stream, context, path = None):
        return 1

    def _build(self, value, stream, context, path):
        count = struct.pack("B", 1)
        value = 1
        stream.write(count)
        if six.PY3:
            stream.write(bytes(value, encoding = "ascii"))
        else:
            stream.write(bytes(value))

class Block(Construct):

    BYTEORDER = ''
    SIZE = None
    MASK = None

    def __init__(self, *args):
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super().__init__()

    def _parse(self, stream, context, path = None):
        msk = "{}{}".format(self.BYTEORDER, self.MASK)
        count = stream.read(self.SIZE)
        count = struct.unpack(msk, count)[0]
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value, stream, context, path):
        msk = "{}{}".format(self.BYTEORDER, self.MASK)
        count = struct.pack(msk, len(value))
        stream.write(count)
        if six.PY3:
            stream.write(bytes(value, encoding = "ascii"))
        else:
            stream.write(bytes(value))


@singleton
class BlockUleb(Block):

    def _parse(self, stream, context, path = None):
        count = ULEB.parse_stream(stream)
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value, stream, context, path):
        count = ULEB.build(len(value))
        stream.write(count)
        if six.PY3:
            stream.write(bytes(value, encoding = "ascii"))
        else:
            stream.write(bytes(value))

@singleton
class Block1(Block):

    SIZE = 1
    MASK = "B"
    BYTEORDER = "<"


@singleton
class Block2l(Block):

    SIZE = 2
    MASK = "H"
    BYTEORDER = "<"


@singleton
class Block2b(Block):

    SIZE = 2
    MASK = "H"
    BYTEORDER = ">"


@singleton
class Block4l(Block):

    SIZE = 4
    MASK = "L"
    BYTEORDER = "<"


@singleton
class Block4b(Block):

    SIZE = 4
    MASK = "L"
    BYTEORDER = ">"


class Address(Construct):

    TYPES = {
        1: (Int8ul, Int8ul),
        2: (Int16ul, Int16ub),
        4: (Int32ul, Int32ub),
        8: (Int64ul, Int64ub),
    }

    def __init__(self, size, endianess):
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super().__init__()
        idx = endianess
        if size not in (1, 2, 4, 8):
            raise ValueError("Address size '{}' not supported.".format(size))
        if not isinstance(size, int):
            print("**SIZE is not int", size, endianess, idx, type(str))
        if not isinstance(idx, int):
            print("**IDX is not int", size, endianess, idx, type(idx))
        self.type = self.TYPES[size][idx]

    def _parse(self, stream, context, path = None):
        return self.type.parse_stream(stream)

    def _build(self, value, stream, context, path):
        stream.write(self.type.build(value))


class StrP(Construct):

    BYTEORDER = ''
    SIZE = None
    MASK = None

    def __init__(self, image, endianess):
        self.image = image
        self.endianess = endianess
        self.ntype = (Int32ul, Int32ub)[0 if endianess == 1 else 1]
        self.stype = CString(encoding = "utf8")
        if six.PY3:
            super(__class__, self).__init__()
        else:
            super().__init__()

    def _parse(self, stream, context, path = None):
        offset = self.ntype.parse_stream(stream)
        #self.image.seek(offset)
        data = self.image[offset : ]
        result = self.stype.parse(data)
        return result

    def _build(self, value, stream, context, path):
        stream.write(self.type.build(value))
