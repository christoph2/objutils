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

import objutils.elf as Elf
import objutils.elf.defs as defs
#import objutils.utils as utils
from objutils.elf.visual.template import render

def _basePath():
    import objutils as ot
    return ot.__path__[0]

BASE_PATH = _basePath()
PATH_TO_TEST_FILES = os.path.abspath(os.path.join(BASE_PATH, 'tests/ELFFiles'))
#print(os.listdir(PATH_TO_TEST_FILES))

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

FILE_HEADER_TMPL = """ELF Header:
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
%if sectionHeaders and header.e_phnum == defs.PN_XNUM and sectionHeaders[0].sh_info !=0:
  Number of program headers:         ${"{0:d} ({0:d})".format(header.elfNumberOfPHs, section_headers[0].sh_info)}
%else:
  Number of program headers:         ${"{0:d}".format(header.elfNumberOfPHs)}
%endif
  Size of section headers:           ${"{0:d} (bytes)".format(header.elfSHTEntrySize)}
%if sectionHeaders and header.e_shnum == defs.SHN_UNDEF:
  Number of section headers:         ${"{0:d} ({0:d})".format(header.elfNumberOfSHs, section_headers[0].sh_size)}
%else:
  Number of section headers:         ${"{0:d}".format(header.elfNumberOfSHs)}
%endif
%if sectionHeaders and header.e_shstrndx == defs.SHN_XINDEX:
  Section header string table index: ${"{0:d} ({0:d})".format(header.elfStringTableIndex, section_headers[0].sh_link)}
%else:
  Section header string table index: ${"{0:d}".format(header.elfStringTableIndex)}
%endif
%if header.e_shstrndx != defs.SHN_UNDEF and header.e_shstrndx > header.e_shnum:
 <corrupt: out of range>
%endif
"""

SECTION_HEADER_TMPL = """
%if not header.e_shnum:

There are no sections in this file.
<% return STOP_RENDERING %>
%endif
%if header.e_shnum > 1:
Section Headers:
%else:
Section Header:
%endif
%if not header.is64Bit:
%if doSectionDetails:
  [Nr] Name
       Type            Addr     Off    Size   ES   Lk Inf Al
%else:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
%endif
%elif wideScreen:
%if doSectionDetails:
  [Nr] Name
       Type            Address          Off    Size   ES   Lk Inf Al
%else:
  [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
%endif
%else:
%if doSectionDetails:
  [Nr] Name
       Type              Address          Offset            Link
       Size              EntSize          Info              Align
%else:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
%endif
%endif
%if doSectionDetails:
       Flags
%endif

%for section in sectionHeaders:
%if doSectionDetails:
${"  [{0:2d}] {1}".format(loop.index, section.shName)}
%if wideScreen:
${"       {0:<15}".format(section.shTypeName)}
%else:
${"       {0:<15.15}".format(section.shTypeName)}
%endif
%else:
%if wideScreen:
${"  [{0:2d}] {1:<17.17}{2:<15}".format(loop.index, section.shName, section.shTypeName)}
%else:
${"  [{0:2d}]  {1:<17.17}{2:<15.15}".format(loop.index, section.shName, section.shTypeName)}
%endif
%endif
<% shortFlags, longFlags = section.flags %>
%if not header.is64Bit:
<% linkToBig = "" %>
 ${"{0:08x} {1:06x} {2:06x} {3:02x}".format(section.shAddress, section.shOffset, section.shSize, section.shEntitySize)}
%if doSectionDetails:
XXX
%else:
${" {0:3}".format(shortFlags)}
%endif

%if section.shLink >= header.e_shnum:
##    %if header.e_machine in (defs.ELFMachineType.EM_386, defs.ELFMachineType.EM_486,
##        defs.ELFMachineType.EM_X86_64, defs.ELFMachineType.EM_L1OM, defs.ELFMachineType.EM_K1OM,
##        defs.ELFMachineType.EM_OLD_SPARCV9, defs.ELFMachineType.EM_SPARC32PLUS, defs.ELFMachineType.EM_SPARCV9,
##        defs.ELFMachineType.EM_SPARC
##    ):
        %if section.shLink ==  defs.SHN_BEFORE:
            linkToBig = "BEFORE"
        %elif section.shLink ==  defs.SHN_AFTER:
            linkToBig = "AFTER"
        %endif
%if self.doSectionDetails:
    %if linkToBig:
        print("<{0}>".format(linkToBig)),
    %else:
        print("{0:2d}".format(section.shLink)),
    %endif
    print("{0:3d} {1:2d}".format(section.shInfo, section.shAddressAlign))
%else:
    print("{0:2d} {1:3d} {2:2d}".format(section.shLink, section.shInfo, section.shAddressAlign))
##if (link_too_big && ! * link_too_big)
##    warn (_("section %u: sh_link value of %u is larger than the number of sections\n"), i, section->sh_link);
%endif
%endif
%endif
%endfor
"""

