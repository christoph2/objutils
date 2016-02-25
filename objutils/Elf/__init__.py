#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import enum
from collections import namedtuple, OrderedDict
import mmap
import os
import sys
import types
import struct

from objutils.Elf import defs
from objutils.logger import Logger


#
#   Reference:
#   ----------
#   Tool Interface Standard (TIS): Executable and Linking Format (ELF) Specification Version 1.2
#


class Alias(object):
    # Install more convenient names.
    def __init__(self,key, convert = False):
        self.key = key
        self.convert = convert

    def __get__(self, obj, objtype = None):
        if obj is None:
            return self
        value = getattr(obj, self.key)
        return value

    def __set__(self, obj, value):
        data = getattr(obj, 'data')
        setattr(data, self.key,value)
        c = getattr(data, self.key)

    def __delete__(self, obj):
        raise AttributeError("can't delete attribute")



class FormatError(Exception): pass

import struct


INDENT_HEADER_FORMAT = "B" * defs.EI_NIDENT
IndentHeaderType = namedtuple("IndentHeaderType", """e_ident0 e_ident1 e_ident2 e_ident3 e_ident4 e_ident5 e_ident6
e_ident7 e_ident8 e_ident9 e_ident10 e_ident11 e_ident12 e_ident13 e_ident14 e_ident15""")  # MagicHeaderAttributes


class Attributor(object):

    def __init__(self, format, attributes, byteOrderPrefix = "@"):
        self.format = format
        self.length = struct.calcsize(format)
        self.attributes = attributes
        self.byteOrderPrefix = byteOrderPrefix

    def apply(self, data, target):
        ddd = self.attributes(*struct.unpack("{0}{1}".format(self.byteOrderPrefix, self.format), data))
        for name, value in ddd._asdict().items():
            setattr(target, name, value)

    def __len__(self):
        return self.length

