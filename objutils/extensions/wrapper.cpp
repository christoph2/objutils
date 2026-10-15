#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <stdexcept>

#include "difflib.h"
#include "elf_parser.hpp"

namespace py = pybind11;
using namespace difflib;

namespace {

constexpr uint64_t DW_FORM_implicit_const = 0x21;

[[nodiscard]] uint64_t read_uleb(const uint8_t*& p, const uint8_t* end) {
	uint64_t result = 0;
	unsigned shift = 0;
	while (p < end) {
		const uint8_t byte = *p++;
		result |= static_cast<uint64_t>(byte & 0x7Fu) << shift;
		if ((byte & 0x80u) == 0u) {
			return result;
		}
		shift += 7u;
	}
	throw std::runtime_error("truncated ULEB128 in .debug_abbrev section");
}

} // namespace

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

	m.def(
		"parse_abbrev_table",
		[](py::bytes abbrev_data, uint32_t abbr_offset, uint64_t target_code) {
			const char* raw = nullptr;
			Py_ssize_t raw_size = 0;
			if (PyBytes_AsStringAndSize(abbrev_data.ptr(), const_cast<char**>(&raw), &raw_size) < 0) {
				throw py::error_already_set();
			}

			const auto* data = reinterpret_cast<const uint8_t*>(raw);
			const auto* end = data + static_cast<std::size_t>(raw_size);
			if (static_cast<std::size_t>(abbr_offset) >= static_cast<std::size_t>(raw_size)) {
				throw std::out_of_range("abbreviation offset out of range");
			}

			const uint8_t* p = data + abbr_offset;
			py::list result;

			while (p < end) {
				const uint64_t code = read_uleb(p, end);
				if (code == 0) {
					continue;
				}

				const uint64_t tag = read_uleb(p, end);
				if (p >= end) {
					throw std::runtime_error("truncated abbreviation header");
				}
				const bool children = (*p++ != 0u);

				py::list attrs;
				while (true) {
					const uint64_t attr_value = read_uleb(p, end);
					const uint64_t form_value = read_uleb(p, end);
					if (attr_value == 0 || form_value == 0) {
						break;
					}

					py::object special = py::none();
					if (form_value == DW_FORM_implicit_const) {
						special = py::int_(read_uleb(p, end));
					}
					attrs.append(py::make_tuple(attr_value, form_value, std::move(special)));
				}

				py::dict entry;
				entry["code"] = code;
				entry["tag"] = tag;
				entry["children"] = children;
				entry["attrs"] = std::move(attrs);
				result.append(std::move(entry));
				if (code == target_code) {
					return result;
				}
			}

			return result;
		},
		py::arg("abbrev_data"),
		py::arg("abbr_offset"),
		py::arg("target_code"),
		R"doc(
Parse DWARF abbreviation entries starting at a CU-specific offset.

The function scans .debug_abbrev from abbr_offset until the requested code is
found, returning every parsed abbreviation entry along the way so Python can
populate its cache just like the pure-Python path.

Each returned list item is a dict with keys:
  code (int), tag (int), children (bool), attrs (list[tuple[int, int, int|None]])
)doc"
	);
}
