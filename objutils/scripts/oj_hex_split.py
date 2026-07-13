#!/usr/bin/env python
"""Splits a HEX file into multiple files based on its sections."""

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
from pathlib import Path

from objutils import load, probe, dump
from ufilename import build_filename, SuffixPolicy, IdentityPolicy


def main():
    parser = argparse.ArgumentParser(description="Splits a HEX file into multiple files based on its sections.")
    parser.add_argument(
        "input_file",
        help="Input HEX file to be split.",
    )
    parser.add_argument(
        "-o",
        "--output-names",
        nargs="+",
        help="Optional list of output base names. If not provided, section numbers are used.",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="output_type",
        help="Output file type (e.g., ihex, srec). If omitted, it's inferred from the input file extension.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help="Prefix for output filenames. Defaults to input filename (without extension).",
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

    if not path.exists(args.input_file):
        print(f"File '{args.input_file}' does not exist.")
        sys.exit(1)

    with open(args.input_file, "rb") as f:
        file_type = probe(f)

    if file_type is None:
        print(f"Could not determine file type for '{args.input_file}'.")
        sys.exit(1)

    img = load(file_type, args.input_file)

    if not img.sections:
        print(f"No sections found in '{args.input_file}'.")
        sys.exit(0)

    output_type = args.output_type
    input_path = Path(args.input_file)
    if not output_type:
        ext = input_path.suffix.lower()
        if ext in (".hex", ".ihex"):
            output_type = "ihex"
        elif ext in (".s19", ".srec", ".mot"):
            output_type = "srec"
        elif ext in (".bin",):
            output_type = "bin"
        else:
            output_type = "ihex"  # Fallback

    base_prefix = args.prefix if args.prefix else input_path.stem
    output_ext = input_path.suffix if not args.output_type else f".{args.output_type}"
    # Normalize extension mapping for ufilename
    if args.output_type:
        if args.output_type == "ihex":
            output_ext = ".hex"
        elif args.output_type == "srec":
            output_ext = ".s19"
        elif args.output_type == "bin":
            output_ext = ".bin"

    if args.verbose:
        print(f"Splitting '{args.input_file}' into {len(img.sections)} sections...")

    split_images = img.split()

    for idx, new_img in enumerate(split_images):
        section = new_img.sections[0]
        if args.output_names and idx < len(args.output_names):
            # User provided a list of names
            name_policy = IdentityPolicy()
            out_base = args.output_names[idx]
        else:
            # Default: append section number
            name_policy = SuffixPolicy(suffix=f"_{idx:03d}")
            out_base = base_prefix

        out_filename = build_filename(name_policy, out_base, output_ext)

        print(f"Writing '{out_filename}'...")
        if args.verbose:
            print(f"  Section {idx:03d} (0x{section.start_address:08x}, {len(section)} bytes)")

        dump(output_type, out_filename, new_img)

    print(f"Successfully split into {len(split_images)} files.")


if __name__ == "__main__":
    main()
