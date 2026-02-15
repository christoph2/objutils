#!/usr/bin/env python
"""Section: Continuous Memory Regions with Address and Data.

This module provides the `Section` class, a fundamental building block of the objutils
library. A Section represents a contiguous block of memory with a start address and
associated data, similar to sections in object files (ELF, PE/COFF, etc.).

Overview
--------
Every binary file format (Intel HEX, Motorola S-Records, ELF, PE/COFF) organizes
data into sections - continuous memory regions that are loaded at specific addresses.
The Section class provides:

- **Memory abstraction**: Start address + data bytes
- **Typified access**: Read/write integers, floats, arrays, strings with explicit endianness
- **Validation**: Automatic bounds checking for all accesses
- **Conversion**: Create sections from strings, bytearrays, arrays, or other sections
- **Joining**: Automatically merge consecutive sections
- **Hexdump**: Display contents in canonical hexadecimal format
- **Diffing**: Compare sections with sequence matching

Architecture
------------
::

    Section
    ├── start_address: int           # Memory address where section begins
    ├── data: bytearray              # Actual bytes (mutable)
    └── name: str                    # Optional identifier

    Typified Access:
    ├── read/write(addr, length)             # Raw bytes
    ├── read_numeric/write_numeric(addr, dtype)   # Single values
    ├── read_numeric_array/write_numeric_array()  # Arrays
    ├── read_string/write_string()                # Null-terminated strings
    └── read_ndarray/write_ndarray()              # NumPy arrays

Usage Examples
--------------
**Creating sections from various sources**::

    from objutils import Section

    # From bytes
    s1 = Section(start_address=0x1000, data=b"Hello")

    # From string (ASCII encoded)
    s2 = Section(0x2000, "World")

    # From bytearray
    s3 = Section(0x3000, bytearray([0x01, 0x02, 0x03]))

    # From array
    from array import array
    s4 = Section(0x4000, array('B', [0xFF, 0xFE, 0xFD]))

**Typified access with explicit endianness**::

    # Write integers with explicit byte order
    section = Section(0x1000, bytearray(100))
    section.write_numeric(0x1000, 0x12345678, "uint32_le")  # Little-endian
    section.write_numeric(0x1004, 0x87654321, "uint32_be")  # Big-endian

    # Read back
    value_le = section.read_numeric(0x1000, "uint32_le")  # 0x12345678
    value_be = section.read_numeric(0x1004, "uint32_be")  # 0x87654321

    # Floating-point values
    section.write_numeric(0x1008, 3.14159, "float32_le")
    pi = section.read_numeric(0x1008, "float32_le")

**Array operations**::

    # Write array of 16-bit values
    data = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
    section.write_numeric_array(0x2000, data, "uint16_be")

    # Read array back
    values = section.read_numeric_array(0x2000, length=4, dtype="uint16_be")

**String operations**::

    # Write null-terminated string
    section.write_string(0x3000, "Hello World", encoding="utf-8")

    # Read null-terminated string
    text = section.read_string(0x3000, encoding="utf-8")  # "Hello World"

**NumPy array support**::

    import numpy as np

    # Write 2D array (C-order by default)
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
    section.write_ndarray(0x4000, arr)

    # Write Fortran-ordered array
    section.write_ndarray(0x5000, arr, order="F")

    # Read back with shape
    arr2 = section.read_ndarray(0x4000, length=12, dtype="uint16_le", shape=(2, 3))

**Joining consecutive sections**::

    from objutils.section import join_sections

    sections = [
        Section(0x1000, b"Hello"),
        Section(0x1005, b"World"),  # Consecutive with previous
        Section(0x2000, b"Gap"),     # Not consecutive
    ]

    joined = join_sections(sections)
    # Result: [Section(0x1000, b"HelloWorld"), Section(0x2000, b"Gap")]

**Hexdump display**::

    section = Section(0x1000, b"Hello World\\x00" * 3)
    section.hexdump()
    # Output:
    # 00001000  48 65 6c 6c 6f 20 57 6f  72 6c 64 00 48 65 6c 6c  |Hello World.Hell|
    # 00001010  6f 20 57 6f 72 6c 64 00  48 65 6c 6c 6f 20 57 6f  |o World.Hello Wo|
    # 00001020  72 6c 64 00                                       |rld.|

Data Type Specification
-----------------------
All numeric read/write methods require explicit endianness specification:

**Supported types**:
- ``uint8``, ``int8``          - 8-bit integers (endianness not needed for single bytes)
- ``uint16_le``, ``uint16_be`` - 16-bit integers
- ``int16_le``, ``int16_be``   - 16-bit signed integers
- ``uint32_le``, ``uint32_be`` - 32-bit integers
- ``int32_le``, ``int32_be``   - 32-bit signed integers
- ``uint64_le``, ``uint64_be`` - 64-bit integers
- ``int64_le``, ``int64_be``   - 64-bit signed integers
- ``float32_le``, ``float32_be`` - 32-bit floating-point
- ``float64_le``, ``float64_be`` - 64-bit floating-point

**Note**: Unlike some libraries, objutils *requires* explicit endianness to avoid
ambiguity in cross-platform embedded systems development.

Integration
-----------
Section objects are created by:
- **Image** class (objutils.image) - Contains multiple sections
- **File parsers** (ihex, srec, ELF, PE/COFF readers) - Parse binary formats into sections
- **User code** - Manual section creation for testing or manipulation

See Also
--------
- :mod:`objutils.image` - Image class that contains multiple sections
- :mod:`objutils.hexfile` - Base classes for format readers/writers
- :mod:`objutils.hexdump` - Hexadecimal dump formatting
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <github.com/Christoph2,
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

import re
import reprlib
import struct
import sys
from array import array
from collections import namedtuple
from copy import copy
from dataclasses import dataclass, field
from functools import reduce
from operator import attrgetter, mul
from typing import Any, Union

import numpy as np

import objutils.hexdump as hexdump
from objutils.exceptions import InvalidAddressError


try:
    from .hexfiles_ext import SequenceMatcher  # noqa: F401
except ImportError:
    print("Error: cannot import `SequenceMatcher` from C++-extension, falling back to `difflib`")
    from difflib import SequenceMatcher  # noqa: F401


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
    "uint8": 1,
    "int8": 1,
    "uint16": 2,
    "int16": 2,
    "uint32": 4,
    "int32": 4,
    "uint64": 8,
    "int64": 8,
    "float32": 4,
    "float64": 8,
}


BYTEORDER = {
    "le": "<",
    "be": ">",
}

TypeInformation = namedtuple("TypeInformation", "type byte_order size")

DTYPE = re.compile(
    r"""
      (?:(?P<uns>u)?int(?P<len>8 | 16 | 32 | 64)(?P<sep>[-/_:])(?P<end> be | le))
    | (?P<byte>byte)
    | (?P<flt>float)(?P<flen>32 | 64)""",
    re.IGNORECASE | re.VERBOSE,
)

NumberRange = namedtuple("NumberRange", "lower upper")


def signed_range(x: int) -> NumberRange:
    return NumberRange(*(int(-(2**x / 2)), int((2**x / 2) - 1)))


def unsigned_range(x: int) -> NumberRange:
    return NumberRange(*(0, int((2**x) - 1)))


INT8_RANGE = signed_range(8)
INT16_RANGE = signed_range(16)
INT32_RANGE = signed_range(32)
INT64_RANGE = signed_range(64)
UINT8_RANGE = unsigned_range(8)
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


def filler(ch: int, n: int) -> bytearray:
    """Create a bytearray consisting of ``n`` repetitions of ``ch``.

    Utility function for creating filled byte arrays, useful for padding
    or initializing memory regions.

    Args:
        ch: Fill character (0 <= ch <= 255)
        n: Number of repetitions (must be >= 1)

    Returns:
        bytearray of length ``n`` filled with ``ch``

    Raises:
        TypeError: If ``ch`` or ``n`` are not integers
        ValueError: If ``ch`` is out of range or ``n`` < 1

    Example::

        # Create 16 bytes of 0xFF padding
        padding = filler(0xFF, 16)
        # Result: bytearray(b'\\xff\\xff\\xff...')

        # Create 8 bytes of zeros
        zeros = filler(0x00, 8)
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


