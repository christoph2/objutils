#!/usr/bin/env python
"""Merges multiple HEX files into one."""

__copyright__ = """
   objutils - Object file library for Python.

  (C) 2010-2026 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from objutils import load, probe, dump, Image


def main():
    parser = argparse.ArgumentParser(description="Merges multiple HEX files into one.")
    parser.add_argument(
        "input_files",
        nargs="+",
        help="Input HEX files to be merged.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output HEX file.",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="output_type",
        help="Output file type (e.g., ihex, srec). If omitted, it's inferred from the output file extension.",
    )
    parser.add_argument(
        "-p",
        "--print-filename",
        dest="print_filename",
        action="store_true",
        default=False,
        help="Print filenames while processing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Verbose output",
    )

    args = parser.parse_args()

    output_type = args.output_type
    if not output_type:
        ext = path.splitext(args.output)[1].lower()
        if ext in (".hex", ".ihex"):
            output_type = "ihex"
        elif ext in (".s19", ".srec", ".mot"):
            output_type = "srec"
        elif ext in (".bin",):
            output_type = "bin"
        else:
            print(f"Could not infer output type from extension '{ext}'. Please specify with -t.")
            sys.exit(1)

    all_sections = []

    for filename in args.input_files:
        if not path.exists(filename):
            print(f"File '{filename}' does not exist.")
            sys.exit(1)

        if args.print_filename:
            print(f"Processing '{filename}'...")

        with open(filename, "rb") as f:
            file_type = probe(f)

        if file_type is None:
            print(f"Could not determine file type for '{filename}'.")
            sys.exit(1)

        img = load(file_type, filename)
        for section in img:
            # Check for overlaps manually to satisfy "No overlaps allowed during merge"
            for existing in all_sections:
                if not (
                    section.start_address + section.length <= existing.start_address
                    or section.start_address >= existing.start_address + existing.length
                ):
                    overlap_start = max(section.start_address, existing.start_address)
                    print(f"Error: Overlap detected at 0x{overlap_start:08x} between input files.")
                    sys.exit(1)
            all_sections.append(section)

    merged_image = Image(all_sections, join=True)

    if args.verbose:
        print("\nMerged Image Sections:")
        print("Num   Address    Length")
        print("-" * 79)
        for idx, sec in enumerate(merged_image):
            print(f"{idx:03d}   0x{sec.start_address:08x} {sec.length}")
        print("-" * 79)
        print(f"                 {len(merged_image)} total bytes")

    dump(output_type, args.output, merged_image)
    print(f"Successfully merged into '{args.output}' (type: {output_type}).")


if __name__ == "__main__":
    main()
