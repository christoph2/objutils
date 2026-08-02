/**
 * @file elf_parser.cpp
 * @brief Fast C++ ELF symbol-table parser.
 *
 * Design notes
 * ------------
 * The Python/construct-based implementation in ElfParser._parse_symbol_section
 * is slow because it:
 *   1.  Invokes the construct DSL parser once per symbol entry.
 *   2.  Calls CString.parse() (another construct round-trip) for every name.
 *   3.  Had a caching bug so the SQLAlchemy section lookup was never cached.
 *
 * This C++ implementation avoids all of that:
 *   - Direct pointer arithmetic over the raw symbol-table bytes.
 *   - strnlen / pointer scan for null-terminated strings.
 *   - Single allocation: one std::vector<SymbolEntry> for the whole table.
 *   - Byte swapping only when target endianness != host endianness.
 *
 * ELF symbol layout (System V ABI)
 * ---------------------------------
 * Elf32_Sym  (16 bytes, offsets):
 *    0  st_name   uint32
 *    4  st_value  uint32
 *    8  st_size   uint32
 *   12  st_info   uint8    (bind << 4 | type)
 *   13  st_other  uint8
 *   14  st_shndx  uint16
 *
 * Elf64_Sym  (24 bytes, offsets):
 *    0  st_name   uint32
 *    4  st_info   uint8
 *    5  st_other  uint8
 *    6  st_shndx  uint16
 *    8  st_value  uint64
 *   16  st_size   uint64
 */

#include "elf_parser.hpp"

#include <bit>        // std::endian  (C++20)
#include <cstdint>
#include <cstring>    // std::memcpy, strnlen
#include <string>
#include <vector>

// ── Platform byte-swap helpers ────────────────────────────────────────────────

namespace {

inline uint16_t bswap16(uint16_t v) noexcept {
#if defined(_MSC_VER)
    return _byteswap_ushort(v);
#else
    return __builtin_bswap16(v);
#endif
}

inline uint32_t bswap32(uint32_t v) noexcept {
#if defined(_MSC_VER)
    return _byteswap_ulong(v);
#else
    return __builtin_bswap32(v);
#endif
}

inline uint64_t bswap64(uint64_t v) noexcept {
#if defined(_MSC_VER)
    return _byteswap_uint64(v);
#else
    return __builtin_bswap64(v);
#endif
}

// Is the current host little-endian?  Evaluated at compile time on C++20.
constexpr bool HOST_LE = (std::endian::native == std::endian::little);

// Read an integer of type T from raw bytes and convert from file endianness
// to host endianness.  Single-byte types are returned unchanged.
template <typename T>
[[nodiscard]] T read_val(const uint8_t* p, bool file_le) noexcept {
    T v{};
    std::memcpy(&v, p, sizeof(T));
    if constexpr (sizeof(T) == 1) {
        return v;
    }
    if (file_le != HOST_LE) {   // need a swap
        if constexpr (sizeof(T) == 2) v = static_cast<T>(bswap16(static_cast<uint16_t>(v)));
        else if constexpr (sizeof(T) == 4) v = static_cast<T>(bswap32(static_cast<uint32_t>(v)));
        else if constexpr (sizeof(T) == 8) v = static_cast<T>(bswap64(static_cast<uint64_t>(v)));
    }
    return v;
}

// ── String-table helper ───────────────────────────────────────────────────────

// Retrieve a null-terminated ASCII string from an ELF string table.
// Returns an empty string when the offset is out of range.
[[nodiscard]] std::string strtab_get(
    const uint8_t* strtab,
    std::size_t    strtab_size,
    uint32_t       offset) noexcept
{
    if (static_cast<std::size_t>(offset) >= strtab_size) {
        return {};
    }
    const char* s   = reinterpret_cast<const char*>(strtab + offset);
    std::size_t max = strtab_size - static_cast<std::size_t>(offset);
    std::size_t len = strnlen(s, max);
    return {s, len};
}

// ── Per-symbol intermediate representation ───────────────────────────────────

struct SymEntry {
    uint64_t    st_value;
    uint64_t    st_size;
    uint32_t    st_name;
    uint16_t    st_shndx;
    uint8_t     st_bind;    // st_info >> 4
    uint8_t     st_type;    // st_info & 0x0F
    uint8_t     st_other;
    std::string symbol_name;
};

// ── ELF32 parser ─────────────────────────────────────────────────────────────

//  Elf32_Sym layout (16 bytes):
//   [0] st_name  : u32
//   [4] st_value : u32
//   [8] st_size  : u32
//  [12] st_info  : u8
//  [13] st_other : u8
//  [14] st_shndx : u16

static constexpr std::size_t SYM32_SIZE = 16;

std::vector<SymEntry> parse_sym32(
    const uint8_t* sym_ptr, std::size_t sym_size,
    const uint8_t* str_ptr, std::size_t str_size,
    bool le)
{
    const std::size_t count = sym_size / SYM32_SIZE;
    std::vector<SymEntry> result;
    result.reserve(count);

    for (std::size_t i = 0; i < count; ++i) {
        const uint8_t* p = sym_ptr + i * SYM32_SIZE;

        SymEntry e{};
        e.st_name   = read_val<uint32_t>(p +  0, le);
        e.st_value  = read_val<uint32_t>(p +  4, le);
        e.st_size   = read_val<uint32_t>(p +  8, le);
        const uint8_t info = p[12];
        e.st_bind   = static_cast<uint8_t>(info >> 4u);
        e.st_type   = static_cast<uint8_t>(info & 0x0Fu);
        e.st_other  = p[13];
        e.st_shndx  = read_val<uint16_t>(p + 14, le);
        e.symbol_name = strtab_get(str_ptr, str_size, e.st_name);
        result.push_back(std::move(e));
    }
    return result;
}

// ── ELF64 parser ─────────────────────────────────────────────────────────────

//  Elf64_Sym layout (24 bytes):
//   [0] st_name  : u32
//   [4] st_info  : u8
//   [5] st_other : u8
//   [6] st_shndx : u16
//   [8] st_value : u64
//  [16] st_size  : u64

static constexpr std::size_t SYM64_SIZE = 24;

std::vector<SymEntry> parse_sym64(
    const uint8_t* sym_ptr, std::size_t sym_size,
    const uint8_t* str_ptr, std::size_t str_size,
    bool le)
{
    const std::size_t count = sym_size / SYM64_SIZE;
    std::vector<SymEntry> result;
    result.reserve(count);

    for (std::size_t i = 0; i < count; ++i) {
        const uint8_t* p = sym_ptr + i * SYM64_SIZE;

        SymEntry e{};
        e.st_name   = read_val<uint32_t>(p +  0, le);
        const uint8_t info = p[4];
        e.st_bind   = static_cast<uint8_t>(info >> 4u);
        e.st_type   = static_cast<uint8_t>(info & 0x0Fu);
        e.st_other  = p[5];
        e.st_shndx  = read_val<uint16_t>(p +  6, le);
        e.st_value  = read_val<uint64_t>(p +  8, le);
        e.st_size   = read_val<uint64_t>(p + 16, le);
        e.symbol_name = strtab_get(str_ptr, str_size, e.st_name);
        result.push_back(std::move(e));
    }
    return result;
}

} // anonymous namespace