def _data_converter(data: Union[str, bytearray, array, Any]) -> bytearray:
    if isinstance(data, bytearray):
        pass  # no conversion needed.
    elif isinstance(data, int):
        raise ValueError("single int not permitted")
    elif isinstance(data, str):
        data = bytearray(data, encoding="ascii")
    elif isinstance(data, array) and data.typecode != "B":
        data = bytearray(data.tobytes())
    elif isinstance(data, Section):
        data = copy(data.data)  # just copy data from other section.
    else:
        try:
            data = bytearray(data)
        except Exception as e:
            raise ValueError(f"cannot convert {data!r} to bytearray()") from e
    return data


def fortran_array_from_buffer(arr: bytearray, shape: tuple, dtype: str) -> np.ndarray:
    """Converts a bytearray to a Fortran-ordered numpy array."""
    return np.frombuffer(arr, dtype=dtype).reshape(shape, order="F")


def fortran_array_to_buffer(array: np.ndarray) -> bytearray:
    shape = array.shape
    if array.ndim <= 2:
        return array.tobytes("F")
    else:
        lhs = shape[:-2]
        num_slices = reduce(mul, lhs, 1)
        rhs = shape[-2:]
        slice_len = reduce(mul, rhs, 1)
        rs_arr = array.reshape(num_slices, *rhs)
        offset = 0
        result = bytearray(array.nbytes)
        for idx in range(num_slices):
            slice = rs_arr[idx]
            result[offset : offset + slice_len] = slice.T.tobytes()
            offset += slice_len
        return result