class ELFHeader(object):

    magicHeader = Attributor(INDENT_HEADER_FORMAT, IndentHeaderType)

    def __init__(self, parent):
        self.parent = parent
        parent.fp.seek(0, os.SEEK_SET)
        self.magicBytes = parent.fp.read(len(self.magicHeader))

        if self.magicBytes[ : 4] != defs.ELF_MAGIC:    # 7f 45 4c 46
            raise FormatError("Not an ELF file - it has the wrong magic bytes at the start.")

        self.magicHeader.apply(self.magicBytes, self)
        self.is64Bit = (self.elfClass ==  defs.ELFClass.ELFCLASS64)
        self.byteOrderPrefix = defs.BYTEORDER_PREFIX[defs.ELFDataEncoding(self.elfByteOrder)]

        elfHeader = Attributor(defs.HDR_FMT64 if self.is64Bit else defs.HDR_FMT32, defs.Elf32_Ehdr, self.byteOrderPrefix)
        rawData = parent.fp.read(len(elfHeader))
        elfHeader.apply(rawData, self)

        if self.elfEHSize!= (len(self.magicHeader) + len(elfHeader)):
            raise FormatError("Wrong header size.")
        self.hasStringTable = not (self.elfStringTableIndex == defs.SHN_UNDEF)


    @property
    def elfTypeName(self):
        return defs.ELF_TYPE_NAMES.get(defs.ELFType(self.elfType), "Processor-specific.")

    @property
    def elfMachineName(self):
        try:
            return defs.ELF_MACHINE_NAMES.get(defs.ELFMachineType(self.elfMachine))
        except ValueError:
            return "<unknown>: 0x{0:04x}".format(self.elfMachine)

    @property
    def elfClassName(self):
        return defs.ELF_CLASS_NAMES.get(defs.ELFClass(self.elfClass), "<unknown>")

    @property
    def elfByteOrderName(self):
        return defs.ELF_BYTE_ORDER_NAMES.get(defs.ELFDataEncoding(self.elfByteOrder), "<unknown>")

    # Install pretty names.
    elfClass                    = Alias("e_ident4")
    elfByteOrder                = Alias("e_ident5")
    elfVersion                  = Alias("e_ident6")
    elfOsAbi                    = Alias("e_ident7")
    elfAbiVersion               = Alias("e_ident8")
    elfType                     = Alias("e_type")
    elfMachine                  = Alias("e_machine")
    elfEntryPoint               = Alias("e_entry")
    elfProgramHeaderTableOffset = Alias("e_phoff")
    elfSectionHeaderTableOffset = Alias("e_shoff")
    elfFlags                    = Alias("e_flags")
    elfEHSize                   = Alias("e_ehsize")
    elfPHTEntrySize             = Alias("e_phentsize")
    elfNumberOfPHs              = Alias("e_phnum")
    elfSHTEntrySize             = Alias("e_shentsize")
    elfNumberOfSHs              = Alias("e_shnum")
    elfStringTableIndex         = Alias("e_shstrndx")

    def elfClassAsString(self):
        result = ""
        if self.elfClass == defs.ELFClass.ELFCLASSNONE:
            result = "none"
        elif self.elfClass == defs.ELFClass.ELFCLASS32:
            result = "ELF32"
        elif self.elfClass == defs.ELFClass.ELFCLASS64:
            result = "ELF64"
        else:
            result = "<unknown: {0:x}>".format(self.elfClass)
        return result

    def elfDataEncodingAsString(self):
        result = ""
        if self.elfByteOrder == defs.ELFDataEncoding.ELFDATANONE:
            result = "none"
        elif self.elfByteOrder == defs.ELFDataEncoding.ELFDATA2LSB:
            result = "2's complement, little endian"
        elif self.elfByteOrder == defs.ELFDataEncoding.ELFDATA2MSB:
            result = "2's complement, big endian"
        else:
            result = "<unknown: {0:x}>".format(self.elfByteOrder)
        return result

    def getVersionAsString(self):
        result = ""
        if self.elfVersion == defs.EV_CURRENT:
            result = "(current)"
        elif self.elfVersion != defs.EV_NONE:
            result = "<unknown: {0:lx}>".format(self.elfVersion)
        return result

    def getAbiNameAsString(self):
        result = ""
        if self.elfOsAbi == defs.ELFAbiType.ELFOSABI_NONE:
            result = "UNIX - System V"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_HPUX:
            result = "UNIX - HP-UX"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_NETBSD:
            result = "UNIX - NetBSD"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_GNU:
            result = "UNIX - GNU"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_SOLARIS:
            result = "UNIX - Solaris"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_AIX:
            result = "UNIX - AIX"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_IRIX:
            result = "UNIX - IRIX"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_FREEBSD:
            result = "UNIX - FreeBSD"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_TRU64:
            result = "UNIX - TRU64"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_MODESTO:
            result = "Novell - Modesto"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_OPENBSD:
            result = "UNIX - OpenBSD"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_OPENVMS:
            result = "VMS - OpenVMS"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_NSK:
            result = "HP - Non-Stop Kernel"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_AROS:
            result = "AROS"
        elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_FENIXOS:
            result = "FenixOS"
        elif self.elfOsAbi >= 64:
            if self.elfMachine == defs.ELFMachineType.EM_ARM:
                if self.elfOsAbi == defs.ELFAbiType.ELFOSABI_ARM:
                    result = "ARM"
            elif self.elfMachine in (defs.ELFMachineType.EM_MSP430, defs.ELFMachineType.EM_MSP430_OLD):
                if self.elfOsAbi == defs.ELFAbiType.ELFOSABI_STANDALONE:
                    result = "Standalone App"
            elif self.elfMachine == defs.ELFMachineType.EM_TI_C6000:
                if self.elfOsAbi == defs.ELFAbiType.ELFOSABI_C6000_ELFABI:
                    result = "Bare-metal C6000"
                elif self.elfOsAbi == defs.ELFAbiType.ELFOSABI_C6000_LINUX:
                    result = "Linux C6000"
        else:
            result = "<unknown: {0:x}>".format(self.elfOsAbi)
        return result


    def getElfTypeAsString(self):
        result = ""
        if self.elfType == defs.ELFType.ET_NONE:
            result = "NONE (None)"
        elif self.elfType == defs.ELFType.ET_REL:
            result = "REL (Relocatable file)"
        elif self.elfType == defs.ELFType.ET_EXEC:
            result = "EXEC (Executable file)"
        elif self.elfType == defs.ELFType.ET_DYN:
            result = "DYN (Shared object file)"
        elif self.elfType == defs.ELFType.ET_CORE:
            result = "CORE (Core file)"
        else:
            if self.elfType >= defs.ELFType.ET_LOPROC and self.elfType <= defs.ELFType.ET_HIPROC:
                result = "Processor Specific: ({0:x})".format(self.elfType)
            elif self.elfType >= defs.ELFType.ET_LOOS and self.elfType <= defs.ELFType.ET_HIOS:
                result = "OS Specific: ({0:x})".format(self.elfType)
            else:
                result = "<unknown>: {0:x}".format(self.elfType)
        return result


