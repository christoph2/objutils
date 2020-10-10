#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

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

from array import array
from collections import namedtuple
from copy import copy
from operator import attrgetter
import re
import reprlib
import struct
import sys

import attr
from sortedcontainers import SortedList

from objutils.exceptions import InvalidAddressError, FeatureNotAvailableError
import objutils.hexdump as hexdump
from objutils.utils import PYTHON_VERSION


##
## todo: find/search methode(n) mit slice funktion!
## Basic patch-interface: (addr (plus ext!), datatype (endianess)) - readAs()/writeAs()
## API to change start_address (but not length!) /w check for overlapps.
## split (for some reason) contingous regions into separate segments (splitAt [addresses], splitInto [n pieces]) inplace or new object.
## cut/copy/paste/delete
##

FORMATS = {
    "uint8": "B",
    "int8": "b",
    "uint16": "H",
    "int16": "h",
    "uint32": "I",
    "int32": "i",
    "uint64": "Q",
    "int64": "q",
    "float32": "f",
    "float64": "d",
}

TYPE_SIZES = {
    "uint8":    1,
    "int8":     1,
    "uint16":   2,
    "int16":    2,
    "uint32":   4,
    "int32":    4,
    "uint64":   8,
    "int64":    8,
    "float32":  4,
    "float64":  8,
}


BYTEORDER = {
    "le": "<",
    "be": ">",
}

TypeInformation = namedtuple("TypeInformation", "type byte_order size")

DTYPE = re.compile(r"""
      (?:(?P<uns>u)?int(?P<len>8 | 16 | 32 | 64)(?P<sep>[-/_:])(?P<end> be | le))
    | (?P<byte>byte)
    | (?P<flt>float)(?P<flen>32 | 64)""", re.IGNORECASE | re.VERBOSE)

NumberRange = namedtuple("NumberRange", "lower upper")

signed_range = lambda x: NumberRange( *(int(-(2 ** x / 2)), int((2 ** x / 2) - 1)))
unsigned_range = lambda x: NumberRange( *(0, int((2 ** x) - 1)))

INT8_RANGE  = signed_range(8)
INT16_RANGE = signed_range(16)
INT32_RANGE = signed_range(32)
INT64_RANGE = signed_range(64)
UINT8_RANGE  = unsigned_range(8)
UINT16_RANGE = unsigned_range(16)
UINT32_RANGE = unsigned_range(32)
UINT64_RANGE = unsigned_range(64)

RANGES = {
    "byte": UINT8_RANGE,
    "uint8": UINT8_RANGE,
    "int8": INT8_RANGE,
    "uint16": UINT16_RANGE,
    "int16": INT16_RANGE,
    "uint32": UINT32_RANGE,
    "int32": INT32_RANGE,
    "uint64": UINT64_RANGE,
    "int64": INT64_RANGE,
}

def filler(ch, n):
    """Create an bytearray consisting of `n` `ch`s.

    Parameters
    ----------
    ch: int (0 <= ch <= 255)
        fill char
    n: int
        repetition count

    Returns
    -------
    bytearray
    """
    if not isinstance(ch, int):
        raise TypeError("ch must be of type int")
    if not (0 <= ch < 256):
        raise ValueError("ch must be between 0 and 255")
    if not isinstance(n, int):
        raise TypeError("n must be of type int")
    if n < 1:
        raise ValueError("n must be >= 1")
    return bytearray([ch] * n)


def _data_converter(data):
    if isinstance(data, bytearray):
        pass    # no conversion needed.
    elif isinstance(data, int):
        raise ValueError("single int not permitted")
    elif isinstance(data, str):
        if PYTHON_VERSION.major == 3 :
            data = bytearray(data, encoding = "ascii")
        else:
            data = bytearray(data)
    elif isinstance(data, array) and data.typecode != 'B':
        if PYTHON_VERSION.major == 3:
            data = bytearray(data.tobytes())
        else:
            data = bytearray(data.tostring())
    elif isinstance(data, Section):
        data = copy(data.data)    # just copy data from other section.
    else:
        try:
            data = bytearray(data)
        except Exception:
            raise ValueError("cannot convert '{}' to bytearray()".format(data))
    return data


