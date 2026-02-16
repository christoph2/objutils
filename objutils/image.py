#!/usr/bin/env python
"""Image: Container for Multiple Memory Sections with Typified Access.

This module provides the `Image` class, the primary abstraction for working with
binary data in objutils. An Image is a collection of `Section` objects representing
potentially non-contiguous memory regions, along with metadata and powerful operations
for reading and writing typed data.

Overview
--------
While a Section represents a single continuous memory region, an Image represents
an entire binary file or memory layout composed of multiple sections. The Image class
provides:

- **Section management**: Automatic joining/merging of consecutive sections
- **Typified access**: Read/write integers, floats, arrays, strings with explicit endianness
- **Address validation**: Automatic routing of operations to correct section
- **Format conversion**: Central abstraction for converting between file formats
- **Metadata support**: Arbitrary key-value metadata storage
- **Diffing**: Compare images section-by-section

Every hex file parser (Intel HEX, Motorola S-Records, ELF, PE/COFF, etc.) produces
an Image object. The Image abstraction enables format-agnostic manipulation of binary
data.

Architecture
------------
::

    Image
    ├── sections: list[Section]      # Sorted by start address
    ├── meta: dict[str, Any]         # Arbitrary metadata
    └── join: bool                   # Auto-merge consecutive sections

    Typified Access (delegates to Section):
    ├── read/write(addr, length)              # Raw bytes
    ├── read_numeric/write_numeric(addr, dtype)    # Single values
    ├── read_numeric_array/write_numeric_array()   # Arrays
    ├── read_string/write_string()                 # Null-terminated strings
    └── read_ndarray/write_ndarray()               # NumPy arrays

Format Conversion Pattern
--------------------------
The Image class is the key to format conversion in objutils. The standard idiom::

    import objutils

    # Load from one format
    img = objutils.load("srec", "firmware.srec")

    # Manipulate if needed
    img.write_numeric(0x1000, 0x12345678, "uint32_le")

    # Save to another format
    objutils.dump("ihex", "firmware.hex", img)

All format readers produce Image objects, and all format writers consume them.
This enables seamless conversion between 13+ different file formats.

Usage Examples
--------------
**Creating images**::

    from objutils import Image, Section

    # Empty image
    img = Image()

    # From single section
    section = Section(0x1000, b"Hello World")
    img = Image(section)

    # From multiple sections (auto-joined if consecutive)
    sections = [
        Section(0x1000, b"Hello"),
        Section(0x1005, b" "),      # Consecutive with previous
        Section(0x1006, b"World"),  # Consecutive with previous
    ]
    img = Image(sections, join=True)  # Results in single merged section

    # Disable auto-joining
    img = Image(sections, join=False)  # Keeps sections separate

**Typified access with explicit endianness**::

    from objutils import Image, Section

    # Create image with data
    section = Section(0x1000, bytearray(1000))
    img = Image(section)

    # Write different types with explicit endianness
    img.write_numeric(0x1000, 0x12, "uint8")
    img.write_numeric(0x1001, 0x1234, "uint16_le")
    img.write_numeric(0x1003, 0x12345678, "uint32_be")
    img.write_numeric(0x1007, 3.14159, "float32_le")

    # Read values back
    byte_val = img.read_numeric(0x1000, "uint8")        # 0x12
    word_le = img.read_numeric(0x1001, "uint16_le")     # 0x1234
    dword_be = img.read_numeric(0x1003, "uint32_be")    # 0x12345678
    float_val = img.read_numeric(0x1007, "float32_le")  # 3.14159

**Array operations**::

    # Write array of values
    data = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
    img.write_numeric_array(0x2000, data, "uint16_be")

    # Read array back
    values = img.read_numeric_array(0x2000, length=4, dtype="uint16_be")

**String operations**::

    # Write null-terminated string
    img.write_string(0x3000, "Firmware v1.2.3", encoding="utf-8")

    # Read null-terminated string
    version = img.read_string(0x3000, encoding="utf-8")

**NumPy array support**::

    import numpy as np

    # Create 2D array
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)

    # Write to image (C-order by default)
    img.write_ndarray(0x4000, arr)

    # Write Fortran-ordered
    img.write_ndarray(0x5000, arr, order="F")

    # Read back with shape
    arr2 = img.read_ndarray(0x4000, length=12, dtype="uint16_le", shape=(2, 3))

**Format conversion**::

    import objutils

    # Intel HEX to Motorola S-Record
    img = objutils.load("ihex", "bootloader.hex")
    objutils.dump("srec", "bootloader.srec", img)

    # ELF to TI-TXT
    img = objutils.load("elf", "firmware.elf")
    objutils.dump("titxt", "firmware.txt", img)

**Working with metadata**::

    # Load with metadata
    img = objutils.load("ihex", "firmware.hex")

    # Access metadata (format-specific)
    if "start_address" in img.meta:
        entry_point = img.meta["start_address"]

    # Add custom metadata
    img.meta["version"] = "1.2.3"
    img.meta["build_date"] = "2025-01-15"

**Checking address coverage**::

    # Check if address is in any section
    if 0x1050 in img:
        data = img.read(0x1050, 16)

    # Iterate over sections
    for section in img:
        print(f"Section at 0x{section.start_address:08X}, "
              f"length {section.length}")

**Section management**::

    # Get section count
    num_sections = len(img.sections)

    # Get specific section by index
    first_section = img[0]

    # Get section containing address
    section = img.get_section(0x1050)

    # Insert new section
    new_section = Section(0x8000, b"New data")
    img.insert_section(new_section)

    # Join sections manually (if join=False initially)
    img.join_sections()

Data Type Specification
-----------------------
All numeric operations require explicit endianness to avoid ambiguity:

**Supported types**:
- ``uint8``, ``int8``          - 8-bit integers
- ``uint16_le``, ``uint16_be`` - 16-bit integers
- ``int16_le``, ``int16_be``   - 16-bit signed integers
- ``uint32_le``, ``uint32_be`` - 32-bit integers
- ``int32_le``, ``int32_be``   - 32-bit signed integers
- ``uint64_le``, ``uint64_be`` - 64-bit integers
- ``int64_le``, ``int64_be``   - 64-bit signed integers
- ``float32_le``, ``float32_be`` - 32-bit floating-point
- ``float64_le``, ``float64_be`` - 64-bit floating-point

**Rationale**: Explicit endianness is mandatory in objutils to prevent bugs in
cross-platform embedded systems development where target endianness differs from
host endianness.

Section Joining
---------------
When ``join=True`` (default), consecutive sections are automatically merged::

    sections = [
        Section(0x1000, b"AAA"),
        Section(0x1003, b"BBB"),  # Consecutive: 0x1000 + 3 = 0x1003
        Section(0x2000, b"CCC"),  # Gap: not consecutive
    ]
    img = Image(sections, join=True)
    # Result: 2 sections
    #   - Section(0x1000, b"AAABBB")
    #   - Section(0x2000, b"CCC")

This is useful when parsing file formats that represent data in small chunks
(like Intel HEX records) but you want to work with larger contiguous blocks.

Set ``join=False`` to preserve section boundaries as-is.

Integration
-----------
Image objects are created by:
- **File parsers**: All format readers (ihex, srec, ELF, PE/COFF, etc.)
- **objutils.load()**: High-level loading function
- **User code**: Manual image construction for testing or manipulation

Image objects are consumed by:
- **File writers**: All format writers
- **objutils.dump()**: High-level saving function
- **User code**: Application-specific processing

See Also
--------
- :mod:`objutils.section` - Section class for continuous memory regions
- :mod:`objutils.hexfile` - Base classes for format readers/writers
- :mod:`objutils.registry` - Format registration and load/dump functions

"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import enum
import sys
from bisect import bisect_right
from operator import attrgetter, eq
from typing import Any, Optional, Protocol, Union
from collections.abc import Iterable

from objutils.exceptions import InvalidAddressError
from objutils.section import Section, join_sections


# NOTE: Crypto hashes could be used for optimized comparison and storage.
# This would require adding a dependency on hashlib and implementing hash
# caching for sections. Consider implementing if performance becomes an issue
# with large images or frequent comparisons.


class AddressSpace(enum.IntEnum):
    """Address-space constants for different architecture widths.

    Attributes:
        AS_16: 16-bit address space.
        AS_24: 24-bit address space.
        AS_32: 32-bit address space.
        AS_64: 64-bit address space.
    """

    AS_16 = 0
    AS_24 = 1
    AS_32 = 2
    AS_64 = 3


class AddressFunction(Protocol):
    """Protocol for section address functions.

    Defines the interface that section methods must implement for
    address-based operations.
    """

    def __call__(self, addr: int, *args: Any, **kwargs: Any) -> Any:
        """Execute address-based operation.

        Args:
            addr: Target address.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Result of the operation.
        """
        ...


class Image:
    """Manage binary images composed of memory sections.

    An Image is a collection of :class:`Section` objects representing potentially
    non-contiguous memory regions, along with metadata. It provides the primary
    abstraction for working with binary data in objutils, enabling format-agnostic
    manipulation and conversion.

    The Image class automatically routes read/write operations to the appropriate
    section based on the target address, validates address ranges, and optionally
    merges consecutive sections for more efficient processing.

    Attributes:
        sections (list[Section]): Sorted list of sections (read-only, use property)
        meta (dict[str, Any]): Arbitrary metadata dictionary (format-specific or user-defined)
        address (int): Current address pointer (for sequential operations)

    Args:
        sections: The sections to initialize the image with. Can be:
            - None or empty list: Creates empty image
            - Single Section: Creates image with one section
            - Iterable of Sections: Creates image with multiple sections
        join: If True (default), automatically merge consecutive sections
            (sections where end of one == start of next). If False, preserve
            section boundaries as-is.
        meta: Optional metadata dictionary. Commonly used for:
            - start_address: Entry point address
            - format: Source file format identifier
            - version: Firmware version string
            - Any user-defined key-value pairs

    Raises:
        TypeError: If sections argument is not a Section, iterable, or None.

    Examples:
        Create empty image and add sections::

            img = Image()
            img.insert_section(Section(0x1000, b"Hello"))
            img.insert_section(Section(0x2000, b"World"))

        Create with auto-joining::

            sections = [
                Section(0x1000, b"AAA"),
                Section(0x1003, b"BBB"),  # Consecutive, will be merged
            ]
            img = Image(sections, join=True)
            assert len(img.sections) == 1  # Merged into one section

        Create without joining::

            img = Image(sections, join=False)
            assert len(img.sections) == 2  # Sections kept separate

        Load from file format::

            import objutils
            img = objutils.load("ihex", "firmware.hex")
            print(f"Loaded {len(img.sections)} sections")
            print(f"Entry point: 0x{img.meta.get('start_address', 0):08X}")

        Typified access::

            img = Image(Section(0x1000, bytearray(100)))
            img.write_numeric(0x1000, 0x12345678, "uint32_le")
            value = img.read_numeric(0x1000, "uint32_le")

        Check address coverage::

            if 0x1050 in img:
                data = img.read(0x1050, 16)
            else:
                print("Address not in image")

        Iterate over sections::

            for i, section in enumerate(img):
                print(f"Section {i}: 0x{section.start_address:08X}, "
                      f"{section.length} bytes")

    Note:
        Sections are automatically sorted by start address. Overlapping sections
        are detected and will raise a validation error during construction.
    """

    def __init__(
        self,
        sections: Optional[Union[Section, Iterable[Section]]] = None,
        join: bool = True,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        if meta is None:
            meta = {}
        if not sections:
            sections = []
        elif isinstance(sections, Section) or hasattr(sections, "__iter__"):
            sections = list(sections)
        else:
            raise TypeError(f"Argument section is of wrong type {sections!r}")
        self._sections = sorted(sections, key=attrgetter("start_address"))
        self._join = join
        if join:
            self.join_sections()
        _validate_sections(self._sections)
        self.address = 0
        # if meta and not isinstance(meta, MetaRecord):
        #    raise TypeError("meta-data must be of instance 'MetaRecord'")
        self.meta = meta

    def __repr__(self) -> str:
        """Return string representation of all sections."""
        result = []
        for segment in self.sections:
            result.append(repr(segment))
        return "\n".join(result)

    __str__ = __repr__

    def __len__(self) -> int:
        """Return total number of bytes across all sections."""
        return sum(len(s) for s in self.sections)

    def __iter__(self):
        """Iterate over sections."""
        return iter(self.sections)

    def __getitem__(self, idx: int) -> Section:
        """Get section by index."""
        return self.sections[idx]

    def __eq__(self, other: object) -> bool:
        """Check equality with another Image."""
        if not isinstance(other, Image):
            return NotImplemented
        if len(self.sections) == len(other.sections):
            return all(eq(left, right) for left, right in zip(self.sections, other.sections, strict=True))
        else:
            return False

    def __ne__(self, other: object) -> bool:
        """Check inequality with another Image."""
        return not (self == other)

    def __contains__(self, addr: int) -> bool:
        """Check if address is contained in any section."""
        return any(addr in sec for sec in self.sections)

    def hexdump(self, fp=sys.stdout) -> None:
        """Print hexadecimal dump of all sections.

        Args:
            fp: File-like object to write output to. Defaults to stdout.
        """
        for idx, section in enumerate(self.sections):
            print(f"\nSection #{idx:04d}", file=fp)
            print("-" * 13, file=fp)
            section.hexdump(fp)

    def _call_address_function(self, func_name: str, addr: int, *args: Any, **kws: Any) -> Any:
        """Call a section method on the section containing the given address.

        Args:
            func_name: Name of the method to call on the section.
            addr: Target address to locate the appropriate section.
            *args: Positional arguments to pass to the section method.
            **kws: Keyword arguments to pass to the section method.

        Returns:
            Result from the section method call.

        Raises:
            InvalidAddressError: If address is not contained in any section.
        """
        for section in self.sections:
            if addr in section:
                func = getattr(section, func_name)
                return func(addr, *args, **kws)
        raise InvalidAddressError(f"Address 0x{addr:08x} not in range.")

    def read(self, addr: int, length: int, **kws: Any) -> bytes:
        """Read bytes from image.

        Args:
            addr: Start address to read from.
            length: Number of bytes to read.
            **kws: Additional keyword arguments passed to section read method.

        Returns:
            Bytes read from the image.

        Raises:
            InvalidAddressError: If address is out of range.

        Note:
            If addr + length extends beyond section boundary, result is
            silently truncated without raising an exception.
        """
        return self._call_address_function("read", addr, length, **kws)

    def write(self, addr: int, data: Union[bytes, bytearray], **kws: Any) -> None:
        """Write bytes to image.

        Args:
            addr: Start address to write to.
            data: Bytes to write to the image.
            **kws: Additional keyword arguments passed to section write method.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        self._call_address_function("write", addr, data, **kws)

    def read_numeric(self, addr: int, dtype: str, **kws: Any) -> Union[int, float]:
        """Read a single numeric value with explicit endianness.

        Reads an integer or floating-point value from the specified address,
        automatically routing to the section containing that address.

        Args:
            addr: Absolute memory address to read from
            dtype: Data type with endianness (e.g., ``"uint32_le"``, ``"float64_be"``)
            **kws: Optional keyword arguments:
                - bit_mask (int): Apply bitmask to result

        Returns:
            int or float depending on dtype

        Raises:
            InvalidAddressError: If address is not in any section
            TypeError: If dtype is invalid or missing endianness suffix

        Supported types:
            - ``uint8``, ``int8`` - 8-bit integers
            - ``uint16_le``, ``uint16_be``, ``int16_le``, ``int16_be``
            - ``uint32_le``, ``uint32_be``, ``int32_le``, ``int32_be``
            - ``uint64_le``, ``uint64_be``, ``int64_le``, ``int64_be``
            - ``float32_le``, ``float32_be``
            - ``float64_le``, ``float64_be``

        Example::

            img = objutils.load("ihex", "firmware.hex")

            # Read 32-bit little-endian value
            version = img.read_numeric(0x1000, "uint32_le")

            # Read floating-point with big-endian
            pi = img.read_numeric(0x2000, "float32_be")

            # Read with bitmask
            flags = img.read_numeric(0x3000, "uint32_le", bit_mask=0x00FF)

        Note:
            Endianness must always be specified (``_le`` or ``_be`` suffix) to
            avoid ambiguity in cross-platform embedded development.
        """
        return self._call_address_function("read_numeric", addr, dtype, **kws)

    def write_numeric(self, addr: int, value: Union[int, float], dtype: str, **kws: Any) -> None:
        """Write a single numeric value with explicit endianness.

        Writes an integer or floating-point value to the specified address,
        automatically routing to the section containing that address.

        Args:
            addr: Absolute memory address to write to
            value: Integer or float value to write
            dtype: Data type with endianness (e.g., ``"uint32_le"``, ``"float64_be"``)
            **kws: Optional keyword arguments (reserved for future use)

        Raises:
            InvalidAddressError: If address is not in any section
            TypeError: If dtype is invalid or missing endianness suffix

        Example::

            img = objutils.load("ihex", "firmware.hex")

            # Write different types
            img.write_numeric(0x1000, 0x12, "uint8")
            img.write_numeric(0x1001, 0x1234, "uint16_le")
            img.write_numeric(0x1003, 0x12345678, "uint32_be")
            img.write_numeric(0x1007, 3.14159, "float32_le")

            # Save modified image
            objutils.dump("ihex", "modified.hex", img)

        Note:
            Endianness must always be specified to avoid bugs when working
            with cross-platform embedded systems.
        """
        self._call_address_function("write_numeric", addr, value, dtype, **kws)

    def read_numeric_array(self, addr: int, length: int, dtype: str, **kws: Any) -> list[Union[int, float]]:
        """Read array of numeric values from image.

        Args:
            addr: Start address to read from.
            length: Number of elements to read.
            dtype: Data type specification (e.g., 'uint8', 'int16', 'float32').
            **kws: Additional keyword arguments passed to section method.

        Returns:
            List of numeric values read from the image.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        return self._call_address_function("read_numeric_array", addr, length, dtype, **kws)

    def write_numeric_array(self, addr: int, data: Iterable[Union[int, float]], dtype: str, **kws: Any) -> None:
        """Write array of numeric values to image.

        Args:
            addr: Start address to write to.
            data: Iterable of numeric values to write.
            dtype: Data type specification (e.g., 'uint8', 'int16', 'float32').
            **kws: Additional keyword arguments passed to section method.

        Raises:
            InvalidAddressError: If address is out of range.

        Note:
            Bounds checking is performed by the underlying section method.
        """
        self._call_address_function("write_numeric_array", addr, data, dtype, **kws)

    def write_ndarray(self, addr: int, array: Any, order: Optional[str] = None, **kws: Any) -> None:
        """Write NumPy ndarray to image.

        Args:
            addr: Start address to write to.
            array: NumPy ndarray to write.
            order: Memory layout order ('C' for row-major, 'F' for column-major).
            **kws: Additional keyword arguments passed to section method.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        self._call_address_function("write_ndarray", addr, array, order=order, **kws)

    def read_ndarray(
        self,
        addr: int,
        length: int,
        dtype: str,
        shape: Optional[tuple[int, ...]] = None,
        order: Optional[str] = None,
        **kws: Any,
    ) -> Any:
        """Read NumPy ndarray from image.

        Args:
            addr: Start address to read from.
            length: Number of elements to read.
            dtype: NumPy data type specification.
            shape: Shape tuple for the resulting array.
            order: Memory layout order ('C' for row-major, 'F' for column-major).
            **kws: Additional keyword arguments passed to section method.

        Returns:
            NumPy ndarray with the specified shape and dtype.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        return self._call_address_function("read_ndarray", addr, length, dtype, shape, order, **kws)

    def read_string(self, addr: int, encoding: str = "latin1", length: int = -1, **kws: Any) -> str:
        """Read string from image.

        Args:
            addr: Start address to read from.
            encoding: Character encoding to use (default: 'latin1').
            length: Maximum length to read. If -1, reads until null terminator.
            **kws: Additional keyword arguments passed to section method.

        Returns:
            Decoded string from the image.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        return self._call_address_function("read_string", addr, encoding, length, **kws)

    def write_string(self, addr: int, value: str, encoding: str = "latin1", **kws: Any) -> None:
        """Write string to image.

        Args:
            addr: Start address to write to.
            value: String to write.
            encoding: Character encoding to use (default: 'latin1').
            **kws: Additional keyword arguments passed to section method.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        self._call_address_function("write_string", addr, value, encoding, **kws)

    def _address_contained(self, address: int, length: int) -> bool:
        """Check if address range is contained in the image.

        Args:
            address: Start address to check.
            length: Length of the address range.

        Returns:
            True if the address range is contained in any section, False otherwise.
        """
        return address in self or (address + length - 1) in self

    def insert_section(
        self, data: Union[bytes, bytearray, memoryview, str], start_address: Optional[int] = None, join: bool = True
    ) -> None:
        """Insert/add a new section to image.

        Args:
            data: Bytes making up the section. Can be bytes, bytearray,
                memoryview, or string (will be converted to bytes).
            start_address: Start address for the new section. If None, continues
                from the last inserted section's end address.
            join: If True, automatically merge adjacent sections.

        Raises:
            InvalidAddressError: If the new section overlaps with existing sections.

        Note:
            Overlapping sections are not supported. To update/replace a section
            use :meth:`update_section`.
        """
        start_address = (
            start_address if start_address is not None else self.address
        )  # If Address omitted, create continuous address space.
        if self._address_contained(start_address, len(data)):
            raise InvalidAddressError("Overlapping address-space")
        if isinstance(data, str):
            data = [ord(x) for x in data]  # array.array('B',data)
        self._sections.append(Section(start_address, data))
        if join:
            self.join_sections()
        self.address = start_address + len(data)

    @property
    def sections(self) -> list[Section]:
        """Get list of sections in the image.

        Returns:
            List of Section objects, sorted by start address.
        """
        return self._sections

    def get_section(self, address: int) -> Section:
        """Get section containing the specified address.

        Args:
            address: Address to locate within sections.

        Returns:
            Section object containing the specified address.

        Raises:
            InvalidAddressError: If address is not contained in any section.
        """
        if address not in self:
            raise InvalidAddressError("Address not in range")
        result = bisect_right(self._sections, address, key=attrgetter("start_address"))
        return self._sections[result - 1]

    def update_section(self, data: Union[bytes, bytearray], address: Optional[int] = None) -> None:
        """Update existing section data.

        Args:
            data: New data to write to the section.
            address: Start address of the data to update. If None, uses
                the current address pointer.

        Raises:
            InvalidAddressError: If address range is not contained in existing sections.

        Note:
            This method currently only validates the address range but does not
            perform the actual update operation. Full implementation is pending.
        """
        if not self._address_contained(address, len(data)):
            raise InvalidAddressError("Address-space not in range")

    def delete_section(self, address: Optional[int] = None) -> None:
        """Delete section containing the specified address.

        Args:
            address: Address within the section to delete. If None, uses
                the current address pointer.

        Raises:
            InvalidAddressError: If address is not contained in any section.
            NotImplementedError: This method is not yet implemented.

        Note:
            This method is currently not implemented and needs to be developed
            for production use.
        """
        raise NotImplementedError("delete_section() is not yet implemented")

    def join_sections(self) -> None:
        """Merge adjacent or overlapping sections.

        Combines sections that are contiguous or overlapping in address space
        into single sections, reducing fragmentation and improving efficiency.
        """
        self._sections = join_sections(self._sections)

    def split(self, at: Optional[int] = None, equal_parts: Optional[int] = None, remap: Optional[bool] = None) -> None:
        """Split image into multiple parts.

        Args:
            at: Address at which to split the image.
            equal_parts: Number of equal-sized parts to split into.
            remap: If True, remap addresses after splitting.

        Raises:
            NotImplementedError: This method is not yet implemented.

        Note:
            This method is currently a placeholder and needs to be fully
            implemented for production use. The parameters define different
            splitting strategies that need to be developed.
        """
        raise NotImplementedError(f"split() is not yet implemented. Called with: at={at}, equal_parts={equal_parts}, remap={remap}")


def _validate_sections(sections: Iterable[Section]) -> None:
    """Validate that sections fulfill the required protocol.

    Args:
        sections: Iterable of section objects to validate.

    Raises:
        TypeError: If sections is not iterable or if any section is missing
            required attributes (start_address, length, data).
    """
    ATTRIBUTES = ("start_address", "length", "data")
    if "__iter__" not in dir(sections):
        raise TypeError("Sections must be iterable.")
    for section in sections:
        if not all(hasattr(section, attr) for attr in ATTRIBUTES):
            raise TypeError(f"Section '{section}' doesn't fulfill required protocol (missing attributes).")
