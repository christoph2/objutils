#!/usr/bin/env python
"""DWARF importer and CU explorer.

Converts ELF DWARF sections into a .prgdb database (like dwarfer.py) and optionally
prints compile-unit summaries or walks DIE attributes (like cu_info.py).
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from objutils.dwarf.constants import Tag
from objutils.dwarf.traverser import AttributeParser
from objutils.elf import import_dwarf_to_db, model


def _parse_offset(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid offset '{text}'") from exc


def _attr_value(die: Any, name: str) -> Any:
    attrs = getattr(die, "attributes_map", {}) or {}
    attr = attrs.get(name)
    return None if attr is None else getattr(attr, "raw_value", None)


def _print_cus(cus: Iterable[Any], *, quiet: bool) -> None:
    if quiet:
        return
    print("Compilation Units:")
    print("-------------------")
    for idx, cu in enumerate(cus, 1):
        name = _attr_value(cu, "name") or ""
        low_pc = _attr_value(cu, "low_pc")
        high_pc = _attr_value(cu, "high_pc")
        low_pc_str = f"0x{int(low_pc):08x}" if low_pc is not None else "-"
        high_pc_str = f"0x{int(high_pc):08x}" if high_pc is not None else "-"
        print(f"[{idx:03d}] off=0x{int(cu.offset):08x} name={name} range={low_pc_str}..{high_pc_str}")


def _print_summary(session, *, quiet: bool) -> None:
    if quiet:
        return
    die_count = session.query(model.DebugInformationEntry).count()
    attr_count = session.query(model.DIEAttribute).count()
    print(f"DIEs: {die_count:,}")
    print(f"Attributes: {attr_count:,}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import DWARF sections into a .prgdb and optionally inspect compile units.")
    parser.add_argument("elf", help="Path to ELF file with DWARF sections")
    parser.add_argument("--out-db", help="Output .prgdb path (defaults to <elf>.prgdb)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing database")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose DWARF processing output")
    parser.add_argument("--skip-lines", action="store_true", help="Skip .debug_line processing")
    parser.add_argument("--skip-pubnames", action="store_true", help="Skip .debug_pubnames processing")
    parser.add_argument("--skip-aranges", action="store_true", help="Skip .debug_aranges processing")
    parser.add_argument("--skip-mac", action="store_true", help="Skip .debug_macro processing")
    parser.add_argument("--list-cus", action="store_true", help="List compile units after import")
    parser.add_argument("--summary", action="store_true", help="Print DIE/attribute counts after import")
    parser.add_argument(
        "--walk-attrs",
        action="store_true",
        help="Traverse DIE attributes with AttributeParser (starts at first DIE unless --offset is set).",
    )
    parser.add_argument(
        "--offset",
        type=_parse_offset,
        help="Absolute DIE offset (decimal or 0x-prefixed hex) used for --walk-attrs start point.",
    )
    args = parser.parse_args(argv)

    rc = import_dwarf_to_db(
        args.elf,
        args.out_db,
        quiet=args.quiet,
        verbose=args.verbose,
        run_lines=not args.skip_lines,
        run_pubnames=not args.skip_pubnames,
        run_aranges=not args.skip_aranges,
        run_mac=not args.skip_mac,
        force=args.force,
    )
    if rc != 0:
        return rc

    post_actions = args.list_cus or args.summary or args.walk_attrs
    if not post_actions:
        return 0

    db_path = Path(args.out_db) if args.out_db else Path(args.elf).with_suffix(model.DB_EXTENSION)
    try:
        db = model.Model(str(db_path))
    except (OSError, SQLAlchemyError, ValueError) as exc:
        if not args.quiet:
            print(f"Failed to open database '{db_path}': {exc}")
        return 4

    try:
        session = db.session
        if args.summary:
            _print_summary(session, quiet=args.quiet)

        if args.list_cus or args.walk_attrs:
            DIE = model.DebugInformationEntry
            cus = session.query(DIE).filter(DIE.tag == Tag.compile_unit).order_by(DIE.offset).all()
            if args.list_cus:
                _print_cus(cus, quiet=args.quiet)

            if args.walk_attrs:
                start_die = None
                if args.offset is not None:
                    start_die = session.query(DIE).filter(DIE.offset == int(args.offset)).first()
                    if start_die is None and not args.quiet:
                        print(f"No DIE found at offset 0x{int(args.offset):08x}; falling back to first entry.")
                if start_die is None:
                    start_die = session.query(DIE).first()
                if start_die is None:
                    if not args.quiet:
                        print("No DebugInformationEntry available in the database to traverse.")
                    return 5
                ap = AttributeParser(session=session)
                ap.traverse_tree(start_die)
    except (OSError, SQLAlchemyError, RuntimeError, ValueError) as exc:
        if not args.quiet:
            print(f"Post-processing failed: {exc}")
        return 5
    finally:
        try:
            db.close()
        except SQLAlchemyError:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