@dataclass(repr=False, order=True)
class Section:
    """Continuous block of bytes with start address and known length.

    A Section represents a contiguous memory region, the fundamental building block
    for all binary file formats. Every section has a start address, data bytes, and
    optional name. Sections can be:

    - Created from strings, bytes, bytearrays, arrays, or other sections
    - Accessed with typified read/write operations (integers, floats, arrays, strings)
    - Joined with consecutive sections automatically
    - Displayed as hexdump
    - Compared/diffed with other sections

    All numeric operations require explicit endianness (``_le`` or ``_be`` suffix)
    to avoid ambiguity in cross-platform embedded development.

    Attributes:
        start_address: Memory address where section begins (default: 0)
        data: Byte array containing section data (mutable, default: empty bytearray)
        name: Optional section name/identifier (default: empty string)

    Properties:
        length: Number of bytes in section (read-only, equals ``len(data)``)
        address: Alias for ``start_address`` (read-only)

    Examples:
        Create section from bytes::

            section = Section(0x1000, b"Hello World")
            print(len(section))  # 11
            print(0x1005 in section)  # True

        Typified access with explicit endianness::

            section = Section(0x1000, bytearray(100))
            section.write_numeric(0x1000, 0x12345678, "uint32_le")
            value = section.read_numeric(0x1000, "uint32_le")  # 0x12345678

        String operations::

            section.write_string(0x2000, "Test", encoding="utf-8")
            text = section.read_string(0x2000)  # "Test"

        Check if address is in section::

            if 0x1050 in section:
                data = section.read(0x1050, 10)

    Note:
        Sections are hashable and orderable by start address. Two sections
        are equal if they have the same start address, data, and name.
    """

    start_address: int = field(hash=True, compare=True, default=0)
    data: bytearray = field(default_factory=bytearray, compare=True, hash=True)
    name: str = field(default="", compare=True, hash=True)

    def __post_init__(self):
        self.repr = reprlib.Repr()
        self.repr.maxstring = 64
        self.repr.maxother = 64
        self.data = _data_converter(self.data)

    def __iter__(self):
        yield self

    def hexdump(self, fp=sys.stdout):
        """Display section contents in canonical hexdump format.

        Outputs a hexadecimal dump similar to ``hexdump -C`` on Unix systems,
        showing address, hex bytes, and ASCII representation.

        Args:
            fp: File object to write output to (default: sys.stdout)

        Example::

            section = Section(0x1000, b"Hello World!")
            section.hexdump()
            # Output:
            # 00001000  48 65 6c 6c 6f 20 57 6f  72 6c 64 21              |Hello World!|
        """
        dumper = hexdump.CanonicalDumper(fp)
        dumper.dump_data(self)

    def tobytes(self) -> bytes:
        return array("B", self.data).tobytes()

    def tolist(self) -> list[int]:
        return array("B", self.data).tolist()

    def _verify_dtype(self, dtype: str) -> str:
        """ """
        dtype = dtype.lower().strip()
        if dtype == "byte":
            return "uint8", "le"  # Completly arbitrary,
        if "_" not in dtype or not (dtype.endswith("_le") or dtype.endswith("_be")):
            print("DTYPE:", dtype)
            raise TypeError("dtype must be suffixed with '_be' or '_le'")
        match = DTYPE.match(dtype)
        if not match:
            raise TypeError(f"Invalid datatype {dtype!r}")
        return dtype.split("_")

    def _getformat(self, dtype: str, length: int = 1) -> str:
        """ """
        fmt, bo = self._verify_dtype(dtype)

        if length > 1:
            return f"{BYTEORDER.get(bo)}{length}{FORMATS.get(fmt)}"
        else:
            return f"{BYTEORDER.get(bo)}{FORMATS.get(fmt)}"

    def read(self, addr: int, length: int, **kws) -> bytes:
        """Read raw bytes from section at specified address.

        Args:
            addr: Absolute memory address to read from
            length: Number of bytes to read
            **kws: Reserved for future extensions

        Returns:
            bytes object containing the read data

        Raises:
            InvalidAddressError: If address is out of bounds or read would exceed section

        Example::

            section = Section(0x1000, b"Hello World")
            data = section.read(0x1000, 5)  # b"Hello"
            data = section.read(0x1006, 5)  # b"World"
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"read(0x{addr:08x}) access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError(f"read(0x{addr:08x}) access out of bounds.")
        data = self.data[offset : offset + length]
        return data

    def write(self, addr: int, data: bytes, **kws) -> None:
        """Write raw bytes to section at specified address.

        Args:
            addr: Absolute memory address to write to
            data: Bytes to write
            **kws: Reserved for future extensions

        Raises:
            InvalidAddressError: If address is out of bounds or write would exceed section

        Example::

            section = Section(0x1000, bytearray(100))
            section.write(0x1000, b"Hello")
            section.write(0x1010, b"World")
        """
        length = len(data)
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"write(0x{addr:08x}) access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError(f"write(0x{addr:08x}) access out of bounds.")
        self.data[offset : offset + length] = data

    def read_numeric(self, addr: int, dtype: str, **kws) -> Union[int, float]:
        """Read a single numeric value with explicit endianness.

        Reads an integer or floating-point value from the specified address.
        Endianness must be explicitly specified with ``_le`` or ``_be`` suffix.

        Args:
            addr: Absolute memory address to read from
            dtype: Data type with endianness (e.g., ``"uint32_le"``, ``"float64_be"``)
            **kws: Optional keyword arguments:
                - bit_mask (int): Apply bitmask to result before returning

        Returns:
            int or float depending on dtype

        Raises:
            InvalidAddressError: If address is out of bounds
            TypeError: If dtype is invalid or missing endianness suffix

        Supported types:
            - ``uint8``, ``int8`` (endianness optional for single bytes)
            - ``uint16_le``, ``uint16_be``, ``int16_le``, ``int16_be``
            - ``uint32_le``, ``uint32_be``, ``int32_le``, ``int32_be``
            - ``uint64_le``, ``uint64_be``, ``int64_le``, ``int64_be``
            - ``float32_le``, ``float32_be``
            - ``float64_le``, ``float64_be``

        Example::

            section = Section(0x1000, bytearray(100))

            # Write and read 32-bit little-endian integer
            section.write_numeric(0x1000, 0x12345678, "uint32_le")
            value = section.read_numeric(0x1000, "uint32_le")  # 0x12345678

            # With bitmask to extract specific bits
            value = section.read_numeric(0x1000, "uint32_le", bit_mask=0xFF00)
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"read_numeric(0x{addr:08x}) access out of bounds.")
        fmt = self._getformat(dtype)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError(f"read_numeric(0x{addr:08x}) access out of bounds.")
        data = self.data[offset : offset + data_size]
        if "bit_mask" in kws:
            bit_mask = kws.pop("bit_mask")
            data = self.apply_bitmask(data, dtype, bit_mask)
        return struct.unpack(fmt, data)[0]

    def apply_bitmask(self, data: bytes, dtype: str, bit_mask: int) -> bytes:
        """ """
        dtype, byteorder = dtype.lower().strip().split("_")
        byteorder = "little" if byteorder == "le" else "big"
        # type_size = TYPE_SIZES.get(dtype)
        data_size = len(data)
        tmp = int.from_bytes(data, byteorder, signed=False)
        tmp &= bit_mask
        return tmp.to_bytes(data_size, byteorder, signed=False)

    def write_numeric(self, addr: int, value: Union[int, float], dtype: str, **kws) -> None:
        """Write a single numeric value with explicit endianness.

        Writes an integer or floating-point value to the specified address.
        Endianness must be explicitly specified with ``_le`` or ``_be`` suffix.

        Args:
            addr: Absolute memory address to write to
            value: Integer or float value to write
            dtype: Data type with endianness (e.g., ``"uint32_le"``, ``"float64_be"``)
            **kws: Optional keyword arguments (reserved for future use)

        Raises:
            InvalidAddressError: If address is out of bounds
            TypeError: If dtype is invalid or missing endianness suffix

        Example::

            section = Section(0x1000, bytearray(100))

            # Write different sized values
            section.write_numeric(0x1000, 0x12, "uint8")
            section.write_numeric(0x1001, 0x1234, "uint16_le")
            section.write_numeric(0x1003, 0x12345678, "uint32_be")
            section.write_numeric(0x1007, 3.14159, "float32_le")
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"write_numeric(0x{addr:08x}) access out of bounds.")
        fmt = self._getformat(dtype)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError(f"write_numeric(0x{addr:08x}) access out of bounds.")
        if "bit_mask" in kws:
            bit_mask = kws.pop("bit_mask")  # noqa: F841

        self.data[offset : offset + data_size] = struct.pack(fmt, value)

    def read_numeric_array(self, addr: int, length: int, dtype: str, **kws) -> Union[list[int], list[float]]:
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"read_numeric_array(0x{addr:08x}) access out of bounds.")
        fmt = self._getformat(dtype, length)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError(f"read_numeric_array(0x{addr:08x}) access out of bounds.")
        data = self.data[offset : offset + data_size]
        return struct.unpack(fmt, data)

    def write_numeric_array(self, addr: int, data: Union[list[int], list[float]], dtype: str, **kws) -> None:
        if not hasattr(data, "__iter__"):
            raise TypeError("data must be iterable")
        length = len(data)
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"write_numeric_array(0x{addr:08x}) access out of bounds.")
        fmt = self._getformat(dtype, length)
        data_size = struct.calcsize(fmt)
        if offset + data_size > self.length:
            raise InvalidAddressError(f"write_numeric_array(0x{addr:08x}) access out of bounds.")
        self.data[offset : offset + data_size] = struct.pack(fmt, *data)

    def read_string(self, addr: int, encoding: str = "latin1", length: int = -1, **kws) -> str:
        """Read a null-terminated or fixed-length string from section.

        Args:
            addr: Absolute memory address to read from
            encoding: Character encoding (default: "latin1")
            length: Maximum length in bytes, or -1 for null-terminated (default: -1)
            **kws: Reserved for future extensions

        Returns:
            Decoded string (without null terminator)

        Raises:
            InvalidAddressError: If address is out of bounds
            TypeError: If string is not null-terminated and length is -1

        Example::

            section = Section(0x1000, bytearray(100))

            # Write and read null-terminated string
            section.write_string(0x1000, "Hello World")
            text = section.read_string(0x1000)  # "Hello World"

            # Read with encoding
            section.write_string(0x2000, "Grüße", encoding="utf-8")
            text = section.read_string(0x2000, encoding="utf-8")  # "Grüße"

            # Read fixed-length string
            text = section.read_string(0x1000, length=5)  # "Hello"
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"read_string(0x{addr:08x}) access out of bounds.")
        if length == -1:
            pos = self.data[offset:].find(b"\x00")
        else:
            pos = length
        if pos == -1:
            raise TypeError("Unterminated String!!!")  # TODO: Testcase.
        return self.data[offset : offset + pos].decode(encoding=encoding)

    def write_string(self, addr: int, value: str, encoding: str = "latin1", **kws):
        """Write a null-terminated string to section.

        Writes the string with an appended null terminator (0x00 byte).

        Args:
            addr: Absolute memory address to write to
            value: String to write
            encoding: Character encoding (default: "latin1")
            **kws: Reserved for future extensions

        Raises:
            InvalidAddressError: If address is out of bounds

        Example::

            section = Section(0x1000, bytearray(100))

            # Write ASCII string
            section.write_string(0x1000, "Hello")

            # Write UTF-8 string
            section.write_string(0x2000, "Grüße", encoding="utf-8")
        """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"write_string(0x{addr:08x}) access out of bounds.")
        self.data[offset : offset + len(value)] = bytes(value, encoding=encoding)
        self.data[offset + len(value)] = 0

    def write_ndarray(self, addr: int, array: np.ndarray, order: str = None, **kws) -> None:
        """ """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"write_ndarray(0x{addr:08x}) access out of bounds.")
        if not isinstance(array, np.ndarray):
            raise TypeError("array must be of type numpy.ndarray.")
        data_size = array.nbytes
        if offset + data_size > self.length:
            raise InvalidAddressError(f"write_ndarray(0x{addr:08x}) access out of bounds.")
        if order is not None and order == "F":
            self.data[offset : offset + data_size] = fortran_array_to_buffer(array=array)
        else:
            self.data[offset : offset + data_size] = array.tobytes()

    def read_ndarray(self, addr: int, length: int, dtype: str, shape: tuple = None, order: str = None, **kws) -> np.ndarray:
        """ """
        offset = addr - self.start_address
        if offset < 0:
            raise InvalidAddressError(f"read_ndarray(0x{addr:08x}) access out of bounds.")
        if offset + length > self.length:
            raise InvalidAddressError(f"read_ndarray(0x{addr:08x}) access out of bounds.")
        type_, byte_order = self._verify_dtype(dtype)
        dt = np.dtype(type_)
        dt = dt.newbyteorder(BYTEORDER.get(byte_order))
        if order is not None and order == "F":
            arr = fortran_array_from_buffer(arr=self.data[offset : offset + length], shape=shape, dtype=dt)
        else:
            arr = np.frombuffer(self.data[offset : offset + length], dtype=dt).reshape(shape)
        return arr

    """
    def write_timestamp():
        pass

    def read_timestamp():
        pass
    """

    def find(self, expr: str, addr: int = -1) -> int:
        for item in re.finditer(bytes(expr), self.data):
            yield (self.start_address + item.start(), item.end() - item.start())

    def __repr__(self) -> str:
        return "Section(address = 0X{:08X}, length = {:d}, data = {})".format(
            self.start_address,
            self.length,
            self.repr.repr(memoryview(self.data).tobytes()),
        )

    def __len__(self) -> int:
        return len(self.data)

    @property
    def length(self) -> int:
        return len(self)

    def __contains__(self, addr) -> bool:
        return self.start_address <= addr < (self.start_address + self.length)

    @property
    def address(self) -> int:  # Alias
        return self.start_address


