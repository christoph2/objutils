#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

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

import operator
from functools import partial

import objutils.checksums as checksums
import objutils.hexfile as hexfile
import objutils.utils as utils
from objutils.checksums import COMPLEMENT_TWOS, lrc


DATA = 0
EOF = 1
EXTENDED_SEGMENT_ADDRESS = 2
START_SEGMENT_ADDRESS = 3
EXTENDED_LINEAR_ADDRESS = 4
START_LINEAR_ADDRESS = 5


class Reader(hexfile.Reader):
    FORMAT_SPEC = ((hexfile.TYPE_FROM_RECORD, ":LLAAAATTDDCC"),)

    def __init__(self):
        super().__init__()
        self.segmentAddress = 0

    def check_line(self, line, format_type):
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        checksum = checksums.lrc(
            utils.make_list(line.type, line.length, utils.int_to_array(line.address), line.chunk),
            8,
            checksums.COMPLEMENT_TWOS,
        )
        if line.checksum != checksum:
            raise hexfile.InvalidRecordChecksumError()

    def is_data_line(self, line, format_type):
        if line.type == DATA:
            return True
        else:
            return False

    def calculate_extended_address(self, line, shift_by, name):
        if len(line.chunk) == 2:
            segment = ((line.chunk[0]) << 8) | (line.chunk[1])
            line.add_processing_instruction(("segment", segment))
            self._address_calculator = partial(operator.add, segment << shift_by)
            self.debug(f"EXTENDED_{name.upper()}_ADDRESS: {segment:#X}")
        else:
            self.error(f"Bad Extended {name} Address at line #{line.line_number}.")

    def special_processing(self, line, format_type):
        if line.type == DATA:
            line.address = self._address_calculator(line.address)
        elif line.type == EXTENDED_SEGMENT_ADDRESS:
            self.calculate_extended_address(line, 4, "Segment")
        elif line.type == START_SEGMENT_ADDRESS:
            if len(line.chunk) == 4:
                cs = ((line.chunk[0]) << 8) | (line.chunk[1])
                ip = ((line.chunk[2]) << 8) | (line.chunk[3])
                line.add_processing_instruction(("cs", cs))
                line.add_processing_instruction(("ip", ip))
                self.debug(f"START_SEGMENT_ADDRESS: {hex(cs)}:{hex(ip)}")
            else:
                self.error(f"Bad Segment Address at line %{line.line_number:u}.")
        elif line.type == EXTENDED_LINEAR_ADDRESS:
            self.calculate_extended_address(line, 16, "Linear")
        elif line.type == START_LINEAR_ADDRESS:
            if len(line.chunk) == 4:
                eip = ((line.chunk[0]) << 24) | ((line.chunk[1]) << 16) | ((line.chunk[2]) << 8) | (line.chunk[3])
                line.add_processing_instruction(("eip", eip))
                self.debug(f"START_LINEAR_ADDRESS: {hex(eip)}")
            else:
                self.error(f"Bad Linear Address at line #{line.line_number:d}.")
        elif line.type == EOF:
            pass
        else:
            self.warn(f"Invalid record type [{line.type:u}] at line {line.line_number:u}")

    def _address_calculator(self, x):
        return x


class Writer(hexfile.Writer):
    MAX_ADDRESS_BITS = 32
    checksum = staticmethod(partial(lrc, width=8, comp=COMPLEMENT_TWOS))

    def pre_processing(self, image):
        self.previosAddress = None
        self.start_address = 0

    def compose_row(self, address, length, row):
        result = ""
        seg, offs = divmod(address, 0x10000)
        hi, lo = self.word_to_bytes(address)
        if offs != self.previosAddress:
            # print("NEQ: {0:04x} [{1:04x}:{2:04x}]".format(address, seg, offs))
            if address > 0xFFFF:
                if address > 0xFFFFF:
                    segHi, segLo = self.word_to_bytes(seg)
                    result = f":02000004{int(seg):04X}{self.checksum(list((2, 4, segHi, segLo))):02X}\n"
                else:
                    seg = int(seg) << 12
                    segHi, segLo = self.word_to_bytes(seg)
                    result = f":02000002{int(seg):04X}{self.checksum(list((2, 2, segHi, segLo))):02X}\n"
        address = offs
        checksum = self.checksum(list((length, hi, lo)) + list(row))
        self.previosAddress = offs + length
        result += f":{length:02X}{address:04X}{DATA:02X}{Writer.hex_bytes(row)!s}{checksum:02X}"
        return result

    def compose_footer(self, meta):
        hi, lo = self.word_to_bytes(self.start_address)
        return f":00{self.start_address:04X}{EOF:02X}{self.checksum(list((hi, lo, EOF))):02X}\n"
