#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

"""Parser for ELF files.
"""

__copyright__ = """
   objutils - Object file library for Python.

  (C) 2010-2020 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import hashlib
from itertools import groupby
import re
import time


from construct import Adapter, Array, CString, Const, Enum, IfThenElse, Padding, Struct
from construct import BitStruct, BitsInteger, Bytes, Construct, this
from construct import Computed, Pass, Tell, Union, singleton
from construct import Int8ul, Int16ul, Int32ul, Int32sl, Int64ul, Int64sl
from construct import         Int16ub, Int32ub, Int32sb, Int64ub, Int64sb

from sqlalchemy import (func, not_
)

from objutils import Image, Section
from objutils.utils import create_memorymapped_fileview
from objutils.elf import defs, model
from objutils.elf.arm import attributes


MAGIC = b'\x7fELF'


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
        super().__init__()
        self.flagbuildnone = True
    def _parse(self, stream, context, path):
        return None
    def _build(self, obj, stream, context, path):
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


class ElfFileStruct(Struct):

    def __init__(self, *args, **kws):
        super(ElfFileStruct, self).__init__(*args, **kws)

    def elf32Addr(self):
        pass

    def setByteOrder(self):
        print("*** {}".format(self))


DebugInfo = namedtuple('DebugInfo', 'section image')


class DBAPI:
    """

    """

    def __init__(self, parent):
        self._session = parent.session

    @property
    def session(self):
        return self._session

    @property
    def query(self):
        return self.session.query


class SectionAPI(DBAPI):
    """
    """

    def get(self, section_name: str):
        """Get a single section.

        Parameters
        ----------

        section_name: str

        Returns
        -------
        """

        query = self.query(model.Elf_Section)
        query = query.filter(model.Elf_Section.section_name == section_name)
        return query.first()

    def fetch(self, sections: str = None, name_pattern: str = None, order_by_address: bool = True):
        """

        Returns
        -------
        """

        query = self.query(model.Elf_Section)
        if name_pattern:
            query = query.filter(func.regexp(model.Elf_Section.section_name, name_pattern))
        if order_by_address:
            query = query.order_by(model.Elf_Section.sh_addr)
        else:
            query = query.order_by(model.Elf_Section.section_name)
        result = query.all()
        return result


        #query = query.order_by(model.Elf_Symbol.section_name)

        #for key, value in groupby(query.all(), lambda s: s.section_name):
        #    result[key] = list(value)
        #return result


class SymbolAPI(DBAPI):
    """
    """

    def get(self, symbol_name: str, section_name: str = None):
        """Get a single symbol.

        Parameters
        ----------

        symbol_name: str or list of strings.
            Symbol(s) to look for.

        section_name: str
            Consider only named section, else lookup all sections.

        Returns
        -------
        """
        if isinstance(symbol_name, str):
            names = [symbol_name]

        query = self.query(model.Elf_Symbol)
        if section_name:
            query = query.filter(model.Elf_Symbol.section_name == section_name)
        query = query.filter(model.Elf_Symbol.symbol_name == symbol_name)
        return query.first()

    def fetch(self, sections: str = None, name_pattern: str = None,
        bindings : str = None, access: str = None, types_str: str = None, order_by_value: bool = True):
        """

        Returns
        -------
        """
        result = OrderedDict()
        query = self.query(model.Elf_Symbol)
        if sections:
            sections = [s for s in re.split(r"[ ,]", sections) if s]
            query = query.filter(model.Elf_Symbol.section_name.in_(sections))
        if access:
            access = [a for a in re.split(r"[ ,]", access) if a]
            value = 0
            for item in access:
                item = item.lower()
                if item == "a":
                    value |= defs.SectionFlags.SHF_ALLOC
                elif item == "w":
                    value |= defs.SectionFlags.SHF_WRITE
                elif item == "x":
                    value |= defs.SectionFlags.SHF_EXECINSTR
            query = query.filter(model.Elf_Symbol.access.op('&')(value))
        if bindings:
            bindings = [b for b in re.split(r"[ ,]", bindings) if b]
            flt = []
            for item in bindings:
                item = item.lower()
                if item == "g":
                    flt.append(defs.SymbolBinding.STB_GLOBAL)
                elif item == "l":
                    flt.append(defs.SymbolBinding.STB_LOCAL)
                elif item == "w":
                    flt.append(defs.SymbolBinding.STB_WEAK)
            query = query.filter(model.Elf_Symbol.st_bind.in_(flt))
        if types_str:
            types_arr = [t for t in re.split(r"[ ,]", types_str) if t]
            flt = []
            for item in types_arr:
                item = item.lower()
                if item == "notype":
                    flt.append(defs.SymbolType.STT_NOTYPE)
                elif item == "object":
                    flt.append(defs.SymbolType.STT_OBJECT)
                elif item == "func":
                    flt.append(defs.SymbolType.STT_FUNC)
                elif item == "section":
                    flt.append(defs.SymbolType.STT_SECTION)
                elif item == "file":
                    flt.append(defs.SymbolType.STT_FILE)
                elif item == "common":
                    flt.append(defs.SymbolType.STT_COMMON)
                elif item == "tls":
                    flt.append(defs.SymbolType.STT_TLS)
                query = query.filter(model.Elf_Symbol.st_type.in_(flt))
        if name_pattern:
            query = query.filter(func.regexp(model.Elf_Symbol.symbol_name, name_pattern))
        query = query.order_by(model.Elf_Symbol.section_name)
        if order_by_value:
            query = query.order_by(model.Elf_Symbol.st_value)
        else:
            query = query.order_by(model.Elf_Symbol.symbol_name)
        for key, value in groupby(query.all(), lambda s: s.section_name):
            result[key] = list(value)
        return result

    def fetch_gcc_special_symbols(self):
        """

        Returns
        -------

        Note
        ----
        This is a GCC specific feature and will not work with other compilers.
        """
        syms = self.query(model.Elf_Symbol).filter(model.Elf_Symbol.st_shndx == defs.SectionName.SHN_ABS)
        syms = syms.filter(model.Elf_Symbol.symbol_name != "")
        syms = syms.filter(func.regexp(model.Elf_Symbol.symbol_name, "_.*"))
        syms = syms.filter(model.Elf_Symbol.st_type == defs.SymbolType.STT_NOTYPE)
        return syms.order_by(model.Elf_Symbol.st_value).all()


def calculate_crypto_hash(data):
    sha = hashlib.sha512(data)
    return sha.hexdigest()


class ElfParser(object):
    """
    """

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
        "Addr":   (Int64ul, Int64ub),   # 8 - Unsigned program address
        "Off":    (Int64ul, Int64ub),   # 8 - Unsigned file offset
        "Half":   (Int16ul, Int16ub),   # 2 - Unsigned medium integer
        "Word":   (Int32ul, Int32ub),   # 4 - Unsigned integer
        "Sword":  (Int32sl, Int32sb),   # 4 - Signed integer
        "Xword":  (Int64ul, Int64ub),   # 8 - Unsigned long integer
        "Sxword": (Int64sl, Int64sb),   # 8 - Signed long integer
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
        self.fp = create_memorymapped_fileview(filename)
        sha = calculate_crypto_hash(self.fp.tobytes())

        self.db = model.Model()
        self.session = self.db.session
        self.symbols = SymbolAPI(self)
        self.sections = SectionAPI(self)
        self._images = dict()
        self._sections_by_name = OrderedDict()
        self.asciiCString = CString(encoding = "ascii")
        self._basic_header = ElfParser.BasicHeader.parse(self.fp)
        self.b64 = (self.ei_class == 2)
        if self.ei_data == 1:   # Little-Endian
            offset = 0
        elif self.ei_data == 2: # Big-Endian
            offset = 1
        else:
            raise ValueError("EI_DATA has an invalid value. Got: {}".format(self.ei_data))
        self._endianess = "<" if self.ei_data == 1 else ">"
        datatypes = ElfParser.DATATYPES64.items() if self.b64 else ElfParser.DATATYPES32.items()
        for key, value in datatypes:
            setattr(self, key, value[offset])
        self._parser_extended_header()
        self._parse_section_headers()
        self._parse_program_headers()
        self.create_section_to_segment_mapping()
        for section in self._symbol_sections:
            self._parse_symbol_section(section)
        self.session.commit()

    def _parser_extended_header(self):
        ExtendedHeader = Struct(
            "e_type" / self.Half,        # Object file type
            "e_machine" / self.Half,     # Machine type
            "e_version" / self.Word,     # Object file version
            "e_entry" / self.Addr,       # Entry point address
            "e_phoff" / self.Off,        # Program header offset
            "e_shoff" / self.Off,        # Section header offset
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
        sections = []
        self._symbol_sections = []
        if hasattr(self, 'e_shnum'):
            self._section_headers = SectionHeaders.parse(self.fp[self.e_shoff : ])
            for idx, section in enumerate(self._section_headers.sections):
                if section.allocate:
                    image = self.fp[section.sh_offset : section.sh_offset + section.sh_size]
                else:
                    image = None
                if image is not None:
                    image = image.tobytes()
                self._images[idx] = image
                section.image = image
            for idx, section in enumerate(self._section_headers.sections):
                name = self.get_string(self.e_shstrndx, section.sh_name)
                section.name = name
                self._sections_by_name[name] = section
                image = self._images[idx]
                if section.sh_type == defs.SectionType.SHT_NOTE:
                    note_obj = self._parse_note(image)
                    if note_obj:
                        note = model.Elf_Note(
                            section_name = name, type = note_obj.type, name = note_obj.name, desc = note_obj.desc
                        )
                        sections.append(note)
                elif section.sh_type in (defs.SectionType.SHT_SYMTAB, defs.SectionType.SHT_DYNSYM):
                    self._symbol_sections.append(section)
                elif name == ".comment":
                    cmt_text = self._parse_comment(image)
                    if cmt_text:
                        comment = model.Elf_Comment(text = cmt_text)
                        sections.append(comment)
                db_sec = model.Elf_Section(index = idx, section_name = name, sh_name = section.sh_name,
                    sh_type = section.sh_type, sh_flags = section.sh_flags, sh_addr = section.sh_addr,
                    sh_offset = section.sh_offset, sh_size = section.sh_size, sh_link = section.sh_link,
                    sh_info = section.sh_info, sh_addralign = section.sh_addralign, sh_entsize = section.sh_entsize,
                    section_image = image
                )
                sections.append(db_sec)
            self.session.bulk_save_objects(sections)

    def get_string(self, table_index, entry):
        if entry > len(self._images[table_index]):
            return ""
        name = self.asciiCString.parse(self._images[table_index][entry : ])
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
            #if self.e_shnum:
            #    print("PG_size: {}".format(ProgramHeaders.sizeof() / self.e_phnum))
            self._program_headers = ProgramHeaders.parse(self.fp[self.e_phoff : ])

    def _parse_symbol_section(self, section):
        sh_link = section.sh_link
        symbols = []
        Symbol = Struct(
            "st_name" / self.Word,
            "st_value" / self.Addr,
            "st_size" / self.Word,
            "st_info" / BitStruct(
                "st_bind" / BitsInteger(4),
                "st_type" / BitsInteger(4),
            ),
            "st_other" / Int8ul,
            "symbol_name" / Computed(lambda ctx: self.get_string(sh_link, ctx.st_name)),
            "st_shndx" / self.Half,
        )
        symbol_cache = {}
        num_symbols = len(section.image) // Symbol.sizeof()
        for offset in range(0, len(section.image), Symbol.sizeof()):
            sym = Symbol.parse(section.image[offset : offset + Symbol.sizeof()])
            section_header = None
            if sym.st_shndx in defs.SpecialSections:
                section_name = defs.special_section_name(sym.st_shndx)
            else:
                if not sym.st_shndx in symbol_cache:
                    section_header = self.session.query(model.Elf_Section).\
                        filter(model.Elf_Section.index == sym.st_shndx).first()
                    if section_header:
                        section_name = section_header.section_name
                    else:
                        section_name = str(sym.st_shndx)
            db_sym = model.Elf_Symbol(st_name = sym.st_name, st_value = sym.st_value, st_size = sym.st_size,
                st_bind = sym.st_info.st_bind, st_type = sym.st_info.st_type, st_other = sym.st_other,
                st_shndx = sym.st_shndx, symbol_name = sym.symbol_name, section_name = section_name,
                access = section_header.sh_flags if section_header else 0
            )
            symbols.append(db_sym)
        self.session.bulk_save_objects(symbols)
        self.session.commit()

    def _parse_comment(self, data):
        Line = Struct(
            "line" / CString("ascii"),
            "pos" / Tell
        )
        if not data:
            return ""
        length = len(data)
        result = []
        i = 0
        if data.find(b"\x00") == -1:
            return str(data, "ascii")
        while i < length:
            #print("*** LINE", data[i : ])
            line = Line.parse(data[i : ])
            if line.line:
                result.append(line.line)
            i += line.pos
        return '\n'.join(result)

    def _parse_note(self, data):
        Note = Struct(
            "namesz" / self.Word,
            "descsz" / self.Word,
            "type" / self.Word,
            "name" / Bytes(this.namesz),
            "desc" / Bytes(this.descsz)
        )
        if not data:
            return None
        result = Note.parse(data)
        result.desc = binascii.b2a_hex(result.desc).decode()
        result.name = self.asciiCString.parse(result.name)
        return result

    def debug_sections(self):
        ds = OrderedDict()
        for idx, section in enumerate(self.sections.fetch()):
            name = section.section_name
            if name.startswith('.debug'):
                if name == '.debug_abbrev':
                    pass
                ds[name] = section
        result = OrderedDict()
        for name, section in ds.items():
            result[name]= DebugInfo(section, section.section_image)
        return result

    def section_in_segment1(self, section_header, segment, check_vma, strict):
        has_offset = False
        valid_segment = False
        has_VMA = False
        has_dynamic_size = False
        valid_segment = ((section_header.sh_flags & defs.SectionFlags.SHF_TLS) != 0) and (segment.p_type == defs.PT_TLS or \
            segment.p_type == defs.PT_GNU_RELRO or segment.p_type == defs.PT_LOAD) or \
            ((section_header.sh_flags & defs.SectionFlags.SHF_TLS) == 0 and segment.p_type != defs.PT_TLS and \
            segment.p_type != defs.PT_PHDR)
        has_offset = section_header.sh_type == defs.SectionType.SHT_NOBITS or (section_header.sh_offset >= segment.p_offset \
            and (not strict or (section_header.sh_offset - segment.p_offset <= segment.p_filesz - 1)) \
            and ((section_header.sh_offset - segment.p_offset + self.section_size(section_header, segment)) <= \
            (segment.p_filesz)))
        has_VMA = (not check_vma or (section_header.sh_flags & defs.SectionFlags.SHF_ALLOC) == 0 or (section_header.sh_addr >= \
            segment.p_vaddr and (not strict or (section_header.sh_addr - segment.p_vaddr <= segment.p_memsz - 1)) \
            and ((section_header.sh_addr - segment.p_vaddr + self.section_size(section_header, segment)) <= segment.p_memsz))
        )
        has_dynamic_size = (segment.p_type != defs.PT_DYNAMIC or section_header.sh_size != 0 or segment.p_memsz == 0 \
            or ((section_header.sh_type == defs.SectionType.SHT_NOBITS or (section_header.sh_offset > segment.p_offset \
            and (section_header.sh_offset - segment.p_offset < segment.p_filesz))) \
            and ((section_header.sh_flags & defs.SectionFlags.SHF_ALLOC) == 0 \
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
##
##            for j in range(self.e_shnum):
##                section = self.sections[j]
##                if not self.tbss_special(section, segment) and self.section_in_segment_strict(section, segment):
##                    mapping[idx].append(j)
##
        self.sections_to_segments = mapping
        return self.sections_to_segments

    def tbss_special(self, section_header, segment):
       return ((section_header.sh_flags & defs.SectionFlags.SHF_TLS) != 0 and
           section_header.sh_type == defs.SectionType.SHT_NOBITS and segment.p_type != defs.PT_TLS
        )

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
    def endianess(self):
        return self._endianess

    @property
    def segments(self):
        return self._program_headers['segments']

    @property
    def arm_attributes(self):
        res = self.query(model.Elf_Section).filter(model.Elf_Section.section_name == ".ARM.attributes").first()
        if res:
            return attributes.parse(res.section_image, byteorder = self.endianess)
        else:
            return {}

    @property
    def comment(self):
        comment = self.query(model.Elf_Comment).first()
        if comment:
            return comment.text
        else:
            return None

    @property
    def notes(self):
        notes = self.query(model.Elf_Note).order_by(model.Elf_Note.section_name).all()
        if notes:
            return notes
        else:
            return []

    @property
    def query(self):
        return self.session.query

    def create_image(self, join: bool = True, include_pattern: str = None, exclude_pattern: str = None, callback: callable = None):
        """

        Parameters
        ----------
        join: bool
            Try to join/merge sections.

        include_pattern: str
            Include only sections matching a Python RegEx

        exclude_pattern: str
            Exclude sections matching a Python RegEx

        callback: callable
            Could be used to generate output for your command-line tools.

            Called with:
                - state: "start" | "stop" | "section"
                - section -- current section (only applicable to state "section").

        Returns
        -------
        `objutils.Image`

        Note
        ----
        `include_pattern` and `exclude_pattern` should be used mutually exclusive, unless you know what you are doing.

        Note
        ----
        Look at `scripts/oj_elf_extract.py` to see `create_image()` in action.
        """
        query = sections = self.query(model.Elf_Section)
        query = query.filter(
            model.Elf_Section.flag_alloc == True,
            model.Elf_Section.has_content == True,
        )

        if include_pattern:
            query = query.filter(func.regexp(model.Elf_Section.section_name, include_pattern))

        if exclude_pattern:
            query = query.filter(not_(func.regexp(model.Elf_Section.section_name, exclude_pattern)))

        query = query.order_by(model.Elf_Section.sh_addr)
        result = []
        if callback:
            callback("start", None)
        for section in query.all():
            if callback:
                callback("section", section)
            result.append(Section(section.sh_addr, section.section_image))
        img = Image(result, join = join)
        if callback:
            callback("stop", None)
        return img
