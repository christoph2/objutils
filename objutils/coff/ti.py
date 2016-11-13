#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

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

import os
import struct
import time


import construct
from construct import Struct, If, Const, Adapter, FlagsEnum, Enum, String, Array, Padding, HexDump, Probe
from construct import OnDemandPointer, Pointer, Byte, GreedyRange, Bytes, Int16ul, Int32ul, this

from objutils.utils import memoryMap


class UTCTimeStampAdapter(Adapter):
    def _decode(self, obj, context):
        return time.ctime(obj)
    def _encode(self, obj, context):
        return int(time.mktime(time.strptime(obj)))

def UTCTimeStamp(name):
    return UTCTimeStampAdapter(name / Int32ul)


symbol = Struct(
    "name" / String(8, padchar = b"\x00"),
    "symbolValue" / Int32ul,
    "sectionNumber" / Int16ul,
    "reserved" / Int16ul,
    "storageClass" / Enum(Byte,
        C_NULL      = 0,       # No storage class
        C_USTATIC   = 14,      # Undefined static
        C_AUTO      = 1,       # Reserved
        C_ENTAG     = 15,      # Reserved
        C_EXT       = 2,       # External definition
        C_MOE       = 16,      # Reserved
        C_STAT      = 3,       # Static
        C_REGPARM   = 17,      # Reserved
        C_REG       = 4,       # Reserved
        C_FIELD     = 18,      # Reserved
        C_EXTREF    = 5,       # External reference
        C_UEXT      = 19,      # Tentative external definition
        C_LABEL     = 6,       # Label
        C_STATLAB   = 20,      # Static load time label
        C_ULABEL    = 7,       # Undefined label
        C_EXTLAB    = 21,      # External load time label
        C_MOS       = 8,       # Reserved
        C_VARARG    = 27,      # Last declared parameter of a function with a variable number of arguments
        C_ARG       = 9,       # Reserved
        C_BLOCK     = 100,     # Reserved
        C_STRTAG    = 10,      # Reserved
        C_FCN       = 101,     # Reserved
        C_MOU       = 11,      # Reserved
        C_EOS       = 102,     # Reserved
        C_UNTAG     = 12,      # Reserved
        C_FILE      = 103,     # Reserved
        C_TPDEF     = 13,      # Reserved
        C_LINE      = 104,     # Used only by utility programs
    ),
    "numberOfAuxiliaryEntries" / Byte,
)

auxSymbol = Struct(
    "sectionLength" / Int32ul,
    "numberOfRelocationEntries" / Int16ul,
    "numberOfLineNumberEntries" / Int16ul,
    Padding(10),
)

fileHeader = Struct(
    "versionID" / Int16ul,
    "numSectionHeaders" / Int16ul,
    UTCTimeStamp("timestamp"),
    "filePoimter" / Int32ul,
    "numSymbols" / Int32ul,

    "symbols" / Pointer(this.filePoimter,
            #Byte[this.numSymbols * symbol.sizeof()],
            Bytes(this.numSymbols * symbol.sizeof()),
    ),
    #GreedyRange(Byte("foo"))

    "sizeOptHeader" / Int16ul,

    "flags"  / FlagsEnum(Int16ul,
        F_RELFLG    = 0x0001,
        F_EXEC      = 0x0002,
        F_LNNO      = 0x0004,
        F_LSYMS     = 0x0008,
        F_LITTLE    = 0x0100,
        F_BIG       = 0x0200,
        F_SYMMERGE  = 0x1000,
    ),

    "targetID" / Enum(Int16ul,
        TMS470          = 0x0097,
        TMS320C5400     = 0x0098,
        TMS320C6000     = 0x0099,
        TMS320C5500     = 0x009C,
        TMS320C2800     = 0x009D,
        MSP430          = 0x00A0,
        TMS320C5500plus = 0x00A1,
    ),


    "optionalFileHeader" / If(this.sizeOptHeader == 28,
        Struct(
            "magic" / Int16ul, # Const(b'\0x01\0x08'),
            "version" / Int16ul,
            "executableSize" / Int32ul,
            "initializedDataSize" / Int32ul,
            "uninitializedDataSize" / Int32ul,
            "entryPoint" / Int32ul,
            "executableCodeAddress" / Int32ul,
            "initializedDataAddress" / Int32ul,
        )
    ),

    Probe(),

    "sections" / Array(this.numSectionHeaders,   #
        Struct(

               "name" / String(8, padchar = b"\x00"),
               "physiclAddress" / Int32ul,
               "virtualAddress" / Int32ul,
               "sectionSize" / Int32ul,
               "filePointer" / Int32ul,

               "image" / Pointer(this.filePointer, # OnDemandPointer
                    HexDump(Bytes(this.sectionSize))
               ),

               "relocationPointer" / Int32ul,
               "reserved" / Int32ul, # !?
               "numberOfRelocationEntries" / Int32ul,
               "numberOfLineNumberEntries" / Int32ul,

               "flags" / FlagsEnum(Int32ul,
                    STYP_REG        = 0x00000000,     # Regular section (allocated, relocated, loaded)
                    STYP_DSECT      = 0x00000001,     # Dummy section (relocated, not allocated, not loaded)
                    STYP_NOLOAD     = 0x00000002,     # Noload section (allocated, relocated, not loaded)
                    STYP_GROUP      = 0x00000004,     # Grouped section (formed from several input sections). Other devices: Reserved
                    STYP_PAD        = 0x00000008,     # Padding section (loaded, not allocated, not relocated). Other devices: Reserved
                    STYP_COPY       = 0x00000010,     # Copy section (relocated, loaded, but not allocated; relocation entries are processed normally)
                    STYP_TEXT       = 0x00000020,     # Section contains executable code
                    STYP_DATA       = 0x00000040,     # Section contains initialized data
                    STYP_BSS        = 0x00000080,     # Section contains uninitialized data
                    STYP_BLOCK      = 0x00001000,     # Alignment used as a blocking factor.
                    STYP_PASS       = 0x00002000,     # Section should pass through unchanged.
                    STYP_CLINK      = 0x00004000,     # Section requires conditional linking
                    STYP_VECTOR     = 0x00008000,     # Section contains vector table.
                    STYP_PADDED     = 0x00010000,     # Section has been padded.
               ),

               "reserved2" / Int16ul,
               "memoryPageNumber" / Int16ul,
        )
    ),
)



def parseSymbols(coff):
    extraEntry = 0
    for idx in range(coff.numSymbols):
        if extraEntry:
            sym = auxSymbol.parse(coff.symbols[ idx * auxSymbol.sizeof() : ])
            print(sym)
            extraEntry = 0
        else:
            sym = symbol.parse(coff.symbols[ idx * symbol.sizeof() : ])
            print(sym)
            extraEntry = sym.numberOfAuxiliaryEntries

