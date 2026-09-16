#!/usr/bin/env python
"""List symbols contained in a PE/COFF file (COFF table or PDB if available)."""

from __future__ import annotations

import argparse

from objutils.pecoff import PeParser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Display PE/COFF symbols.")
    parser.add_argument("pe_file", help="PE/COFF file (.exe/.dll/.obj)")
    parser.add_argument(
        "-p",
        "--pattern",
        help="Only display symbols whose name contains PATTERN (simple substring)",
        dest="pattern",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-o",
        "--order-by",
        choices=["N", "V"],
        default="V",
        help="Order symbols by name (N) or value (V)",
    )
    args = parser.parse_args(argv)

    try:
        pp = PeParser(args.pe_file)
    except (OSError, ValueError, RuntimeError) as e:
        print(f"\n'{args.pe_file}' is not a valid PE/COFF file. Raised exception: '{e!r}'.")
        return 1

    # Fetch via SymbolAPI to ensure DB is created/reused
    # syms = SymbolAPI(pp).fetch(name_pattern=args.pattern)
    syms = pp.coff_symbols
    if syms:
        if args.order_by == "N":
            syms = sorted(syms, key=lambda s: getattr(s, "name", getattr(s, "symbol_name", "")))

        print("Name")
        print("Value")
        print("-" * 79)
        for sym in syms:
            if not sym.storage_class in (2, 3) or sym.location is None:
                continue
            name = sym.name
            value = sym.value
            address = sym.location
            print(f"{name:40}\n0x{int(value):016X}  0x{int(address):016X}\n")
    syms = pp.pdb_symbols
    if syms:
        syms = sorted(syms, key=lambda s: getattr(s, "name", ""))
        for sym in syms:
            name = sym.name
            name = name.decode("utf-8") if isinstance(name, bytes) else name
            location = sym.location
            print(f"{name:40}\n0x{location:016X}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
