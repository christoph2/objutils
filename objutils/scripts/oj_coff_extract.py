#!/usr/bin/env python
"""Extract sections contributing to program image from a PE/COFF file."""

from __future__ import annotations

import argparse

from objutils import dump
from objutils.pecoff import PeParser


def callback(state, section):
    if state == "start":
        pass
    elif state == "stop":
        print("-" * 45)
    elif state == "section":
        # Section is objutils.Section in PE path
        print(f"{getattr(section, 'name', ''):25s} 0x{int(getattr(section, 'start_address', 0)):08x} {len(section.data)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract sections contributing to program image from a PE/COFF file.")
    parser.add_argument("pe_file", help="PE/COFF file")
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
        help="Exclude sections containing this substring",
        dest="exclude",
        default=None,
    )
    parser.add_argument(
        "-i",
        "--include_pattern",
        help="Include only sections containing this substring",
        dest="include",
        default=None,
    )
    parser.add_argument(
        "-r",
        "--no-image-base",
        help="Use relative virtual addresses (RVAs) instead of absolute addresses. Required for 64-bit PE files "
        "whose image base pushes addresses beyond 32-bit hex format limits.",
        dest="no_image_base",
        action="store_true",
    )
    parser.add_argument("-n", help="Number of data bytes per line", dest="row_length", default=16, type=int)
    args = parser.parse_args(argv)

    try:
        pp = PeParser(args.pe_file)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"\n'{args.pe_file}' is not valid PE/COFF file. Raised exception: '{repr(e)}'.")
        return 1

    add_image_base = not args.no_image_base
    image_base = pp.image_base()
    if args.no_image_base:
        print(f"\nUsing relative addresses (image base {image_base:#010x} subtracted).\n")
    else:
        print(f"\nUsing absolute addresses (image base: {image_base:#010x}).\n")

    print("Extracting from...\n")
    print("Section                   Address    Length")
    print("-" * 45)
    img = pp.create_image(
        callback=callback,
        join=args.join,
        add_image_base=add_image_base,
        exclude_pattern=args.exclude or "",
        include_pattern=args.include or "",
    )
    if img:
        try:
            dump(args.file_type, args.output_file_name, img, row_length=args.row_length)
        except Exception as e:
            if "address too large" in str(e).lower():
                print(f"\nError: {e}")
                print(f"Hint: Try using --no-image-base / -r to use relative addresses (subtract image base {image_base:#010x}).")
                return 1
            raise
        print(f"HEX image written to: '{args.output_file_name}' [{len(img)} total bytes]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
