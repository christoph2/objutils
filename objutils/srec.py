#!/usr/bin/env python

__version__ = "0.1.0"

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

import re
from functools import partial

import objutils.hexfile as hexfile
import objutils.utils as utils
from objutils.checksums import COMPLEMENT_ONES, lrc
from objutils.utils import make_list


S0 = 1
S1 = 2
S2 = 3
S3 = 4
S5 = 5
S7 = 6
S8 = 7
S9 = 8
SYM = 9

BIAS = {S0: 3, S1: 3, S2: 4, S3: 5, S5: 2, S7: 5, S8: 4, S9: 3}

SYMBOLTABLE = re.compile(r"(^\$\$\s+(?P<modulename>\S*)(?P<symbols>.*?)\$\$)", re.MULTILINE | re.DOTALL)
SYMBOL = re.compile(r"\s+(?P<symbol>.*?)\s+\$(?P<value>.+)", re.MULTILINE | re.DOTALL)


class Reader(hexfile.Reader):
    FORMAT_SPEC = (
        (S0, "S0LLAAAADDCC"),
        (S1, "S1LLAAAADDCC"),
        (S2, "S2LLAAAAAADDCC"),
        (S3, "S3LLAAAAAAAADDCC"),
        (S5, "S5LLAAAACC"),
        (S7, "S7LLAAAAAAAACC"),
        (S8, "S8LLAAAAAACC"),
        (S9, "S9LLAAAACC"),
    )

    def load(self, fp, **kws):
        if isinstance(fp, str):
            fp = open(fp, "rb")
        data = self.read(fp)

        ## todo: extract Symbols and wipe them out.
        """
        symbol_tables = SYMBOLTABLE.findall(data)
        if symbol_tables:
            self._strip_symbols(symbol_tables)
        records = SYMBOLTABLE.sub('', data).strip()
        """

        return data

    def check_line(self, line, format_type):
        # todo: Fkt.!!!
        if format_type in (S0, S1, S5, S9):
            checksum_of_address = ((line.address & 0xFF00) >> 8) + (line.address & 0xFF)
        elif format_type in (S2, S8):
            checksum_of_address = ((line.address & 0xFF0000) >> 16) + ((line.address & 0xFF00) >> 8) + (line.address & 0xFF)
        elif format_type in (S3, S7):
            checksum_of_address = (
                ((line.address & 0xFF000000) >> 24)
                + ((line.address & 0xFF0000) >> 16)
                + ((line.address & 0xFF00) >> 8)
                + (line.address & 0xFF)
            )
        else:
            raise TypeError(f"Invalid format type {format_type!r}.")
        if hasattr(line, "chunk"):
            checksum = (~(sum([line.length, checksum_of_address]) + sum(line.chunk))) & 0xFF
        else:
            checksum = (~(sum([line.length, checksum_of_address]))) & 0xFF
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()
        line.length -= BIAS[format_type]  # calculate actual data length.
        if hasattr(line, "chunk") and line.length and (line.length != len(line.chunk)):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")

    def is_data_line(self, line, format_type):
        return format_type in (S1, S2, S3)

    def special_processing(self, line, format_type):
        if format_type == S0:
            # print("S0: [{}]".format(line.chunk))
            pass
        elif format_type == S5:
            # print "S5: [%s]" % line.chunk
            start_address = line.address  # noqa: F841
        elif format_type == S7:
            start_address = line.address  # noqa: F841
            # print "Startaddress[S7]: %u" % start_address
            # print "32-Bit Start-Address: ", hex(start_address)
        elif format_type == S8:
            start_address = line.address  # noqa: F841
            # print "Startaddress[S8]: %u" % start_address
            # print "24-Bit Start-Address: ", hex(start_address)
        elif format_type == S9:
            start_address = line.address  # noqa: F841
            # print "Startaddress[S9]: %u" % start_address
            # print "16-Bit Start-Address: ", hex(start_address)

    def _strip_symbols(self, symbol_tables):
        self.symbols = []
        for _, _module_name, symbol_table in symbol_tables:
            sb = []
            for symbol in symbol_table.splitlines():
                ma = SYMBOL.match(symbol)
                if ma:
                    # print ma.groupdict()
                    gd = ma.groupdict()
                    sb.append((gd["symbol"], int(gd["value"], 16)))
            self.symbols.append(sb)
        # print self.symbols


class Writer(hexfile.Writer):
    record_type = None
    s5record = False
    start_address = None

    MAX_ADDRESS_BITS = 32

    checksum = staticmethod(partial(lrc, width=8, comp=COMPLEMENT_ONES))

    def pre_processing(self, image):
        if self.record_type is None:
            if hasattr(image, "sections"):
                last_segment = sorted(image.sections, key=lambda s: s.start_address)[-1]
            else:
                last_segment = image
            highest_address = last_segment.start_address + last_segment.length
            if highest_address <= 0x000000FFFF:
                self.record_type = 1
            elif highest_address <= 0x00FFFFFF:
                self.record_type = 2
            elif highest_address <= 0xFFFFFFFF:
                self.record_type = 3
        self.address_mask = f"%0{(self.record_type + 1) * 2:d}X"
        self.offset = self.record_type + 2

    def srecord(self, record_type, length, address, data=None):
        if data is None:
            data = []
        length += self.offset
        address_bytes = utils.int_to_array(address)
        checksum = self.checksum(make_list(address_bytes, length, data))
        mask = f"S%u%02X{self.address_mask!s}%s%02X"
        return mask % (record_type, length, address, Writer.hex_bytes(data), checksum)

    def compose_row(self, address, length, row):
        self.record_count += 1
        return self.srecord(self.record_type, length, address, row)

    def compose_header(self, meta):
        self.record_count = 0
        result = []
        if S0 in meta:  # Usually only one S0 record, but be tolerant.
            for m in meta[S0]:
                result.append(self.srecord(0, len(m.chunk), m.address, m.chunk))
        return "\n".join(result)

    def compose_footer(self, meta):
        result = []
        if self.s5record:
            result.append(self.srecord(5, 0, self.record_count))
        if self.start_address is not None:
            if self.record_type == 1:  # 16bit.
                if S9 in meta:
                    s9 = meta[S9][0]
                    result.append(self.srecord(9, 0, s9.address))
                else:
                    result.append(self.srecord(9, 0, self.start_address))
            elif self.record_type == 2:  # 24bit.
                if S8 in meta:
                    s8 = meta[S8][0]
                    result.append(self.srecord(8, 0, s8.address))
                else:
                    result.append(self.srecord(8, 0, self.start_address))
            elif self.record_type == 3:  # 32bit.
                if S7 in meta:
                    s7 = meta[S7][0]
                    result.append(self.srecord(7, 0, s7.address))
                else:
                    result.append(self.srecord(7, 0, self.start_address))
        return "\n".join(result)
