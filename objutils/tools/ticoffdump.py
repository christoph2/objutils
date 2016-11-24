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

from optparse import OptionParser
import construct
from objutils.coff.ti import TICOFF


def main():
    usage = "Usage: ticoff-dump [options] <coff-file>"

    options=[]
    args=[]

    op = OptionParser(usage = usage,version = "%prog " + __version__, description = "Display information about the contents of Texas Instruments COFF format files")

    op.add_option('-a', '--all', help = "Equivalent to: -H -s -S ", dest = "all", action = "store_true", default = False)
    op.add_option('-v', '--verbose', help = "Provide details on errors (if any)", dest = "verbose", action = "store_true", default = False)
    op.add_option('-H', '--file-header', help = "Display the COFF file header (and optional file header if present)", dest = "fileHeader", action = "store_true", default = False)
    op.add_option('-s', '--symbols', help = "Display the symbol table", dest = "symbolTable", action = "store_true", default = False)
    op.add_option('-S', '--section-headers', help = "Display the sections' header", dest = "sectionHeaders",  action = "store_true", default = False)
#  -r --relocs            Display the relocations (if present)

    (options, args) = op.parse_args()
    if not args:
        op.print_help()
        return

    filename = args[0]

    try:
        coff = TICOFF(filename)
    except construct.core.ConstructError as e:
        print("file format not recognized as Texas Instruments COFF")
        if options.verbose:
            print("[{0}]: {1}".format(type(e).__name__, str(e)))
    else:
        if options.fileHeader:
            print("\nCOFF file header:")
            print("  VersionID:                 {:02X}".format(coff.header.versionID))
            print("  Created:                   {}".format(coff.header.timestamp))
            print("  Target:                    {}".format(coff.header.targetID))
            print("  Flags:                     {}".format(getFlags(str(coff.header.flags))))
            print("  Number of section headers: {}".format(coff.header.numSectionHeaders))
            print("  Number of symbols:         {}".format(len(coff.symbols)))
            if coff.coff.optionalFileHeader:
                print("\nOptional file header:")
                ofh = coff.coff.optionalFileHeader
                print("  Magic:                     {:04X}".format(ofh.magic))
                print("  Version                    {:04X}".format(ofh.version))
                print("  Executable size            {}".format(ofh.executableSize))
                print("  Initialized data size      {}".format(ofh.initializedDataSize))
                print("  Uninitialized data size    {}".format(ofh.uninitializedDataSize))
                print("  Entrypoint                 {:08X}".format(ofh.entryPoint))
                print("  Executable code address    {}".format(ofh.executableCodeAddress))
                print("  Initialized data address   {}".format(ofh.initializedDataAddress))
            else:
                print("\n[Optional file header not present]")
        if options.sectionHeaders:
            if not coff.header.numSectionHeaders:
                print("\n[There are no sections in this file.]")
            else:
                if coff.header.numSectionHeaders:
                    print("\nSection Headers:")
                else:
                    print("\nSection Header:")
                print("  [Nr] Name               Phys Addr Virt Addr Size     Page Flags")
                for idx, (key, section) in enumerate(coff.sections.items()):
                    print("  [{:>2}] {:18s} {:08X}  {:08X}  {:08X} {:04X} {}".format(idx, section.name, section.physicalAddress, section.virtualAddress,
                        section.sectionSize, section.memoryPageNumber, getFlags(str(section.flags))))

        if options.symbolTable:
            if not coff.header.numSymbols:
                print("\n[Empty symbol table]")
            else:
                print("\nSymbol table contains {} entries:".format(len(coff.symbols)))
                print("   Num:    Value  Size Class    Number Name")
                for idx, sym in enumerate(coff.symbols):
                    print("  {:4d}: {:08X} {:5d} {:7} {:>7} {}".format(idx, sym.value, sym.sectionLength, sym.sectionNumber, sym.storageClass, sym.name))

def getFlags(flags):
    lines =  [f.strip() for f in flags.split('\n')]
    attrs =  [a.split("=")[0] for a in lines[ 1 : ]]
    return ''.join(attrs)

if __name__=='__main__':
    main()