@attr.s(repr = False, eq = True, order = True)
class Section(object):
    """Manage sections.

    A section is a continuous block of bytes, with a start-address and known length.

    """
    start_address = attr.ib(type = int, eq = True, order = True, default = 0)
    data = attr.ib(default = bytearray(), converter = _data_converter, eq = True, order = True)

    def __attrs_post_init__(self):
        self.repr = reprlib.Repr()
        self.repr.maxstring = 64
        self.repr.maxother = 64

    def __iter__(self):
        yield self

    def hexdump(self, fp = sys.stdout):
        dumper = hexdump.CanonicalDumper(fp)
        dumper.dump_data(self)

    def tobytes(self):
        if PYTHON_VERSION.major == 3:
            return  array('B', self.data).tobytes()
        else:
            return  array('B', self.data).tostring()

    def tolist(self):
        return  array('B', self.data).tolist()

    def _verify_dtype(self, dtype):
        """
        """
        dtype = dtype.lower().strip()
        if dtype == "byte":
            return "uint8", "le"    # Completly arbitrary,
        if not "_" in dtype or not (dtype.endswith("_le") or dtype.endswith("_be")):
                print("DTYPE:", dtype)
                raise TypeError("dtype must be suffixed with '_be' or '_le'")
        match = DTYPE.match(dtype)
        if not match:
            raise TypeError("Invalid datatype '{}'".format(dtype))
        return dtype.split("_")

    def _getformat(self, dtype, length = 1):
        """
        """
        fmt, bo = self._verify_dtype(dtype)

        if length > 1:
            return "{}{}{}".format(BYTEORDER.get(bo), length, FORMATS.get(fmt))
        else:
            return "{}{}".format(BYTEORDER.get(bo), FORMATS.get(fmt))

    def read(self, addr, length, **kws):
        """
        Parameters
        ----------
        addr: int

        length: int
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("read() access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError("read() access out of bounds.")
        data = self.data[offset : offset + length]
        return data

    def write(self, addr, data, **kws):
        """
        Parameters
        ----------
        addr: int

        length: int

        data: array-like
        """
        length = len(data)
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("write() access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError("write() access out of bounds.")
        self.data[offset : offset + length] = data

    def read_numeric(self, addr, dtype, **kws):
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("read_numeric() access out of bounds.")
        fmt = self._getformat(dtype)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError("read_numeric() access out of bounds.")
        data = self.data[offset : offset + data_size]
        if 'bit_mask' in kws:
            bit_mask = kws.pop("bit_mask")
            data = self.apply_bitmask(data, dtype, bit_mask)
        return struct.unpack(fmt, data)[0]

    def apply_bitmask(self, data, dtype, bit_mask):
        """
        """
        dtype, byteorder = dtype.lower().strip().split("_")
        byteorder = "little" if byteorder == "le" else "big"
        type_size = TYPE_SIZES.get(dtype)
        data_size = len(data)
        tmp = int.from_bytes(data, byteorder, signed = False)
        tmp &= bit_mask
        return tmp.to_bytes(data_size, byteorder, signed = False)

    def write_numeric(self, addr, value, dtype, **kws):
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("write_numeric() access out of bounds.")
        fmt = self._getformat(dtype)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError("write_numeric() access out of bounds.")
        if 'bit_mask' in kws:
            bit_mask = kws.pop("bit_mask")
        self.data[offset : offset + data_size] = struct.pack(fmt, value)

    def read_numeric_array(self, addr, length, dtype, **kws):
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("read_numeric_array() access out of bounds.")
        fmt = self._getformat(dtype, length)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError("read_numeric_array() access out of bounds.")
        data = self.data[offset : offset + data_size]
        return struct.unpack(fmt, data)

    def write_numeric_array(self, addr, data, dtype, **kws):
        if not hasattr(data, '__iter__'):
            raise TypeError("data must be iterable")
        length = len(data)
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("write_numeric_array() access out of bounds.")
        fmt = self._getformat(dtype, length)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError("write_numeric_array() access out of bounds.")
        self.data[offset : offset + data_size] = struct.pack(fmt, *data)

    def read_string(self, addr, encoding = "latin1", length = -1, **kws):
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("read_string() access out of bounds.")
        if length == -1:
            pos = self.data[offset : ].find(b'\x00')
        else:
            pos = length
        if pos == -1:
            raise TypeError("Unterminated String!!!")   # TODO: Testcase.
        return self.data[offset : offset + pos].decode(encoding = encoding)

    def write_string(self, addr, value, encoding = "latin1", **kws):
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("write_string() access out of bounds.")
        if PYTHON_VERSION.major == 3:
            self.data[offset : offset +  len(value)] = bytes(value, encoding = encoding)
        else:
            self.data[offset : offset +  len(value)] = bytes(value)
        self.data[offset +  len(value)] = 0

    def write_ndarray(self, addr, array, order = None, **kws):
        """

        """
        try:
            import numpy as np
        except ImportError:
            raise FeatureNotAvailableError("write_ndarray() requires Numpy.")
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("write_ndarray() access out of bounds.")
        if not isinstance(array, np.ndarray):
            raise TypeError("array must be of type numpy.ndarray.")
        data_size = array.nbytes
        if offset + data_size > self.length:
            raise InvalidAddressError("write_ndarray() access out of bounds.")
        self.data[offset : offset + data_size] = array.tobytes()

    def read_ndarray(self, addr, length, dtype, shape = None, order = None, **kws):
        """

        """
        try:
            import numpy as np
        except ImportError:
            raise FeatureNotAvailableError("read_ndarray() requires Numpy.")
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError("read_ndarray() access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError("read_ndarray() access out of bounds.")

        """
        If the buffer has data that is not in machine byte-order, this should
        be specified as part of the data-type, e.g.::

          >>> dt = np.dtype(int)
          >>> dt = dt.newbyteorder('>')
          >>> np.frombuffer(buf, dtype=dt)
        """
        type_, byte_order = self._verify_dtype(dtype)
        dt = np.dtype(type_)
        dt = dt.newbyteorder(BYTEORDER.get(byte_order))
        arr = np.frombuffer(self.data[offset : offset + length], dtype = dt).reshape(shape)
        if order == "F":
            return arr.T    # Fortran deposit, i.e. col-maj means transposition.
        else:
            return arr


    """
    def write_timestamp():
        pass

    def read_timestamp():
        pass
    """

    def find(self, expr, addr = -1):
        for item in re.finditer(bytes(expr), self.data):
            yield (self.start_address + item.start(), item.end()- item.start())

    def __repr__(self):
        return "Section(address = 0X{0:08X}, length = {1:d}, data = {2})".format(
            self.start_address,
            self.length,
            self.repr.repr(memoryview(self.data).tobytes())
        )

    def __len__(self):
        return len(self.data)

    @property
    def length(self):
        return len(self)

    def __contains__(self, addr):
        return self.start_address <= addr < (self.start_address + self.length)

    @property
    def address(self):  # Alias
        return self.start_address


def join_sections(sections):
    if isinstance(sections, SortedList):
        result_sections = SortedList(key = attrgetter("start_address"))
    else:
        result_sections = []
    prev_section = Section()
    while sections:
        section = sections.pop(0)
        if not isinstance(section, Section):
            raise TypeError("'{}' is not a 'Section' instance", section)
        if section.start_address == prev_section.start_address + prev_section.length and result_sections:
            last_segment = result_sections[-1]
            last_segment.data.extend(section.data)
        else:
            # Create a new section.
            if isinstance(sections, SortedList):
                result_sections.add(Section(section.start_address, section.data))
            else:
                result_sections.append(Section(section.start_address, section.data))
        prev_section = section
    if result_sections:
        return result_sections
    else:
        if isinstance(sections, SortedList):
            return SortedList(key = attrgetter("start_address"))
        else:
            return []
