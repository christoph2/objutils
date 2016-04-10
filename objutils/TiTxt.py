#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import sys
import objutils.HexFile as HexFile
from objutils.Segment import Segment, joinSegments
from objutils.Image import Image
from objutils.utils import PYTHON_VERSION
from objutils.registry import register


class Reader(HexFile.ASCIIHexReader):
    """
    """

    def __init__(self, addressPattern = r'^@(?P<address>[0-9a-zA-Z]{2,8})\s*$',
                 dataPattern = r'^(?:[0-9a-zA-Z]{{2,4}}[{0}]?)*\s*$', etxPattern = r'^q.*$'):
        super(Reader, self).__init__(addressPattern, dataPattern, etxPattern)


class Writer(HexFile.ASCIIHexWriter):

    def __init__(self, addressDesignator = '@'):
        super(Writer, self).__init__(addressDesignator)

    def composeFooter(self, meta):
        return "q"

register('titxt', Reader, Writer, "Texas Instruments MSP430 text format.")

