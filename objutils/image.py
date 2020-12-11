#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

from __future__ import print_function

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from collections import namedtuple
import enum
from operator import attrgetter, eq
import sys

from sortedcontainers import SortedList

from objutils.section import Section, join_sections
from objutils.exceptions import InvalidAddressError

SearchType = namedtuple("SearchType", "start_address")


#
# TODO: Use crypto hashes (comparison, optimized storage, ...)
#

class AddressSpace(enum.IntEnum):
    """Adress-space constants.
    """
    AS_16   = 0
    AS_24   = 1
    AS_32   = 2
    AS_64   = 3


class Image(object):
    """Manage images.

    An image is a collection of :class:`Section`s and meta-data.

    Parameters
    ----------
    sections: iteratable (typically `list`or `tuple`
        The sections the image should initialized with.
    meta: object
        Arbitrary meta-data.
    """

    def __init__(self, sections = None, join = True, meta = None):
        if meta is None:
            meta = {}
        if not sections:
            sections = []
        elif isinstance(sections, Section) or hasattr(sections, "__iter__"):
            sections = list(sections)
        else:
            raise TypeError("Argument section is of wrong type '{}'".format(sections))
        self._sections = SortedList(sections, key = attrgetter("start_address"))
        self._join = join
        if join:
            self.join_sections()
        _validate_sections(self._sections)
        self.address = 0
        #if meta and not isinstance(meta, MetaRecord):
        #    raise TypeError("meta-data must be of instance 'MetaRecord'")
        self.meta = meta

    def __repr__(self):
        result = []
        for segment in self.sections:
            result.append(repr(segment))
        return '\n'.join(result)

    __str__ = __repr__

    def __len__(self):
        return sum(len(s) for s in self.sections)

    def __iter__(self):
        return iter(self.sections)

    def __getitem__(self, idx):
        return self.sections[idx]

    def __eq__(self, other):
        if len(self.sections) == len(other.sections):
            return all(eq(l, r) for l, r in zip(self.sections, other.sections))
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __contains__(self, addr):
        return any(addr in sec for sec in self.sections)

    def hexdump(self, fp = sys.stdout):
        """

        """
        for idx, section in enumerate(self.sections):
            print("\nSection #{0:04d}".format(idx ), file = fp)
            print("-" * 13, file = fp)
            section.hexdump(fp)

    def _call_address_function(self, func_name, addr, *args, **kws):
        for section in self.sections:
            if addr in section:
                func = getattr(section, func_name)
                return func(addr, *args, **kws)
        raise InvalidAddressError("Address 0x{:08x} not in range.".format(addr))

    def read(self, addr, length, **kws):
        """Read bytes from image.

        Parameters
        ----------
        addr: int
            Startaddress.

        length: int
            Number of bytes to read.

        Returns
        -------
        bytes

        Raises
        ------
        :class:`InvalidAddressError`
            if `addr` is out of range

        Note
        ----
            if `addr` + `len` is out of range, result is silently truncated, i.e. without raising an exception.
        """
        return self._call_address_function("read", addr, length, **kws)

    def write(self, addr, data, **kws):
        """Write bytes to image.

        Parameters
        ----------
        addr: int
            Startaddress.

        data: bytes

        Raises
        ------
        :class:`InvalidAddressError`
            if `addr` is out of range
        """
        self._call_address_function("write", addr, data, **kws)

    def read_numeric(self, addr, dtype, **kws):
        """

        """
        return self._call_address_function("read_numeric", addr, dtype, **kws)

    def write_numeric(self, addr, value, dtype, **kws):
        """
        """
        self._call_address_function("write_numeric", addr, value, dtype, **kws)

    def read_numeric_array(self, addr, length, dtype, **kws):
        """

        """
        return self._call_address_function("read_numeric_array", addr, length, dtype, **kws)

    def write_numeric_array(self, addr, data, dtype, **kws):# TODO: bounds-checking.
        """
        """
        self._call_address_function("write_numeric_array", addr, data, dtype)

    def write_ndarray(self, addr, array, order = None, **kws):
        """
        """
        self._call_address_function("write_ndarray", addr, array, order = None, **kws)

    def read_ndarray(self, addr, length, dtype, shape = None, order = None, **kws):
        """
        """
        return self._call_address_function("read_ndarray", addr, length, dtype, shape, order, **kws)


    def read_string(self, addr, encoding = "latin1", length = -1, **kws):
        """

        """
        return self._call_address_function("read_string", addr, encoding, length, **kws)

    def write_string(self, addr, value, encoding = "latin1", **kws):
        """

        """
        self._call_address_function("write_string", addr, value, encoding, **kws)


    def _address_contained(self, address, length):
        """Check if address space exists.

        Parameters
        ----------
        address: int
        length: int

        Returns
        -------
        bool
        """
        return address in self or (address + length - 1) in self

    def insert_section(self, data, start_address = None, join = True):
        """Insert/add a new section to image.

        Parameters
        ----------
        data: convertible to bytearray() -- s. :func:`_data_converter`.
            Bytes making up the section.
        start_address: int
        join: bool
            Join/merge adjacent section.

        Raises
        ------
        :class:`InvalidAddressError`

        Notes
        -----
        Overlapping sections are not supported.
        To update/replace a section use :meth:`update_section`.
        """
        start_address = start_address if start_address is not None else self.address  # If Address omitted, create continuous address space.
        if self._address_contained(start_address, len(data)):
            raise InvalidAddressError("Overlapping address-space")
        if isinstance(data, str):
            data = [ord(x) for x in data] # array.array('B',data)
        self._sections.add(Section(start_address, data))
        if join:
            self.join_sections()
        self.address = start_address + len(data)

    @property
    def sections(self):
        return self._sections

    def get_section(self, address):
        """Get :class:`Section` containing `address`.
        Parameters
        ----------
        address: int

        Returns
        -------
        :class:`Section`

        Raises
        ------
        :class:`InvalidAddressError`
        """
        if not address in self:
            raise InvalidAddressError("Address not in range")
        result = self._sections.bisect_right(SearchType(address))
        return self._sections[result - 1]


    def update_section(self, data, address = None):
        """

        """
        if not self._address_contained(address, len(data)):
            raise InvalidAddressError("Address-space not in range")

    def delete_section(self, address = None):
        """

        """

    def join_sections(self):
        """

        """
        self._sections = join_sections(self._sections)

    def split(self, at = None, equal_parts = None, remap = None):
        print("SPLIT-IMAGE", at, equal_parts, remap)

def _validate_sections(sections):
    """Test for required protocol
    """
    ATTRIBUTES = ('start_address', 'length', 'data')
    if not '__iter__' in dir(sections):
        raise TypeError("Sections must be iteratable.")
    for section in sections:
        if not all( hasattr(section, attr) for attr in ATTRIBUTES):
            raise TypeError("Section '{0}' doesn't fulfills required protocol (missing attributes).")