class ELFSymbol(object):
    def __init__(self, parent, data):
        pass


class ELFSectionHeaderTable(object):
    def __init__(self, parent, atPosition = 0):
        self.parent = parent
        self._name = None
        parent.fp.seek(atPosition, os.SEEK_SET)

        data = parent.fp.read(defs.ELF_SECTION_SIZE64 if parent.is64Bit else defs.ELF_SECTION_SIZE32)
        format = defs.SEC_FMT64 if parent.is64Bit else defs.SEC_FMT32
        attributes = defs.Elf_Shdr

        sectionHeader = Attributor(format, attributes, parent.byteOrderPrefix)
        sectionHeader.apply(data, self)

        if self.sh_size and self.sh_entsize:
            self.numEntries = self.sh_size / self.sh_entsize
        else:
            self.numEntries = None

        if self.shType not in (defs.SHT_NOBITS, defs.SHT_NULL) and self.shSize > 0:
            pos = self.shOffset
            parent.fp.seek(pos, os.SEEK_SET)
            self.image = parent.fp.read(self.shSize)
        else:
            self.image = None

        if self.shType in (defs.SHT_SYMTAB, defs.SHT_DYNSYM):
            self.symbols = {}
            format = defs.SYMTAB_FMT64 if parent.is64Bit else defs.SYMTAB_FMT32
            attributes = defs.Elf64_Sym if parent.is64Bit else defs.Elf32_Sym
            size = defs.ELF64_SYM_TABLE_SIZE if parent.is64Bit else defs.ELF32_SYM_TABLE_SIZE
            for idx, symbol in enumerate(range(self.shSize / size)):

                offset = idx * size
                data = self.image[offset : offset + size]
                symbol = Attributor(format, attributes, parent.byteOrderPrefix)
                symbol.apply(data, symbol)
                self.symbols[idx] = symbol

        if self.shType in (defs.SHT_REL, defs.SHT_RELA):
            pass

    shAddress       = Alias("sh_addr")
    shAddressAlign  = Alias("sh_addralign")
    shEntitySize    = Alias("sh_entsize")
    shFlags         = Alias("sh_flags")
    shInfo          = Alias("sh_info")
    shLink          = Alias("sh_link")
    shNameIdx       = Alias("sh_name")
    shOffset        = Alias("sh_offset")
    shSize          = Alias("sh_size")
    shType          = Alias("sh_type")

    @property
    def shTypeName(self):
        TYPES = {
            defs.SHT_NULL            : "NULL",
            defs.SHT_PROGBITS        : "PROGBITS",
            defs.SHT_SYMTAB          : "SYMTAB",
            defs.SHT_STRTAB          : "STRTAB",
            defs.SHT_RELA            : "RELA",
            defs.SHT_HASH            : "HASH",
            defs.SHT_DYNAMIC         : "DYNAMIC",
            defs.SHT_NOTE            : "NOTE",
            defs.SHT_NOBITS          : "NOBITS",
            defs.SHT_REL             : "REL",
            defs.SHT_SHLIB           : "SHLIB",
            defs.SHT_DYNSYM          : "DYNSYM",
            defs.SHT_INIT_ARRAY      : "INIT_ARRAY",
            defs.SHT_FINI_ARRAY      : "FINI_ARRAY",
            defs.SHT_PREINIT_ARRAY   : "PREINIT_ARRAY",
            defs.SHT_GROUP           : "GROUP",
            defs.SHT_SYMTAB_SHNDX    : "SYMTAB_SHNDX",
            defs.SHT_NUM             : "NUM",
            defs.SHT_LOOS            : "LOOS",
            defs.SHT_GNU_ATTRIBUTES  : "NU_ATTRIBUTES",
            defs.SHT_GNU_HASH        : "GNU_HASH",
            defs.SHT_GNU_LIBLIST     : "GNU_LIBLIST",
            defs.SHT_CHECKSUM        : "CHECKSUM",
            defs.SHT_LOSUNW          : "LOSUNW",
            defs.SHT_SUNW_move       : "SUNW_move",
            defs.SHT_SUNW_COMDAT     : "UNW_COMDAT",
            defs.SHT_SUNW_syminfo    : "SUNW_syminfo",
            defs.SHT_GNU_verdef      : "VERDEF",
            defs.SHT_GNU_verneed     : "VERNEED",
            defs.SHT_GNU_versym      : "VERSYM",
            #defs.SHT_HISUNW          : "HISUNW",
            #defs.SHT_HIOS            : "HIOS",
            defs.SHT_ARM_EXIDX       : "ARM_EXIDX",
            defs.SHT_ARM_PREEMPTMAP  : "ARM_PREEMPTMAP",
            defs.SHT_ARM_ATTRIBUTES  : "ARM_ATTRIBUTES",
            defs.SHT_ARM_DEBUGOVERLAY    : "ARM_DEBUGOVERLAY",
            defs.SHT_ARM_OVERLAYSECTION  : "ARM_OVERLAYSECTION",
            defs.SHT_LOPROC          : "LOPROC",
            defs.SHT_HIPROC          : "HIPROC",
            defs.SHT_LOUSER          : "LOUSER",
            defs.SHT_HIUSER          : "HIUSER"
        }
        return TYPES.get(self.shType, "UNKNOWN")

    @property
    def shName(self):
        return self._name


