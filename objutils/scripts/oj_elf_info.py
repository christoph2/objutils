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

from objutils.elf import ElfParser, model
from objutils.elf.defs import (
    ELFMachineType,
    ELF_MACHINE_NAMES,
    ELF_CLASS_NAMES,
    ELFType,
    ELF_TYPE_NAMES,
    ELF_BYTE_ORDER_NAMES,
    ELFAbiType,
)


def main():
    parser = argparse.ArgumentParser(
        description="Display informations about ELF files."
    )
    parser.add_argument("elf_file", help="ELF file")  # , nargs = "+"
    parser.add_argument(
        "-k",
        dest="keepDirectory",
        action="store_true",
        default=False,
        help="keep directory; otherwise create db in current directory",
    )
    parser.add_argument(
        "-l",
        help="loglevel [warn | info | error | debug]",
        dest="loglevel",
        type=str,
        default="warn",
    )
    parser.add_argument(
        "-S",
        "--sections",
        "--section-headers",
        help="Display the sections' headers.",
        dest="sections",
        action="store_false",
    )
    parser.add_argument(
        "-u",
        help="Generate UTF-8 encoded output (otherwise Latin-1).",
        dest="ucout",
        action="store_true",
    )

    args = parser.parse_args()
    # print("ARGS", args)
    print("")

    ep = ElfParser(args.elf_file)
    print("Class:       {}".format(ELF_CLASS_NAMES.get(ep.ei_class, "*** INVALID ***")))
    print(
        "Type:        {} [{}]".format(
            ELFType(ep.e_type).name[3:], ELF_TYPE_NAMES.get(ep.e_type, "")
        )
    )
    print(
        "Machine:     {} [{}]".format(
            ELFMachineType(ep.e_machine).name[3:],
            ELF_MACHINE_NAMES.get(ep.e_machine, ""),
        )
    )
    print(
        "Data:        {}".format(
            ELF_BYTE_ORDER_NAMES.get(ep.ei_data, "*** INVALID ***")
        )
    )
    print(
        "OS/ABI       {} / v{}".format(
            ELFAbiType(ep.ei_osabi).name[9:], ep.ei_abiversion
        )
    )

    sections = ep.query(model.Elf_Section).order_by(model.Elf_Section.index).all()
    print_header("Sections")
    print("Name                      Type           Addr     Offs     Size   Al")
    print("-" * 79)
    for sec in sections:
        flags = []
        print(
            "{:25} {:14} {:08x} {:08x} {:06x} {:2}".format(
                sec.section_name,
                sec.section_type.name[4:],
                sec.sh_addr,
                sec.sh_offset,
                sec.sh_size,
                sec.sh_addralign,
            )
        )
    comment = ep.comment
    if comment:
        print_header(".comment")
        print(comment)
    for note in ep.notes:
        print_header(note.section_name)
        print("Type Name            Desc")
        print("-" * 79)
        print("{:4} {:15} {}".format(note.type, note.name, note.desc))

    # dbSecs = ep.debug_sections()
    # if dbSecs:
    #    dp = DwarfProcessor(dbSecs, ep.b64, ep.endianess)
    #    dp.do_abbrevs()
    #    dp.do_mac_info()
    #    dp.do_dbg_info()


def print_header(text):
    print("\n{1:}\n{0:}\n{1:}\n".format(text, "=" * len(text)))


if __name__ == "__main__":
    main()
