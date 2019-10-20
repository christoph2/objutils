#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

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

from operator import attrgetter, eq
import sys

from objutils.section import Section, join_sections

class AddressError(Exception): pass

## Adress-space constants.
AS_16   = 0
AS_24   = 1
AS_32   = 2
AS_64   = 3

class Image(object):
    """
    """

    def __init__(self, sections = None, meta = None, valid = False):
        if meta is None:
            meta = {}
        self.sections = sections if sections else []
        _validate_sections(self.sections)
        self.meta = meta
        self.valid = valid

    def __repr__(self):
        result = []
        for segment in self.sections:
            result.append(repr(segment))
        return '\n'.join(result)

    def __len__(self):
        return len(self.sections)

    def __iter__(self):
        return iter(self.sections)

    def __getitem__(self, idx):
        return self.sections[idx]

    def __eq__(self, other):
        if len(self.sections) == len(other.sections):
            return all( eq(l, r) for l, r in zip(self.sections, other.sections))
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def hexdump(self, fp = sys.stdout):
        for idx, section in enumerate(self.sections):
            print("\nSection #{0:04d}".format(idx ), file = fp)
            print("-" * 13, file = fp)
            section.hexdump(fp)

    def _call_address_function(self, func_name, addr, *args):
        for section in self.sections:
            if addr in section:
                func = getattr(section, func_name)
                return func(addr, *args)
        raise AddressError("Address 0x{:08x} not found.".format(addr))

    def read(self, addr, length):
        return self._call_address_function("read", addr, length)

    def write(self, addr, length, data):
        self._call_address_function("write", addr, length, data)

    def read_numeric(self, addr, dtype):
        return self._call_address_function("readNumeric", addr, dtype)

    def write_numeric(self, addr, value, dtype):
        self._call_address_function("writeNumeric", addr, value, dtype)

    def read_string(self, addr, encoding = "latin1", length = -1):
        return self._call_address_function("readString", addr, encoding, length)

    def write_string(self, addr, value, encoding = "latin1"):
        self._call_address_function("writeString", addr, value, encoding)

    def split(self, at = None, equal_parts = None, remap = None):
        print("SPLIT-IMAGE", at, equal_parts, remap)


class Builder(object):
    """Construct and :class:`Image` object.
    """

    def __init__(self, sections = None, auto_join = False, auto_sort = False):
        if auto_sort:
            self._need_sorting = True
            if sections:
                self._sections = sorted(sections, key = attrgetter("start_address"))
            else:
                self._sections = []
        else:
            self._need_sorting = False
            self._sections = sections if sections else []
        if self._sections and auto_join:
            self.join_sections()
        _validate_sections(self._sections)
        self.address = 0
        self.auto_join = auto_join

    def add_section(self, data, address = None, dont_join = False):   # TODO: 'polymorphic' signature, move 'dontJoin' to segment!
        address = address if address else self.address  # If Address omitted, create continuous address space.
        if isinstance(data, str):
            data = [ord(x) for x in data] # array.array('B',data)
        self._sections.append(Section(address, data))
        if self._need_sorting:
            self._sections.sort(key = attrgetter("start_address"))
        if self.auto_join:
            self.join_sections()
        self.address = address + len(data)

    def add_metadata(self, meta_data):
        pass

    def join_sections(self, order_segments = None):
        self._sections = join_sections(self._sections, order_segments)

    def hexdump(self, fp = sys.stdout):
        self.image.hexdump(fp)

    @property
    def image(self):
        return Image(self._sections)


def _validate_sections(sections):
    """Test for required protocol
    """
    ATTRIBUTES = ('start_address', 'length', 'data')
    if not '__iter__' in dir(sections):
        raise TypeError("Sections must be iteratable.")
    for section in sections:
        if not all( hasattr(section, attr) for attr in ATTRIBUTES):
            raise TypeError("Section '{0}' doesn't fulfills required protocol (missing attributes).")
