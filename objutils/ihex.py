#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <github.com/Christoph2,
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

from functools import partial
import operator
import objutils.hexfile as hexfile
from objutils.checksums import lrc, COMPLEMENT_TWOS
import objutils.utils as utils
import objutils.checksums as checksums

DATA                        = 0
EOF                         = 1
EXTENDED_SEGMENT_ADDRESS    = 2
START_SEGMENT_ADDRESS       = 3
EXTENDED_LINEAR_ADDRESS     = 4
START_LINEAR_ADDRESS        = 5


class Reader(hexfile.Reader):

    FORMAT_SPEC = (
        (hexfile.TYPE_FROM_RECORD, ":LLAAAATTDDCC"),
        )

    def __init__(self):
        super(Reader,self).__init__()
        self.segmentAddress = 0

    def check_line(self, line, format_type):
        if line.length != len(line.chunk):
            raise hexfile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        checksum = checksums.lrc(utils.make_list(line.type, line.length, utils.int_to_array(line.address), line.chunk), 8, checksums.COMPLEMENT_TWOS)
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
                line.add_processing_instruction(('segment', segment))
                self._address_calculator = partial(operator.add, segment << shift_by)
                self.debug("EXTENDED_{0}_ADDRESS: {1:#X}".format(name.upper(), segment))
            else:
                self.error("Bad Extended {0} Address at line #{1}.".format(name, line.line_number))

    def special_processing(self, line, format_type):
        if line.type == DATA:
            line.address = self._address_calculator(line.address)
        elif line.type == EXTENDED_SEGMENT_ADDRESS:
            self.calculate_extended_address(line, 4, "Segment")
        elif line.type == START_SEGMENT_ADDRESS:
            if len(line.chunk) == 4:
                cs = ((line.chunk[0]) << 8) | (line.chunk[1])
                ip = ((line.chunk[2]) << 8) | (line.chunk[3])
                line.add_processing_instruction(('cs', cs))
                line.add_processing_instruction(('ip', ip))
                self.debug("START_SEGMENT_ADDRESS: {0}:{1}".format(hex(cs), hex(ip)))
            else:
                self.error("Bad Segment Address at line %{0:u}.".format(line.line_number))
        elif line.type == EXTENDED_LINEAR_ADDRESS:
            self.calculate_extended_address(line, 16, "Linear")
        elif line.type == START_LINEAR_ADDRESS:
            if len(line.chunk) == 4:
                eip = ((line.chunk[0]) << 24) | ((line.chunk[1]) << 16) | ((line.chunk[2]) << 8) | (line.chunk[3])
                line.add_processing_instruction(('eip', eip))
                self.debug("START_LINEAR_ADDRESS: {0}".format(hex(eip)))
            else:
                self.error("Bad Linear Address at line #{0:d}.".format(line.line_number))
        elif line.type == EOF:
            pass
        else:
            self.warn("Invalid record type [{0:u}] at line {1:u}".format(line.type, line.line_number))

    _address_calculator = utils.identity


def divmod(a, b):
    return a / b, a % b

class Writer(hexfile.Writer):

    MAX_ADDRESS_BITS = 32
    checksum = partial(lrc, width = 8, comp = COMPLEMENT_TWOS)

    def pre_processing(self, image):
        self.previosAddress = None
        self.start_address = 0

    def compose_row(self, address, length, row):
        result = ''
        seg, offs = divmod(address, 0x10000)
        h, l = self.word_to_bytes(address)
        if offs != self.previosAddress:
            #print("NEQ: {0:04x} [{1:04x}:{2:04x}]".format(address, seg, offs))
            if address > 0xffff:
                if address > 0xfffff:
                    segHi, segLo = self.word_to_bytes(seg)
                    result = ":02000004{0:04X}{1:02X}\n".format(int(seg), self.checksum(list((2, 4, segHi, segLo))))
                else:
                    seg = int(seg) << 12
                    segHi, segLo = self.word_to_bytes(seg)
                    result = ":02000002{0:04X}{1:02X}\n".format(int(seg), self.checksum(list((2, 2, segHi, segLo))))
        address = offs
        checksum = self.checksum(list((length, h, l)) + list(row))
        self.previosAddress = offs + length
        result += ":{0:02X}{1:04X}{2:02X}{3!s}{4:02X}".format(length, address, DATA, Writer.hex_bytes(row), checksum)
        return result

    def compose_footer(self, meta):
        h, l = self.word_to_bytes((self.start_address))
        return ":00{1:04X}{0:02X}{2:02X}\n".format(EOF, self.start_address, self.checksum(list((h, l, EOF))))
