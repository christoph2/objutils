#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2015 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from objutils.registry import getCodec

##
##  Interface to OBJUTILS.
##
def load(codecName, *args, **kws):
    return getCodec(codecName).reader.load(*args, **kws)

def loads(codecName, *args, **kws):
    return getCodec(codecName).reader.loads(*args, **kws)

def dump(codecName, *args, **kws):
    getCodec(codecName).writer.dump(*args, **kws)

def dumps(codecName, *args, **kws):
    return getCodec(codecName).writer.dumps(*args, **kws)


def _importer():
    import objutils.Sig
    import objutils.SRecords
    #import objutils.ASH
    import objutils.EMon52
    import objutils.Elf
    import objutils.ETek
    import objutils.FPC
    import objutils.IEEE695
    import objutils.IHex
    import objutils.MOSTec
    import objutils.RCA
    import objutils.Tek

_importer()