def join_sections(sections: list[Section]) -> list[Section]:
    """Join consecutive sections into contiguous blocks.

    Merges sections that are adjacent in memory (where one section's end address
    equals the next section's start address) into single sections. Non-consecutive
    sections remain separate.

    The function sorts sections by start address before processing.

    Args:
        sections: List of Section objects to join

    Returns:
        New list of Section objects with consecutive sections merged

    Raises:
        TypeError: If any element is not a Section instance

    Example::

        from objutils import Section
        from objutils.section import join_sections

        sections = [
            Section(0x1000, b"Hello"),
            Section(0x1005, b" "),      # Consecutive with previous
            Section(0x1006, b"World"),  # Consecutive with previous
            Section(0x2000, b"Gap"),    # Not consecutive - separate region
        ]

        joined = join_sections(sections)
        # Result: [
        #     Section(0x1000, b"Hello World"),
        #     Section(0x2000, b"Gap")
        # ]

    Note:
        This function is automatically called when creating an Image with
        ``join=True`` parameter.
    """
    result_sections = []
    sections.sort(key=attrgetter("start_address"))
    prev_section = Section()
    for section in sections:
        if not isinstance(section, Section):
            raise TypeError("'{}' is not a 'Section' instance", section)
        if section.start_address == prev_section.start_address + prev_section.length and result_sections:
            last_segment = result_sections[-1]
            last_segment.data.extend(section.data)
        else:
            # Create a new section.
            result_sections.append(Section(section.start_address, section.data))
        prev_section = section
    if result_sections:
        return result_sections
    else:
        return []
