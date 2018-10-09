#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2017 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from collections import namedtuple, OrderedDict
import os
import struct
import time


import construct
from construct import Struct, If, Const, Adapter, FlagsEnum, Enum, String, Array, Padding, HexDump, Probe, CString, IfThenElse
from construct import Pointer, Byte, GreedyRange, Bytes, Int16ul, Int32ul, Construct, this, GreedyBytes, Switch

from objutils.utils import createMemoryMappedFileView


class UTCTimeStampAdapter(Adapter):

    def _decode(self, obj, context):
        return time.ctime(obj)

    def _encode(self, obj, context):
        return int(time.mktime(time.strptime(obj)))


def UTCTimeStamp(name):
    return UTCTimeStampAdapter(name / Int32ul)


class ListToBytesAdapter(Adapter):

    def _decode(self, obj, context):
        return bytes(obj)

    def _encode(self, obj, context):
        return list(obj)


class PrintContext(Construct):

    def _parse(self, stream, context, *args, **kws):
        print("CTX: {} {} {}".format(context, args, kws))
        print("CTX_END")


symbol = Struct(
    "name" / Bytes(8),
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

relocationType = Enum(Int16ul,
    R_ABS       = 0x0000,     # No relocation
    R_REL24     = 0x0005,     # 24-bit reference to symbol's address
    R_RELBYTE   = 0x000F,     # 8-bit direct reference to symbol's address
    R_RELWORD   = 0x0010,     # 16-bit direct reference to symbol's address
    R_RELLONG   = 0x0011,     # 32-bit direct reference to symbol's address
    R_PCR23H    = 0x0016,     # 23-bit PC-relative reference to a symbol's address, in halfwords (divided by 2)

    #R_RELBYTE   = 0x0017,     # 8-bit direct reference to symbol's address
    #R_PCR24W    = 0x0017,     # 24-bit PC-relative reference to a symbol's address, in words (divided by 4)

    #R_RELWORD   = 0x0020,     # 16-bit direct reference to symbol's address
    #R_RELLONG   = 0x0021,     # 32-bit direct reference to symbol's address
                              #
    R_PARTLS7   = 0x0028,     # 7 LSBs of an address
    R_PARTMS9   = 0x0029,     # 9 MSBs of an address
    R_REL13     = 0x002A,     # 13-bit direct reference to symbol's address
    R_C60BASE   = 0x0050,     # Data page pointer-based offset
    R_C60DIR15  = 0x0051,     # Load or store long displacement
    R_C60PCR21  = 0x0052,     # 21-bit packet, PC relative
    R_C60PCR10  = 0x0053,     # 10-bit Packet PC Relative (BDEC, BPOS)
    R_C60LO16   = 0x0054,     # MVK instruction low half register
    R_C60HI16   = 0x0055,     # MVKH or MVKLH high half register
    R_C60SECT   = 0x0056,     # Section-based offset
    R_C60S16    = 0x0057,     # Signed 16-bit offset for MVK
    R_PARTLS6   = 0x005D,     # 6-bit offset of a 22-bit address
    R_PARTMID10 = 0x005E,     # Middle 10 bits of a 22-bit address
    R_REL22     = 0x005F,     # 22-bit direct reference to a symbol's address
    R_PARTMS6   = 0x0060,     # Upper 6 bits of an 22-bit address
    R_PARTS16   = 0x0061,     # Upper 16 bits of an 22-bit address
    R_C28PCR16  = 0x0062,     # PC relative 16-bit address
    R_C28PCR8   = 0x0063,     # PC relative 8-bit address
    R_C28PTR    = 0x0064,     # 22-bit pointer
    R_C28HI16   = 0x0065,     # High 16 bits of address data
    R_C28LOPTR  = 0x0066,     # Pointer to low 64K
    R_C28NWORD  = 0x0067,     # 16-bit negated relocation
    R_C28NBYTE  = 0x0068,     # 8-bit negated relocation
    R_C28HIBYTE = 0x0069,     # High 8 bits of a 16-bit data
    R_C28RELS13 = 0x006A,     # Signed 13-bit value relocated as a 16-bit value
    R_C60PCR7   = 0x0070,     # 7-bit Packet PC Relative (ADDKPC)
    R_C60PCR12  = 0x0071,     # 12-bit Packet PC Relative (BNOP)
    R_LD3_DMA   = 0x0170,     # 7 MSBs of a byte, unsigned; used in DMA address
    R_LD3_MDP   = 0x0172,     # 7 bits spanning 2 bytes, unsigned; used as MDP register value
    R_LD3_PDP   = 0x0173,     # 9 bits spanning 2 bytes, unsigned; used as PDP register value
    R_LD3_REL23 = 0x0174,     # 23-bit unsigned value in 24-bit field
    R_LD3_k8    = 0x0210,     # 8-bit unsigned direct reference
    R_LD3_k16   = 0x0211,     # 16-bit unsigned direct reference
    R_LD3_K8    = 0x0212,     # 8-bit signed direct reference
    R_LD3_K16   = 0x0213,     # 16-bit signed direct reference
    R_LD3_I8    = 0x0214,     # 8-bit unsigned PC-relative reference
    R_LD3_I16   = 0x0215,     # 16-bit unsigned PC-relative reference
    R_LD3_L8    = 0x0216,     # 8-bit signed PC-relative reference
    R_LD3_L16   = 0x0217,     # 16-bit signed PC-relative reference
    R_LD3_k4    = 0x0220,     # Unsigned 4-bit shift immediate
    R_LD3_k5    = 0x0221,     # Unsigned 5-bit shift immediate
    R_LD3_K5    = 0x0222,     # Signed 5-bit shift immediate
    R_LD3_k6    = 0x0223,     # Unsigned 6-bit shift immediate
    R_LD3_k12   = 0x0224,     # Unigned 12-bit shift immediate
                              #
    RE_ADD      = 0x4000,     # Addition (+)
    RE_SUB      = 0x4001,     # Subtraction (-)
    RE_NEG      = 0x4002,     # Negate (-)
    RE_MPY      = 0x4003,     # Multiplication (*)
    RE_DIV      = 0x4004,     # Division (/)
    RE_MOD      = 0x4005,     # Modulus (%)
    RE_SR       = 0x4006,     # Logical shift right (unsigned >>)
    RE_ASR      = 0x4007,     # Arithmetic shift right (signed >>)
    RE_SL       = 0x4008,     # Shift left (<<)
    RE_AND      = 0x4009,     # And (&)
    RE_OR       = 0x400A,     # Or (|)
    RE_XOR      = 0x400B,     # Exclusive Or (^)
    RE_NOTB     = 0x400C,     # Not (~)
    RE_ULDFLD   = 0x400D,     # Unsigned relocation field load
    RE_SLDFLD   = 0x400E,     # Signed relocation field load
    RE_USTFLD   = 0x400F,     # Unsigned relocation field store
    RE_SSTFLD   = 0x4010,     # Signed relocation field store
    RE_PUSH     = 0x4011,     # Push symbol on the stack
    RE_PUSHSK   = 0x4012,     # Push signed constant on the stack
    RE_PUSHUK   = 0x4013,     # Push unsigned constant on the stack
    RE_PUSHPC   = 0x4014,     # Push current section PC on the stack
    RE_DUP      = 0x4015,     # Duplicate top-of-stack and push a copy
    RE_XSTFLD   = 0x4016,     # Relocation field store, signedness is irrelevant
    RE_PUSHSV   = 0xC011,     # Push symbol: SEGVALUE flag is set
)

relocation10 = Struct(
    "virtualAddress" / Int32ul,
    "symbolTableIndex" / Int16ul,
    Padding(2),
    "relocationType" / Int16ul,
    #relocationType
)

relocation12 = Struct(
    "virtualAddress" / Int32ul,
    "symbolTableIndex" / Int32ul,
    "addressExtension" / Int16ul,
    "relocationType" / Int16ul,
    #relocationType
)


fileHeader = Struct(
    "versionID" / Int16ul,
    "numSectionHeaders" / Int16ul,
    UTCTimeStamp("timestamp"),
    "filePoimter" / Int32ul,
    "numSymbols" / Int32ul,

    "symbols" / Pointer(this.filePoimter,
            Bytes(this.numSymbols * symbol.sizeof()),
    ),


    "stringTable" / Pointer( (this.filePoimter + (this.numSymbols * symbol.sizeof()) + 0),
            ListToBytesAdapter(GreedyRange(Byte))
    ),


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

    "sections" / Array(this.numSectionHeaders,
        Struct(

               "name" / Bytes(8),
               "physicalAddress" / Int32ul,
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

               "parsedRelocations" / Pointer(this.relocationPointer,
                    Array(this.numberOfRelocationEntries,
                          Struct(
                              "virtualAddress" / Int32ul,
                              "symbolTableIndex" / IfThenElse(lambda ctx: ctx._._.targetID in ("TMS320C2800", "TMS320C6000", "TMS470", "MSP430"),
                                    Int16ul,
                                    Int32ul
                              ),
                              IfThenElse(lambda ctx: ctx._._.targetID in ("TMS320C2800", "TMS320C6000", "TMS470", "MSP430"),
                                    Padding(2),
                                    "addressExtension" / Int16ul
                              ),
                              "relocationType" / Int16ul,

##
##                              "relocationType" / Enum(Int16ul,
##                                  Switch(lambda ctx: ctx._._.targetID,
##                                    {
##                                        1:Byte,
##                                        2:Int32ub
##                                    }
##                                  ),
##                                  RE_ADD      = 0x4000,     # Addition (+)
##                                  RE_SUB      = 0x4001,     # Subtraction (-)
##                                  RE_NEG      = 0x4002,     # Negate (-)
##                                  RE_MPY      = 0x4003,     # Multiplication (*)
##                                  RE_DIV      = 0x4004,     # Division (/)
##                                  RE_MOD      = 0x4005,     # Modulus (%)
##                                  RE_SR       = 0x4006,     # Logical shift right (unsigned >>)
##                                  RE_ASR      = 0x4007,     # Arithmetic shift right (signed >>)
##                                  RE_SL       = 0x4008,     # Shift left (<<)
##                                  RE_AND      = 0x4009,     # And (&)
##                                  RE_OR       = 0x400A,     # Or (|)
##                                  RE_XOR      = 0x400B,     # Exclusive Or (^)
##                                  RE_NOTB     = 0x400C,     # Not (~)
##                                  RE_ULDFLD   = 0x400D,     # Unsigned relocation field load
##                                  RE_SLDFLD   = 0x400E,     # Signed relocation field load
##                                  RE_USTFLD   = 0x400F,     # Unsigned relocation field store
##                                  RE_SSTFLD   = 0x4010,     # Signed relocation field store
##                                  RE_PUSH     = 0x4011,     # Push symbol on the stack
##                                  RE_PUSHSK   = 0x4012,     # Push signed constant on the stack
##                                  RE_PUSHUK   = 0x4013,     # Push unsigned constant on the stack
##                                  RE_PUSHPC   = 0x4014,     # Push current section PC on the stack
##                                  RE_DUP      = 0x4015,     # Duplicate top-of-stack and push a copy
##                                  RE_XSTFLD   = 0x4016,     # Relocation field store, signedness is irrelevant
##                                  RE_PUSHSV   = 0xC011,     # Push symbol: SEGVALUE flag is set
##                              )
##
                          )
                    ),
                ),
               Probe(),
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


SymbolTuple = namedtuple("SymbolTuple", "name value sectionNumber storageClass sectionLength numberOfRelocationEntries numberOfLineNumberEntries")


class TICOFF(object):
    """
    """

    def __init__(self, filename):
        self.fp = createMemoryMappedFileView(filename)
        self.coff = fileHeader.parse(self.fp, size = self.fp.size())

        self.header = self.parseHeader()
        self.symbols = self.parseSymbols()
        self.sections = self.parseSections()


    def symbolName(self, name):
        if name.startswith(b'\x00\x00\x00\x00'):
            vs = Struct(Padding(4), "value" / Int32ul).parse(name)
            return CString().parse(self.coff.stringTable[vs.value : ]).decode("ascii")
        else:
            return String(8, padchar = b"\x00").parse(name).decode("ascii")


    def parseSymbols(self):
        extraEntry = 0
        #result = OrderedDict()
        result = []

        SECTION_NUMBERS = {
            0xfffd:  "N_RES",
            0xfffe:  "N_ABS",
            0     :  "N_UNDEF",
        }
        st = None
        sectionLength = 0
        numberOfRelocationEntries = 0
        numberOfLineNumberEntries = 0
        for idx in range(self.coff.numSymbols):
            if extraEntry:
                sym = auxSymbol.parse(self.coff.symbols[ idx * auxSymbol.sizeof() : ])

                st = result.pop()
                result.append(st._replace(sectionLength = sym.sectionLength, numberOfRelocationEntries = sym.numberOfRelocationEntries,
                            numberOfLineNumberEntries = sym.numberOfLineNumberEntries
                ))

                extraEntry = 0
            else:
                sym = symbol.parse(self.coff.symbols[ idx * symbol.sizeof() : ])

                name = self.symbolName(sym.name)
                st = SymbolTuple(name, sym.symbolValue, sym.storageClass, SECTION_NUMBERS.get(sym.sectionNumber, sym.sectionNumber),0 ,0, 0)
                result.append(st)
                extraEntry = sym.numberOfAuxiliaryEntries
        return result

    Header = namedtuple('Tuple', 'versionID timestamp numSectionHeaders numSymbols flags targetID')

    def parseHeader(self):
        self.coff.targetID

        return self.Header(self.coff.versionID, self.coff.timestamp, self.coff.numSectionHeaders, self.coff.numSymbols,
                self.coff.flags, self.coff.targetID)

    Section = namedtuple("Section", "name physicalAddress virtualAddress sectionSize flags memoryPageNumber image")

    def parseSections(self):
        result = OrderedDict()
        for section in self.coff.sections:
            name = self.symbolName(section.name)
            result[name] = self.Section(name, section.physicalAddress, section.virtualAddress, section.sectionSize,
                section.flags, section.memoryPageNumber, section.image)
        return result

    def getRelocations(self, section):
        pass

