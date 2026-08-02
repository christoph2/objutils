
#pragma once

/**
 * @file elf_parser.hpp
 * @brief Fast C++ ELF symbol-table parser exposed via pybind11.
 *
 * parse_symbol_table() replaces the Python/construct-based loop in
 * ElfParser._parse_symbol_section().  It reads raw ELF32_Sym / ELF64_Sym
 * entries directly with pointer arithmetic – no Python object overhead per
 * entry – and resolves symbol names from the string table in a single pass.
 *
 * Supported:
 *   - 32-bit and 64-bit ELF
 *   - Little-endian and big-endian ELF files on any host
 *
 * Return value:
 *   Python list of dicts, one entry per symbol, with keys:
 *     st_name (int), st_value (int), st_size (int),
 *     st_bind (int), st_type (int), st_other (int),
 *     st_shndx (int), symbol_name (str)
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

/**
 * @brief Parse a raw ELF symbol-table section.
 *
 * @param symtab_data  Raw bytes of the symbol-table section (SHT_SYMTAB / SHT_DYNSYM).
 * @param strtab_data  Raw bytes of the associated string-table section (.strtab / .dynstr).
 * @param is_64bit     True for ELF64, false for ELF32.
 * @param little_endian True when the ELF file uses little-endian encoding (EI_DATA == 1).
 * @return             Python list of dicts – one per symbol.
 */
py::list parse_symbol_table(
    py::bytes symtab_data,
    py::bytes strtab_data,
    bool      is_64bit,
    bool      little_endian
);
