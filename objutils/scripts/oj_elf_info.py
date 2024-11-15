#!/usr/bin/env python
"""while the basic option are the same it is currently not intended to be another readelf clone.
"""

__version__ = "0.1.0"

__copyright__ = """
   objutils - Object file library for Python.

  (C) 2010-2024 by Christoph Schueler <cpu12.gems@googlemail.com>

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

# from objutils.dwarf import DwarfProcessor
from objutils.elf import ElfParser, model
from objutils.elf.defs import (
    ELF_BYTE_ORDER_NAMES,
    ELF_CLASS_NAMES,
    ELF_TYPE_NAMES,
    ELFAbiType,
    ELFType,
    program_header_flags_name,
    program_header_name,
)


def main():
    parser = argparse.ArgumentParser(description="Display informations about ELF files.")
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
    ep = ElfParser(args.elf_file)
    print(f"Class:       {ELF_CLASS_NAMES.get(ep.ei_class, '*** INVALID ***')}")
    print(f"Type:        {ELFType(ep.e_type).name[3:]} [{ELF_TYPE_NAMES.get(ep.e_type, '')}]")
    print(f"Machine:     {ep.machine_data}")
    print(f"Data:        {ELF_BYTE_ORDER_NAMES.get(ep.ei_data, '*** INVALID ***')}")
    print(f"OS/ABI       {ELFAbiType(ep.ei_osabi).name[9:]} / v{ep.ei_abiversion}")

    sections = ep.query(model.Elf_Section).order_by(model.Elf_Section.index).all()
    print_header("Sections")
    print("Name                      Type           Addr     Offs     Size   Al")
    print("-" * 79)
    for sec in sections:
        print(
            f"{sec.section_name:25} {sec.section_display_name[4:]:14} {sec.sh_addr:08x} {sec.sh_offset:08x}"
            f" {sec.sh_size:06x} {sec.sh_addralign:2}"
        )

    print_header("Segments")
    print("Type         Offset     VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align")
    print("-" * 71)
    for segment in ep.segments:
        print(
            f"{program_header_name(segment.p_type):12} 0x{segment.p_offset:08x} 0x{segment.p_vaddr:08x} 0x{segment.p_paddr:08x} 0x{segment.p_filesz:05x} 0x{segment.p_memsz:05x} {program_header_flags_name(segment.p_flags):3} {segment.p_align:>5}"
        )
        """
        p_type = 1
        p_offset = 148
        p_vaddr = 0
        p_paddr = 0
        p_filesz = 12924
        p_memsz = 12924
        p_flags = 5
        p_align = 2
        """

    comment = ep.comment
    if comment:
        print_header(".comment")
        print(comment)
    for note in ep.notes:
        print_header(note.section_name)
        print("Type Name            Desc")
        print("-" * 79)
        print(f"{note.type:4} {note.name:15} {note.desc}")

    # dbSecs = ep.debug_sections()
    # dbSecs = ep.sections.fetch(name_pattern=".debug*")
    # dbSecs = ep.sections.fetch(name_pattern="*")

    # if dbSecs:
    #     dp = DwarfProcessor(dbSecs, ep.b64, ep.endianess)
    #     dp.do_abbrevs()
    #     dp.do_mac_info()
    #     dp.do_dbg_info()
    from objutils.dwarf import DwarfProcessor

    if ep.debug_sections():
        dp = DwarfProcessor(ep)
        dp.pubnames()
        dp.aranges()
        dp.do_lines()
        dp.do_dbg_info()
        # dp.processDebugInfo()
        dp.do_mac_info()


def print_header(text):
    print("\n{1:}\n{0:}\n{1:}\n".format(text, "=" * len(text)))


if __name__ == "__main__":
    main()