class ELFProgramHeaderTable(object):
    def __init__(self, parent, atPosition = 0):
        parent.fp.seek(atPosition, os.SEEK_SET)

        data = parent.fp.read(defs.ELF_PHDR_SIZE64 if parent.is64Bit else defs.ELF_PHDR_SIZE32)

        format = defs.PHDR_FMT64 if parent.is64Bit else defs.PHDR_FMT32
        attributes = defs.Elf64_Phdr if parent.is64Bit else defs.Elf32_Phdr

        elfHeader = Attributor(format, attributes, parent.byteOrderPrefix)
        elfHeader.apply(data, self)

        parent.fp.seek(self.p_offset, os.SEEK_SET)
        self.image = parent.fp.read(self.p_filesz)
        if self.p_type in (defs.PT_DYNAMIC, defs.PT_INTERP, defs.PT_NOTE, defs.PT_SHLIB, defs.PT_PHDR):
            pass

    @property
    def phTypeName(self):
        NAMES = {
            0           : 'NULL',
            1           : 'LOAD',
            2           : 'DYNAMIC',
            3           : 'INTERP',
            4           : 'NOTE',
            5           : 'SHLIB',
            6           : 'PHDR',
            7           : 'TLS',
            8           : 'NUM',
            0x60000000  : 'LOOS',
            0x6474e550  : 'GNU_EH_FRAME',
            0x6474e551  : 'GNU_STACK',
            0x6474e552  : 'GNU_RELRO',
            #0x6ffffffa  : 'LOSUNW',
            0x6ffffffa  : 'SUNWBSS',
            0x6ffffffb  : 'SUNWSTACK',
            0x6fffffff  : 'HIOS',
            defs.PT_ARM_EXIDX: 'EXIDX',
        }
        if self.phType in NAMES:
            return NAMES.get(self.phType)
        elif defs.PT_LOPROC <= self.phType <= defs.PT_HIPROC:
            #print("{0:#x}".format(self.phType))
            return "PROCESSOR SPECIFIC"
        else:
            return "RES"

    phType              = Alias("p_type")
    phOffset            = Alias("p_offset")
    phVirtualAddress    = Alias("p_vaddr")
    phPhysicalAddress   = Alias("p_paddr")
    phFileSize          = Alias("p_filesz")
    phMemSize           = Alias("p_memsz")
    phFlags             = Alias("p_flags")
    phAlign             = Alias("p_align")


