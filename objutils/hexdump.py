#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

__version__ = "0.1.1"

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

import math
import sys


isprintable = lambda ch: 0x1F < ch < 0x80

def unpack(*args):
    return args

class Dumper(object):

    def __init__(self, fp = sys.stdout, num_address_bits = 32):
        self._fp = fp
        self._rolloverMask = 2 ** num_address_bits
        self._nibbles = num_address_bits >> 2
        self._addressMask = "%0{0:d}x ".format(self._nibbles)
        self.previous_row = bytes()  # bytearray()
        self.elided = False

    def dump_data(self, section, offset = 0):
        end = section.length
        line_count = math.ceil(len(section.data) / self.LINE_LENGTH)
        start_pos = 0
        line_num = 0
        end_pos = self.LINE_LENGTH
        while end_pos < end:
            line_num += 1
            row = section.data[start_pos : end_pos]
            if row == self.previous_row:
                if not self.elided:
                    print("          *", file = self._fp)
                    self.elided = True
            else:
                self.dump_row(row, start_pos + section.start_address)
                self.elided = False
            start_pos = end_pos
            end_pos = end_pos + self.LINE_LENGTH
            self.previous_row = row
        row = section.data[start_pos : end_pos]
        self.dump_row(row, start_pos + section.start_address)
        print("-" * 15, file = self._fp)
        print("{0:-9d} bytes".format(section.length), file = self._fp)
        print("-" * 15, file = self._fp)


class CanonicalDumper(Dumper):
    LINE_LENGTH = 0x10

    def printhex_bytes(self, row):
        row = list(row)
        filler = list([0x20] * (self.LINE_LENGTH - len(row)))
        print('|{0}|'.format(('%s' * self.LINE_LENGTH) % unpack(*[isprintable(x) and chr(x) or '.' for x in row + filler] )), file = self._fp)

    def dump_row(self, row, startAddr):
        start_pos = 0
        print(self._addressMask % ((start_pos + startAddr) % self._rolloverMask), file = self._fp, end = " "),
        print('%02x ' * len(row) % unpack(*row), file = self._fp, end = " "),
        if len(row) == 0:
            print("", file = self._fp, end = "")
        if len(row) < self.LINE_LENGTH:
            spaces = "   " * (self.LINE_LENGTH - len(row))
            print(spaces, file = self._fp, end = ""),
        self.printhex_bytes(row)
