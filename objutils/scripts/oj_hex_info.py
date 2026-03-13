#!/usr/bin/env python
"""Displays informations about HEX files."""

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
import sys
from os import path

from objutils import load, probe


def main():
    parser = argparse.ArgumentParser(description="Displays informations about HEX files.")
    parser.add_argument(
        "file_or_type",
        nargs="?",
        help="file type or HEX file (if type is omitted)",
    )
    parser.add_argument("hex_file", nargs="?", help="HEX file")
    parser.add_argument(
        "-d",
        "--dump",
        dest="dump",
        action="store_true",
        default=False,
        help="hexdump contents",
    )
    parser.add_argument(
        "-p",
        "--print-filename",
        dest="print_filename",
        action="store_true",
        default=False,
        help="Print filename including path",
    )
    parser.add_argument(
        "-j",
        "--join-sections",
        dest="join_section",
        action="store_true",
        default=False,
        help="Join adjacent sections",
    )

    args = parser.parse_args()

    if args.hex_file is None:
        if args.file_or_type is None:
            parser.error("too few arguments")
        # Only one positional argument given: it's the hex_file, type is to be probed.
        hex_file = args.file_or_type
        file_type = None
    else:
        # Two positional arguments given: type and file.
        file_type = args.file_or_type
        hex_file = args.hex_file

    if not path.exists(hex_file):
        print(f"File '{hex_file}' does not exist.")
        sys.exit(1)

    if file_type is None:
        with open(hex_file, "rb") as f:
            file_type = probe(f)

    if file_type is None:
        print(f"Could not determine file type for '{hex_file}'.")
        sys.exit(1)

    img = load(file_type.lower(), hex_file, join=args.join_section)
    if args.print_filename:
        print(f"\nFile: {hex_file}")
    print("\nSections")
    print("--------\n")
    print("Num   Address    Length")
    print("-" * 79)
    for idx, sec in enumerate(img):
        print(f"{idx:03d}   0x{sec.start_address:08x} {sec.length}")
    print("-" * 79)
    print(f"                 {len(img)} total bytes")
    if args.dump:
        img.hexdump()


if __name__ == "__main__":
    main()
