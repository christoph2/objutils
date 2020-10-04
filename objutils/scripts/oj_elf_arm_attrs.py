#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Dumps '.ARM.attributes' section in an ELF file.
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
from pprint import pprint


from objutils.elf import defs, ElfParser, model

def main():
    parser = argparse.ArgumentParser(description = "'Dump '.ARM.attributes' section.")
    parser.add_argument("elf_file", help = ".elf file")
    #parser.add_argument("-l", help = "loglevel [warn | info | error | debug]", dest = "loglevel", type = str, default = "warn")
    args = parser.parse_args()
    try:
        ep = ElfParser(args.elf_file)
    except Exception as e:
        print("\n'{}' is not valid ELF file. Raised exception: '{}'.".format(args.elf_file, repr(e)))
        exit(1)
    if not ep.e_machine in (defs.ELFMachineType.EM_ARM, defs.ELFMachineType.EM_AARCH64):
        print("\n'{}' is not an ARM architecture file.".format(args.elf_file))
        exit(2)
    print("")
    arm_attrs = ep.arm_attributes
    if arm_attrs:
        for key, entries in arm_attrs.items():
            print("{1:}\n{0:}\n{1:}\n".format(key, "=" * len(key)))
            print("Name                           Value\nDescription")
            print("-" * 79)
            for attr in entries:
                print("{:30} {}\n{}\n".format(attr.tag_name, attr.value, attr.description))
    else:
        print("*** No .ARM.attributes section ***")

if __name__ == '__main__':
    main()