PROGRAM_HEADER_TMPL = """
%if header.e_phnum == 0:
%if header.e_phoff != 0:
possibly corrupt ELF header - it has a non-zero program header offset, but no program headers
%elif self.doSegments:
There are no program headers in this file.
<% return STOP_RENDERING %>
%endif
%endif
%if doSegments and not doHeader:
Elf file type is ${"{0!s}".format(header.getElfTypeAsString())}
Entry point ${"0x{0:x}".format(header.e_entry)}
There are ${"{0:d}".format(header.e_phnum)} program headers, starting at offset ${"{0:d}".format(header.e_phoff)}
%elif not doSegments:
<% return STOP_RENDERING %>
%endif

Program Headers:
%if not header.is64Bit:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
%elif wideScreen:
  Type           Offset   VirtAddr           PhysAddr           FileSiz  MemSiz   Flg Align
%else:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
%endif
%for hdr in programHeaders:
%if not header.is64Bit:
  ${"{0:<14.14} 0x{1:06x} 0x{2:08x} 0x{3:08x} 0x{4:05x} 0x{5:05x} {6:<3} {7:d}".format(
    hdr.phTypeName, hdr.phOffset, hdr.phVirtualAddress, hdr.phPhysicalAddress,
    hdr.phFileSize, hdr.phMemSize, hdr.flags, hdr.phAlign)
}
%elif wideScreen:
  ${"{0:<14.14} 0x{1:6x} 0x{2:016x} 0x{3:016x} 0x{4:06x} 0x{5:06x} {6:<3} {7:d}".format(hdr.phTypeName,
    hdr.phOffset, hdr.phVirtualAddress, hdr.phPhysicalAddress, hdr.phFileSize,
    hdr.phMemSize, hdr.flags, hdr.phAlign)
}
%else:
  ${"{0:<14.14} 0x{1:016x} 0x{2:016x} 0x{3:016x}".format(hdr.phTypeName, hdr.phOffset, hdr.phVirtualAddress, hdr.phPhysicalAddress)}
  ${"               0x{0:016x} 0x{1:016x}  {2:<6} {3:d}".format(hdr.phFileSize, hdr.phMemSize,hdr.flags, hdr.phAlign)}
%endif
%if hdr.phType == defs.PT_INTERP:
%if doSegments:
      ${"[Requesting program interpreter: {}]".format(hdr.image.strip())}
%endif
%endif
%endfor
%if doSegments and sectionHeaders:   # and reader.stringTable

 Section to Segment mapping:
  Segment Sections...
%for entry in sectionsToSegments.values():
   ${"{0:02d}     {1}".format(loop.index, " ".join([x.shName for x in entry]))}
%endfor
%endif
"""

class ReadElf(object):

    def __init__(self, fname):
        self.reader = Elf.Reader(fname)

    def renderHeader(self):
        ns = {'defs': defs, 'header': self.reader.header, 'getMachineFlags': getMachineFlags, 'sectionHeaders': self.reader.sectionHeaders}
        return render(FILE_HEADER_TMPL, ns)


