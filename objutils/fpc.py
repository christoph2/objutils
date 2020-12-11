#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

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
from functools import partial
import os
import re
import objutils.hexfile as hexfile
from objutils.utils import create_string_buffer, slicer, PYTHON_VERSION
from objutils import checksums
import objutils.utils as utils


DATA_ABS    = 1
DATA_INC    = 2
DATA_REL    = 3
EOF         = 4

PREFIX      = '$'

MAPPING = dict(enumerate(chr(n) for n in range(37, 123) if not n in (42, )))
REV_MAPPING = {ord(value): key for key, value in MAPPING.items()}
NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)
VALID_CHARS = re.compile("^\{0}[{1}]+$".format(PREFIX, re.escape(''.join(MAPPING.values()))))

atoi16 = partial(int, base = 16)


class Reader(hexfile.Reader):

    FORMAT_SPEC = (
        (DATA_ABS,  "CCLL0000AAAAAAAADD"),
        (DATA_INC,  "CCLL0001DD"),
        (DATA_REL,  "CCLL0002AAAAAAAADD"),
        (EOF,       "00000000")
    )

    def decode(self, fp):
        self.last_address = 0    # TODO: decode!
        out_lines = []
        for line in fp.readlines():
            line = line.strip()
            startSym, line = line[0], line[1:]

            if startSym != PREFIX:
                pass # todo: FormatError!!!

            if (len(line) % 5) != 0:
                pass # todo: FormatError!!!

            values = []
            for quintuple in self.split_quintuples(line):
                value = self.convert_quintuple(quintuple)
                values.append("{0:08X}".format(value))
            out_lines.append(''.join(values))
        return '\n'.join(out_lines)

    def read(self, fp):
        return super(Reader, self).read(
            create_string_buffer(
                bytearray(self.decode(fp), "ascii")
            )
        )

    def convert_quintuple(self, quintuple):
        res = 0         # reduce(lambda accu, x: (accu * 85) + x, value, 0)
        for ch  in quintuple:
            v = REV_MAPPING[bytearray((ch, ))[0]]
            res = v + (res * 85)
        return res

    def split_quintuples(self, line):
        res = []
        for i in range(0, len(line), 5):
            res.append(line[i : i + 5])
        return res

    def check_line(self, line, format_type):
        if format_type == EOF:
            return True
        line.length -= 4
        if line.length != len(line.chunk):
            line.chunk = line.chunk[ : line.length] # Cut padding.
        if format_type == DATA_ABS:
            tmp = 0
            self.last_address = line.address + line.length
        elif format_type == DATA_INC:
            tmp = 1
            line.address = self.last_address
        elif format_type == DATA_REL:
            self.error("relative adressing not supported.")
            tmp = 2
        else:
            self.error("Invalid format type: '{0}'".format(format_type))
            tmp = 0
        checksum = checksums.lrc(utils.make_list(tmp, line.length + 4, utils.int_to_array(line.address), line.chunk), 8, checksums.COMPLEMENT_TWOS)
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line, format_type):
        return format_type in (DATA_ABS, DATA_INC, DATA_REL)

    def probe(self, fp):
        for idx, line in enumerate(fp, 1):
            if not VALID_CHARS.match(line.decode()):
                fp.seek(0, os.SEEK_SET)
                return False
            if idx > 3:
                break
        fp.seek(0, os.SEEK_SET)
        return super(Reader, self).probe(
            create_string_buffer(bytearray(self.decode(fp), "ascii"))
        )


class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 16

    def compose_row(self, address, length, row):
        tmp = 0 # TODO: format type!?
        checksum = checksums.lrc(utils.make_list(tmp, length + 4, utils.int_to_array(address), row), 8, checksums.COMPLEMENT_TWOS)
        if length < self.row_length:
            lengthToPad = self.row_length - length
            padding = [0] * (lengthToPad)
            row.extend(padding)
        line = "{0:02X}{1}0000{2:08X}{3}".format(checksum, length - 2, address, Writer.hex_bytes(row))
        return line

    def compose_footer(self, meta):
        return "00000000"

    def post_processing(self, data):
        result = []
        for line in data.splitlines():
            if len(line) % 4:
                self.error("Size of line must be a multiple of 4.")
                continue
            res = []
            for item in slicer(line, 8, atoi16):
                item = self.convert_quintuple(item)
                res.append(item)
            result.append("{0}{1}".format(PREFIX, ''.join(res)))
        if PYTHON_VERSION.major == 3:
            return bytes('\n'.join(result), "ascii")
        else:
            return bytes('\n'.join(result))

    def convert_quintuple(self, value):
        result = []
        while value:
            result.append(MAPPING[value % 85])
            value //= 85
        if len(result) < 5:
            result.extend([MAPPING[0]] * (5 - len(result)))
        return ''.join(reversed(result))
