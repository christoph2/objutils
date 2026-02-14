#!/usr/bin/env python
"""Import basic PE/COFF information (header, sections, symbols) into an SQLite database."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from objutils.pecoff import PeParser
from objutils.pecoff import model as pe_model


def default_out_path(pe_path: str) -> str:
    p = Path(pe_path)
    return str(p.with_suffix(p.suffix + ".pedb"))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oj-coff-import",
        description="Import PE/COFF header, sections, and symbols into an SQLite database.",
    )
    p.add_argument("pe", help="Path to the PE/COFF file (.exe/.dll/.obj)")
    p.add_argument("--out", "-o", help="Output .db path (defaults to <pe>.<ext>.pedb)")
    p.add_argument("--force", "-f", action="store_true", help="Overwrite output if it already exists")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    out_db = args.out or default_out_path(args.pe)
    if os.path.exists(out_db) and not args.force:
        print(f"Output database already exists: '{out_db}'. Use --force to overwrite.")
        return 2

    try:
        pp = PeParser(args.pe)
    except Exception as e:
        print(f"\n'{args.pe}' is not a valid PE/COFF file. Raised exception: '{repr(e)}'.")
        return 1

    # Build DB and populate
    mdl = pe_model.Model(out_db)
    with mdl.session() as ses:
        # Header
        hdr = pe_model.Pe_Header(
            machine=pp.coff_header.get("machine", 0) if pp.coff_header else 0,
            number_of_sections=pp.coff_header.get("number_of_sections", 0) if pp.coff_header else 0,
            time_date_stamp=pp.coff_header.get("time_date_stamp", 0) if pp.coff_header else 0,
            characteristics=pp.coff_header.get("characteristics", 0) if pp.coff_header else 0,
            image_base=pp.optional_header.get("image_base", 0) if pp.optional_header else 0,
            section_alignment=pp.optional_header.get("section_alignment", 0) if pp.optional_header else 0,
            file_alignment=pp.optional_header.get("file_alignment", 0) if pp.optional_header else 0,
        )
        ses.add(hdr)

        # Sections
        for s in pp.sections:
            ses.add(
                pe_model.Pe_Section(
                    name=s["name"],
                    vaddr=s["virtual_address"],
                    vsize=s["virtual_size"],
                    file_offset=s["pointer_to_raw_data"],
                    size=s["size_of_raw_data"],
                    characteristics=s["characteristics"],
                )
            )

        # Symbols
        for sym in pp.symbols:
            ses.add(
                pe_model.Pe_Symbol(
                    name=sym["name"],
                    value=int(sym.get("value", 0)),
                    section_number=sym.get("section_number", 0),
                    type=int(sym.get("type", 0)),
                    storage_class=int(sym.get("storage_class", 0)),
                )
            )
        ses.commit()

    print(f"PE/COFF database written to: '{out_db}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
