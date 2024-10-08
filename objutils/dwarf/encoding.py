#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <github.com/Christoph2,
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
import time
from dataclasses import dataclass
from enum import IntEnum

from construct import Int8ul, Int16ub, Int16ul, Int32ub, Int32ul, Int64ub, Int64ul
from construct.core import Bytes, Construct, ConstructError, CString, singleton


# from objutils.dwarf.lineprog import Line

NULL_CHAR: bytes = b"\x00"


class Endianess(IntEnum):
    Little = 0
    Big = 1


class ULEBError(ConstructError):
    pass


class SLEBError(ConstructError):
    pass


@singleton
class ULEB(Construct):
    def __init__(self, *args):
        super(__class__, self).__init__()

    def _parse(self, stream, context, path=None):
        result = 0
        shift = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise ULEBError(str(e)) from e
            result |= (bval & 0x7F) << shift
            if bval & 0x80 == 0:
                break
            shift += 7
        return result

    def _build(self, value, stream, context, path):
        if value < 0:
            raise ULEBError("value must be non-negative.")
        result = []
        while True:
            bval = value & 0x7F
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
        super(__class__, self).__init__()

    def _parse(self, stream, context, path=None):
        result = 0
        shift = 0
        idx = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise SLEBError(str(e)) from e
            result |= (bval & 0x7F) << shift
            shift += 7
            idx += 1
            if bval & 0x80 == 0:
                break
        if (shift < 32) or (bval & 0x40) == 0x40:
            mask = -(1 << (idx * 7))
            result |= mask
        return result

    def _build(self, value, stream, context, path):
        result = []
        more = 1
        while more:
            bval = value & 0x7F
            value >>= 7
            if (value == 0 and (bval & 0x40) == 0x00) or (value == -1 and (bval & 0x40) == 0x40):
                more = 0
            else:
                bval |= 0x80
            result.append(bval)
        stream.write(bytes(result))


@singleton
class One(Construct):
    def __init__(self, *args):
        super(__class__, self).__init__()

    def _parse(self, stream, context, path=None):
        return 1

    def _build(self, value, stream, context, path):
        count = struct.pack("B", 1)
        value = 1
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


class Block(Construct):
    BYTEORDER = ""
    SIZE = None
    MASK = None

    def __init__(self, *args):
        super(__class__, self).__init__()

    def _parse(self, stream, context, path=None):
        msk = f"{self.BYTEORDER}{self.MASK}"
        count = stream.read(self.SIZE)
        count = struct.unpack(msk, count)[0]
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value, stream, context, path):
        msk = f"{self.BYTEORDER}{self.MASK}"
        count = struct.pack(msk, len(value))
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


@singleton
class BlockUleb(Block):
    def _parse(self, stream, context, path=None):
        count = ULEB.parse_stream(stream)
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value, stream, context, path):
        count = ULEB.build(len(value))
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


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

    def __init__(self, size, endianess: Endianess):
        super(__class__, self).__init__()
        idx = 0 if endianess == Endianess.Little else 1
        if size not in (1, 2, 4, 8):
            raise ValueError(f"Address size '{size}' not supported.")
        if not isinstance(size, int):
            print("**SIZE is not int", size, endianess, idx, type(str))
        if not isinstance(idx, int):
            print("**IDX is not int", size, endianess, idx, type(idx))
        self.type = self.TYPES[size][idx]

    def _parse(self, stream, context, path=None):
        return self.type.parse_stream(stream)

    def _build(self, value, stream, context, path):
        stream.write(self.type.build(value))


class StrP(Construct):
    BYTEORDER = ""
    SIZE = None
    MASK = None

    def __init__(self, image, endianess: Endianess):
        self.image = image
        self.endianess = endianess
        self.ntype = (Int32ul, Int32ub)[0 if endianess == Endianess.Little else 1]
        self.stype = CString(encoding="utf8")
        super(__class__, self).__init__()

    def _parse(self, stream, context, path=None):
        offset = self.ntype.parse_stream(stream)
        data = self.image[offset:]
        result = self.stype.parse(data)
        return result

    def _build(self, value, stream, context, path):
        stream.write(self.type.build(value))


class ArrayOfCStrings(Construct):

    def __init__(self, encoding: str = "ascii") -> None:
        self.str_type = CString(encoding=encoding)
        super().__init__()

    def _parse(self, stream, context, path=None):
        result = []

        while True:
            value = CString(encoding="utf8").parse_stream(stream)
            if not value:
                break
            result.append(value)
        # term = stream.read(1)
        return result

    def _build(self, values, stream, context, path):
        if values:
            for value in values:
                stream.write(self.str_type.build(value))
        else:
            stream.write(NULL_CHAR)
        # stream.write(NULL_CHAR)


@dataclass
class Filename:
    name: str
    dir_index: int
    last_modified: int
    length: int


class FilenameSequence(Construct):

    def __init__(self, encoding: str = "ascii") -> None:
        self.str_type = CString(encoding=encoding)
        super().__init__()

    def _parse(self, stream, context, path=None):
        result = {}
        idx = 1
        while True:
            current = stream.tell()
            ch = stream.read(1)
            if ch == NULL_CHAR:
                break
            stream.seek(current)
            name = self.str_type.parse_stream(stream)
            if not name:
                break
            dir_index = ULEB.parse_stream(stream)
            last_mod = ULEB.parse_stream(stream)
            file_length = ULEB.parse_stream(stream)
            result[idx] = Filename(name, dir_index, time.ctime(last_mod), file_length)
            idx += 1
        return result

    def _build(self, values, stream, context, path):
        if values:
            for value in values:
                stream.write(self.str_type.build(value))
        else:
            stream.write(NULL_CHAR)
        stream.write(NULL_CHAR)
