#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2022 by Christoph Schueler <cpu12.gems@googlemail.com>

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


"""BinDiff

Represents a difference between two binaries.

Attributes
----------

    type: str
        Type of Modification:

        - 'A' something was appended.
        - 'D' something was deleted.
        - 'M' a modification happend.

    offset: int
        Location

    a: bytes or bytearray
        Considered as the original.

    b: bytes or bytearray
        Considered as the modification.
"""
BinDiff = namedtuple("BinDiff", "type offset a b")


def diff_bin(a, b):
    """Simplicistic binary diff algorithm.

    Parameters
    ----------
    a: bytes or bytearray
        Considered as the original.

    b: bytes or bytearray
        Considered as the modification.

    Returns
    list of `BinDiff`s.
    -------
    """
    if not isinstance(a, (bytes, bytearray)):
        raise TypeError("Parameter `a` must be of type `bytes` or `bytearray`")
    if not isinstance(b, (bytes, bytearray)):
        raise TypeError("Parameter `b` must be of type `bytes` or `bytearray`")
    la, lb = len(a), len(b)
    length = min(la, lb)
    tmp = []
    start_offset = 0
    diff_bytes_a, diff_bytes_b = bytearray(), bytearray()
    for offset in range(length):
        ai = a[offset]
        bi = b[offset]
        diff = ai - bi
        if diff:
            if not diff_bytes_a:
                start_offset = offset
            diff_bytes_a.append(ai)
            diff_bytes_b.append(bi)
        else:
            if diff_bytes_a:
                tmp.append(BinDiff("M", start_offset, diff_bytes_a, diff_bytes_b))
                diff_bytes_a, diff_bytes_b = bytearray(), bytearray()
    if lb > la:
        tmp.append(BinDiff("A", len(a), None, b[-(lb - la) :]))
    elif lb < la:
        tmp.append(BinDiff("D", len(b), a[-(la - lb) :], None))
    result = tmp
    return result
