#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
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

import binascii
from collections import namedtuple, OrderedDict
import enum
import os
from pprint import pprint
import struct
import time


from construct import Struct, If, Const, Adapter, FlagsEnum, Enum, String, Array, Padding, HexDump, Probe, CString, IfThenElse
from construct import Pointer, Byte, GreedyRange, Bytes, Construct, this, GreedyBytes, RepeatUntil, BitStruct, BitsInteger
from construct import singleton, Pass, Computed, Switch, Union, GreedyString, GreedyBytes, Tell, Computed
from construct import Int8ul, Int16ul, Int32ul, Int32sl, Int64ul, Int64sl
from construct import         Int16ub, Int32ub, Int32sb, Int64ub, Int64sb

from objutils.utils import create_memorymapped_fileview
from objutils.elf import defs

from objutils.dwarf import DwarfProcessor

def is_hidden_symbol(sym):
    return sym.st_other in (defs.SymbolVisibility.STV_HIDDEN, defs.SymbolVisibility.STV_INTERNAL)

@singleton
class Pass2(Construct):
    r"""
    A do-nothing construct, useful as the default case for Switch. Returns None on parsing, puts nothing on building.
    Example::
        >>> Pass.parse(b"")
        >>> Pass.build(None)
        b''
        >>> Pass.sizeof()
        0
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.flagbuildnone = True
    def _parse(self, stream, context, path):
        #print("ÜÜÜ", context)
        return None
    def _build(self, obj, stream, context, path):
        #print(obj)
        pass
    def _sizeof(self, context, path):
        return 0

Test = Struct(
    "ei_version"  / Enum(Int8ul, default = Pass,
        EV_NONE = 0,
        EV_CURRENT = 1,
    )
)


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

MAGIC = b'\x7fELF'

import datetime
import time
import mmap

class Sh_Type(enum.IntEnum):
    """

    """
    SHT_NULL        = 0
    SHT_PROGBITS    = 1
    SHT_SYMTAB      = 2
    SHT_STRTAB      = 3
    SHT_RELA        = 4
    SHT_HASH        = 5
    SHT_DYNAMIC     = 6
    SHT_NOTE        = 7
    SHT_NOBITS      = 8
    SHT_REL         = 9
    SHT_SHLIB       = 10
    SHT_DYNSYM      = 11
    SHT_LOPROC      = 0x70000000
    SHT_HIPROC      = 0x7fffffff
    SHT_LOUSER      = 0x80000000
    SHT_HIUSER      = 0xffffffff


class ElfFileStruct(Struct):

    def __init__(self, *args, **kws):
        super(ElfFileStruct, self).__init__(*args, **kws)

    def elf32Addr(self):
        pass

    def setByteOrder(self):
        print("*** {}".format(self))



DebugInfo = namedtuple('DebugInfo', 'section image')

class ElfParser(object):

    EI_NIDENT = 16

    DATATYPES32 = {
        "Addr":   (Int32ul, Int32ub),   # 4 - Unsigned program address
        "Half":   (Int16ul, Int16ub),   # 2 - Unsigned medium integer
        "Off":    (Int32ul, Int32ub),   # 4 - Unsigned file offset
        "Sword":  (Int32sl, Int32sb),   # 4 - Signed large integer
        "Word":   (Int32ul, Int32ub),   # 4 - Unsigned large integer
        "Xword":  (Int32ul, Int32ub),   # 8 - Unsigned long integer
        "Sxword": (None, None),         # 8 - Signed long integer
    }

    DATATYPES64 = {
        "Addr":   (Int64ul, Int64ub), # 8 - Unsigned program address
        "Off":    (Int64ul, Int64ub), # 8 - Unsigned file offset
        "Half":   (Int16ul, Int16ub), # 2 - Unsigned medium integer
        "Word":   (Int32ul, Int32ub), # 4 - Unsigned integer
        "Sword":  (Int32sl, Int32sb), # 4 - Signed integer
        "Xword":  (Int64ul, Int64ub), # 8 - Unsigned long integer
        "Sxword": (Int64sl, Int64sb), # 8 - Signed long integer
    }


    BasicHeader = Struct(
        "header" / Union(None,
            "fields"/ Struct(
                Const(MAGIC),
                "ei_class"  / Int8ul,
                "ei_data"  / Int8ul,
                "ei_version"  / Int8ul,
                "ei_osabi" / Int8ul,
                "ei_abiversion" / Int8ul,
                Padding(7),
            ),
            "bytes" / Bytes(EI_NIDENT)
        ),
    )

    def __init__(self, filename):
        self._images = dict()
        self._sections_by_name = OrderedDict()
        self.asciiCString = CString(encoding = "ascii")
        self.fp = create_memorymapped_fileview(filename)
        print(filename, flush = True)
        self._basic_header = ElfParser.BasicHeader.parse(self.fp)
        self.b64 = (self.ei_class == 2)
        self.endianess = self.ei_data
        if self.ei_data == 1:   # Little-Endian
            offset = 0
        elif self.ei_data == 2: # Big-Endian
            offset = 1
        else:
            offset = 0          # TODO: Error!!!
        datatypes = ElfParser.DATATYPES64.items() if self.b64 else ElfParser.DATATYPES32.items()
        for key, value in datatypes:
            setattr(self, key, value[offset])
        print(self._basic_header)
        self._parser_extended_header()
        self._parse_section_headers()
        self._parse_program_headers()
        self.create_section_to_segment_mapping()

    def _parser_extended_header(self):
        ExtendedHeader = Struct(
            "e_type" / self.Half,        # Object file type
            "e_machine" / self.Half,     # Machine type
            "e_version" / self.Word,     # Object file version
            "e_entry" / self.Addr,       # Entry point address
            "e_phoff" / self.Off,         # Program header offset
            "e_shoff" / self.Off,         # Section header offset
            "e_flags" / self.Word,       # Processor-specific flags
            "e_ehsize" / self.Half,      # ELF header size
            "e_phentsize" / self.Half,   # Size of program header entry
            "e_phnum" / self.Half,       # Number of program header entries
            "e_shentsize" / self.Half,   # Size of section header entry
            "e_shnum" / self.Half,       # Number of section header entries
            "e_shstrndx" / self.Half,    # Section name string table index
        )
        self._extended_header = ExtendedHeader.parse(self.fp[self.EI_NIDENT : ])

    def _parse_section_headers(self):
        SectionHeaders = Struct(
            "sections" / Array(lambda ctx: self.e_shnum,
                "section" / Struct(
                    "sh_name" / self.Word,
                    "sh_type" / self.Word,
                    "sh_flags" / self.Xword,
                    "sh_addr" / self.Addr,
                    "sh_offset" / self.Off,
                    "sh_size" / self.Xword,
                    "sh_link" / self.Word,
                    "sh_info" / self.Word,
                    "sh_addralign" / self.Xword,
                    "sh_entsize" /self.Xword,
                    "allocate" / Computed(lambda ctx: (ctx.sh_type not in (0, 8) and ctx.sh_size > 0)),
                )
            )
        )
        if hasattr(self, 'e_shnum'):
            if self.e_shnum:
                print("SH_size: {}".format(SectionHeaders.sizeof() / self.e_shnum))
            self._section_headers = SectionHeaders.parse(self.fp[self.e_shoff : ])
            for idx, section in enumerate(self._section_headers.sections):
                if section.allocate:
                    image = self.fp[section.sh_offset : section.sh_offset + section.sh_size]
                else:
                    image = None
                self._images[idx] = image
                section.image = image
            for section in self._section_headers.sections:
                name = self.get_string(self.e_shstrndx, section.sh_name)
                section.name = name
                self._sections_by_name[name] = section
                if section.sh_type == Sh_Type.SHT_NOTE:
                    print("NOTE!!! {:08X} {:04X}".format(section.sh_offset, section.sh_size))
                    self._parse_note(self.fp[section.sh_offset : section.sh_offset + section.sh_size])
                elif section.sh_type in (defs.SHT_SYMTAB, defs.SHT_DYNSYM):
                    self._parse_symbol_section(section)

    def get_string(self, table_index, entry):
        name = self.asciiCString.parse(self._images[table_index][entry : ])
        print("get_string: {}".format(name))
        return name

    def _parse_program_headers(self):
        ProgramHeaders = Struct(
            "segments" / Array(lambda ctx: self.e_phnum,
                "segment" / IfThenElse(lambda ctx: self.b64,
                    Struct(
                        "p_type" / self.Word,
                        "p_flags" / self.Word,
                        "p_offset" / self.Off,
                        "p_vaddr" / self.Addr,
                        "p_paddr" / self.Addr,
                        "p_filesz" / self.Xword,
                        "p_memsz" / self.Xword,
                        "p_align" / self.Xword,
                    ),
                    Struct(
                        "p_type" / self.Word,
                        "p_offset" / self.Off,
                        "p_vaddr" / self.Addr,
                        "p_paddr" / self.Addr,
                        "p_filesz" / self.Word,
                        "p_memsz" / self.Word,
                        "p_flags" / self.Word,
                        "p_align" / self.Word,
                    )
                ),
            )
        )
        if hasattr(self, 'e_shnum'):
            if self.e_shnum:
                print("PG_size: {}".format(ProgramHeaders.sizeof() / self.e_phnum))
            self._program_headers = ProgramHeaders.parse(self.fp[self.e_phoff : ])

    def _parse_symbol_section(self, section):
        Symbol = Struct(
            "st_name" / self.Word,
            "st_value" / self.Addr,
            "st_size" / self.Word,
            "st_info" / BitStruct(
                "bind" / BitsInteger(4),
                "type" / BitsInteger(4),
            ),
            "st_other" / Int8ul,
            "st_shndx" / self.Half,
             "hidden" / Computed(lambda ctx: ctx.st_other in
                 (defs.SymbolVisibility.STV_HIDDEN, defs.SymbolVisibility.STV_INTERNAL)),
        )
        num_symbols = len(section.image) // Symbol.sizeof()
        for offset in range(0, len(section.image), Symbol.sizeof()):
            sym = Symbol.parse(section.image[offset : offset + Symbol.sizeof()])
            print(sym)

    def _parse_note(self, data):
        Note = Struct(
            "namesz" / self.Word,
            "descsz" / self.Word,
            "type" / self.Word,
            "name" / Bytes(this.namesz),
            "desc" / Bytes(this.descsz)
        )
        print(len(data), data.tobytes())
        result = Note.parse(data)
        #result.name = binascii.b2a_hex(result.name).decode()
        result.desc = binascii.b2a_hex(result.desc).decode()
        print(result.desc)
        print(result)

    def debug_sections(self):
        ds = OrderedDict()
        for idx, section in enumerate(self.sections):
            name = section.name
            if name.startswith('.debug'):
                print(name)
                if name == '.debug_abbrev':
                    pass
                ds[name] = section
        result = OrderedDict()
        for name, section in ds.items():
            result[name]= DebugInfo(section, section.image)
        return result

    def section_in_segment1(self, section_header, segment, check_vma, strict):
        has_offset = False
        valid_segment = False
        has_VMA = False
        has_dynamic_size = False
        valid_segment = ((section_header.sh_flags & defs.SHF_TLS) != 0) and (segment.p_type == defs.PT_TLS or \
            segment.p_type == defs.PT_GNU_RELRO or segment.p_type == defs.PT_LOAD) or \
            ((section_header.sh_flags & defs.SHF_TLS) == 0 and segment.p_type != defs.PT_TLS and \
            segment.p_type != defs.PT_PHDR)
        has_offset = section_header.sh_type == defs.SHT_NOBITS or (section_header.sh_offset >= segment.p_offset \
            and (not strict or (section_header.sh_offset - segment.p_offset <= segment.p_filesz - 1)) \
            and ((section_header.sh_offset - segment.p_offset + self.section_size(section_header, segment)) <= \
            (segment.p_filesz)))
        has_VMA = (not check_vma or (section_header.sh_flags & defs.SHF_ALLOC) == 0 or (section_header.sh_addr >= \
            segment.p_vaddr and (not strict or (section_header.sh_addr - segment.p_vaddr <= segment.p_memsz - 1)) \
            and ((section_header.sh_addr - segment.p_vaddr + self.section_size(section_header, segment)) <= segment.p_memsz))
        )
        has_dynamic_size = (segment.p_type != defs.PT_DYNAMIC or section_header.sh_size != 0 or segment.p_memsz == 0 \
            or ((section_header.sh_type == defs.SHT_NOBITS or (section_header.sh_offset > segment.p_offset \
            and (section_header.sh_offset - segment.p_offset < segment.p_filesz))) \
            and ((section_header.sh_flags & defs.SHF_ALLOC) == 0 \
            or (section_header.sh_addr > segment.p_vaddr \
            and (section_header.sh_addr - segment.p_vaddr < segment.p_memsz)))) \
        )
        return (valid_segment and has_offset and has_VMA and has_dynamic_size)

    def section_in_segment(self, section_header, segment):
        return self.section_in_segment1(section_header, segment, 1, 0)

    def section_in_segment_strict(self, section_header, segment):
        return self.section_in_segment1(section_header, segment, 1, 1)

    def create_section_to_segment_mapping(self):
        mapping = OrderedDict()
        for idx in range(self.e_phnum):
            segment = self.segments[idx]
            mapping[idx] = []
            for j in range(self.e_shnum):
                section = self.sections[j]
                if not self.tbss_special(section, segment) and self.section_in_segment_strict(section, segment):
                    mapping[idx].append(j)
                    print(section)
        self.sections_to_segments = mapping
        return self.sections_to_segments

    def tbss_special(self, section_header, segment):
       return ((section_header.sh_flags & defs.SHF_TLS) != 0 and
           section_header.sh_type == defs.SHT_NOBITS and segment.p_type != defs.PT_TLS
        )

    def buildSymbols(self):
        for section in self.sectionHeaders:
            if section.shType in (defs.SHT_SYMTAB, defs.SHT_DYNSYM):
                syms = []
                for idx, symbol in section.symbols.items():
#                    sym = Symbol(self.getString(section.shLink, symbol.st_name), symbol.st_value, symbol.st_size,
#                                 self.getSymbolType(symbol.st_info & 0x0f),
#                                 self.getSymbolBinding(symbol.st_info >> 4), self.getSymbolVisibility(symbol.st_other),
#                        self.getSymbolIndexType(self.header, symbol.st_shndx))
                    syms.append(sym)
                self.symbols[section.shName] = syms


    def section_size(self, section_header, segment):
        return 0 if self.tbss_special(section_header, segment) else section_header.sh_size

    def get_basic_header_field(self, name):
        return getattr(self._basic_header.header.fields, name)

    def get_extended_header_field(self, name):
        return getattr(self._extended_header, name)

    @property
    def ei_class(self):
        return self.get_basic_header_field('ei_class')

    @property
    def ei_data(self):
        return self.get_basic_header_field('ei_data')

    @property
    def ei_version(self):
        return self.get_basic_header_field('ei_version')

    @property
    def ei_osabi(self):
        return self.get_basic_header_field('ei_osabi')

    @property
    def ei_abiversion(self):
        return self.get_basic_header_field('ei_abiversion')

    @property
    def header_bytes(self):
        return self._basic_header.header.bytes

    @property
    def e_type(self):
        return self.get_extended_header_field('e_type')

    @property
    def e_machine(self):
        return self.get_extended_header_field('e_machine')

    @property
    def e_version(self):
        return self.get_extended_header_field('e_version')

    @property
    def e_entry(self):
        return self.get_extended_header_field('e_entry')

    @property
    def e_phoff(self):
        return self.get_extended_header_field('e_phoff')

    @property
    def e_shoff(self):
        return self.get_extended_header_field('e_shoff')

    @property
    def e_flags(self):
        return self.get_extended_header_field('e_flags')

    @property
    def e_ehsize(self):
        return self.get_extended_header_field('e_ehsize')

    @property
    def e_phentsize(self):
        return self.get_extended_header_field('e_phentsize')

    @property
    def e_phnum(self):
        return self.get_extended_header_field('e_phnum')

    @property
    def e_shentsize(self):
        return self.get_extended_header_field('e_shentsize')

    @property
    def e_shnum(self):
        return self.get_extended_header_field('e_shnum')

    @property
    def e_shstrndx(self):
        return self.get_extended_header_field('e_shstrndx')

    @property
    def sections(self):
        return self._section_headers.sections

    @property
    def segments(self):
        return self._program_headers['segments']

def main():
    #fname = r'f:\projekte\csProjects\yOBJl\objutils\tests\ELFFiles\lib_with_two_dynstr_sections_reversed.so.1.elf'
    fname = r'f:\projekte\csProjects\yOBJl\objutils\tests\ELFFiles\testfile51'
    #fname = r'C:\projekte\csProjects\yOBJl\objutils\tests\ELFFiles\testfile_i686_core'
    ep = ElfParser(fname)
    print(ep.ei_class)
    print(ep.e_machine)
    print(ep.header_bytes)
    #pprint(ep._sections_by_name)
    print(Sh_Type.SHT_NOTE == 7)
    dbSecs = ep.debug_sections()
    abbrevs = dbSecs['.debug_abbrev']

    dp = DwarfProcessor(dbSecs, ep.b64, ep.endianess)
    dp.doAbbrevs()
    dp.doMacInfo()

    #doAbbrevs(abbrevs)
    #macs = dbSecs['.debug_macinfo']
    #doMacInfo(macs)
    #print(bytes(macs.image))

if __name__ == '__main__':
    main()

