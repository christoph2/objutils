#!/usr/bin/env python

__version__ = "0.1.2"

__all__ = [
    "Dumper",
    "CanonicalDumper",
    "isprintable",
]

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import sys
from collections.abc import Sequence
from typing import TextIO


def isprintable(ch: int) -> bool:
    return 0x1F < ch < 0x7f


def unpack(*args: int) -> Sequence[int]:
    return args


class Dumper:
    LINE_LENGTH: int = 16

    def __init__(self, fp: TextIO = sys.stdout, num_address_bits: int = 32) -> None:
        self._fp: TextIO = fp
        self._rolloverMask: int = 2**num_address_bits
        self._nibbles: int = num_address_bits >> 2
        self._addressMask: str = f"%0{self._nibbles:d}x "
        self.previous_row: bytes = b""
        self.elided: bool = False

    def dump_data(self, section, offset: int = 0) -> None:
        end = section.length
        start_pos = 0
        line_num = 0
        end_pos = self.LINE_LENGTH
        while end_pos < end:
            line_num += 1
            row = section.data[start_pos:end_pos]
            if row == self.previous_row:
                if not self.elided:
                    print("          *", file=self._fp)
                    self.elided = True
            else:
                self.dump_row(row, start_pos + section.start_address)
                self.elided = False
            start_pos = end_pos
            end_pos = end_pos + self.LINE_LENGTH
            self.previous_row = row
        row = section.data[start_pos:end_pos]
        self.dump_row(row, start_pos + section.start_address)
        print("-" * 15, file=self._fp)
        print(f"{section.length:-9d} bytes", file=self._fp)
        print("-" * 15, file=self._fp)


class CanonicalDumper(Dumper):
    LINE_LENGTH = 0x10

    def printhex_bytes(self, row: Sequence[int]) -> None:
        row = list(row)
        filler = [0x20] * (self.LINE_LENGTH - len(row))
        ascii_part = [isprintable(x) and chr(x) or "." for x in row + filler]
        print("|{}|".format(("%s" * self.LINE_LENGTH) % unpack(*ascii_part)), file=self._fp)

    def dump_row(self, row: Sequence[int] | bytes | bytearray, startAddr: int) -> None:
        start_pos = 0
        print(self._addressMask % ((start_pos + startAddr) % self._rolloverMask), file=self._fp, end=" ")
        # Convert row to a tuple of ints to avoid TypeError for empty sequences
        ints = tuple(row)
        if ints:
            print("%02x " * len(ints) % unpack(*ints), file=self._fp, end=" ")
        else:
            print("", file=self._fp, end="")
        if len(ints) < self.LINE_LENGTH:
            spaces = "   " * (self.LINE_LENGTH - len(ints))
            print(spaces, file=self._fp, end="")
        self.printhex_bytes(ints)