'''
    def printSectionsHeaders(self, reader):
###
            if not self.reader.header.is64Bit:
                linkToBig = ""
                print( "{0:08x} {1:06x} {2:06x} {3:02x}".format(section.shAddress, section.shOffset, section.shSize, section.shEntitySize)),
                if self.doSectionDetails:
                    print(" "),
                else:
                    print(" {0:3}".format(flags)),
                if section.shLink >= self.reader.header.e_shnum:
                    if self.reader.header.e_machine in (defs.ELFMachineType.EM_386, defs.ELFMachineType.EM_486,
                        defs.ELFMachineType.EM_X86_64, defs.ELFMachineType.EM_L1OM, defs.ELFMachineType.EM_K1OM,
                        defs.ELFMachineType.EM_OLD_SPARCV9, defs.ELFMachineType.EM_SPARC32PLUS, defs.ELFMachineType.EM_SPARCV9,
                        defs.ELFMachineType.EM_SPARC
                    ):
                        if section.shLink ==  defs.SHN_BEFORE:
                            linkToBig = "BEFORE"
                        elif section.shLink ==  defs.SHN_AFTER:
                            linkToBig = "AFTER"
                if self.doSectionDetails:
                    if linkToBig:
                        print("<{0}>".format(linkToBig)),
                    else:
                        print("{0:2d}".format(section.shLink)),
                    print("{0:3d} {1:2d}".format(section.shInfo, section.shAddressAlign))
                else:
                    print("{0:2d} {1:3d} {2:2d}".format(section.shLink, section.shInfo, section.shAddressAlign))
                #if (link_too_big && ! * link_too_big)
                #    warn (_("section %u: sh_link value of %u is larger than the number of sections\n"), i, section->sh_link);
####
            elif self.options.wideScreen:
                print("{0:016x} {1:06x} {2:06x} {3:02x}".format(section.shAddress, section.shOffset, section.shSize, section.shEntitySize)),
                if self.doSectionDetails:
                    print(" "),
                else:
                    print("{0:3}".format(flags))
                print("{0:2d} {1:3d} {2:2d}".format(section.shLink, section.shInfo, section.shAddressAlign))
            elif self.doSectionDetails:
                print("       {0:<15s}  {1:016x}  {2:016x}  {3:d}".format(section.shTypeName, section.shAddress, section.shOffset, section.shLink))
                print("       {0:016x} {1:016x}  {2:<16d}  {3:d}".format(section.shSize, section.shEntitySize, section.shInfo, section.shAddressAlign))
            else:
                print(" {0:016x}  {1:08x}".format(section.shAddress, section.shOffset))
                print("       {0:016x}  {1:016x}  {2:3s}".format(section.shSize, section.shEntitySize, flags)),
                print("    {0:2d}   {1:3d}     {2:d}".format(section.shLink, section.shInfo, section.shAddressAlign))
            if self.doSectionDetails:
                if self.reader.header.is64Bit:
                    print("       [{0:016x}]: {1}".format(section.shFlags, ', '.join(flagsLong)))
                else:
                    print("       [{0:08x}]: {1}".format(section.shFlags, ', '.join(flagsLong)))
        if not self.doSectionDetails:
            print("""Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings)
  I (info), L (link order), G (group), T (TLS), E (exclude), x (unknown)
  O (extra OS processing required) o (OS specific), p (processor specific)""")
        else:
            """      if (elf_header.e_machine == EM_X86_64
          || elf_header.e_machine == EM_L1OM
          || elf_header.e_machine == EM_K1OM)
            """
##
##            print("""Key to Flags:
##  W (write), A (alloc), X (execute), M (merge), S (strings), l (large)
##  I (info), L (link order), G (group), T (TLS), E (exclude), x (unknown)
##  O (extra OS processing required) o (OS specific), p (processor specific)""")
##
'''

#from mako.template import Template
#from mako.lookup import TemplateLookup
#
#mylookup = TemplateLookup(directories=['/docs'], module_directory='/tmp/mako_modules'', collection_size=500, output_encoding='utf-8', encoding_errors='replace')
#def serve_template(templatename, **kwargs):
#    mytemplate = mylookup.get_template(templatename)
#    print(mytemplate.render(**kwargs))
#    print(mytemplate.render_unicode().encode('utf-8', 'replace'))

