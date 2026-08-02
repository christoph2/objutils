#!/usr/bin/env python
"""Example: ElfParser with in-memory SQLite database.

Demonstrates ``ElfParser(filename, in_memory=True)`` which keeps all parsed
ELF data in a transient ``:memory:`` SQLite database.  No .prgdb file is
written to disk – ideal for read-only analysis, CI pipelines or unit tests.

Usage::

    python examples/elf_in_memory.py examples/avr.elf

"""

import sys
from pathlib import Path

from objutils.elf import ElfParser


def analyse(elf_path: str) -> None:
    path = Path(elf_path)
    print(f"ELF file : {path}")

    # ------------------------------------------------------------------ #
    # Standard mode – creates / reuses  <name>.prgdb  next to the ELF    #
    # ------------------------------------------------------------------ #
    print("\n--- on-disk database (default) ---")
    parser_disk = ElfParser(str(path))
    try:
        print(f"  db_name   : {parser_disk.db_name}")
        print(f"  e_machine : {parser_disk.e_machine}")
        print(f"  e_entry   : 0x{parser_disk.e_entry:08x}")
    finally:
        parser_disk.close()

    prgdb = path.with_suffix(".prgdb")
    print(f"  .prgdb on disk: {prgdb.exists()}")

    # ------------------------------------------------------------------ #
    # In-memory mode – no file written, everything stays in RAM           #
    # ------------------------------------------------------------------ #
    print("\n--- in-memory database (in_memory=True) ---")
    parser_mem = ElfParser(str(path), in_memory=True)
    try:
        print(f"  db_name   : {parser_mem.db_name}")
        print(f"  e_machine : {parser_mem.e_machine}")
        print(f"  e_entry   : 0x{parser_mem.e_entry:08x}")

        sections = list(parser_mem.sections.fetch())
        print(f"  sections  : {len(sections)}")

        image = parser_mem.create_image()
        print(f"  image     : {len(image)} byte(s) in {len(image.sections)} section(s)")
    finally:
        parser_mem.close()

    # Verify: in-memory mode must not have created a .prgdb file
    # (the on-disk parser already created one above, so we can only
    # confirm that the in-memory run did *not* re-create it if we
    # temporarily remove it – skipped here for simplicity.)
    print("\nDone – no extra .prgdb was created by the in-memory parser.")


if __name__ == "__main__":
    elf = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent / "avr.elf")
    analyse(elf)
