#!/usr/bin/env python
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

from objutils import dump
from objutils.elf import ElfParser


# import sys
# sys.argv.extend(["-t", "ihex", "./examples/hello_xcp.ino.elf", "./examples/hello_xcp.hex"])


def callback(state, section):
    """ """
    if state == "start":
        pass
    elif state == "stop":
        print("-" * 45)
    elif state == "section":
        print(f"{section.section_name:25s} 0x{section.sh_addr:08x} {section.sh_size}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract sections contributing to program image, e.g. for flash programming applications."
    )
    parser.add_argument("elf_file", help="ELF file")
    parser.add_argument("output_file_name", help="Output filename.")
    parser.add_argument(
        "-j",
        "--join",
        help="Try to make continuous sections.",
        dest="join",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--file-type",
        help="Type of output HEX file.",
        choices=["ihex", "shf", "srec", "titxt"],
        default="ihex",
        dest="file_type",
    )
    parser.add_argument(
        "-e",
        "--exclude_pattern",
        help="Exclude sections matching a Python RegEx",
        dest="exclude",
        default=None,
    )
    parser.add_argument(
        "-i",
        "--include_pattern",
        help="Include only sections matching a Python RegEx",
        dest="include",
        default=None,
    )
    parser.add_argument("-n", help="Number of data bytes per line", dest="row_length", default=16, type=int)
    args = parser.parse_args()
    try:
        ep = ElfParser(args.elf_file)
    except Exception as e:
        print(f"\n'{args.elf_file}' is not valid ELF file. Raised exception: '{repr(e)}'.")
        exit(1)
    print("\nExtracting from...\n")
    print("Section                   Address    Length")
    print("-" * 45)
    img = ep.create_image(
        callback=callback,
        join=args.join,
        exclude_pattern=args.exclude,
        include_pattern=args.include,
    )
    if img:
        dump(args.file_type, args.output_file_name, img, row_length=args.row_length)
        print(f"HEX image written to: '{args.output_file_name}' [{len(img)} total bytes]")


if __name__ == "__main__":
    main()
