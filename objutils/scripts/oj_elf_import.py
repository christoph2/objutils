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
import shutil
from pathlib import Path
from typing import Optional

from objutils.dwarf import DwarfProcessor
from objutils.elf import ElfParser
from objutils.elf import model as elf_model


def _print(msg: str, quiet: bool = False):
    if not quiet:
        print(msg)


def import_dwarf_to_db(
    elf_path: str,
    out_db: str | None,
    *,
    quiet: bool = False,
    verbose: bool = False,
    run_lines: bool = True,
    run_pubnames: bool = True,
    run_aranges: bool = True,
    run_mac: bool = False,
    force: bool = False,
) -> int:
    """Import DWARF data from ELF into a .prgdb database file.

    Returns an exit code as per module docstring.
    """
    elf_p = Path(elf_path)
    if not elf_p.exists() or not elf_p.is_file():
        _print(f"ELF file not found: {elf_path}", quiet)
        return 2

    # If forcing, remove any preexisting default DB and output DB to avoid stale schema/data
    default_db_path = elf_p.with_suffix(elf_model.DB_EXTENSION)
    try:
        if force:
            if default_db_path.exists():
                try:
                    default_db_path.unlink()
                except Exception:
                    # non-fatal; ElfParser will rebuild if needed
                    pass
            if out_db:
                outp = Path(out_db)
                if outp.exists():
                    try:
                        outp.unlink()
                    except Exception:
                        pass
    except Exception:
        # do not abort on cleanup issues
        pass

    try:
        ep = ElfParser(str(elf_p))
    except Exception as e:
        _print(f"Failed to open ELF file '{elf_path}': {e}", quiet)
        return 2

    if verbose:
        _print(str(ep), quiet)

    # Initialize DWARF processing; this will raise TypeError if no DWARF sections exist
    try:
        dp = DwarfProcessor(ep)
    except TypeError as te:
        _print(f"No DWARF sections available in '{elf_path}': {te}", quiet)
        return 1

    # Optional passes (non-fatal)
    if run_pubnames:
        try:
            dp.pubnames()
        except Exception as e:
            if verbose:
                _print(f"Warning: pubnames failed: {e}", quiet)
    if run_aranges:
        try:
            dp.aranges()
        except Exception as e:
            if verbose:
                _print(f"Warning: aranges failed: {e}", quiet)
    if run_lines:
        try:
            dp.do_lines()
        except Exception as e:
            if verbose:
                _print(f"Warning: do_lines failed: {e}", quiet)

    # Required: import .debug_info (and attributes) into DB
    try:
        dp.do_dbg_info()
    except Exception as e:
        _print(f"Error while parsing .debug_info: {e}", quiet)
        return 3

    if run_mac:
        try:
            dp.do_mac_info()
        except Exception as e:
            if verbose:
                _print(f"Warning: do_mac_info failed: {e}", quiet)

    # If an explicit output DB is requested and differs from default, copy the DB
    try:
        if out_db:
            src_db = default_db_path
            dst_db = Path(out_db)
            if str(dst_db.resolve()) != str(src_db.resolve()):
                # Ensure source DB exists: ElfParser always creates it in create_db_on_demand
                if not src_db.exists():
                    # As a fallback, flush current session into a new Model at dst_db
                    # (This branch should rarely happen; copying is the preferred path.)
                    with elf_model.Model(str(dst_db)) as _mdb:  # type: ignore[attr-defined]
                        pass
                else:
                    # Close current DB handle to release locks before copying
                    try:
                        ep.db.close()
                    except Exception:
                        pass
                    # Copy database file
                    shutil.copyfile(str(src_db), str(dst_db))
                    _print(f"Wrote database: {dst_db}", quiet)
            else:
                _print(f"Database available at: {src_db}", quiet)
        else:
            _print(f"Database available at: {default_db_path}", quiet)
    except Exception as e:
        _print(f"Failed to write/copy database: {e}", quiet)
        return 4

    return 0


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
