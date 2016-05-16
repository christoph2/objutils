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
import objutils.sig
reg.register('sig', objutils.sig.Reader, objutils.sig.Writer, "Signetics format.")

import objutils.srec
reg.register('srec', objutils.srec.Reader, objutils.srec.Writer, "Motorola S-Records (a.k.a. S19).")

import objutils.titxt
reg.register('titxt', objutils.titxt.Reader, objutils.titxt.Writer, "Texas Instruments MSP430 text format.")

import objutils.emon52
reg.register('emon52', objutils.emon52.Reader, objutils.emon52.Writer, "Elektor Monitor (EMON52) file format.")

#import objutils.Elf
# TODO!!!

import objutils.etek
reg.register('etek', objutils.etek.Reader, objutils.etek.Writer, "Extended Tektonix format.")

import objutils.fpc
reg.register('fpc', objutils.fpc.Reader, objutils.fpc.Writer, "Four packed code file format.")

#import objutils.ieee695
# TODO!!!

import objutils.ihex
reg.register('ihex', objutils.ihex.Reader, objutils.ihex.Writer, "Intel IHex format.")

import objutils.mostec
reg.register('mostec', objutils.mostec.Reader, objutils.mostec.Writer, "MOSTech format.")

import objutils.rca
reg.register('rca', objutils.rca.Reader, objutils.rca.Writer, "RCA format.")

import objutils.tek
reg.register('tek', objutils.tek.Reader, objutils.tek.Writer, "Tektonix format.")

import objutils.cosmac
reg.register('cosmac', objutils.cosmac.Reader, objutils.cosmac.Writer, "RCA COSMAC format.")

import objutils.ash
reg.register('ash', objutils.ash.Reader, objutils.ash.Writer, "ASCII hex space formats.")

##
##  Interface to objutils.
##
def load(codecName, *args, **kws):
    return reg.get(codecName).Reader().load(*args, **kws)

def loads(codecName, *args, **kws):
    return reg.get(codecName).Reader().loads(*args, **kws)

def probe(*args, **kws):
    found = False
    for name, codec in reg._codecs.items():
        reader = codec.Reader()
        found = reader.probe(*args, **kws)
        if found:
            break
    return reader.codecName if found else None

def probes(*args, **kws):
    found = False
    for name, codec in reg:
        reader = codec.Reader()
        found = reader.probes(*args, **kws)
        if found:
            break
    return reader.codecName if found else None

def dump(codecName, *args, **kws):
    reg.get(codecName).Writer().dump(*args, **kws)

def dumps(codecName, *args, **kws):
    return reg.get(codecName).Writer().dumps(*args, **kws)

