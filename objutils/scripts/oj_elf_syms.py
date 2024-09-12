#!/usr/bin/env python
"""List symbols contained in an ELF file (but not DWARF symbols!).
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

from objutils.elf import ElfParser


def main():
    parser = argparse.ArgumentParser(description="Display ELF symbols.")
    parser.add_argument("elf_file", help="ELF file")
    parser.add_argument(
        "-s",
        "--sections",
        help="Use only symbols from listed sections",
        dest="sections",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-p",
        "--pattern",
        help="Only display symbols matching a (Python) regex",
        dest="pattern",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-t",
        "--types",
        help="Use only symbols with listed types",
        dest="types",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-a",
        "--access",
        type=str,
        default=None,
        help="Use only symbols with listed access specifiers:  A (allocate), W (write), X (execute)",
    )
    parser.add_argument(
        "-b",
        "--bindings",
        help="Use only symbols with listed bindings",
        dest="bindings",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-o",
        "--order-by",
        choices=["N", "V"],
        default="V",
        help="Order symbols by name or value",
    )
    args = parser.parse_args()
    try:
        ep = ElfParser(args.elf_file)
    except Exception as e:
        print(f"\n'{args.elf_file}' is not valid ELF file. Raised exception: '{repr(e)}'.")
        exit(1)
    for section, syms in ep.symbols.fetch(
        sections=args.sections,
        name_pattern=args.pattern,
        order_by_value=True if args.order_by == "V" else False,
        bindings=args.bindings,
        types_str=args.types,
        access=args.access,
    ).items():
        separator = "=" * len(section)
        print("\n{1:}\n{0:}\n{1:}\n".format(section, separator))
        print("Name")
        print("Value     Size Bind       Type      Access")
        print("-" * 79)
        for sym in syms:
            access_str = "{}{}{}".format(
                "A" if sym.allocate else " ",
                "W" if sym.writeable else " ",
                "X" if sym.executeable else " ",
            )
            print(
                "{:30}\n{:08x} {:5d} {:10} {:9} {}\n".format(
                    sym.symbol_name,
                    sym.st_value,
                    sym.st_size,
                    sym.symbol_bind.name[4:],
                    sym.symbol_type.name[4:],
                    access_str,
                )
            )


if __name__ == "__main__":
    main()
