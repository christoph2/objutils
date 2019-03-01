#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Reader/Writer for plain binfiles.
"""

__version__ = "0.1.1"

__copyright__ = """
    pyObjUtils - Object file library for Python.

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

from collections import defaultdict, namedtuple
import logging
from functools import partial
import math
import os
import re
import sys

from objutils.section import Section, joinSections
from objutils.image import Image
from operator import itemgetter
from objutils.pickleif import PickleIF
from objutils.utils import slicer, createStringBuffer, PYTHON_VERSION
from objutils.logger import Logger

##
## TODO: binzipped format: a separate file for each section + MANIFEST (csv: fname, address, length)
##

class Reader(object):

    def load(self, fp, address = 0x0000):
        data = fp.read()
        sec = Section(address, data)
        img = Image([sec], valid = True)
        if hasattr(fp, "close"):
            fp.close()
        return img

    def loads(self, image, address = 0x0000):
        if PYTHON_VERSION.major == 3:
            if isinstance(image, str):
                return self.load(createStringBuffer(bytes(image, "ascii")), address)
            else:
                return self.load(createStringBuffer(image), address)
        else:
            return self.load(createStringBuffer(image), address)


class Writer(object):
    pass

