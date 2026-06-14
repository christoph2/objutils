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
    parser.add_argument("--symbols", "-s", action="store_true", help="Dump symbols from PDB file if available")
    args = parser.parse_args(argv)

    # dump_type_tree: bool = False

    try:
        pp = PeParser(args.pe_file, pdb_path=args.pdb_file)
    except (OSError, ValueError, RuntimeError) as e:
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

    if pp.symbols and args.symbols:
        # pp.symbols = sorted(pp.symbols, key=lambda s: s.name)
        pp.symbols = sorted(pp.symbols, key=lambda s: s.location)

        print_header("Symbols (COFF or PDB)")
        print("Name                                               Value              Size")
        print("-" * 80)
        for sym in pp.symbols:
            print(f"{sym.name.decode():<50} 0x{sym.location:016X} {sym.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
