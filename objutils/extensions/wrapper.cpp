
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "difflib.h"
#include "elf_parser.hpp"

namespace py = pybind11;
using namespace difflib;


PYBIND11_MODULE(hexfiles_ext, m) {
	// ── difflib.SequenceMatcher ────────────────────────────────────────────
	py::class_<SequenceMatcher<std::string>>(m, "SequenceMatcher")
		.def(py::init<const std::string &, const std::string &, SequenceMatcher<std::string>::junk_function_type, bool>(),
		     py::arg("a"), py::arg("b"),
		     py::arg("is_junk") = nullptr, py::arg("auto_junk") = true)
		.def("ratio",      &SequenceMatcher<std::string>::ratio)
		.def("get_opcodes",&SequenceMatcher<std::string>::get_opcodes)
	;

	// ── ELF symbol-table parser ────────────────────────────────────────────
	m.def(
		"parse_symbol_table",
		&parse_symbol_table,
		py::arg("symtab_data"),
		py::arg("strtab_data"),
		py::arg("is_64bit"),
		py::arg("little_endian"),
		R"doc(
Parse a raw ELF symbol-table section in C++ and return a list of dicts.

This is a high-performance replacement for the construct-based loop in
ElfParser._parse_symbol_section().  It handles both ELF32 and ELF64 as
well as little-endian and big-endian ELF files.

Parameters
----------
symtab_data : bytes
    Raw bytes of the SHT_SYMTAB / SHT_DYNSYM section.
strtab_data : bytes
    Raw bytes of the associated string-table section (.strtab / .dynstr).
is_64bit : bool
    True for ELF64 (24-byte Elf64_Sym entries), False for ELF32 (16-byte).
little_endian : bool
    True when EI_DATA == ELFDATA2LSB (little-endian).

Returns
-------
list[dict]
    One dict per symbol with keys:
      st_name (int), st_value (int), st_size (int),
      st_bind (int), st_type (int), st_other (int),
      st_shndx (int), symbol_name (str).
)doc"
	);
}
