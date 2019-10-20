#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.1"

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

from collections import namedtuple

from objutils.registry import registry

##
##  registryister codecs.
##

import objutils.binfile
registry.register('bin', objutils.binfile.Reader, objutils.binfile.Writer, "Plain binary format.")
registry.register('binzip', objutils.binfile.BinZipReader, objutils.binfile.BinZipWriter, "Zipped binary format.")

import objutils.sig
registry.register('sig', objutils.sig.Reader, objutils.sig.Writer, "Signetics format.")

import objutils.srec
registry.register('srec', objutils.srec.Reader, objutils.srec.Writer, "Motorola S-Records (a.k.a. S19).")

import objutils.titxt
registry.register('titxt', objutils.titxt.Reader, objutils.titxt.Writer, "Texas Instruments MSP430 text format.")

import objutils.emon52
registry.register('emon52', objutils.emon52.Reader, objutils.emon52.Writer, "Elektor Monitor (EMON52) file format.")

#import objutils.elf
# TODO!!!

import objutils.etek
registry.register('etek', objutils.etek.Reader, objutils.etek.Writer, "Extended Tektonix format.")

import objutils.fpc
registry.register('fpc', objutils.fpc.Reader, objutils.fpc.Writer, "Four packed code file format.")

#import objutils.ieee695
# TODO!!!

import objutils.ihex
registry.register('ihex', objutils.ihex.Reader, objutils.ihex.Writer, "Intel IHex format.")

import objutils.mostec
registry.register('mostec', objutils.mostec.Reader, objutils.mostec.Writer, "MOSTech format.")

import objutils.rca
registry.register('rca', objutils.rca.Reader, objutils.rca.Writer, "RCA format.")

import objutils.tek
registry.register('tek', objutils.tek.Reader, objutils.tek.Writer, "Tektonix format.")

import objutils.cosmac
registry.register('cosmac', objutils.cosmac.Reader, objutils.cosmac.Writer, "RCA COSMAC format.")

import objutils.ash
registry.register('ash', objutils.ash.Reader, objutils.ash.Writer, "ASCII hex space formats.")

##
##  Interface to objutils.
##
def load(codecName, *args, **kws):
    return registry.get(codecName).Reader().load(*args, **kws)

def loads(codecName, *args, **kws):
    return registry.get(codecName).Reader().loads(*args, **kws)

def probe(*args, **kws):
    found = False
    for name, codec in registry._codecs.items():
        reader = codec.Reader()
        found = reader.probe(*args, **kws)
        if found:
            break
    return reader.codecName if found else None

def probes(*args, **kws):
    found = False
    for name, codec in registry:
        reader = codec.Reader()
        found = reader.probes(*args, **kws)
        if found:
            break
    return reader.codecName if found else None

def dump(codecName, *args, **kws):
    registry.get(codecName).Writer().dump(*args, **kws)

def dumps(codecName, *args, **kws):
    return registry.get(codecName).Writer().dumps(*args, **kws)

