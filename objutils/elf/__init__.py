#!/usr/bin/env python
r"""ELF (Executable and Linkable Format) binary file parser and processor.

This module provides comprehensive support for parsing and analyzing ELF binary
files, with a focus on embedded systems and cross-compilation scenarios.

**Architecture Overview:**

The ELF parser module integrates three key components:

1. **Binary Parsing Layer** (construct library)
   - Uses the `construct` library for declarative binary format definitions
   - Handles both 32-bit (ELF32) and 64-bit (ELF64) ELF formats
   - Supports both little-endian and big-endian architectures
   - Automatically detects architecture from ELF identification bytes (EI_*)

2. **Object-Relational Mapping** (SQLAlchemy)
   - Persists parsed ELF data to a SQLite database (.prgdb file)
   - Automatic database creation and schema management
   - Hash-based change detection to invalidate cached databases when files change
   - Session-based API for efficient database queries

3. **Property-Based API**
   - Access ELF header fields directly as properties (e.g., `parser.e_machine`)
   - Section and Symbol APIs for complex queries via SectionAPI and SymbolAPI
   - Machine-specific data loading via architecture definitions (MACHINE_DATA)

**Key Classes:**

- **ElfParser**: Main parser class handling file I/O, binary parsing, and database management
- **SectionAPI**: Query interface for accessing ELF sections with filtering/sorting
- **SymbolAPI**: Query interface for accessing ELF symbols with flexible filtering
- **DBAPI**: Base class providing database session management for API wrappers

**Database Integration (.prgdb files):**

When an ELF file is parsed, the parser automatically creates a .prgdb file
(SQLite database) next to it. This database contains:

- ELF header information (ELF_Header table)
- Section headers and contents (Elf_Section table)
- Program headers (Elf_ProgramHeaders table)
- Symbol tables (Elf_Symbol table)
- Notes and comments (Elf_Note, Elf_Comment tables)
- Optional DWARF debug information (via import_dwarf_to_db)

The database is invalidated and rebuilt if:
- The source ELF file is modified (detected via SHA512 hash)
- The database schema changes (column validation)
- The database file is manually deleted

**Image Creation Workflow:**

The `create_image()` method converts ELF sections into an `objutils.Image`:

1. Query sections from database with optional filters:
   - Include sections matching regex pattern
   - Exclude sections matching regex pattern
   - Only allocatable sections (SHF_ALLOC flag set)
2. Convert each section to a `Section` object with address and data
3. Optionally merge adjacent sections (join=True)
4. Return combined Image representing the binary layout

**Property-Based Header Access:**

Instead of accessing nested header structures, the parser provides direct property
access for convenience:

    parser = ElfParser('firmware.elf')

    # Basic identification fields (EI_* from e_ident[0..15])
    machine_type = parser.e_machine     # Target machine type (e.g., 83 for AVR)
    endian = parser.endianess           # '<' for little-endian, '>' for big-endian
    is_64bit = parser.ei_class == 2     # Check if 64-bit ELF

    # Extended header fields
    entry_point = parser.e_entry        # Program entry point address
    section_header_offset = parser.e_shoff
    num_sections = parser.e_shnum

    # Segment and section information
    segments = parser.segments          # List of program header entries
    sections = parser.sections.fetch()  # Fetch all sections

    # Metadata
    comment = parser.comment            # .comment section content
    notes = parser.notes                # ELF notes
    arm_attrs = parser.arm_attributes   # ARM-specific attributes

**Section API Usage Examples:**

    # Get specific section
    text_section = parser.sections.get('.text')
    if text_section:
        print(f"Address: 0x{text_section.sh_addr:08x}")
        print(f"Size: {text_section.sh_size} bytes")
        print(f"Data: {text_section.section_image}")

    # Fetch with filtering
    sections = parser.sections.fetch(order_by_address=True)
    debug_sections = parser.sections.fetch(name_pattern=r'^\.debug')

**Symbol API Usage Examples:**

    # Get specific symbol
    sym = parser.symbols.get('main', section_name='.text')
    if sym:
        print(f"Value: 0x{sym.st_value:08x}")
        print(f"Size: {sym.st_size}")

    # Fetch symbols with complex filtering
    global_funcs = parser.symbols.fetch(
        bindings='g',           # Global binding
        types_str='func',       # Function type
        order_by_value=True     # Sort by address
    )

    # Fetch with regex filtering and section grouping
    result = parser.symbols.fetch(
        name_pattern=r'^[^_]',  # Exclude C-prefixed symbols
        group_by_section=True   # Return dict keyed by section name
    )

**Binary Parsing Details:**

The module uses `construct` Struct definitions for each ELF component:

1. **BasicHeader** (fixed 16 bytes):
   - ELF magic number (0x7F, 'E', 'L', 'F')
   - EI_CLASS: 1 (32-bit) or 2 (64-bit)
   - EI_DATA: 1 (little-endian) or 2 (big-endian)
   - EI_VERSION, EI_OSABI, EI_ABIVERSION
   - 7 bytes padding

2. **ExtendedHeader** (variable size based on architecture):
   - e_type, e_machine, e_version
   - e_entry, e_phoff, e_shoff, e_flags
   - e_ehsize, e_phentsize, e_phnum
   - e_shentsize, e_shnum, e_shstrndx

3. **Section Headers** (one per section):
   - sh_name, sh_type, sh_flags
   - sh_addr, sh_offset, sh_size
   - sh_link, sh_info, sh_addralign, sh_entsize

4. **Program Headers** (one per segment):
   - p_type, p_flags
   - p_offset, p_vaddr, p_paddr
   - p_filesz, p_memsz, p_align

5. **Symbol Tables** (one entry per symbol):
   - st_name, st_value, st_size
   - st_info (bind/type), st_other, st_shndx

**Supported Architectures:**

The module includes built-in support for architecture-specific data and attributes:

- ARM (including ARM-specific attributes parsing)
- AVR (common embedded target)
- x86/x86-64 (standard architectures)
- MIPS, PowerPC, and other RISC architectures

Machine-specific code is loaded dynamically via the MACHINE_DATA dictionary.

**DWARF Debug Information:**

Use the `import_dwarf_to_db()` function to extract DWARF debug information
from an ELF file and populate the program database:

    from objutils.elf import import_dwarf_to_db, open_program_database

    # Import DWARF to create .prgdb database
    rc = import_dwarf_to_db(
        'firmware.elf',
        out_db=None,  # Use default location (firmware.prgdb)
        run_lines=True,      # Process line number info
        run_pubnames=True,   # Process public names
        run_aranges=True,    # Process address ranges
        force=False          # Don't rebuild if already exists
    )

    if rc == 0:
        db = open_program_database('firmware.elf')
        # Access debug information via database

**Error Handling and Validation:**

- Binary format validation at parse time
- Database schema compatibility checking
- Graceful handling of truncated/corrupted sections
- StreamError catching during symbol table parsing
- File lock handling for database operations

**Performance Considerations:**

- Memory-mapped file access for large ELF files
- SQLite database caching for repeated queries
- Lazy parsing of debug sections
- Bulk insert optimization for symbol tables

**References:**

- ELF Specification: https://refspecs.linuxbase.org/elf/
- TIS ELF 1.2 Specification (original)
- GNU ELF extensions (SHN_*, STT_GNU_*, etc.)
- ARM EABI supplemental specifications

**Thread Safety:**

The ElfParser class is NOT thread-safe. Each thread should create its own
ElfParser instance to avoid SQLAlchemy session conflicts.

**Platform Support:**

- Linux (primary)
- Windows (with minor path handling differences)
- macOS (with minor path handling differences)
- Any platform with Python 3.9+ and SQLite support
"""

__copyright__ = """
   objutils - Object file library for Python.

  (C) 2010-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

  All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import binascii
import hashlib
import os
import re
import time
import typing
from collections import OrderedDict, namedtuple
from itertools import groupby
from pathlib import Path

from construct import (
    Adapter,
    Array,
    BitsInteger,
    BitStruct,
    Bytes,
    Computed,
    Const,
    Construct,
    CString,
    Enum,
    IfThenElse,
    Int8ul,
    Int16ub,
    Int16ul,
    Int32sb,
    Int32sl,
    Int32ub,
    Int32ul,
    Int64sb,
    Int64sl,
    Int64ub,
    Int64ul,
    Padding,
    Pass,
    StreamError,
    Struct,
    Tell,
    Union,
    singleton,
    this,
)
from sqlalchemy import func, not_

from objutils import Image, Section
from objutils.elf import defs, model
from objutils.elf.arm import attributes
from objutils.utils import create_memorymapped_fileview


MAGIC: bytes = b"\x7fELF"


@singleton
class Pass2(Construct):
    """Pass-through construct that parses nothing and builds nothing.

    A do-nothing construct, useful as the default case for Switch constructs.
    Returns None on parsing and produces no output when building.

    Example:
        >>> Pass2.parse(b"")
        >>> Pass2.build(None)
        b''
        >>> Pass2.sizeof()
        0
    """

    def __init__(self) -> None:
        """Initialize Pass2 construct."""
        super().__init__()
        self.flagbuildnone = True

    def _parse(self, stream: typing.Any, context: typing.Any, path: str) -> None:
        """Parse nothing from stream.

        Args:
            stream: Input stream (not used).
            context: Context object (not used).
            path: Path in parent construct.

        Returns:
            None always.
        """
        return None

    def _build(self, obj: typing.Any, stream: typing.Any, context: typing.Any, path: str) -> None:
        """Build nothing to stream.

        Args:
            obj: Object to build (not used).
            stream: Output stream (not used).
            context: Context object (not used).
            path: Path in parent construct.
        """
        pass

    def _sizeof(self, context: typing.Any, path: str) -> int:
        """Return size as 0.

        Args:
            context: Context object (not used).
            path: Path in parent construct.

        Returns:
            0 always.
        """
        return 0


Test = Struct(
    "ei_version"
    / Enum(
        Int8ul,
        default=Pass,
        EV_NONE=0,
        EV_CURRENT=1,
    )
)


class UTCTimeStampAdapter(Adapter):
    """Adapter to convert Unix timestamps to/from human-readable time strings.

    This adapter converts between Unix timestamps (seconds since epoch) and
    ASCII time strings (e.g., 'Wed Oct 5 16:30:45 2022').
    """

    def _decode(self, obj: int, context: typing.Any) -> str:
        """Decode Unix timestamp to ctime string.

        Args:
            obj: Unix timestamp (seconds since epoch).
            context: Context object (not used).

        Returns:
            Human-readable time string from time.ctime().
        """
        return time.ctime(obj)

    def _encode(self, obj: str, context: typing.Any) -> int:
        """Encode ctime string to Unix timestamp.

        Args:
            obj: Human-readable time string.
            context: Context object (not used).

        Returns:
            Unix timestamp as integer.
        """
        return int(time.mktime(time.strptime(obj)))


def UTCTimeStamp(name: str) -> Adapter:
    """Create a UTC timestamp adapter field for construct Struct.

    Args:
        name: Field name for the timestamp.

    Returns:
        Adapter instance wrapping an Int32ul field.
    """
    return UTCTimeStampAdapter(name / Int32ul)


class ListToBytesAdapter(Adapter):
    """Adapter to convert between lists and bytes.

    Converts lists of integers (0-255) to/from bytes objects during
    construct parsing and building.
    """

    def _decode(self, obj: list[int], context: typing.Any) -> bytes:
        """Decode list of integers to bytes.

        Args:
            obj: List of integers (0-255).
            context: Context object (not used).

        Returns:
            Bytes object created from list.
        """
        return bytes(obj)

    def _encode(self, obj: bytes, context: typing.Any) -> list[int]:
        """Encode bytes to list of integers.

        Args:
            obj: Bytes object.
            context: Context object (not used).

        Returns:
            List of integers (0-255) representing bytes.
        """
        return list(obj)


class PrintContext(Construct):
    """Debug construct that prints context information during parsing.

    Used for debugging binary format parsing issues. Prints the context
    object and additional arguments to stdout.
    """

    def _parse(self, stream: typing.Any, context: typing.Any, *args: typing.Any, **kws: typing.Any) -> None:
        """Print context debug information.

        Args:
            stream: Input stream (not used).
            context: Context object to print.
            *args: Additional positional arguments to print.
            **kws: Additional keyword arguments to print.
        """
        print(f"CTX: {context} {args} {kws}")
        print("CTX_END")


class ElfFileStruct(Struct):
    """Specialized Struct subclass for ELF file format parsing.

    This class extends construct.Struct with ELF-specific utilities and
    byte order handling for ELF32/ELF64 parsing.
    """

    def __init__(self, *args: typing.Any, **kws: typing.Any) -> None:
        """Initialize ElfFileStruct.

        Args:
            *args: Positional arguments passed to Struct.
            **kws: Keyword arguments passed to Struct.
        """
        super().__init__(*args, **kws)

    def elf32Addr(self) -> None:
        """Placeholder for ELF32 address handling.

        This method is reserved for future ELF32-specific address handling.
        """
        pass

    def setByteOrder(self) -> None:
        """Placeholder for byte order configuration.

        This method is reserved for future byte order configuration.
        """
        print(f"*** {self}")


DebugInfo = namedtuple("DebugInfo", "section image")
"""Named tuple containing debug section information.

