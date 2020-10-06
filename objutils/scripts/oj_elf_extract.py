#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Extract sections contributing to program image, e.g. for flash programming applications.
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

import argparse
from pprint import pprint
from sys import stdout

from objutils import Image, Section, dump
from objutils.elf import ElfParser, model

def main():
    parser = argparse.ArgumentParser(
        description = 'Extract sections contributing to program image, e.g. for flash programming applications.'
    )
    parser.add_argument("elf_file", help = "ELF file")
    parser.add_argument("output_file_name", help = "Output filename.")
    parser.add_argument('-d', '--dry-run', help = "Only list sections used, no output is generated.",
        dest = "dry_run", action = "store_true"
    )
    parser.add_argument("-j", "--join", help = "Try to make continuous sections.", dest = "join", action = "store_true")
    parser.add_argument("-t", "--file-type", help = "Type of output HEX file.", choices = [
        "ihex", 'shf', "srec" # , 'titxt'
    ], default = "ihex", dest = "file_type")
    args = parser.parse_args()
    try:
        ep = ElfParser(args.elf_file)
    except Exception as e:
        print("\n'{}' is not valid ELF file. Raised exception: '{}'.".format(args.elf_file, repr(e)))
        exit(1)
    #ep = ElfParser(args.elf_file)
    #print(args)
    print("\nExtracting from...\n")
    print("Section                   Address    Length")
    print("-" * 45)
    bin_sections = []
    for section in ep.sections.query(model.Elf_Section).filter(model.Elf_Section.has_content == True, model.Elf_Section.flag_alloc == True).all():
        print("{:25s} 0x{:08x} {}".format(section.section_name, section.sh_addr, section.sh_size))
        bin_section = Section(start_address = section.sh_addr, data = section.section_image)
        bin_sections.append(Section(start_address = section.sh_addr, data = section.section_image))
    print("-" * 45)
    if bin_sections:
        img = Image(bin_sections, join = args.join)
        dump(args.file_type, args.output_file_name, img)
        print("HEX image written to: '{}' [{} total bytes]".format(args.output_file_name, len(img)))

if __name__ == '__main__':
    main()