// ── Public API (pybind11) ─────────────────────────────────────────────────────

py::list parse_symbol_table(
    py::bytes symtab_data,
    py::bytes strtab_data,
    bool      is_64bit,
    bool      little_endian)
{
    // Obtain raw pointers without copying – PyBytes_AsStringAndSize is O(1).
    const char* sym_raw  = nullptr;
    Py_ssize_t  sym_raw_size = 0;
    if (PyBytes_AsStringAndSize(symtab_data.ptr(),
                                const_cast<char**>(&sym_raw), &sym_raw_size) < 0) {
        throw py::error_already_set();
    }

    const char* str_raw  = nullptr;
    Py_ssize_t  str_raw_size = 0;
    if (PyBytes_AsStringAndSize(strtab_data.ptr(),
                                const_cast<char**>(&str_raw), &str_raw_size) < 0) {
        throw py::error_already_set();
    }

    const auto*  sym_ptr  = reinterpret_cast<const uint8_t*>(sym_raw);
    const auto*  str_ptr  = reinterpret_cast<const uint8_t*>(str_raw);
    const std::size_t sym_size = static_cast<std::size_t>(sym_raw_size);
    const std::size_t str_size = static_cast<std::size_t>(str_raw_size);

    // Parse all symbol entries in C++.
    std::vector<SymEntry> entries = is_64bit
        ? parse_sym64(sym_ptr, sym_size, str_ptr, str_size, little_endian)
        : parse_sym32(sym_ptr, sym_size, str_ptr, str_size, little_endian);

    // Build Python list of dicts.  The bulk of the per-symbol overhead is now
    // in Python-object construction, which is unavoidable, but still much
    // cheaper than running the construct DSL for each entry.
    py::list result;
    result.attr("__class__");  // force Python to realise the list (no-op, for clarity)

    for (const SymEntry& e : entries) {
        py::dict d;
        d["st_name"]     = static_cast<uint32_t>(e.st_name);
        d["st_value"]    = static_cast<uint64_t>(e.st_value);
        d["st_size"]     = static_cast<uint64_t>(e.st_size);
        d["st_bind"]     = static_cast<uint8_t>(e.st_bind);
        d["st_type"]     = static_cast<uint8_t>(e.st_type);
        d["st_other"]    = static_cast<uint8_t>(e.st_other);
        d["st_shndx"]    = static_cast<uint16_t>(e.st_shndx);
        d["symbol_name"] = e.symbol_name;
        result.append(std::move(d));
    }
    return result;
}
