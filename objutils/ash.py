#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

##
##  ASCII Space Hex format.
##

from functools import partial
import re
import objutils.hexfile as hexfile
from objutils.checksums import lrc

STX = '\x02'
ETX = '\x03'

DATA = re.compile(r'(?:.*?\02)(?P<chunks>.*)(?:\03)\s*(?:\$\$(?P<checksum>[0-9a-zA-Z]{2,4})[,.])?', re.DOTALL | re.MULTILINE)
ADDRESS = re.compile(r'\$A(?P<value>[0-9a-zA-Z]{2,8})[,.]\s*')
LINE_SPLIITER = re.compile(r"[ %,']")

checksum = partial(lrc, width = 16)

class Reader(hexfile.ASCIIHexReader):
    """
    """
    VALID_CHARS = re.compile(r"^[a-fA-F0-9 %,\'\$\x02\x03\n\r]*$")

    def __init__(self, address_pattern = r'^(?:(?P<stx>[\x02])\s+)?\$A(?P<address>[0-9a-zA-Z]{2,8})[,.]\s*$',
                 data_pattern = r'^(?:[0-9a-zA-Z]{{2,4}}[{0}]?)*\s*$', etx_pattern = r'^q.*$'):
        super(Reader, self).__init__(address_pattern, data_pattern, etx_pattern, separators = ", %'")


class Writer(hexfile.ASCIIHexWriter):

    MAX_ADDRESS_BITS = 16
    ADDRESS_DESIGNATOR = '$A'

    def __init__(self, address_designator = '$A'):
        super(Writer, self).__init__(address_designator)

    def compose_header(self, meta):
        self.checksum = 0
        self.previous_address = None
        line ="{0} ".format(STX)
        return line

    def compose_footer(self, meta):
        line = "{0}$${1:04X},".format(ETX, self.checksum % 65536)
        return line

    def row_callout(self, address, length, row):
        self.checksum += checksum(row)
