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
    except Exception as e:
        print(f"\n'{args.pe_file}' is not a valid PE/COFF file. Raised exception: '{repr(e)}'.")
        return 1

    # Fetch via SymbolAPI to ensure DB is created/reused
    syms = pp.SymbolAPI(pp).fetch(name_pattern=args.pattern)  # type: ignore[attr-defined]
    # Fallback: if SymbolAPI attr is not present (static type), use direct list
    if not syms and pp.symbols:
        syms = [type("_S", (), s) for s in pp.symbols]  # quick adapter for printing

    # syms is a list of model.Pe_Symbol; order by value already in fetch()
    if args.order_by == "N":
        syms = sorted(syms, key=lambda s: getattr(s, "name", getattr(s, "symbol_name", "")))

    print("Name")
    print("Value")
    print("-" * 79)
    for sym in syms:
        name = getattr(sym, "name", getattr(sym, "symbol_name", ""))
        value = getattr(sym, "value", getattr(sym, "st_value", 0))
        print(f"{name:40}\n0x{int(value):016X}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
