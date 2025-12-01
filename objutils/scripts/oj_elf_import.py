r"""
Import DWARF sections from an ELF file into a .prgdb SQLite database.

Usage:
    oj-elf-import path\to\program.elf [--out path\to\program.prgdb] [options]

Exit codes:
    0  success
    1  ELF has no DWARF sections
    2  cannot open ELF file
    3  parsing .debug_info failed
    4  output write/copy error

Notes:
- Uses objutils' ElfParser and DwarfProcessor to populate the database.
- Fails gracefully (non-zero exit code + message) if the ELF lacks DWARF.
"""

from __future__ import annotations

import argparse

from objutils.elf import import_dwarf_to_db


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oj-elf-import",
        description="Import DWARF sections from an ELF file into a .prgdb SQLite database.",
    )
    p.add_argument("elf", help="Path to the ELF file")
    p.add_argument("--out", "-o", help="Output .prgdb path (defaults to <elf>.prgdb)")
    p.add_argument("--force", "-f", action="store_true", help="Force rebuild: remove existing DB before import")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging of optional passes")
    p.add_argument("--no-lines", action="store_true", help="Skip parsing line information (.debug_line)")
    p.add_argument("--no-pubnames", action="store_true", help="Skip .debug_pubnames processing")
    p.add_argument("--no-aranges", action="store_true", help="Skip .debug_aranges processing")
    p.add_argument("--mac", action="store_true", help="Try to parse macro information (.debug_macinfo), non-fatal")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    return import_dwarf_to_db(
        elf_path=args.elf,
        out_db=args.out,
        quiet=args.quiet,
        verbose=args.verbose,
        run_lines=not args.no_lines,
        run_pubnames=not args.no_pubnames,
        run_aranges=not args.no_aranges,
        run_mac=args.mac,
        force=args.force,
    )


if __name__ == "__main__":
    raise SystemExit(main())
