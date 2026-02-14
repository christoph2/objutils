r"""
Generate C/C++ declarations from a .prgdb database using DWARF DIEs.

Usage:
    oj-cgen path\to\program.prgdb [--start OFFSET] [--out header.h] [options]

Notes:
- Uses objutils.dwarf.c_generator.CGenerator which, in turn, relies on the
  latest traverser.AttributeParser for correct CU-relative reference handling.
- If --start is not provided, the generator will start at the first root DIE
  (a DIE with no parent), walking that subtree to collect declarations.

Exit codes:
    0  success
    1  cannot open/read database
    2  no starting DIE found
    3  invalid --start offset (not found in DB)
    4  output write error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from objutils.dwarf.c_generator import CGenerator, RenderOptions
from objutils.elf import model


def _print(msg: str, quiet: bool = False):
    if not quiet:
        print(msg)


def _parse_offset(s: str) -> int | None:
    if s is None:
        return None
    try:
        s = s.strip().lower()
        if s.startswith("0x"):
            return int(s, 16)
        return int(s, 10)
    except Exception:
        return None


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oj-cgen",
        description="Generate C/C++ declarations from a .prgdb database using DWARF DIEs.",
    )
    p.add_argument("db", help="Path to the .prgdb SQLite database")
    p.add_argument("--start", "-s", help="Start DIE offset (hex like 0x14182 or decimal)")
    p.add_argument("--out", "-o", help="Output header path (defaults to stdout)")
    p.add_argument("--guard", help="Custom include guard macro name")
    p.add_argument("--no-guard", action="store_true", help="Do not emit include guards")
    p.add_argument(
        "--header-name",
        help="Header name to base include guard on (if --guard not given)",
    )
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose messages")
    return p


def _find_start_die(sess, start_off: int | None):
    """Return a DebugInformationEntry to use as the root for code generation."""
    DIE = model.DebugInformationEntry
    if isinstance(start_off, int):
        die = sess.query(DIE).filter(DIE.offset == int(start_off)).one_or_none()
        if die is None:
            return None
        return die
    # Fallback: first root DIE (no parent)
    die = sess.query(DIE).filter(DIE.parent_id.is_(None)).first()
    return die


def generate_from_db(
    db_path: str,
    *,
    start_offset: int | None = None,
    out_path: str | None = None,
    guard: str | None = None,
    no_guard: bool = False,
    header_name: str | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> int:
    dbp = Path(db_path)
    if not dbp.exists() or not dbp.is_file():
        _print(f"Database not found: {db_path}", quiet)
        return 1

    # Open DB
    try:
        db = model.Model(str(dbp))
        sess = db.session
    except Exception as e:
        _print(f"Failed to open database '{db_path}': {e}", quiet)
        return 1

    # Resolve start DIE
    start_die = _find_start_die(sess, start_offset)
    if start_die is None:
        if start_offset is not None:
            _print(f"Start DIE not found at offset: {hex(start_offset) if isinstance(start_offset, int) else start_offset}", quiet)
            try:
                db.close()
            except Exception:
                pass
            return 3
        else:
            _print("No root DIE found in database (parent_id IS NULL).", quiet)
            try:
                db.close()
            except Exception:
                pass
            return 2

    if verbose:
        _print(f"Using start DIE at offset 0x{start_die.offset:08x} (tag={getattr(start_die.abbrev, 'tag', start_die.tag)})", quiet)

    # Configure generator options
    opts = RenderOptions()
    if no_guard:
        opts.include_guards = False
    if guard:
        opts.include_guards = True
        opts.header_guard = guard

    gen = CGenerator(sess, options=opts)
    try:
        code = gen.generate_header(start_die, header_name=header_name)
    except Exception as e:
        try:
            db.close()
        except Exception:
            pass
        _print(f"Generation failed: {e}", quiet)
        return 1

    # Output
    if out_path:
        try:
            outp = Path(out_path)
            outp.write_text(code, encoding="utf-8")
            if verbose:
                _print(f"Wrote header: {outp}", quiet)
        except Exception as e:
            _print(f"Failed to write output file '{out_path}': {e}", quiet)
            try:
                db.close()
            except Exception:
                pass
            return 4
    else:
        # stdout
        sys.stdout.write(code)

    try:
        db.close()
    except Exception:
        pass
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    start_off = _parse_offset(args.start) if getattr(args, "start", None) else None
    return generate_from_db(
        db_path=args.db,
        start_offset=start_off,
        out_path=args.out,
        guard=args.guard,
        no_guard=args.no_guard,
        header_name=args.header_name,
        quiet=args.quiet,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    raise SystemExit(main())
