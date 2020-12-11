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

import objutils.hexfile as hexfile


class Reader(hexfile.ASCIIHexReader):
    """
    """

    def __init__(self, address_pattern = r'^@(?P<address>[0-9a-zA-Z]{2,8})\s*$',
                 data_pattern = r'^(?:[0-9a-zA-Z]{{2,4}}[{0}]?)*\s*$', etx_pattern = r'^q.*$'):
        super(Reader, self).__init__(address_pattern, data_pattern, etx_pattern)


class Writer(hexfile.ASCIIHexWriter):

    def __init__(self, address_designator = '@'):
        super(Writer, self).__init__(address_designator)

    def compose_footer(self, meta):
        return "q"
