#!/usr/bin/env python
"""Binary diff utilities.

This module provides simple binary diff algorithms for comparing
byte sequences and identifying modifications, additions, and deletions.
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2022-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

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

# Type representing a binary difference
BinDiff = namedtuple("BinDiff", "type offset a b")
BinDiff.__doc__ = """Binary difference between two byte sequences.

Attributes:
    type (str): Type of modification:
        - 'A': Appended data (b has extra bytes at end)
        - 'D': Deleted data (a has extra bytes at end)
        - 'M': Modified data (bytes differ at offset)
    offset (int): Location of difference
    a (bytearray | None): Original bytes (None for 'A' type)
    b (bytearray | None): Modified bytes (None for 'D' type)
"""


def diff_bin(a: bytes | bytearray, b: bytes | bytearray) -> list[BinDiff]:
    """Simple binary diff algorithm.

    Compares two byte sequences and identifies differences as modifications,
    additions, or deletions. Adjacent differing bytes are grouped together.

    Args:
        a: Original byte sequence
        b: Modified byte sequence

    Returns:
        List of BinDiff objects describing all differences

    Raises:
        TypeError: If a or b are not bytes or bytearray

    Example:
        >>> a = b'\\x00\\x01\\x02\\x03'
        >>> b = b'\\x00\\x01\\xFF\\x03'
        >>> diffs = diff_bin(a, b)
        >>> diffs[0].type
        'M'
        >>> diffs[0].offset
        2
    """
    if not isinstance(a, (bytes, bytearray)):
        raise TypeError("Parameter 'a' must be of type 'bytes' or 'bytearray'")
    if not isinstance(b, (bytes, bytearray)):
        raise TypeError("Parameter 'b' must be of type 'bytes' or 'bytearray'")

    la, lb = len(a), len(b)
    length = min(la, lb)
    result: list[BinDiff] = []
    start_offset = 0
    diff_bytes_a = bytearray()
    diff_bytes_b = bytearray()

    # Compare overlapping bytes
    for offset in range(length):
        ai = a[offset]
        bi = b[offset]
        diff = ai - bi
        if diff:
            # Bytes differ - accumulate
            if not diff_bytes_a:
                start_offset = offset
            diff_bytes_a.append(ai)
            diff_bytes_b.append(bi)
        else:
            # Bytes match - flush accumulated diffs
            if diff_bytes_a:
                result.append(BinDiff("M", start_offset, diff_bytes_a, diff_bytes_b))
                diff_bytes_a = bytearray()
                diff_bytes_b = bytearray()

    # Flush any remaining diffs
    if diff_bytes_a:
        result.append(BinDiff("M", start_offset, diff_bytes_a, diff_bytes_b))

    # Handle length differences
    if lb > la:
        # b is longer - data was appended
        result.append(BinDiff("A", len(a), None, b[-(lb - la) :]))
    elif lb < la:
        # a is longer - data was deleted
        result.append(BinDiff("D", len(b), a[-(la - lb) :], None))

    return result
