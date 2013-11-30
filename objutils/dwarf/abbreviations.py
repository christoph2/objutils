#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2013 by Christoph Schueler <github.com/Christoph2,
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

from collections import namedtuple
from operator import itemgetter, attrgetter

from objutils.dwarf import constants, dwarfreader

AbbreviationEntry = namedtuple('Abbreviation', 'tag, children, attrs')

SET_OFFSET      = 1
IGNORE_OFFSET   = 2

def processAbbreviations(section):
    image = section.image
    dr = dwarfreader.DwarfReader(image)
    totalSize = len(image)
    abbrevs = {}
    abbrevEntries = {}
    offsetState = SET_OFFSET
    while dr.pos < totalSize:
        if offsetState == SET_OFFSET:
            offset = dr.pos
            offsetState = IGNORE_OFFSET
        code = dr.uleb()
        if code == 0:
            abbrevs[offset] = abbrevEntries
            abbrevEntries = {}
            offsetState = SET_OFFSET
            continue
        tagValue = dr.uleb()
        tag = constants.TAG_MAP.get(tagValue, tagValue)
        children = dr.u8()
        attrSpecs = []
        while True:
            attrValue = dr.uleb()
            attr = constants.AttributeEncoding(attrValue)
            formValue = dr.uleb()
            form = constants.AttributeForm(formValue)
            if attrValue == 0 and formValue == 0:
                break
            attrSpecs.append((attr, form))
        abbrevEntries[code] = AbbreviationEntry(tag, "DW_CHILDREN_yes" if children == constants.DW_CHILDREN_yes else "DW_CHILDREN_no", attrSpecs)
    return abbrevs

