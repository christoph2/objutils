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

from collections import namedtuple

from objutils.registry import Registry

reg = Registry()

##
##  Register codecs.
##
import objutils.ASH
reg.register('ash', objutils.ASH.Reader, objutils.ASH.Writer, "ASCII hex space formats.")

import objutils.Sig
reg.register('sig', objutils.Sig.Reader, objutils.Sig.Writer, "Signetics format.")

import objutils.SRecords
reg.register('srec', objutils.SRecords.Reader, objutils.SRecords.Writer, "Motorola S-Records (a.k.a. S19).")

import objutils.TiTxt
reg.register('titxt', objutils.TiTxt.Reader, objutils.TiTxt.Writer, "Texas Instruments MSP430 text format.")

import objutils.EMon52
reg.register('emon52', objutils.EMon52.Reader, objutils.EMon52.Writer, "Elektor Monitor (EMON52) file format.")

import objutils.Elf
# TODO!!!

import objutils.ETek
reg.register('etek', objutils.ETek.Reader, objutils.ETek.Writer, "Extended Tektonix format.")

import objutils.FPC
reg.register('fpc', objutils.FPC.Reader, objutils.FPC.Writer, "Four packed code file format.")

import objutils.IEEE695
# TODO!!!

import objutils.IHex
reg.register('ihex', objutils.IHex.Reader, objutils.IHex.Writer, "Intel IHex format.")

import objutils.MOSTec
reg.register('mostec', objutils.MOSTec.Reader, objutils.MOSTec.Writer, "MOSTech format.")

import objutils.RCA
reg.register('rca', objutils.RCA.Reader, objutils.RCA.Writer, "RCA format.")

#import objutils.cosmac
#reg.register('cosmac', objutils.cosmac.Reader, objutils.cosmac.Writer, "RCA COSMAC format.")

import objutils.Tek
reg.register('tek', objutils.Tek.Reader, objutils.Tek.Writer, "Tektonix format.")

##
##  Interface to objutils.
##
def load(codecName, *args, **kws):
    return reg.get(codecName).Reader().load(*args, **kws)

def loads(codecName, *args, **kws):
    return reg.get(codecName).Reader().loads(*args, **kws)

def dump(codecName, *args, **kws):
    reg.get(codecName).Writer().dump(*args, **kws)

def dumps(codecName, *args, **kws):
    return reg.get(codecName).Writer().dumps(*args, **kws)

