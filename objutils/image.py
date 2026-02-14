#!/usr/bin/env python
"""Image management for object files.

This module provides the Image class for managing collections of memory sections
with associated metadata and operations for reading, writing, and manipulating
binary data.
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
from typing import Any, Iterable, Optional, Protocol, Union

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

    An image is a collection of :class:`Section`s with associated meta-data,
    providing operations for reading, writing, and manipulating binary data
    across potentially non-contiguous memory regions.

    Args:
        sections: The sections the image should be initialized with. Can be a
            single Section, an iterable of Sections, or None for empty image.
        join: If True, automatically merge adjacent/overlapping sections.
        meta: Arbitrary meta-data dictionary associated with the image.

    Raises:
        TypeError: If sections argument is not a Section, iterable, or None.
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
        """Read numeric value from image.

        Args:
            addr: Address to read from.
            dtype: Data type specification (e.g., 'uint8', 'int16', 'float32').
            **kws: Additional keyword arguments passed to section method.

        Returns:
            Numeric value read from the image.

        Raises:
            InvalidAddressError: If address is out of range.
        """
        return self._call_address_function("read_numeric", addr, dtype, **kws)

    def write_numeric(self, addr: int, value: Union[int, float], dtype: str, **kws: Any) -> None:
        """Write numeric value to image.

        Args:
            addr: Address to write to.
            value: Numeric value to write.
            dtype: Data type specification (e.g., 'uint8', 'int16', 'float32').
            **kws: Additional keyword arguments passed to section method.

        Raises:
            InvalidAddressError: If address is out of range.
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

    def write_numeric_array(
        self, addr: int, data: Iterable[Union[int, float]], dtype: str, **kws: Any
    ) -> None:
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

    def split(
        self, at: Optional[int] = None, equal_parts: Optional[int] = None, remap: Optional[bool] = None
    ) -> None:
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
        raise NotImplementedError(
            f"split() is not yet implemented. Called with: at={at}, equal_parts={equal_parts}, remap={remap}"
        )


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