def getSpecialSectionName(section):
    if section == defs.SHN_UNDEF:
        return "UNDEF"
    elif section == defs.SHN_ABS:
        return "ABS"
    elif section == defs.SHN_COMMON:
        return "COMMON"
    #elif SHN_LOPROC <= section <= SHN_HIPROC:
    #    return "PROC"
    elif section == defs.SHN_BEFORE:
        return "BEFORE"
    elif section == defs.SHN_AFTER:
        return "AFTER"
    elif section == defs.SHN_HIPROC:
        return "HIPROC"
    elif section == defs.SHN_LOOS:
        return "LOOS"
    elif section == defs.SHN_HIOS:
        return "HIOS"
    elif section == defs.SHN_XINDEX:
        return "XINDEX"
    elif defs.SHN_COMMON < section < defs.SHN_HIRESERVE:
        return "RES"
    else:
        return "<section: {0}>".format(section)


class Relocation(object):

    def __init__(self, is64Bit):
        self.is64Bit = is64Bit

    def _getSymbol(self):
        if self.is64Bit:
            return
        else:
            return

    def _getType(self):
        if self.is64Bit:
            return
        else:
            return

    def _getInfo(self):
        if self.is64Bit:
            return
        else:
            return

    symbol = property(_getSymbol)
    type = property(_getType)
    info = property(_getInfo)

    """
    r_offset r_info r_addend

    #define ELF32_R_SYM(val)                ((val) >> 8)
    #define ELF32_R_TYPE(val)               ((val) & 0xff)
    #define ELF32_R_INFO(sym, type)         (((sym) << 8) + ((type) & 0xff))

    #define ELF64_R_SYM(i)                  ((i) >> 32)
    #define ELF64_R_TYPE(i)                 ((i) & 0xffffffff)
    #define ELF64_R_INFO(sym,type)          ((((Elf64_Xword) (sym)) << 32) + (type))
    """


