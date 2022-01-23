#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Displays informations about HEX files.
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
from os import path
import sys

from objutils import load


def main():

    parser = argparse.ArgumentParser(
        description="Displays informations about HEX files."
    )
    parser.add_argument(
        "file_type",
        help="file type",
        choices=[
            "ash",
            "cosmac",
            "emon52",
            "etek",
            "fpc",
            "ihex",
            "mostec",
            "rca",
            "shf",
            "sig",
            "srec",
            "tek",
            "titxt",
        ],
    )
    parser.add_argument("hex_file", help="HEX file")
    parser.add_argument(
        "-d",
        "--dump",
        dest="dump",
        action="store_true",
        default=False,
        help="hexdump contents",
    )

    args = parser.parse_args()

    if not path.exists(args.hex_file):
        print("File '{}' does not exist.".format(args.hex_file))
        sys.exit(1)

    img = load(args.file_type.lower(), args.hex_file)
    # print(img.meta)
    print("\nSections")
    print("--------\n")
    print("Num   Address    Length")
    print("-" * 79)
    for idx, sec in enumerate(img):
        print("{:03d}   0x{:08x} {}".format(idx, sec.start_address, sec.length))
    print("-" * 79)
    print("                 {} total bytes".format(len(img)))
    if args.dump:
        img.hexdump()


if __name__ == "__main__":
    main()
