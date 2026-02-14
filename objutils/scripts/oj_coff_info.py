#!/usr/bin/env python
"""Display information about PE/COFF files (similar spirit to oj_elf_info)."""

from __future__ import annotations

import argparse

from objutils.pecoff import PeParser
from objutils.pecoff import defs as pe_defs


def print_header(text: str) -> None:
    print("\n{1}\n{0}\n{1}\n".format(text, "=" * len(text)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Display informations about PE/COFF files.")
    parser.add_argument("pe_file", help="PE/COFF file (.exe/.dll/.obj)")
    parser.add_argument("--pdb", "-p", dest="pdb_file", nargs="*", help="Path to PDB file if not in same location as PE file")
    args = parser.parse_args(argv)
    print("Pths", args.pdb_file)
    try:
        pp = PeParser(args.pe_file, pdb_path=args.pdb_file)
    except Exception as e:
        print(f"\n'{args.pe_file}' is not a valid PE/COFF file. Raised exception: '{repr(e)}'.")
        return 1

    machine = pp.machine() or 0
    machine_names = {
        pe_defs.IMAGE_FILE_MACHINE_I386: "I386",
        pe_defs.IMAGE_FILE_MACHINE_AMD64: "AMD64",
        pe_defs.IMAGE_FILE_MACHINE_ARM: "ARM",
        pe_defs.IMAGE_FILE_MACHINE_ARM64: "ARM64",
    }
    machine_name = machine_names.get(machine, f"0x{machine:04X}")
    num_secs = pp.coff_header.get("number_of_sections", 0) if pp.coff_header else 0
    characteristics = pp.coff_header.get("characteristics", 0) if pp.coff_header else 0
    img_base = pp.image_base()

    print(f"Machine:         {machine_name}")
    print(f"Sections:        {num_secs}")
    print(f"ImageBase:       0x{img_base:016X}")
    print(f"Characteristics: {' · '.join(pe_defs.decode_characteristics(characteristics))}")

    print_header("Sections")
    print("Name                      RVA        FileOff    RawSize  VSize")
    print("-" * 79)
    for s in pp.sections:
        print(
            f"{s['name']:25} 0x{s['virtual_address']:08X} 0x{s['pointer_to_raw_data']:08X} "
            f"0x{s['size_of_raw_data']:06X} 0x{s['virtual_size']:06X}"
        )

    if pp.symbols:
        print_header("Symbols (COFF or PDB)")
        print("Name                           Value")
        print("-" * 79)
        # for sym in
        #   pp.symbols, key=lambda x: (x.get("value", 0), x.get("name", ""))):
        for sym in pp.symbols:
            print(f"{sym.name[:30]:30} 0x{sym.rel_address:016X} {sym.tag}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