class Reader(object):
    def __init__(self, fp, readContent = True):
        if not hasattr(fp, 'read'):
            raise TypeError("Need a file-like object.")
        self.fp = fp
        self.header = ELFHeader(self)
        self.is64Bit = self.header.is64Bit

        self.programHeaders = []
        self.sectionHeaders = []
        self._sectionHeadersByName = {}
        self._stringCache = {}

        self.logger = Logger("ELF")

        pos = self.header.e_phoff
        if pos:
            for _ in range(self.header.elfNumberOfPHs):
                self.programHeaders.append(ELFProgramHeaderTable(self, pos))
                pos += self.header.elfPHTEntrySize

        pos = self.header.e_shoff
        if pos:
            for _ in range(self.header.elfNumberOfSHs):
                self.sectionHeaders.append(ELFSectionHeaderTable(self, pos))
                pos += self.header.elfSHTEntrySize

        for idx, sectionHeader in enumerate(self.sectionHeaders):
            if sectionHeader.shType in (defs.SHT_SYMTAB, defs.SHT_DYNSYM):
                for _, symbol in sectionHeader.symbols.items():
                    symbol.sectionName = getSpecialSectionName(symbol.st_shndx)
            elif sectionHeader.shType in (defs.SHT_REL, defs.SHT_RELA):
                symtab = sectionHeader.shLink
                sectionToModify = sectionHeader.shInfo
                offset = 0

                if sectionHeader.shType == defs.SHT_REL:
                    format = defs.REL_FMT64 if self.is64Bit else defs.REL_FMT32
                    entrySize = defs.ELF_RELOCATION_SIZE64 if self.is64Bit else defs.ELF_RELOCATION_SIZE32
                    elfRelocation = Attributor(format, defs.Elf_Rel, self.byteOrderPrefix)
                else:
                    format = defs.RELA_FMT64 if self.is64Bit else defs.RELA_FMT32
                    entrySize = defs.ELF_RELOCATION_A_SIZE64 if self.is64Bit else defs.ELF_RELOCATION_A_SIZE32
                    elfRelocation = Attributor(format, defs.Elf_Rela, self.byteOrderPrefix)
                img = sectionHeader.image
                for pos in range(len(img) / entrySize):
                    data = img[offset : offset + entrySize]
                    reloc = Relocation(self.is64Bit)
                    elfRelocation.apply(data, reloc)
                    offset += entrySize
            elif sectionHeader == defs.SHT_NOTE:
                pass
        for section in self.sectionHeaders:
            name = self.getString(self.header.elfStringTableIndex, section.shNameIdx)
            section._name = name
            self._sectionHeadersByName[name] = section
        self.createSectionToSegmentMapping()

    def sectionHeaderByName(self, name):
        return self._sectionHeadersByName.get(name)

    def getString(self, tableIndex, entry):
        if (tableIndex, entry) in self._stringCache:
            return self._stringCache[(tableIndex, entry)]
        else:
            unterminatedString = self.sectionHeaders[tableIndex].image[entry : ]
            terminatedString = unterminatedString[ : unterminatedString.index('\x00')]
            self._stringCache[(tableIndex,entry)] = terminatedString
            return terminatedString

    def createSectionToSegmentMapping(self):
        mapping = OrderedDict()
        for idx in range(self.header.e_phnum):
            segment = self.programHeaders[idx]
            mapping[segment] = []
            for j in range(self.header.e_shnum):
                section = self.sectionHeaders[j]
                if not self.tbssSpecial(section, segment) and self.sectioInSegmentStrict(section, segment):
                    mapping[segment].append(section)
        self.sectionsToSegments = mapping

    def tbssSpecial(self, sectionHeader, segment):
       return ((sectionHeader.sh_flags & defs.SHF_TLS) != 0 and sectionHeader.sh_type == defs.SHT_NOBITS and segment.p_type != defs.PT_TLS)

    def sectionSize(self, sectionHeader, segment):
        return 0 if self.tbssSpecial(sectionHeader, segment) else sectionHeader.sh_size

    def sectionInSegment1(self, sectionHeader, segment, check_vma, strict):
        hasOffset = False
        validSegment = False
        hasVMA = False
        hasDynamicSize = False

        validSegment =((sectionHeader.sh_flags & defs.SHF_TLS) != 0) and (segment.p_type == defs.PT_TLS or segment.p_type == defs.PT_GNU_RELRO \
            or segment.p_type == defs.PT_LOAD) or \
            ((sectionHeader.sh_flags & defs.SHF_TLS) == 0 and segment.p_type != defs.PT_TLS and segment.p_type != defs.PT_PHDR)
        hasOffset = sectionHeader.sh_type == defs.SHT_NOBITS \
            or (sectionHeader.sh_offset >= segment.p_offset \
            and (not strict or (sectionHeader.sh_offset - segment.p_offset <= segment.p_filesz - 1)) \
            and ((sectionHeader.sh_offset - segment.p_offset + self.sectionSize(sectionHeader, segment)) <= (segment.p_filesz)))
        hasVMA = (not check_vma or (sectionHeader.sh_flags & defs.SHF_ALLOC) == 0 or (sectionHeader.sh_addr >= segment.p_vaddr \
            and (not strict or (sectionHeader.sh_addr - segment.p_vaddr <= segment.p_memsz - 1)) \
            and ((sectionHeader.sh_addr - segment.p_vaddr + self.sectionSize(sectionHeader, segment)) <= segment.p_memsz))
        )
        hasDynamicSize = (segment.p_type != defs.PT_DYNAMIC or sectionHeader.sh_size != 0 or segment.p_memsz == 0 \
            or ((sectionHeader.sh_type == defs.SHT_NOBITS or (sectionHeader.sh_offset > segment.p_offset \
            and (sectionHeader.sh_offset - segment.p_offset < segment.p_filesz))) \
            and ((sectionHeader.sh_flags & defs.SHF_ALLOC) == 0 \
            or (sectionHeader.sh_addr > segment.p_vaddr \
            and (sectionHeader.sh_addr - segment.p_vaddr < segment.p_memsz)))) \
        )

        result = validSegment and hasOffset and hasVMA and hasDynamicSize
        return result


    def sectionInSegment(self, sectionHeader, segment):
        return self.sectionInSegment1(sectionHeader, segment, 1, 0)

    def sectioInSegmentStrict(self, sectionHeader, segment):
        return self.sectionInSegment1(sectionHeader, segment, 1, 1)

    @property
    def byteOrderPrefix(self):
        return self.header.byteOrderPrefix