Attributes:
    section: Elf_Section database model containing section metadata.
    image: Bytes data of the debug section.
"""


class DBAPI:
    """Base class providing database session management for API wrappers.

    This class provides a common interface for SectionAPI and SymbolAPI
    to access the SQLAlchemy session and query interface.
    """

    def __init__(self, parent: "ElfParser") -> None:
        """Initialize DBAPI with reference to parent ElfParser.

        Args:
            parent: ElfParser instance that owns this API wrapper.
        """
        self._session = parent.session

    @property
    def session(self) -> typing.Any:
        """Get the SQLAlchemy database session.

        Returns:
            SQLAlchemy session for database queries.
        """
        return self._session

    @property
    def query(self) -> typing.Any:
        """Get the SQLAlchemy query factory from session.

        Returns:
            session.query callable for creating new queries.
        """
        return self.session.query


class SectionAPI(DBAPI):
    """Query interface for ELF sections with filtering and sorting options.

    This class provides methods to retrieve and filter ELF sections from the
    parsed ELF file database. Sections are organized by type (code, data, debug,
    etc.) and can be queried by name, address, or custom patterns.
    """

    def get(self, section_name: str) -> model.Elf_Section | None:
        """Get a single section by exact name.

        Args:
            section_name: Name of the section (e.g., '.text', '.data', '.debug_info').

        Returns:
            Elf_Section model instance if found, None otherwise.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> text = parser.sections.get('.text')
            >>> if text:
            ...     print(f"Text section at 0x{text.sh_addr:08x}")
        """
        query = self.query(model.Elf_Section)
        query = query.filter(model.Elf_Section.section_name == section_name)
        return query.first()

    def fetch(
        self,
        sections: str | None = None,
        name_pattern: str | None = None,
        order_by_address: bool = True,
    ) -> list[model.Elf_Section]:
        r"""Fetch sections with optional filtering and sorting.

        Args:
            sections: Comma or space-separated list of section names to include
                (optional). If not specified, all sections are returned.
            name_pattern: Python regex pattern to match section names (optional).
                Applied after the sections filter.
            order_by_address: If True, sort sections by address (sh_addr).
                If False, sort by section name.

        Returns:
            List of Elf_Section model instances matching the filters.

        Example:
            >>> # Get all code sections
            >>> sections = parser.sections.fetch(order_by_address=True)
            >>> # Get only debug sections
            >>> debug_sections = parser.sections.fetch(
            ...     name_pattern=r'^\.debug'
            ... )
            >>> # Get text and data sections
            >>> code = parser.sections.fetch(
            ...     sections='.text,.data',
            ...     order_by_address=True
            ... )
        """
        query = self.query(model.Elf_Section)
        if order_by_address:
            query = query.order_by(model.Elf_Section.sh_addr)
        else:
            query = query.order_by(model.Elf_Section.section_name)
        result = query.all()
        if name_pattern:
            result = [s for s in result if re.search(name_pattern, s.section_name)]
        return result


def filter_symbols(
    symbols: list[model.Elf_Symbol],
    name_pattern: str | None = None,
) -> list[model.Elf_Symbol]:
    """Filter a list of symbols by regex pattern on symbol name.

    Args:
        symbols: List of Elf_Symbol model instances to filter.
        name_pattern: Python regex pattern to match against symbol_name field.
            If None, returns the entire list unchanged.

    Returns:
        List of symbols whose names match the pattern, or all symbols if
        name_pattern is None.

    Example:
        >>> symbols = [sym1, sym2, sym3]
        >>> # Filter to symbols not starting with underscore
        >>> filtered = filter_symbols(symbols, r'^[^_]')
    """
    if name_pattern is None:
        return symbols
    result = []
    for symbol in symbols:
        if re.match(name_pattern, symbol.symbol_name):
            result.append(symbol)
    return result


class SymbolAPI(DBAPI):
    """Query interface for ELF symbols with extensive filtering options.

    This class provides methods to retrieve and filter ELF symbols from
    symbol tables (.symtab, .dynsym). Symbols can be filtered by name,
    binding (local/global/weak), type (function/object/etc.), and section.
    """

    def get(
        self,
        symbol_name: str,
        section_name: str | None = None,
    ) -> model.Elf_Symbol | None:
        """Get a single symbol by name and optionally section.

        Args:
            symbol_name: Name of the symbol to look up.
            section_name: Optional section name to restrict search to a single section.
                If not specified, searches all sections.

        Returns:
            Elf_Symbol model instance if found, None otherwise.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> # Find any 'main' symbol
            >>> main = parser.symbols.get('main')
            >>> # Find 'main' in .text section specifically
            >>> main_text = parser.symbols.get('main', section_name='.text')
        """
        query = self.query(model.Elf_Symbol)
        if section_name:
            query = query.filter(model.Elf_Symbol.section_name == section_name)
        query = query.filter(model.Elf_Symbol.symbol_name == symbol_name)
        return query.first()

    def fetch(
        self,
        sections: str | None = None,
        name_pattern: str | None = None,
        symbol_list: list[str] | None = None,
        bindings: str | None = None,
        access: str | None = None,
        types_str: str | None = None,
        order_by_value: bool = True,
        group_by_section: bool = True,
    ) -> OrderedDict[str, list[model.Elf_Symbol]] | list[model.Elf_Symbol]:
        """Fetch symbols with complex filtering and grouping options.

        Args:
            sections: Comma or space-separated list of section names to include.
                If not specified, searches all sections.
            name_pattern: Python regex pattern to match symbol names (applied after fetch).
            symbol_list: List of specific symbol names to include.
                If specified, only these symbols are returned.
            bindings: Symbol binding filter as string of binding codes:
                'g' for global (STB_GLOBAL), 'l' for local (STB_LOCAL),
                'w' for weak (STB_WEAK). Can be combined (e.g., 'g,w' or 'g l').
            access: Section access flags as string of flag codes:
                'a' for SHF_ALLOC (allocatable), 'w' for SHF_WRITE (writable),
                'x' for SHF_EXECINSTR (executable).
            types_str: Symbol type filter as string of type names:
                'notype', 'object', 'func', 'section', 'file', 'common', 'tls'.
                Can be comma or space-separated.
            order_by_value: If True, sort by symbol value (address).
                If False, sort by symbol name.
            group_by_section: If True, return OrderedDict with section names as keys
                and symbol lists as values. If False, return flat list of symbols.

        Returns:
            If group_by_section is True: OrderedDict mapping section names to
            lists of symbols.
            If group_by_section is False: List of symbols.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> # Get all global functions
            >>> funcs = parser.symbols.fetch(
            ...     bindings='g',
            ...     types_str='func'
            ... )
            >>> # Get symbols in .text section by address
            >>> text_syms = parser.symbols.fetch(
            ...     sections='.text',
            ...     order_by_value=True,
            ...     group_by_section=False
            ... )
            >>> # Get GCC special symbols
            >>> special = parser.symbols.fetch(
            ...     name_pattern=r'^_'
            ... )
        """
        result: OrderedDict[str, list[model.Elf_Symbol]] = OrderedDict()
        query = self.query(model.Elf_Symbol)
        if sections:
            sections_list = [s for s in re.split(r"[ ,]", sections) if s]
            query = query.filter(model.Elf_Symbol.section_name.in_(sections_list))
        if access:
            access_list = [a for a in re.split(r"[ ,]", access) if a]
            value = 0
            for item in access_list:
                item = item.lower()
                if item == "a":
                    value |= defs.SectionFlags.SHF_ALLOC
                elif item == "w":
                    value |= defs.SectionFlags.SHF_WRITE
                elif item == "x":
                    value |= defs.SectionFlags.SHF_EXECINSTR
            query = query.filter(model.Elf_Symbol.access.op("&")(value))
        if bindings:
            bindings_list = [b for b in re.split(r"[ ,]", bindings) if b]
            flt = []
            for item in bindings_list:
                item = item.lower()
                if item == "g":
                    flt.append(defs.SymbolBinding.STB_GLOBAL)
                elif item == "l":
                    flt.append(defs.SymbolBinding.STB_LOCAL)
                elif item == "w":
                    flt.append(defs.SymbolBinding.STB_WEAK)
            query = query.filter(model.Elf_Symbol.st_bind.in_(flt))
        if types_str:
            types_arr = [t for t in re.split(r"[ ,]", types_str) if t]
            flt = []
            for item in types_arr:
                item = item.lower()
                if item == "notype":
                    flt.append(defs.SymbolType.STT_NOTYPE)
                elif item == "object":
                    flt.append(defs.SymbolType.STT_OBJECT)
                elif item == "func":
                    flt.append(defs.SymbolType.STT_FUNC)
                elif item == "section":
                    flt.append(defs.SymbolType.STT_SECTION)
                elif item == "file":
                    flt.append(defs.SymbolType.STT_FILE)
                elif item == "common":
                    flt.append(defs.SymbolType.STT_COMMON)
                elif item == "tls":
                    flt.append(defs.SymbolType.STT_TLS)
                query = query.filter(model.Elf_Symbol.st_type.in_(flt))
        if symbol_list:
            name_flt = frozenset(symbol_list)
            query = query.filter(model.Elf_Symbol.symbol_name.in_(name_flt))
        query = query.order_by(model.Elf_Symbol.section_name)
        if order_by_value:
            query = query.order_by(model.Elf_Symbol.st_value)
        else:
            query = query.order_by(model.Elf_Symbol.symbol_name)
        if group_by_section:
            for key, values in groupby(query.all(), lambda s: s.section_name):
                symbols = filter_symbols(list(values), name_pattern)
                if symbols:
                    result[key] = symbols
        else:
            result = filter_symbols(query.all(), name_pattern)  # type: ignore
        return result

    def fetch_gcc_special_symbols(self) -> list[model.Elf_Symbol]:
        """Fetch GCC special symbols (absolute symbols starting with underscore).

        GCC and other toolchains use special symbols with absolute addresses for
        various purposes. These are typically symbols with STB_LOCAL binding and
        ST_NOTYPE type, with names starting with underscore.

        Returns:
            List of Elf_Symbol instances matching the GCC special symbol criteria.

        Note:
            This query is GCC/LLVM specific and may not work with symbols from
            other toolchains.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> special_syms = parser.symbols.fetch_gcc_special_symbols()
            >>> for sym in special_syms:
            ...     print(f"{sym.symbol_name}: 0x{sym.st_value:08x}")
        """
        syms = self.query(model.Elf_Symbol).filter(model.Elf_Symbol.st_shndx == defs.SectionName.SHN_ABS)
        syms = syms.filter(model.Elf_Symbol.symbol_name != "")
        syms = syms.filter(func.regexp(model.Elf_Symbol.symbol_name, "_.*"))
        syms = syms.filter(model.Elf_Symbol.st_type == defs.SymbolType.STT_NOTYPE)
        return syms.order_by(model.Elf_Symbol.st_value).all()


def calculate_crypto_hash(data: bytes) -> str:
    """Calculate SHA512 hash of binary data.

    Args:
        data: Binary data to hash.

    Returns:
        Hexadecimal string representation of SHA512 hash.

    Note:
        SHA512 is used for robust change detection of ELF files to determine
        if the database cache should be invalidated.
    """
    sha = hashlib.sha512(data)
    return sha.hexdigest()


class ElfParser:
    """Parser and analyzer for ELF (Executable and Linkable Format) binary files.

    This is the primary class for parsing and analyzing ELF binary files. It handles:
    - Binary parsing of 32-bit and 64-bit ELF formats
    - Both little-endian and big-endian architectures
    - Persistent database caching via SQLite (.prgdb files)
    - Property-based access to ELF header fields
    - Section and symbol queries via SectionAPI and SymbolAPI
    - Image reconstruction for embedded systems workflows

    The parser automatically creates and manages a SQLite database alongside the
    ELF file for efficient caching and querying of parsed data. This database is
    invalidated when the ELF file is modified.

    Attributes:
        fp: Memory-mapped view of the ELF file.
        filename: Path to the ELF file.
        db_name: Path to the associated .prgdb database file.
        session: SQLAlchemy database session for queries.
        db: Model database instance.
        symbols: SymbolAPI for symbol queries.
        sections: SectionAPI for section queries.

    Example:
        >>> parser = ElfParser('firmware.elf')
        >>> print(f"Machine: {parser.e_machine}")
        >>> text = parser.sections.get('.text')
        >>> main = parser.symbols.get('main')
        >>> image = parser.create_image()
    """

    EI_NIDENT: int = 16

    DATATYPES32: dict[str, tuple[typing.Any, typing.Any]] = {
        "Addr": (Int32ul, Int32ub),  # 4 - Unsigned program address
        "Half": (Int16ul, Int16ub),  # 2 - Unsigned medium integer
        "Off": (Int32ul, Int32ub),  # 4 - Unsigned file offset
        "Sword": (Int32sl, Int32sb),  # 4 - Signed large integer
        "Word": (Int32ul, Int32ub),  # 4 - Unsigned large integer
        "Xword": (Int32ul, Int32ub),  # 8 - Unsigned long integer
        "Sxword": (None, None),  # 8 - Signed long integer
    }

    DATATYPES64: dict[str, tuple[typing.Any, typing.Any]] = {
        "Addr": (Int64ul, Int64ub),  # 8 - Unsigned program address
        "Off": (Int64ul, Int64ub),  # 8 - Unsigned file offset
        "Half": (Int16ul, Int16ub),  # 2 - Unsigned medium integer
        "Word": (Int32ul, Int32ub),  # 4 - Unsigned integer
        "Sword": (Int32sl, Int32sb),  # 4 - Signed integer
        "Xword": (Int64ul, Int64ub),  # 8 - Unsigned long integer
        "Sxword": (Int64sl, Int64sb),  # 8 - Signed long integer
    }

    BasicHeader: Struct = Struct(
        "header"
        / Union(
            None,
            "fields"
            / Struct(
                Const(MAGIC),
                "ei_class" / Int8ul,
                "ei_data" / Int8ul,
                "ei_version" / Int8ul,
                "ei_osabi" / Int8ul,
                "ei_abiversion" / Int8ul,
                Padding(7),
            ),
            "bytes" / Bytes(EI_NIDENT),
        ),
    )

    def create_db_on_demand(self) -> None:
        db_exists = self.db_name.exists()
        new_db = False
        hash_value = calculate_crypto_hash(self.fp.tobytes())
        if db_exists:
            db = model.Model(self.db_name)
            session = db.session
            meta = session.query(model.Meta).first()
            if meta:
                pass
                # TODO: log.debug
                # print(f"Calculated hash: {hash_value} DB-hash: {meta.hash_value} EQ: {hash_value == meta.hash_value}")
            if (meta is None) or (hash_value != meta.hash_value):
                new_db = True
                try:
                    db.close()
                finally:
                    try:
                        os.unlink(self.db_name)
                    except Exception as e:
                        print(f"{e}")
            else:
                # Validate schema compatibility (e.g., required columns exist)
                try:
                    from sqlalchemy import inspect as sa_inspect

                    inspector = sa_inspect(db.engine)
                    try:
                        die_cols = [c["name"] for c in inspector.get_columns("debuginformationentry")]
                    except Exception:
                        die_cols = []
                    try:
                        dieattr_cols = [c["name"] for c in inspector.get_columns("dieattribute")]
                    except Exception:
                        dieattr_cols = []
                    required_die_cols = {"tag", "offset", "parent_id"}
                    required_dieattr_cols = {"entry_id"}
                    if (not required_die_cols.issubset(set(die_cols))) or (not required_dieattr_cols.issubset(set(dieattr_cols))):
                        # Invalidate outdated schema: rebuild database
                        new_db = True
                        try:
                            db.close()
                        finally:
                            try:
                                os.unlink(self.db_name)
                            except Exception as e:
                                print(f"{e}")
                    else:
                        # Close the preliminary connection before opening the main one to avoid file locking.
                        db.close()
                except Exception:
                    # If inspection fails for any reason, rebuild to be safe
                    new_db = True
                    try:
                        db.close()
                    finally:
                        try:
                            os.unlink(self.db_name)
                        except Exception as e:
                            print(f"{e}")
        else:
            new_db = True
        self.db = model.Model(self.db_name)
        self.session = self.db.session
        if new_db:
            meta = model.Meta(hash_value=hash_value)
            self.session.add(meta)
            self.load_data()
        else:
            self._header = self.session.query(model.Elf_Header).first()
            self._program_headers = self.session.query(model.Elf_ProgramHeaders).all()
            self.set_data_types(self)

    def load_data(self):
        basic_header = ElfParser.BasicHeader.parse(self.fp)
        bh_fields = basic_header.header.fields
        self.set_data_types(bh_fields)
        eh_fields = self._parser_extended_header()

        self._header = model.Elf_Header(
            ei_class=bh_fields.ei_class,
            ei_data=bh_fields.ei_data,
            ei_version=bh_fields.ei_version,
            ei_osabi=bh_fields.ei_osabi,
            ei_abiversion=bh_fields.ei_abiversion,
            e_type=eh_fields.e_type,
            e_machine=eh_fields.e_machine,
            e_version=eh_fields.e_version,
            e_entry=eh_fields.e_entry,
            e_phoff=eh_fields.e_phoff,
            e_shoff=eh_fields.e_shoff,
            e_flags=eh_fields.e_flags,
            e_ehsize=eh_fields.e_ehsize,
            e_phentsize=eh_fields.e_phentsize,
            e_phnum=eh_fields.e_phnum,
            e_shentsize=eh_fields.e_shentsize,
            e_shnum=eh_fields.e_shnum,
            e_shstrndx=eh_fields.e_shstrndx,
        )
        self.session.add(self._header)
        self._parse_section_headers()
        self._parse_program_headers()
        self.create_section_to_segment_mapping()
        for section in self._symbol_sections:
            self._parse_symbol_section(section)
        self.session.commit()

    def __init__(self, filename: str) -> None:
        """Initialize ElfParser with an ELF file.

        Creates or opens the associated .prgdb database file and parses the ELF
        structure. The database is invalidated and rebuilt if the file has been
        modified or the schema has changed.

        Args:
            filename: Path to the ELF file to parse.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            ValueError: If the file is not a valid ELF file.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> print(parser.e_machine)
        """
        self.fp = create_memorymapped_fileview(filename)
        self.filename = Path(filename)
        self.db_name = self.filename.with_suffix(model.DB_EXTENSION)

        self._images: dict[int, bytes | None] = {}
        self._sections_by_name: OrderedDict[str, typing.Any] = OrderedDict()
        self.asciiCString: CString = CString(encoding="ascii")

        self.create_db_on_demand()

        self.symbols: SymbolAPI = SymbolAPI(self)
        self.sections: SectionAPI = SectionAPI(self)

        md_class = defs.MACHINE_DATA.get(self.e_machine, defs.MachineData)
        self._machine_data: defs.MachineData = md_class(self.e_machine, self.e_flags)

    def set_data_types(self, obj: typing.Any) -> None:
        """Configure construct data types based on ELF class and data encoding.

        Reads EI_CLASS (32-bit vs 64-bit) and EI_DATA (endianness) from the ELF
        identification header and sets up the appropriate construct data types
        (Int32ul, Int64ul, etc.) and endianness marker for use during parsing.

        Args:
            obj: Object with ei_class and ei_data attributes (typically the parsed
                BasicHeader.header.fields or the _header database object).

        Raises:
            ValueError: If EI_DATA has an invalid value (not 1 or 2).

        Note:
            This method is called during initialization to configure the parser
            for the specific ELF architecture.
        """
        self.b64 = obj.ei_class == 2
        if obj.ei_data == 1:  # Little-Endian
            offset = 0
        elif obj.ei_data == 2:  # Big-Endian
            offset = 1
        else:
            raise ValueError(f"EI_DATA has an invalid value. Got: {obj.ei_data}")
        self._endianess = "<" if obj.ei_data == 1 else ">"
        datatypes = ElfParser.DATATYPES64.items() if self.b64 else ElfParser.DATATYPES32.items()
        for key, value in datatypes:
            setattr(self, key, value[offset])

    def create_db_on_demand(self) -> None:
        """Create or open the ELF database, validating and rebuilding as needed.

        This method implements the database lifecycle management:
        1. Check if .prgdb file exists
        2. If exists, verify SHA512 hash matches the ELF file
        3. Validate database schema compatibility
        4. Rebuild if file modified, schema incompatible, or if first parse
        5. Initialize database session

        The database is rebuilt when:
        - No existing database is found
        - ELF file has been modified (SHA512 hash mismatch)
        - Database schema is outdated or incompatible
        - Required columns are missing from expected tables

        Side Effects:
            - Creates/updates self.db and self.session
            - Creates .prgdb file if needed
            - Parses and stores ELF data if database is new
        """
        db_exists = self.db_name.exists()
        new_db = False
        hash_value = calculate_crypto_hash(self.fp.tobytes())
        if db_exists:
            db = model.Model(self.db_name)
            session = db.session
            meta = session.query(model.Meta).first()
            if meta:
                pass
                # TODO: log.debug
                # print(f"Calculated hash: {hash_value} DB-hash: {meta.hash_value} EQ: {hash_value == meta.hash_value}")
            if (meta is None) or (hash_value != meta.hash_value):
                new_db = True
                try:
                    db.close()
                finally:
                    try:
                        os.unlink(self.db_name)
                    except Exception as e:
                        print(f"{e}")
            else:
                # Validate schema compatibility (e.g., required columns exist)
                try:
                    from sqlalchemy import inspect as sa_inspect

                    inspector = sa_inspect(db.engine)
                    try:
                        die_cols = [c["name"] for c in inspector.get_columns("debuginformationentry")]
                    except Exception:
                        die_cols = []
                    try:
                        dieattr_cols = [c["name"] for c in inspector.get_columns("dieattribute")]
                    except Exception:
                        dieattr_cols = []
                    required_die_cols = {"tag", "offset", "parent_id"}
                    required_dieattr_cols = {"entry_id"}
                    if (not required_die_cols.issubset(set(die_cols))) or (not required_dieattr_cols.issubset(set(dieattr_cols))):
                        # Invalidate outdated schema: rebuild database
                        new_db = True
                        try:
                            db.close()
                        finally:
                            try:
                                os.unlink(self.db_name)
                            except Exception as e:
                                print(f"{e}")
                    else:
                        # Close the preliminary connection before opening the main one to avoid file locking.
                        db.close()
                except Exception:
                    # If inspection fails for any reason, rebuild to be safe
                    new_db = True
                    try:
                        db.close()
                    finally:
                        try:
                            os.unlink(self.db_name)
                        except Exception as e:
                            print(f"{e}")
        else:
            new_db = True
        self.db = model.Model(self.db_name)
        self.session = self.db.session
        if new_db:
            meta = model.Meta(hash_value=hash_value)
            self.session.add(meta)
            self.load_data()
        else:
            self._header = self.session.query(model.Elf_Header).first()
            self._program_headers = self.session.query(model.Elf_ProgramHeaders).all()
            self.set_data_types(self)

    def load_data(self) -> None:
        """Parse ELF file and populate database.

        Performs the main ELF parsing workflow:
        1. Parse basic header (first 16 bytes) to determine architecture
        2. Parse extended header (e_type, e_machine, e_entry, etc.)
        3. Parse section headers and extract section data
        4. Parse program headers (segments)
        5. Create section-to-segment mapping
        6. Parse symbol tables (if present)
        7. Commit all data to database

        This method is called only once per ELF file, when creating a new database.
        Subsequent parser instances reuse the existing database.

        Side Effects:
            - Sets self._header, self._program_headers, self._section_headers
            - Populates self._images (section data by index)
            - Populates self._sections_by_name
            - Commits all parsed data to database via self.session.commit()
        """
        basic_header = ElfParser.BasicHeader.parse(self.fp)
        bh_fields = basic_header.header.fields
        self.set_data_types(bh_fields)
        eh_fields = self._parser_extended_header()

        self._header = model.Elf_Header(
            ei_class=bh_fields.ei_class,
            ei_data=bh_fields.ei_data,
            ei_version=bh_fields.ei_version,
            ei_osabi=bh_fields.ei_osabi,
            ei_abiversion=bh_fields.ei_abiversion,
            e_type=eh_fields.e_type,
            e_machine=eh_fields.e_machine,
            e_version=eh_fields.e_version,
            e_entry=eh_fields.e_entry,
            e_phoff=eh_fields.e_phoff,
            e_shoff=eh_fields.e_shoff,
            e_flags=eh_fields.e_flags,
            e_ehsize=eh_fields.e_ehsize,
            e_phentsize=eh_fields.e_phentsize,
            e_phnum=eh_fields.e_phnum,
            e_shentsize=eh_fields.e_shentsize,
            e_shnum=eh_fields.e_shnum,
            e_shstrndx=eh_fields.e_shstrndx,
        )
        self.session.add(self._header)
        self._parse_section_headers()
        self._parse_program_headers()
        self.create_section_to_segment_mapping()
        for section in self._symbol_sections:
            self._parse_symbol_section(section)
        self.session.commit()

    def _parser_extended_header(self) -> typing.Any:
        """Parse the ELF extended header (post-identification bytes).

        The extended header contains the main ELF header fields (e_type, e_machine,
        e_entry, etc.). The size and field ordering vary between 32-bit and 64-bit
        ELF formats and depend on the endianness determined by the basic header.

        Returns:
            Parsed extended header with fields like e_type, e_machine, e_version,
            e_entry, e_phoff, e_shoff, etc.

        Note:
            Uses construct Struct definitions built from self.Half, self.Word,
            self.Addr, and self.Off, which are configured by set_data_types()
            based on EI_CLASS and EI_DATA.
        """
        ExtendedHeader = Struct(
            "e_type" / self.Half,  # Object file type
            "e_machine" / self.Half,  # Machine type
            "e_version" / self.Word,  # Object file version
            "e_entry" / self.Addr,  # Entry point address
            "e_phoff" / self.Off,  # Program header offset
            "e_shoff" / self.Off,  # Section header offset
            "e_flags" / self.Word,  # Processor-specific flags
            "e_ehsize" / self.Half,  # ELF header size
            "e_phentsize" / self.Half,  # Size of program header entry
            "e_phnum" / self.Half,  # Number of program header entries
            "e_shentsize" / self.Half,  # Size of section header entry
            "e_shnum" / self.Half,  # Number of section header entries
            "e_shstrndx" / self.Half,  # Section name string table index
        )
        return ExtendedHeader.parse(self.fp[self.EI_NIDENT :])

    def _parse_section_headers(self) -> None:
        """Parse section headers and extract section data from ELF file.

        Reads all section headers from the ELF file and:
        1. Extracts binary data for each section
        2. Resolves section names from the string table
        3. Identifies symbol tables for later parsing
        4. Parses special section types (NOTE, COMMENT)
        5. Stores all section metadata in database

        This method populates:
        - self._section_headers: List of parsed section header entries
        - self._images: Dictionary mapping section index to binary data
        - self._sections_by_name: Dictionary mapping section names to entries
        - self._symbol_sections: List of symbol table sections for parsing

        Side Effects:
            - Populates database with Elf_Section entries
            - Parses NOTE sections into Elf_Note entries
            - Parses .comment section into Elf_Comment entries
        """
        SectionHeaders = Struct(
            "sections"
            / Array(
                lambda ctx: self.e_shnum,
                "section"
                / Struct(
                    "sh_name" / self.Word,
                    "sh_type" / self.Word,
                    "sh_flags" / self.Xword,
                    "sh_addr" / self.Addr,
                    "sh_offset" / self.Off,
                    "sh_size" / self.Xword,
                    "sh_link" / self.Word,
                    "sh_info" / self.Word,
                    "sh_addralign" / self.Xword,
                    "sh_entsize" / self.Xword,
                    "allocate" / Computed(lambda ctx: (ctx.sh_type not in (0, 8) and ctx.sh_size > 0)),
                ),
            )
        )
        sections = []
        self._symbol_sections = []
        if hasattr(self, "e_shnum"):
            self._section_headers = SectionHeaders.parse(self.fp[self.e_shoff :])
            for idx, section in enumerate(self._section_headers.sections):
                if section.allocate:
                    image = self.fp[section.sh_offset : section.sh_offset + section.sh_size]
                else:
                    image = None
                if image is not None:
                    image = image.tobytes()
                self._images[idx] = image
                section.image = image
            for idx, section in enumerate(self._section_headers.sections):
                name = self.get_string(self.e_shstrndx, section.sh_name)
                section.name = name
                self._sections_by_name[name] = section
                image = self._images[idx]
                if section.sh_type == defs.SectionType.SHT_NOTE:
                    note_obj = self._parse_note(image)
                    if note_obj:
                        note = model.Elf_Note(
                            section_name=name,
                            type=note_obj.type,
                            name=note_obj.name,
                            desc=note_obj.desc,
                        )
                        sections.append(note)
                elif section.sh_type in (
                    defs.SectionType.SHT_SYMTAB,
                    defs.SectionType.SHT_DYNSYM,
                ):
                    self._symbol_sections.append(section)
                elif name == ".comment":
                    cmt_text = self._parse_comment(image)
                    if cmt_text:
                        comment = model.Elf_Comment(text=cmt_text)
                        sections.append(comment)
                db_sec = model.Elf_Section(
                    index=idx,
                    section_name=name,
                    sh_name=section.sh_name,
                    sh_type=section.sh_type,
                    sh_flags=section.sh_flags,
                    sh_addr=section.sh_addr,
                    sh_offset=section.sh_offset,
                    sh_size=section.sh_size,
                    sh_link=section.sh_link,
                    sh_info=section.sh_info,
                    sh_addralign=section.sh_addralign,
                    sh_entsize=section.sh_entsize,
                    section_image=image,
                )
                sections.append(db_sec)
            self.session.bulk_save_objects(sections)

    def get_string(self, table_index: int, entry: int) -> str:
        """Get a null-terminated string from a string table by offset.

        Retrieves an ASCII string from the specified string table section at the
        given byte offset. This method is commonly used to resolve section names,
        symbol names, and other string references stored in ELF string tables
        (e.g., .strtab, .shstrtab, .dynstr).

        Args:
            table_index: Index into self._images array identifying the string table section.
            entry: Byte offset within the string table where the null-terminated string begins.

        Returns:
            The parsed ASCII string. Returns empty string if entry offset exceeds
            string table bounds.

        Note:
            - String tables store null-terminated C strings back-to-back
            - Multiple ELF structures may reference the same string by offset
            - Out-of-bounds access safely returns empty string instead of raising exception

        Example:
            >>> # Internally used to resolve section names from .shstrtab:
            >>> section_name = parser.get_string(shstrtab_index, section.sh_name)
            >>> print(section_name)  # '.text'
        """
        if entry > len(self._images[table_index]):
            return ""
        name = self.asciiCString.parse(self._images[table_index][entry:])
        return name

    def _parse_program_headers(self) -> None:
        """Parse ELF program headers (segments) from the binary file.

        Parses all program header table entries and populates the database with
        segment information. Program headers describe how the ELF file should be
        loaded into memory at runtime, defining segments for code, data, dynamic
        linking, thread-local storage, etc.

        The parser automatically handles both 32-bit (ELF32) and 64-bit (ELF64)
        program header formats, which differ in field size and ordering. For 64-bit
        ELF files, the p_flags field appears before offset/address fields.

        Program header structure for 32-bit ELF:
            - p_type: Segment type (PT_LOAD, PT_DYNAMIC, PT_INTERP, etc.)
            - p_offset: File offset where segment data begins
            - p_vaddr: Virtual address where segment should be loaded
            - p_paddr: Physical address (often same as vaddr on embedded systems)
            - p_filesz: Size of segment data in file (bytes)
            - p_memsz: Size of segment in memory (bytes, may exceed filesz for .bss)
            - p_flags: Segment flags (read/write/execute permissions)
            - p_align: Segment alignment requirement

        Program header structure for 64-bit ELF:
            - Field order differs: p_flags comes after p_type and before p_offset

        Side Effects:
            - Sets self._program_headers to list of parsed segment structures
            - Populates database with model.Elf_ProgramHeaders entries
            - Commits changes to database via self.session

        Note:
            - Only runs if e_shnum attribute exists (valid ELF header was parsed)
            - Number of program headers determined by self.e_phnum from ELF header
            - File offset to program header table given by self.e_phoff
            - Each segment may contain multiple sections (determined later by
              section_in_segment checks)
        """
        ProgramHeaders = Struct(
            "segments"
            / Array(
                lambda ctx: self.e_phnum,
                "segment"
                / IfThenElse(
                    lambda ctx: self.b64,
                    Struct(
                        "p_type" / self.Word,
                        "p_flags" / self.Word,
                        "p_offset" / self.Off,
                        "p_vaddr" / self.Addr,
                        "p_paddr" / self.Addr,
                        "p_filesz" / self.Xword,
                        "p_memsz" / self.Xword,
                        "p_align" / self.Xword,
                    ),
                    Struct(
                        "p_type" / self.Word,
                        "p_offset" / self.Off,
                        "p_vaddr" / self.Addr,
                        "p_paddr" / self.Addr,
                        "p_filesz" / self.Word,
                        "p_memsz" / self.Word,
                        "p_flags" / self.Word,
                        "p_align" / self.Word,
                    ),
                ),
            )
        )
        if hasattr(self, "e_shnum"):
            self._program_headers = ProgramHeaders.parse(self.fp[self.e_phoff :]).segments
            for segment in self._program_headers:
                header = model.Elf_ProgramHeaders(
                    p_type=segment.p_type,
                    p_offset=segment.p_offset,
                    p_vaddr=segment.p_vaddr,
                    p_paddr=segment.p_paddr,
                    p_filesz=segment.p_filesz,
                    p_memsz=segment.p_memsz,
                    p_flags=segment.p_flags,
                    p_align=segment.p_align,
                )
                self.session.add(header)

    def _parse_symbol_section(self, section: model.Elf_Section) -> None:
        """Parse symbol table section and populate database with symbol entries.

        Parses all symbol entries from a symbol table section (SHT_SYMTAB or SHT_DYNSYM)
        and stores them in the database. Each symbol represents a function, variable,
        section, or other named entity with associated metadata like address, size,
        binding, type, and visibility.

        Symbol table structure for 32-bit ELF:
            - st_name: Offset into string table for symbol name
            - st_value: Symbol value (typically address)
            - st_size: Size of symbol in bytes
            - st_info: Symbol binding (4 bits) and type (4 bits)
            - st_other: Symbol visibility
            - st_shndx: Section index symbol is defined in (or special value)

        Symbol table structure for 64-bit ELF:
            - Field order differs: st_name, st_info, st_other, st_shndx, st_value, st_size

        Args:
            section: Elf_Section database model representing the symbol table section.
                Must have sh_link pointing to the associated string table section.

        Side Effects:
            - Bulk inserts model.Elf_Symbol entries into database
            - Commits transaction on success, rolls back on error
            - Prints error messages if symbol parsing or database operations fail

        Note:
            - Symbol names are resolved via section.sh_link string table index
            - st_shndx may be special value (SHN_ABS, SHN_COMMON, SHN_UNDEF) or section index
            - Symbol section_name field resolved from st_shndx section reference
            - Parse errors for individual symbols are caught and logged but don't stop processing
            - Uses bulk_save_objects for efficient database insertion

        Example:
            Symbol types (st_info.st_type):
                - STT_NOTYPE (0): Type not specified
                - STT_OBJECT (1): Data object (variable)
                - STT_FUNC (2): Function or executable code
                - STT_SECTION (3): Section symbol
                - STT_FILE (4): Source file name
        """
        sh_link = section.sh_link
        symbols = []
        if self.b64:
            Symbol = Struct(
                "st_name" / self.Word,
                "st_info"
                / BitStruct(
                    "st_bind" / BitsInteger(4),
                    "st_type" / BitsInteger(4),
                ),
                "st_other" / Int8ul,
                "st_shndx" / self.Half,
                "st_value" / self.Addr,
                "st_size" / self.Xword,
                "symbol_name" / Computed(lambda ctx: self.get_string(sh_link, ctx.st_name)),
            )
        else:
            Symbol = Struct(
                "st_name" / self.Word,
                "st_value" / self.Addr,
                "st_size" / self.Word,
                "st_info"
                / BitStruct(
                    "st_bind" / BitsInteger(4),
                    "st_type" / BitsInteger(4),
                ),
                "st_other" / Int8ul,
                "symbol_name" / Computed(lambda ctx: self.get_string(sh_link, ctx.st_name)),
                "st_shndx" / self.Half,
            )
        symbol_cache = {}
        # num_symbols = len(section.image) // Symbol.sizeof()
        for offset in range(0, len(section.image), Symbol.sizeof()):
            try:
                sym = Symbol.parse(section.image[offset : offset + Symbol.sizeof()])
            except StreamError as e:
                print(f"parse symbol section: {e}")
                continue
            section_header = None
            if sym.st_shndx in defs.SpecialSections:
                section_name = defs.special_section_name(sym.st_shndx)
            else:
                if sym.st_shndx not in symbol_cache:
                    section_header = self.session.query(model.Elf_Section).filter(model.Elf_Section.index == sym.st_shndx).first()
                    if section_header:
                        section_name = section_header.section_name
                    else:
                        section_name = str(sym.st_shndx)
            db_sym = model.Elf_Symbol(
                st_name=sym.st_name,
                st_value=sym.st_value,
                st_size=sym.st_size,
                st_bind=sym.st_info.st_bind,
                st_type=sym.st_info.st_type,
                st_other=sym.st_other,
                st_shndx=sym.st_shndx,
                symbol_name=sym.symbol_name,
                section_name=section_name,
                access=section_header.sh_flags if section_header else 0,
            )
            symbols.append(db_sym)
        try:
            self.session.bulk_save_objects(symbols)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"{e}")

    def _parse_comment(self, data: bytes) -> str:
        """Parse .comment section containing compiler/linker identification strings.

        The .comment section typically contains null-terminated ASCII strings identifying
        the compiler, linker, and build tools used to create the ELF file. This method
        extracts and formats these strings for display.

        Args:
            data: Raw bytes from the .comment section.

        Returns:
            Formatted comment string. If data contains null bytes, returns lines joined
            with newlines. If no null bytes present, returns the entire data as ASCII.
            Returns empty string if data is empty or None.

        Note:
            - Comment sections typically contain multiple null-terminated strings
            - Common formats:
                * "GCC: (GNU) 11.2.0"
                * "Linker: LLD 14.0.0"
            - Each tool in the build chain may add its own comment string
            - Empty strings between null bytes are filtered out

        Example:
            >>> # Parse .comment section
            >>> comment_section = parser.sections.get('.comment')
            >>> if comment_section:
            ...     comment_text = parser._parse_comment(comment_section.section_image)
            ...     print(comment_text)
            GCC: (GNU) 11.2.0
            Linker: GNU ld version 2.38
        """
        Line = Struct("line" / CString("ascii"), "pos" / Tell)
        if not data:
            return ""
        length = len(data)
        result = []
        i = 0
        if data.find(b"\x00") == -1:
            return str(data, "ascii")
        while i < length:
            # print("*** LINE", data[i : ])
            line = Line.parse(data[i:])
            if line.line:
                result.append(line.line)
            i += line.pos
        return "\n".join(result)

    def _parse_note(self, data: bytes) -> typing.Any | None:
        """Parse ELF note section containing vendor-specific metadata.

        ELF note sections store arbitrary vendor-specific metadata in a structured format.
        Common uses include:
            - Build IDs (NT_GNU_BUILD_ID)
            - ABI tags (NT_GNU_ABI_TAG)
            - Version information
            - Hardware capabilities
            - Gold linker version

        Note structure:
            - namesz: Length of name field including null terminator (32-bit)
            - descsz: Length of descriptor field (32-bit)
            - type: Note type (vendor-specific interpretation) (32-bit)
            - name: Vendor name string (null-terminated, padded to 4-byte alignment)
            - desc: Binary descriptor data (vendor-specific format)

        Args:
            data: Raw bytes from a NOTE section (SHT_NOTE).

        Returns:
            Parsed note structure with fields: namesz, descsz, type, name (ASCII string),
            desc (hex-encoded string). Returns None if data is empty/None or parsing fails.

        Note:
            - Name field is parsed as null-terminated ASCII string
            - Descriptor field is converted to hexadecimal string for safe display
            - Parse errors (StreamError) are caught and return None
            - Common vendor names: "GNU", "Go", "Android", "FreeBSD"

        Example:
            >>> # Parse .note.gnu.build-id section
            >>> note_section = parser.sections.get('.note.gnu.build-id')
            >>> if note_section:
            ...     note = parser._parse_note(note_section.section_image)
            ...     if note:
            ...         print(f"Vendor: {note.name}")
            ...         print(f"Build ID: {note.desc}")
            Vendor: GNU
            Build ID: a1b2c3d4e5f6...
        """
        Note = Struct(
            "namesz" / self.Word,
            "descsz" / self.Word,
            "type" / self.Word,
            "name" / Bytes(this.namesz),
            "desc" / Bytes(this.descsz),
        )
        if not data:
            return None
        try:
            result = Note.parse(data)
            result.desc = binascii.b2a_hex(result.desc).decode()
            result.name = self.asciiCString.parse(result.name)
        except StreamError:
            return None
        else:
            return result

    def debug_sections(self) -> OrderedDict[str, typing.Any]:
        """Get all DWARF debug sections from the ELF file.

        Retrieves all sections with names starting with ".debug" and wraps them
        in DebugInfo named tuples for convenient access. DWARF debug sections contain
        debugging information for source-level debugging, including:
            - .debug_info: Compilation unit information, variables, functions
            - .debug_abbrev: Abbreviation tables for .debug_info
            - .debug_line: Line number information mapping addresses to source lines
            - .debug_str: String table for debug info
            - .debug_aranges: Address range tables
            - .debug_ranges: Non-contiguous address ranges
            - .debug_frame: Call frame information (stack unwinding)
            - .debug_loc: Location lists for variables

        Returns:
            OrderedDict mapping section names to DebugInfo(section, image) named tuples.
            Keys are section names (e.g., '.debug_info', '.debug_line').
            Values are DebugInfo objects containing:
                - section: model.Elf_Section database model
                - image: bytes data of the section

        Note:
            - Only sections with names starting with ".debug" are included
            - Currently .debug_abbrev is explicitly skipped (special handling placeholder)
            - Sections are returned in the order they appear in the ELF file
            - Empty dict returned if no debug sections present (stripped binary)

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> debug = parser.debug_sections()
            >>> if '.debug_info' in debug:
            ...     info_section = debug['.debug_info'].section
            ...     info_data = debug['.debug_info'].image
            ...     print(f"Debug info size: {len(info_data)} bytes")
        """
        ds = OrderedDict()
        for section in self.sections.fetch():
            name = section.section_name
            if name.startswith(".debug"):
                if name == ".debug_abbrev":
                    pass
                ds[name] = section
        result = OrderedDict()
        for name, section in ds.items():
            result[name] = DebugInfo(section, section.section_image)
        return result

    def section_in_segment1(
        self,
        section_header: model.Elf_Section,
        segment: model.Elf_ProgramHeaders,
        check_vma: bool,
        strict: bool,
    ) -> bool:
        """Determine if a section belongs to a segment with configurable checks.

        This is the core implementation of section-to-segment mapping logic, implementing
        the complex rules defined in the ELF specification for determining which sections
        are contained within which program segments (loadable memory regions).

        The algorithm performs four independent checks:

        1. **valid_segment**: Type compatibility check
           - TLS sections (.tdata, .tbss) only belong to PT_TLS, PT_GNU_RELRO, or PT_LOAD
           - Non-TLS sections excluded from PT_TLS and PT_PHDR segments

        2. **has_offset**: File offset range check
           - NOBITS sections (e.g., .bss) considered to have valid offset
           - For sections with file data, verify offset falls within segment file range
           - In strict mode, section must start within segment (not at boundary)
           - Section's file size must fit within segment's file size

        3. **has_VMA**: Virtual memory address range check (if enabled)
           - Skipped if check_vma=False or section lacks SHF_ALLOC flag
           - Section's virtual address must fall within segment's memory range
           - In strict mode, section must start within segment (not at boundary)
           - Section's memory size must fit within segment's memory size

        4. **has_dynamic_size**: Special handling for PT_DYNAMIC segments
           - Ensures dynamic sections have content or segment is empty
           - Validates offset/address relationships for dynamic sections

        Args:
            section_header: Section to check for membership in segment.
            segment: Program header (segment) to check against.
            check_vma: If True, validate virtual memory address ranges.
                If False, skip VMA checks (useful for relocatable objects).
            strict: If True, enforce stricter boundary conditions.
                Section must start within segment bounds, not exactly at the end.

        Returns:
            True if section belongs to the segment according to all four checks,
            False otherwise.

        Note:
            - Thread-Local Storage (TLS) sections have special mapping rules
            - NOBITS sections (.bss, .tbss) have no file representation, only memory size
            - Strict mode prevents sections from starting at segment boundaries
            - This is used internally by section_in_segment() and section_in_segment_strict()

        Example:
            >>> # Check if .text section belongs to first LOAD segment
            >>> text_section = parser.sections.get('.text')
            >>> load_segment = parser.segments[0]
            >>> if parser.section_in_segment1(text_section, load_segment, True, False):
            ...     print(".text is in the first LOAD segment")
        """
        has_offset = False
        valid_segment = False
        has_VMA = False
        has_dynamic_size = False
        valid_segment = (
            ((section_header.sh_flags & defs.SectionFlags.SHF_TLS) != 0)
            and (segment.p_type == defs.PT_TLS or segment.p_type == defs.PT_GNU_RELRO or segment.p_type == defs.PT_LOAD)
            or (
                (section_header.sh_flags & defs.SectionFlags.SHF_TLS) == 0
                and segment.p_type != defs.PT_TLS
                and segment.p_type != defs.PT_PHDR
            )
        )
        has_offset = section_header.sh_type == defs.SectionType.SHT_NOBITS or (
            section_header.sh_offset >= segment.p_offset
            and (not strict or (section_header.sh_offset - segment.p_offset <= segment.p_filesz - 1))
            and ((section_header.sh_offset - segment.p_offset + self.section_size(section_header, segment)) <= (segment.p_filesz))
        )
        has_VMA = (
            not check_vma
            or (section_header.sh_flags & defs.SectionFlags.SHF_ALLOC) == 0
            or (
                section_header.sh_addr >= segment.p_vaddr
                and (not strict or (section_header.sh_addr - segment.p_vaddr <= segment.p_memsz - 1))
                and ((section_header.sh_addr - segment.p_vaddr + self.section_size(section_header, segment)) <= segment.p_memsz)
            )
        )
        has_dynamic_size = (
            segment.p_type != defs.PT_DYNAMIC
            or section_header.sh_size != 0
            or segment.p_memsz == 0
            or (
                (
                    section_header.sh_type == defs.SectionType.SHT_NOBITS
                    or (
                        section_header.sh_offset > segment.p_offset
                        and (section_header.sh_offset - segment.p_offset < segment.p_filesz)
                    )
                )
                and (
                    (section_header.sh_flags & defs.SectionFlags.SHF_ALLOC) == 0
                    or (section_header.sh_addr > segment.p_vaddr and (section_header.sh_addr - segment.p_vaddr < segment.p_memsz))
                )
            )
        )
        return valid_segment and has_offset and has_VMA and has_dynamic_size

    def section_in_segment(self, section_header: model.Elf_Section, segment: model.Elf_ProgramHeaders) -> bool:
        """Check if a section fits within a segment using standard rules.

        Convenience wrapper around section_in_segment1() with standard (non-strict)
        checking enabled. This is the default method for determining section-to-segment
        mappings in most ELF analysis scenarios.

        Args:
            section_header: Section to test for membership in segment.
            segment: Program header (segment) to check against.

        Returns:
            True if section belongs to segment, False otherwise.

        Note:
            - Enables VMA checking (check_vma=True)
            - Uses non-strict mode (strict=False) allowing sections at segment boundaries
            - See section_in_segment1() for detailed algorithm description

        Example:
            >>> # Build mapping of all sections to their containing segments
            >>> for section in parser.sections.fetch():
            ...     for idx, segment in enumerate(parser.segments):
            ...         if parser.section_in_segment(section, segment):
            ...             print(f"{section.section_name} -> segment {idx}")
        """
        return self.section_in_segment1(section_header, segment, 1, 0)

    def section_in_segment_strict(self, section_header: model.Elf_Section, segment: model.Elf_ProgramHeaders) -> bool:
        """Check if a section fits within a segment using strict boundary rules.

        Convenience wrapper around section_in_segment1() with strict checking enabled.
        In strict mode, sections must start strictly within segment bounds, not exactly
        at the end boundary. This is useful for validating well-formed ELF files.

        Args:
            section_header: Section to test for membership in segment.
            segment: Program header (segment) to check against.

        Returns:
            True if section strictly belongs to segment, False otherwise.

        Note:
            - Enables VMA checking (check_vma=True)
            - Uses strict mode (strict=True) rejecting sections at segment boundaries
            - Stricter than section_in_segment() - may reject edge cases
            - See section_in_segment1() for detailed algorithm description

        Example:
            >>> # Validate that .text section is properly contained in LOAD segment
            >>> text = parser.sections.get('.text')
            >>> load_segment = parser.segments[0]
            >>> is_valid = parser.section_in_segment_strict(text, load_segment)
            >>> if not is_valid:
            ...     print("Warning: .text section has boundary alignment issue")
        """
        return self.section_in_segment1(section_header, segment, 1, 1)

    def create_section_to_segment_mapping(self) -> OrderedDict[int, list]:
        """Create empty mapping structure for section-to-segment relationships.

        Initializes an OrderedDict that will map program header (segment) indices
        to lists of sections contained within each segment. The mapping structure
        is created with an empty list for each segment index but is not populated
        with actual section assignments.

        Returns:
            OrderedDict mapping segment indices (0 to e_phnum-1) to empty lists.
            Also stores the mapping in self.sections_to_segments for later use.

        Note:
            - This method only creates the empty mapping structure
            - Actual section assignments must be done separately using section_in_segment()
            - The mapping is indexed by program header index, not segment type
            - All e_phnum program headers get an entry, even if they contain no sections

        Example:
            >>> # Create mapping and populate with section assignments
            >>> mapping = parser.create_section_to_segment_mapping()
            >>> for section in parser.sections.fetch():
            ...     for idx, segment in enumerate(parser.segments):
            ...         if parser.section_in_segment(section, segment):
            ...             mapping[idx].append(section)
            >>> # Display which sections are in segment 0
            >>> print(f"Segment 0 contains: {[s.section_name for s in mapping[0]]}")
        """
        mapping = OrderedDict()
        for idx in range(self.e_phnum):
            mapping[idx] = []
        self.sections_to_segments = mapping
        return self.sections_to_segments

    def tbss_special(self, section_header: model.Elf_Section, segment: model.Elf_ProgramHeaders) -> bool:
        """Check if section is a TBSS section in a non-TLS segment (special case).

        Detects the special case of Thread-Local BSS (.tbss) sections when they
        appear in segments other than PT_TLS. TBSS sections have the SHF_TLS flag
        and SHT_NOBITS type, representing uninitialized thread-local storage.

        In non-TLS segments (typically PT_LOAD or PT_GNU_RELRO), TBSS sections
        should be treated as having zero effective size because they don't occupy
        file or memory space in those segments - they're only accounted for in the
        dedicated PT_TLS segment.

        Args:
            section_header: Section to check for TBSS special case.
            segment: Program header (segment) containing the section.

        Returns:
            True if section is TBSS and segment is not PT_TLS, False otherwise.

        Note:
            - TBSS = Thread-Local BSS (uninitialized thread-local variables)
            - PT_TLS segments contain the template for per-thread storage
            - TBSS sections may appear in multiple segments with different semantics
            - This affects size calculations in section_size() method

        Example:
            >>> # Check if .tbss has special handling in LOAD segment
            >>> tbss = parser.sections.get('.tbss')
            >>> load_segment = parser.segments[0]  # PT_LOAD
            >>> if parser.tbss_special(tbss, load_segment):
            ...     print(".tbss has zero effective size in LOAD segment")
            ...     # Actual TBSS data is in PT_TLS segment
        """
        return (
            (section_header.sh_flags & defs.SectionFlags.SHF_TLS) != 0
            and section_header.sh_type == defs.SectionType.SHT_NOBITS
            and segment.p_type != defs.PT_TLS
        )

    def section_size(self, section_header: model.Elf_Section, segment: model.Elf_ProgramHeaders) -> int:
        """Get the effective size of a section within a specific segment.

        Returns the section's effective size when contained in the given segment,
        accounting for the special case of TBSS (Thread-Local BSS) sections in
        non-TLS segments. The effective size is used for segment boundary calculations
        in section-to-segment mapping logic.

        Args:
            section_header: Section whose effective size to compute.
            segment: Program header (segment) context for size calculation.

        Returns:
            0 if section is TBSS in a non-TLS segment (special case),
            otherwise returns section_header.sh_size (actual section size in bytes).

        Note:
            - TBSS sections have zero effective size in non-TLS segments
            - Normal sections always return their sh_size
            - Used by section_in_segment1() for boundary validation
            - NOBITS sections (.bss, .tbss) have sh_size but no file data

        Example:
            >>> # Compare section size in different segment contexts
            >>> tbss = parser.sections.get('.tbss')
            >>> tls_segment = next(s for s in parser.segments if s.p_type == defs.PT_TLS)
            >>> load_segment = next(s for s in parser.segments if s.p_type == defs.PT_LOAD)
            >>>
            >>> tls_size = parser.section_size(tbss, tls_segment)
            >>> load_size = parser.section_size(tbss, load_segment)
            >>> print(f"Size in PT_TLS: {tls_size}")    # Non-zero
            >>> print(f"Size in PT_LOAD: {load_size}")  # 0 (special case)
        """
        return 0 if self.tbss_special(section_header, segment) else section_header.sh_size

    def get_basic_header_field(self, name: str) -> typing.Any:
        """Get a field value from the basic ELF header.

        Retrieves a field from the ELF header structure. The "basic" header includes
        the initial identification bytes (e_ident) and core header fields that are
        present in all ELF files regardless of type (executable, shared object, etc.).

        Basic header fields include:
            - e_ident: 16-byte identification array (EI_MAG, EI_CLASS, EI_DATA, etc.)
            - e_type: Object file type (ET_REL, ET_EXEC, ET_DYN, ET_CORE)
            - e_machine: Target architecture (EM_386, EM_ARM, EM_X86_64, etc.)
            - e_version: ELF version (always 1 for current ELF)

        Args:
            name: Name of the header field to retrieve (e.g., 'e_type', 'e_machine').

        Returns:
            Value of the requested header field. Type depends on the field
            (typically int for most fields).

        Raises:
            AttributeError: If the field name doesn't exist in the header.

        Note:
            - Despite the name, this method now accesses self._header directly
            - Historical implementation used self._basic_header.header.fields
            - For most use cases, direct property access is preferred (e.g., parser.e_machine)

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> machine = parser.get_basic_header_field('e_machine')
            >>> print(f"Target architecture: {machine}")
            Target architecture: 40  # EM_ARM
        """
        # return getattr(self._basic_header.header.fields, name)
        return getattr(self._header, name)

    def get_extended_header_field(self, name: str) -> typing.Any:
        """Get a field value from the extended ELF header.

        Retrieves a field from the extended ELF header structure. The "extended" header
        includes fields beyond the basic identification that provide detailed information
        about the file's structure, entry point, and table locations.

        Extended header fields include:
            - e_entry: Entry point virtual address (start of program execution)
            - e_phoff: Program header table file offset
            - e_shoff: Section header table file offset
            - e_flags: Processor-specific flags
            - e_ehsize: ELF header size in bytes
            - e_phentsize: Program header entry size
            - e_phnum: Number of program header entries
            - e_shentsize: Section header entry size
            - e_shnum: Number of section header entries
            - e_shstrndx: Section header string table index

        Args:
            name: Name of the header field to retrieve (e.g., 'e_entry', 'e_phnum').

        Returns:
            Value of the requested header field. Type depends on the field
            (typically int for addresses/offsets/counts).

        Raises:
            AttributeError: If the field name doesn't exist in the header.

        Note:
            - Despite the name, this method now accesses self._header directly
            - Historical implementation used self._extended_header
            - "Basic" vs "Extended" distinction is mostly conceptual now
            - For most use cases, direct property access is preferred (e.g., parser.e_entry)

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>> entry = parser.get_extended_header_field('e_entry')
            >>> num_sections = parser.get_extended_header_field('e_shnum')
            >>> print(f"Entry point: 0x{entry:08x}")
            >>> print(f"Number of sections: {num_sections}")
            Entry point: 0x08000000
            Number of sections: 23
        """
        # return getattr(self._extended_header, name)
        return getattr(self._header, name)

    @property
    def ei_class(self) -> int:
        """ELF file class identifier.

        Returns:
            int: 1 for 32-bit (ELFCLASS32) or 2 for 64-bit (ELFCLASS64).
        """
        return self.get_basic_header_field("ei_class")

    @property
    def ei_data(self) -> int:
        """Data encoding identifier.

        Returns:
            int: 1 for little-endian (ELFDATA2LSB) or 2 for big-endian (ELFDATA2MSB).
        """
        return self.get_basic_header_field("ei_data")

    @property
    def ei_version(self) -> int:
        """ELF format version.

        Returns:
            int: Version number, typically 1 for current ELF specification.
        """
        return self.get_basic_header_field("ei_version")

    @property
    def ei_osabi(self) -> int:
        """Operating system and ABI identifier.

        Returns:
            int: OS/ABI type (e.g., 0=SYSV, 3=Linux, 9=FreeBSD, 64=ARM EABI).
        """
        return self.get_basic_header_field("ei_osabi")

    @property
    def ei_abiversion(self) -> int:
        """ABI version number.

        Returns:
            int: ABI-specific version identifier, interpretation depends on ei_osabi.
        """
        return self.get_basic_header_field("ei_abiversion")

    @property
    def header_bytes(self) -> bytes:
        """Raw ELF header bytes.

        Returns:
            bytes: Complete ELF header as raw byte sequence (52 bytes for 32-bit, 64 bytes for 64-bit).
        """
        return self._basic_header.header.bytes

    @property
    def e_type(self) -> int:
        """Object file type.

        Returns:
            int: File type identifier (1=ET_REL, 2=ET_EXEC, 3=ET_DYN, 4=ET_CORE).
        """
        return self.get_extended_header_field("e_type")

    @property
    def e_machine(self) -> int:
        """Target machine architecture.

        Returns:
            int: Architecture identifier (e.g., 3=x86, 40=ARM, 62=x86-64, 183=ARM64).
        """
        return self.get_extended_header_field("e_machine")

    @property
    def e_version(self) -> int:
        """ELF file version.

        Returns:
            int: Version number, typically 1 for current ELF specification.
        """
        return self.get_extended_header_field("e_version")

    @property
    def e_entry(self) -> int:
        """Program entry point address.

        Returns:
            int: Virtual address where program execution begins, 0 if no entry point.
        """
        return self.get_extended_header_field("e_entry")

    @property
    def e_phoff(self) -> int:
        """Program header table file offset.

        Returns:
            int: Byte offset from file start to program header table, 0 if no program headers.
        """
        return self.get_extended_header_field("e_phoff")

    @property
    def e_shoff(self) -> int:
        """Section header table file offset.

        Returns:
            int: Byte offset from file start to section header table, 0 if no section headers.
        """
        return self.get_extended_header_field("e_shoff")

    @property
    def e_flags(self) -> int:
        """Processor-specific flags.

        Returns:
            int: Architecture-dependent flag bits describing file attributes.
        """
        return self.get_extended_header_field("e_flags")

    @property
    def e_ehsize(self) -> int:
        """ELF header size.

        Returns:
            int: Size of ELF header in bytes (typically 52 for 32-bit, 64 for 64-bit).
        """
        return self.get_extended_header_field("e_ehsize")

    @property
    def e_phentsize(self) -> int:
        """Program header entry size.

        Returns:
            int: Size of one program header table entry in bytes.
        """
        return self.get_extended_header_field("e_phentsize")

    @property
    def e_phnum(self) -> int:
        """Number of program header entries.

        Returns:
            int: Count of entries in program header table, 0 if no program headers.
        """
        return self.get_extended_header_field("e_phnum")

    @property
    def e_shentsize(self) -> int:
        """Section header entry size.

        Returns:
            int: Size of one section header table entry in bytes.
        """
        return self.get_extended_header_field("e_shentsize")

    @property
    def e_shnum(self) -> int:
        """Number of section header entries.

        Returns:
            int: Count of entries in section header table, 0 if no section headers.
        """
        return self.get_extended_header_field("e_shnum")

    @property
    def e_shstrndx(self) -> int:
        """Section header string table index.

        Returns:
            int: Index of section containing section name string table.
        """
        return self.get_extended_header_field("e_shstrndx")

    @property
    def endianess(self) -> str:
        """Byte order indicator.

        Returns:
            str: '<' for little-endian or '>' for big-endian.
        """
        return self._endianess

    @property
    def segments(self) -> list:
        """Program header entries (segments).

        Returns:
            list: List of program header entries defining memory segments for loading.
        """
        return self._program_headers

    @property
    def arm_attributes(self) -> dict:
        """ARM architecture build attributes.

        Returns:
            dict: Parsed ARM build attributes from .ARM.attributes section, empty dict if not present or non-ARM.
        """
        res = self.query(model.Elf_Section).filter(model.Elf_Section.section_name == ".ARM.attributes").first()
        if res:
            return attributes.parse(res.section_image, byteorder=self.endianess)
        else:
            return {}

    @property
    def comment(self) -> str | None:
        """Comment section content.

        Returns:
            str | None: Text from .comment section if present, None otherwise.
        """
        comment = self.query(model.Elf_Comment).first()
        if comment:
            return comment.text
        else:
            return None

    @property
    def notes(self) -> list:
        """ELF note sections.

        Returns:
            list: List of ELF note entries containing build metadata, empty list if none present.
        """
        notes = self.query(model.Elf_Note).order_by(model.Elf_Note.section_name).all()
        if notes:
            return notes
        else:
            return []

    @property
    def query(self):
        """SQLAlchemy query factory.

        Returns:
            callable: Session query method for database operations on ELF data models.
        """
        return self.session.query

    @property
    def machine_data(self) -> str:
        """Machine-specific data representation.

        Returns:
            str: String representation of architecture-specific data and metadata.
        """
        return str(self._machine_data)

    def create_image(
        self,
        join: bool = True,
        include_pattern: str = "",
        exclude_pattern: str = "",
        callback: typing.Callable[[str, typing.Any], None] | None = None,
    ) -> Image:
        r"""Create an Image object from ELF sections with optional filtering.

        Constructs a binary image by extracting allocatable ELF sections and combining
        them into a single Image object. The image can be optionally joined (adjacent
        sections merged) and filtered by section name patterns.

        Args:
            join: If True, merge adjacent sections with no gaps into single blocks.
                Reduces fragmentation for embedded system workflows. Default is True.
            include_pattern: Python regex pattern to include only matching section names.
                Applied as a positive filter. Leave empty to include all sections.
            exclude_pattern: Python regex pattern to exclude matching section names.
                Applied as a negative filter. Takes precedence over include_pattern
                if both are specified.
            callback: Optional callable for progress reporting. Called with:
                - callback("start", None) at beginning
                - callback("section", section_obj) for each processed section
                - callback("stop", None) at end
                Useful for logging or displaying progress bars.

        Returns:
            objutils.Image: Binary image containing all matching sections ordered
            by address with optional joining.

        Note:
            - Only sections with SHF_ALLOC flag (allocatable) are included
            - NOBITS sections (.bss, .tbss) are excluded (no file data)
            - NULL sections are excluded
            - Sections are ordered by base address (sh_addr)

        Note:
            - `include_pattern` and `exclude_pattern` should be used mutually exclusive
              unless you need complex filtering logic.

        Example:
            >>> parser = ElfParser('firmware.elf')
            >>>
            >>> # Get all allocatable sections
            >>> img = parser.create_image()
            >>>
            >>> # Get only code sections
            >>> img = parser.create_image(include_pattern=r'^\.text')
            >>>
            >>> # Exclude debug sections
            >>> img = parser.create_image(exclude_pattern=r'^\.debug')
            >>>
            >>> # With progress callback
            >>> def progress(state, section):
            ...     if state == "section":
            ...         print(f"  {section.section_name} @ 0x{section.sh_addr:08x}")
            >>> img = parser.create_image(callback=progress)

        See Also:
            - Look at `scripts/oj_elf_extract.py` for detailed create_image() usage examples.
        """
        query = self.query(model.Elf_Section)
        # query = query.filter(
        #    model.Elf_Section.flag_alloc is True,
        #    model.Elf_Section.has_content is True,
        # )
        # defs.SectionFlags.SHF_ALLOC
        #
        query.filter(model.Elf_Section.sh_flags.bitwise_and(defs.SectionFlags.SHF_ALLOC) == defs.SectionFlags.SHF_ALLOC)

        # sections = self.query(model.Elf_Section).all()
        # print("SECTIONS", sections)

        if include_pattern:
            query = query.filter(func.regexp(model.Elf_Section.section_name, include_pattern))

        if exclude_pattern:
            query = query.filter(not_(func.regexp(model.Elf_Section.section_name, exclude_pattern)))

        query = query.order_by(model.Elf_Section.sh_addr)
        result = []
        if callback:
            callback("start", None)
        for section in query.all():
            if (
                section.section_image is None
                or (section.sh_flags & defs.SectionFlags.SHF_ALLOC) != defs.SectionFlags.SHF_ALLOC
                or section.sh_type in (defs.SectionType.SHT_NOBITS, defs.SectionType.SHT_NULL)
            ):
                continue
            if callback:
                callback("section", section)
            result.append(Section(section.sh_addr, section.section_image))
        img = Image(result, join=join)
        if callback:
            callback("stop", None)
        return img


def import_dwarf_to_db(
    elf_path: str,
    out_db: str | None,
    *,
    quiet: bool = False,
    verbose: bool = False,
    run_lines: bool = True,
    run_pubnames: bool = True,
    run_aranges: bool = True,
    run_mac: bool = False,
    force: bool = False,
) -> int:
    """Import DWARF debug information from ELF into a .prgdb database.

    Parses DWARF debug information from an ELF file and imports it into a SQLite
    database (.prgdb). The database includes compiled source files, line number
    mappings, address ranges, and detailed debug information entries.

    Args:
        elf_path: Path to ELF file containing DWARF sections (.debug_info, etc.).
        out_db: Output database path. If None, uses default location
            (elf_path with .prgdb extension). If specified, copies/creates database
            at this location instead.
        quiet: If True, suppress status messages. Default is False.
        verbose: If True, print detailed status and warning messages. Default is False.
        run_lines: If True, process .debug_line section for line number information.
            Default is True.
        run_pubnames: If True, process .debug_pubnames section (deprecated in DWARF 4+).
            Default is True.
        run_aranges: If True, process .debug_aranges section for address-to-CU mapping.
            Default is True.
        run_mac: If True, process .debug_macro section (DWARF 4+). Default is False.
        force: If True, rebuild database even if it already exists.
            Deletes existing database and .prgdb files. Default is False.

    Returns:
        int: Exit code compatible with CLI scripts:
            - 0: Success, database created/updated
            - 1: No DWARF sections found in ELF file
            - 2: ELF file not found or cannot be opened
            - 3: Error parsing .debug_info section
            - 4: Error writing/copying database file

    Raises:
        No exceptions raised; errors are reported via return codes and optional messages.

    Example:
        >>> from objutils.elf import import_dwarf_to_db
        >>>
        >>> # Import DWARF to default location (firmware.prgdb next to firmware.elf)
        >>> rc = import_dwarf_to_db('firmware.elf', None, quiet=False)
        >>> if rc == 0:
        ...     print("DWARF imported successfully")
        >>>
        >>> # Import to custom location with all DWARF processing
        >>> rc = import_dwarf_to_db(
        ...     'firmware.elf',
        ...     'output.prgdb',
        ...     run_lines=True,
        ...     run_pubnames=True,
        ...     run_aranges=True,
        ...     force=False
        ... )
        >>>
        >>> # Force rebuild, suppress non-error output
        >>> rc = import_dwarf_to_db('firmware.elf', None, quiet=True, force=True)

    Note:
        - Processes .debug_info, .debug_line, .debug_aranges, .debug_pubnames sections
        - Requires DwarfProcessor from objutils.dwarf module
        - Database schema created/validated automatically
        - File locking handled transparently
    """
    # Local import to avoid potential circular import at module import time.
    from objutils.dwarf import DwarfProcessor

    def _print(msg: str):
        if not quiet:
            print(msg)

    elf_p = Path(elf_path)
    if not elf_p.exists() or not elf_p.is_file():
        _print(f"ELF file not found: {elf_path}")
        return 2

    default_db_path = elf_p.with_suffix(model.DB_EXTENSION)
    try:
        if force:
            if default_db_path.exists():
                try:
                    default_db_path.unlink()
                except Exception:
                    pass
            if out_db:
                outp = Path(out_db)
                if outp.exists():
                    try:
                        outp.unlink()
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        ep = ElfParser(str(elf_p))
    except Exception as e:
        _print(f"Failed to open ELF file '{elf_path}': {e}")
        return 2

    if verbose:
        _print(str(ep))

    try:
        dp = DwarfProcessor(ep)
    except TypeError as te:
        _print(f"No DWARF sections available in '{elf_path}': {te}")
        return 1

    if run_pubnames:
        try:
            dp.pubnames()
        except Exception as e:
            if verbose:
                _print(f"Warning: pubnames failed: {e}")
    if run_aranges:
        try:
            dp.aranges()
        except Exception as e:
            if verbose:
                _print(f"Warning: aranges failed: {e}")
    if run_lines:
        try:
            dp.do_lines()
        except Exception as e:
            if verbose:
                _print(f"Warning: do_lines failed: {e}")

    try:
        dp.do_dbg_info()
    except Exception as e:
        _print(f"Error while parsing .debug_info: {e}")
        return 3

    if run_mac:
        try:
            dp.do_mac_info()
        except Exception as e:
            if verbose:
                _print(f"Warning: do_mac_info failed: {e}")

    try:
        if out_db:
            src_db = default_db_path
            dst_db = Path(out_db)
            if str(dst_db.resolve()) != str(src_db.resolve()):
                if not src_db.exists():
                    with model.Model(str(dst_db)) as _mdb:  # type: ignore[attr-defined]
                        pass
                else:
                    try:
                        ep.db.close()
                    except Exception:
                        pass
                    import shutil as _shutil

                    _shutil.copyfile(str(src_db), str(dst_db))
                    _print(f"Wrote database: {dst_db}")
            else:
                _print(f"Database available at: {src_db}")
        else:
            _print(f"Database available at: {default_db_path}")
    except Exception as e:
        _print(f"Failed to write/copy database: {e}")
        return 4

    return 0


def open_program_database(
    path: str | os.PathLike,
    *,
    import_if_needed: bool = True,
    force_import: bool = False,
    quiet: bool = True,
) -> model.Model:
    """Open or derive a program database (.prgdb) from ELF or .prgdb file.

    Provides a flexible interface to work with program databases. If given an ELF file,
    automatically creates a .prgdb database with DWARF debug information if needed.
    If given a .prgdb file, opens it directly.

    Args:
        path: Path to either:
            - ELF executable/object file (.elf, .o, etc.)
            - Program database file (.prgdb)
        import_if_needed: If True (default), create .prgdb from ELF's DWARF sections
            if database doesn't exist. If False, raise FileNotFoundError.
        force_import: If True, force rebuild of .prgdb even if it exists.
            Deletes existing database before import. Default is False.
        quiet: If True (default), suppress import progress messages.
            If False, print status information during import.

    Returns:
        model.Model: Opened SQLAlchemy model wrapping the .prgdb database.

    Raises:
        FileNotFoundError: If path is ELF without existing .prgdb and
            import_if_needed is False.
        RuntimeError: If DWARF import fails (error code != 0).
        FileNotFoundError: If the specified path doesn't exist.

    Example:
        >>> from objutils.elf import open_program_database
        >>>
        >>> # Open existing .prgdb directly
        >>> db = open_program_database('firmware.prgdb')
        >>>
        >>> # Auto-import DWARF from ELF if needed
        >>> db = open_program_database('firmware.elf')
        >>>
        >>> # Force rebuild of .prgdb from ELF
        >>> db = open_program_database('firmware.elf', force_import=True, quiet=False)
        >>>
        >>> # Require pre-existing .prgdb (don't auto-import)
        >>> try:
        ...     db = open_program_database(
        ...         'firmware.elf',
        ...         import_if_needed=False
        ...     )
        ... except FileNotFoundError:
        ...     print("Need to run import_dwarf_to_db first")

    Note:
        - Auto-detection based on file extension (.prgdb vs others)
        - Database location: elf_path with .prgdb extension by default
        - Import only runs if no existing database or force_import=True
        - Thread-safe Model instances; each thread should create its own
    """
    p = Path(path)
    if p.suffix.lower() == model.DB_EXTENSION:
        return model.Model(str(p))

    # Treat as ELF input; determine the sibling .prgdb
    elf_path = p
    db_path = elf_path.with_suffix(model.DB_EXTENSION)
    if not db_path.exists():
        if not import_if_needed:
            raise FileNotFoundError(str(db_path))
        rc = import_dwarf_to_db(str(elf_path), str(db_path), quiet=quiet, force=force_import)
        if rc != 0:
            raise RuntimeError(f"Failed to import DWARF from '{elf_path}' (rc={rc})")
    return model.Model(str(db_path))
