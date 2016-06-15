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

import os

from mako.template import Template
from mako.runtime import Context
from mako import exceptions

import objutils.elf as Elf
import objutils.elf.defs as defs
import objutils.utils as utils

def _basePath():
    import objutils as ot
    return ot.__path__[0]

BASE_PATH = _basePath()
PATH_TO_TEST_FILES = os.path.abspath(os.path.join(BASE_PATH, 'tests/ELFFiles'))
#print(os.listdir(PATH_TO_TEST_FILES))

indentText = lambda text, leftmargin = 0: '\n'.join(["{0}{1}".format((" " * leftmargin), line, ) for line in text.splitlines()])

def renderTemplate(tmpl, namespace = {}, leftMargin = 0, rightMargin = 80, formatExceptions = True, encoding = 'utf-8'):
    buf = utils.createStringBuffer()
    ctx = Context(buf, **namespace)
    try:
        tobj = Template(text = tmpl, output_encoding = encoding, format_exceptions = formatExceptions)
        tobj.render_context(ctx)
    except:
        print(exceptions.text_error_template().render())
        return None
    return indentText(buf.getvalue(), leftMargin)

R0 = """ELF Header:
  Magic:   7f 45 4c 46 02 02 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF64
  Data:                              2's complement, big endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              REL (Relocatable file)
  Machine:                           PowerPC64
  Version:                           0x1
  Entry point address:               0x0
  Start of program headers:          0 (bytes into file)
  Start of section headers:          896 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           0 (bytes)
  Number of program headers:         0
  Size of section headers:           64 (bytes)
  Number of section headers:         24
  Section header string table index: 21"""

def getMachineFlags(flags, machine):
    result = ''
    if flags:
        if machine == defs.ELFMachineType.EM_ARM:
            result = arm.decodeARMMachineFlags(flags)
        elif machine == defs.ELFMachineType.EM_BLACKFIN:
            if flags & defs.EF_BFIN_PIC:
                result += ", PIC"
            if flags & defs.EF_BFIN_FDPIC:
                result += ", FDPIC"
            if flags & defs.EF_BFIN_CODE_IN_L1:
                result += ", code in L1"
            if  flags & defs.EF_BFIN_DATA_IN_L1:
                result += ", data in L1"
    return result

HEADER_TMPL = """ELF Header:
  Magic:   ${' '.join(["{0:02x}".format((ord(x))) for x in header.magicBytes[:16]])}
  Class:                             ${"{}".format((header.elfClassAsString()))}
  Data:                              ${"{}".format(header.elfDataEncodingAsString())}
  Version:                           ${"{0:d} {1}".format(header.elfVersion, header.getVersionAsString())}
  OS/ABI:                            ${"{}".format((header.getAbiNameAsString()))}
  ABI Version:                       ${"{:d}".format((header.elfAbiVersion))}
  Type:                              ${"{}".format(header.getElfTypeAsString())}
  Machine:                           ${"{}".format(header.elfMachineName)}
  Version:                           ${"0x{0:x}".format(header.elfVersion)}
  Entry point address:               ${"0x{0:x}".format(header.elfEntryPoint)}
  Start of program headers:          ${"{0:d} (bytes into file)".format(header.elfProgramHeaderTableOffset)}
  Start of section headers:          ${"{0:d} (bytes into file)".format(header.elfSectionHeaderTableOffset)}
  Flags:                             ${"0x{0:x}{1}".format(header.elfFlags, getMachineFlags(header.elfFlags, header.elfMachine))}
  Size of this header:               ${"{0:d} (bytes)".format(header.elfEHSize)}
  Size of program headers:           ${"{0:d} (bytes)".format(header.elfPHTEntrySize)}
  Number of program headers:         ${"{0:d}".format(header.elfNumberOfPHs)}
%if sectionHeaders and header.e_phnum == defs.PN_XNUM and sectionHeaders[0].sh_info !=0:
${" ({0:d})".format(section_headers[0].sh_info)}
%endif
  Size of section headers:           ${"{0:d} (bytes)".format(header.elfSHTEntrySize)}
  Number of section headers:         ${"{0:d}".format(header.elfNumberOfSHs)}
%if sectionHeaders and header.e_shnum == defs.SHN_UNDEF:
${" ({0:d})".format(section_headers[0].sh_size)}
%endif
  Section header string table index: ${"{0:d}".format(header.elfStringTableIndex)}
%if sectionHeaders and header.e_shstrndx == defs.SHN_XINDEX:
${" ({0:d})".format(section_headers[0].sh_link)}
%elif header.e_shstrndx != defs.SHN_UNDEF and header.e_shstrndx > header.e_shnum:
 <corrupt: out of range>
%endif
"""


reader = Elf.Reader(os.path.join(PATH_TO_TEST_FILES, 'testfile23'))
print(reader)

ns = {'defs': defs, 'header': reader.header, 'getMachineFlags': getMachineFlags, 'sectionHeaders': reader.sectionHeaders}

header = renderTemplate(HEADER_TMPL, ns)
print(header)
print(header == R0, header == R1)
