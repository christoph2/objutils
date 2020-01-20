#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""while the basic option are the same it is currently not intended to be another readelf clone.
"""

__version__ = "0.1.0"

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

import argparse

from objutils.elf import ElfParser

def main():

    parser = argparse.ArgumentParser(description = 'Display informations about ELF files.')
    parser.add_argument("ELF_file", help = "") # , nargs = "+"
    parser.add_argument("-k", dest = 'keepDirectory', action = "store_true", default = False,
        help = "keep directory; otherwise create db in current directory")
    parser.add_argument("-l", help = "loglevel [warn | info | error | debug]", dest = "loglevel", type = str, default = "warn")
    parser.add_argument("-S", "--sections", "--section-headers",  help = "Display the sections' headers.", dest = "sections", action = "store_false")
    parser.add_argument("-u", help = "Generate UTF-8 encoded output (otherwise Latin-1).", dest = "ucout", action = "store_true")

    args = parser.parse_args()
    print("ARGS", args)
    ucout = args.ucout
    for arg in args.vehicle_file:
        for pth in pathlib.Path().glob(arg):
            pass

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

