Known-Good Reference: DWARF Parser

Date: 2025-08-24 11:28 (local)
Commit: b8e63f4fc59695b6229344cdf5b4daff512da411

Scope
- The DWARF parser (objutils/dwarf) and its integration with the ELF layer (objutils/elf) are confirmed working as expected at the above commit.
- This reference marks the current state as a known-good baseline after the latest rollback.

Notes
- Recent improvements include robust database schema checks and a portable examples/dwarfer.py.
- Abbreviation traversal includes caching to avoid repeated re-parsing.

How to verify
1. Use the example script with any ELF containing DWARF sections:
   python examples\\dwarfer.py <path-to-elf>
   - The script will run several DWARF passes and report issues gracefully if a pass is unavailable.
2. Or, programmatically via the library:
   from objutils.elf import ElfParser
   from objutils.dwarf import DwarfProcessor
   ep = ElfParser(<path-to-elf>)
   dp = DwarfProcessor(ep)
   dp.do_dbg_info()

Rolling back to this baseline
- Check out the recorded commit:
  git checkout b8e63f4fc59695b6229344cdf5b4daff512da411

Rationale
- This document serves as an in-repo anchor for the known-good DWARF parser state without changing version numbers or code.
