#!/usr/bin/env python
"""ELF ORM (Object-Relational Mapping) Database Model Layer.

This module provides a comprehensive SQLAlchemy-based ORM for parsing, storing, and
querying ELF (Executable and Linkable Format) file metadata and DWARF debugging information.

The module implements an automatic database persistence layer that creates SQLite database
files (with `.prgdb` extension) to store parsed ELF data. This enables efficient analysis
of large binaries through SQL queries, caching, and relationships between ELF structures.

**Database Architecture:**

The ORM creates tables for the following ELF structures:

- **Elf_Header**: Main ELF file header with architecture/endianness information
  - Stores e_ident fields: ei_class, ei_data, ei_version, ei_osabi, ei_abiversion
  - Stores e_header fields: e_type, e_machine, e_version, e_entry, offsets, sizes, counts
  - Provides hybrid properties: endianess, is_64bit, address_size

- **Elf_ProgramHeaders**: Program segment headers (loadable segments)
  - Stores p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align

- **Elf_Section**: Section headers with content and computed properties
  - Stores sh_* fields: sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, etc.
  - Stores section_name and section_image (content)
  - Provides flag checking: is_debug, is_dwo, has_content, flag_writeable, flag_executable, etc.
  - Hybrid properties enable both Python and SQL filtering

- **Elf_Symbol**: Symbol table entries
  - Stores st_* fields: st_name, st_value, st_size, st_bind, st_type, st_other, st_shndx
  - Stores section_name, symbol_name, access flags
  - Provides properties: hidden, weak, absolute, undefined, local, global_, writeable, etc.

- **DWARF Debug Information Tables**:
  - **DebugInformationEntry (DIE)**: DWARF DIE nodes with tree relationships
    - Stores tag (DW_TAG_*), offset within CU, parent_id for tree traversal
    - Self-referential relationships: parent/children for DIE tree structure
  
  - **DIEAttribute**: DWARF attributes attached to DIE entries
    - Stores attribute name (DW_AT_*), form (DW_FORM_*), and raw_value
    - Foreign key relationship back to DebugInformationEntry

- **Elf_Comment, Elf_Note, DebugInformation, CompilationUnit**: Utility tables

**SQLAlchemy Features Used:**

1. **Declarative Mapping**: All tables inherit from SQLAlchemy Base (declarative_base)
2. **Hybrid Properties**: Computed fields that work both in Python (getter) and SQL (expression)
   - Enable efficient filtering via SQL when using ORM queries
   - Fallback to Python evaluation for complex logic
3. **Hybrid Methods**: Methods that work both on instances and in query expressions
   - Example: test_flags() method can be used in WHERE clauses
4. **Relationships**: Object navigation through foreign keys
   - DIE parent-child tree traversal
   - DIEAttribute access from DebugInformationEntry
5. **SQLite Pragmas**: Performance tuning via set_sqlite3_pragmas event listener
   - PRAGMA FOREIGN_KEYS=ON: Enable referential integrity
   - PRAGMA CACHE_SIZE, PAGE_SIZE: Memory and disk optimization
   - PRAGMA SYNCHRONOUS=OFF: Fast writes
   - PRAGMA LOCKING_MODE=EXCLUSIVE: Prevent concurrent access issues

**Database Auto-Creation (.prgdb files):**

The Model class automatically creates SQLite database files with the `.prgdb` extension
when instantiated. It also handles schema migration for databases created by older versions,
adding missing columns and indexes without rebuilding the database.

Usage:
    >>> from objutils.elf.model import Model
    >>> db = Model("firmware.elf.prgdb")
    >>> # Tables are created automatically
    >>> # Use db.session to query or manipulate data
    >>> db.session.query(Elf_Header).first()
    >>> db.close()

**Key Classes:**

- **Model**: Main database interface, manages engine, session, and schema
- **Elf_Header**: Represents the ELF header
- **Elf_Section**: Represents ELF section headers
- **Elf_Symbol**: Represents symbol table entries
- **DebugInformationEntry (DIE)**: Represents DWARF debug information entries
- **DIEAttribute**: Represents DWARF attributes

**Special Features:**

- Regex support: REGEXP SQL operator for pattern matching
- Cache size tuning: Automatic memory-to-page-size conversion
- Validators: _coerce_name(), _coerce_tag() for flexible input types
- Computed properties: attributes_map, abbrev for convenience access
- Schema migration: _ensure_schema() for backward compatibility

References:
    - SQLAlchemy ORM: https://docs.sqlalchemy.org/
    - ELF Specification: http://www.sco.com/developers/gabi/
    - DWARF Specification: http://www.dwarfstd.org/
    - ARM EABI: https://github.com/ARM-software/abi-aa
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <github.com/Christoph2,
                                         cpu12.gems@googlemail.com>

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

import mmap
import re
import sqlite3
from typing import Any, Callable, Dict, Optional

from sqlalchemy import (
    Column,
    ForeignKey,
    and_,
    create_engine,
    event,
    not_,
    orm,
    text,
    types,
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import declarative_base, declared_attr, relationship, Session
from sqlalchemy.sql import func

from objutils.elf import defs


CACHE_SIZE = 4  # MB
PAGE_SIZE = mmap.PAGESIZE

DB_EXTENSION = ".prgdb"

Base = declarative_base()


class MixInBase:
    """Base mixin class providing common functionality for all ORM models.
    
    This mixin provides automatic table name generation and a comprehensive
    __repr__ method for debugging and logging.
    
    Methods:
        __tablename__: Generated from class name (lowercased)
        __repr__: Returns detailed representation of object attributes
    """

    @declared_attr
    def __tablename__(self) -> str:
        """Generate table name from class name.
        
        Returns:
            str: Lowercase class name used as SQLAlchemy table name.
        """
        return self.__name__.lower()

    def __repr__(self) -> str:
        """Generate detailed string representation of object.
        
        Iterates through all database columns and formats them with their values.
        String values are repr'd; numeric values are formatted as-is.
        
        Returns:
            str: Formatted string like "ClassName(col1 = val1, col2 = val2, ...)"
        """
        columns = [c.name for c in self.__class__.__table__.c]
        result = []
        for name, value in [(n, getattr(self, n)) for n in columns]:
            if isinstance(value, str):
                result.append(f"{name} = {value!r}")
            else:
                result.append(f"{name} = {value}")
        return "{}({})".format(self.__class__.__name__, ", ".join(result))


class RidMixIn(MixInBase):
    """Mixin providing row ID primary key.
    
    Adds an auto-incrementing 'rid' (row ID) column as the primary key
    for all tables that inherit from this mixin.
    """

    rid = Column("rid", types.Integer, primary_key=True)


def StdInteger(
    default: int = 0,
    primary_key: bool = False,
    unique: bool = False,
    nullable: bool = False,
    index: bool = False,
) -> Column:
    """Create a standard INTEGER column.
    
    Args:
        default: Default value for the column (default: 0)
        primary_key: Whether this column is a primary key (default: False)
        unique: Whether values must be unique (default: False)
        nullable: Whether NULL values are allowed (default: False)
        index: Whether to create an index on this column (default: False)
    
    Returns:
        Column: SQLAlchemy Column configured for INTEGER storage
    """
    return Column(
        types.INTEGER,
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
    )


def StdNumeric(
    default: int = 0,
    primary_key: bool = False,
    unique: bool = False,
    nullable: bool = False,
    index: bool = False,
) -> Column:
    """Create a standard NUMERIC column.
    
    Uses NUMERIC(20, 0) for high-precision integer storage without decimals.
    
    Args:
        default: Default value for the column (default: 0)
        primary_key: Whether this column is a primary key (default: False)
        unique: Whether values must be unique (default: False)
        nullable: Whether NULL values are allowed (default: False)
        index: Whether to create an index on this column (default: False)
    
    Returns:
        Column: SQLAlchemy Column configured for NUMERIC(20, 0) storage
    """
    return Column(
        types.NUMERIC(20, 0),
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
    )


def StdBigInt(
    default: int = 0,
    primary_key: bool = False,
    unique: bool = False,
    nullable: bool = False,
    index: bool = False,
) -> Column:
    """Create a standard large INTEGER column.
    
    Args:
        default: Default value for the column (default: 0)
        primary_key: Whether this column is a primary key (default: False)
        unique: Whether values must be unique (default: False)
        nullable: Whether NULL values are allowed (default: False)
        index: Whether to create an index on this column (default: False)
    
    Returns:
        Column: SQLAlchemy Column configured for INTEGER storage
    """
    return Column(
        types.INTEGER,
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
    )


def StdFloat(
    default: float = 0.0,
    primary_key: bool = False,
    unique: bool = False,
    nullable: bool = False,
) -> Column:
    """Create a standard floating-point column.
    
    Args:
        default: Default value for the column (default: 0.0)
        primary_key: Whether this column is a primary key (default: False)
        unique: Whether values must be unique (default: False)
        nullable: Whether NULL values are allowed (default: False)
    
    Returns:
        Column: SQLAlchemy Column configured for floating-point storage
    """
    return Column(
        types.Integer,
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
    )


class Meta(Base, RidMixIn):
    """Metadata table for database schema information.
    
    Stores schema version and creation timestamp information for the database.
    Used for schema migration and versioning.
    
    Attributes:
        hash_value: Hash of ELF file or metadata (VARCHAR)
        ts_created: Timestamp when database was created (DateTime with timezone)
    """

    hash_value = Column(types.VARCHAR)
    ts_created = Column(types.DateTime(timezone=True), server_default=func.now())


class Elf_Header(Base, RidMixIn):
    """ORM model for ELF file header (Elf_Ehdr).
    
    Stores the main ELF header information including file identification (e_ident),
    architecture information, offsets, and counts for all major ELF structures.
    
    This is the entry point for understanding any ELF file's structure and properties.
    
    Attributes:
        ei_class (int): ELF file class (32-bit=1, 64-bit=2)
        ei_data (int): ELF data encoding (little-endian=1, big-endian=2)
        ei_version (int): ELF header version
        ei_osabi (int): Operating system/ABI identification
        ei_abiversion (int): ABI version
        e_type (int): ELF file type (ET_REL=1, ET_EXEC=2, ET_DYN=3, ET_CORE=4)
        e_machine (int): Target machine architecture (EM_386=3, EM_ARM=40, etc.)
        e_version (int): ELF file version
        e_entry (int): Entry point virtual address
        e_phoff (int): Program header table file offset
        e_shoff (int): Section header table file offset
        e_flags (int): Machine-specific flags
        e_ehsize (int): ELF header size in bytes
        e_phentsize (int): Program header entry size
        e_phnum (int): Program header entry count
        e_shentsize (int): Section header entry size
        e_shnum (int): Section header entry count
        e_shstrndx (int): Section header string table index
    """

    ei_class = StdBigInt()
    ei_data = StdBigInt()
    ei_version = StdBigInt()
    ei_osabi = StdBigInt()
    ei_abiversion = StdBigInt()
    e_type = StdBigInt()
    e_machine = StdBigInt()
    e_version = StdBigInt()
    e_entry = StdBigInt()
    e_phoff = StdBigInt()
    e_shoff = StdBigInt()
    e_flags = StdBigInt()
    e_ehsize = StdBigInt()
    e_phentsize = StdBigInt()
    e_phnum = StdBigInt()
    e_shentsize = StdBigInt()
    e_shnum = StdBigInt()
    e_shstrndx = StdBigInt()

    @hybrid_property
    def endianess(self) -> defs.ELFDataEncoding:
        """Get the endianness of the ELF file.
        
        Determined by ei_data field:
        - 1 = Little-endian (ELFDATA2LSB)
        - 2 = Big-endian (ELFDATA2MSB)
        
        Returns:
            defs.ELFDataEncoding: Enum representing file endianness
        
        Raises:
            ValueError: If ei_data contains an invalid value
        """
        if self.ei_data == 1:  # Little-Endian
            return defs.ELFDataEncoding.ELFDATA2LSB
        elif self.ei_data == 2:  # Big-Endian
            return defs.ELFDataEncoding.ELFDATA2MSB
        else:
            raise ValueError(f"EI_DATA has an invalid value. Got: {self.ei_data}")

    @hybrid_property
    def is_64bit(self) -> bool:
        """Check if ELF file is 64-bit.
        
        Based on ei_class field:
        - 1 = 32-bit
        - 2 = 64-bit
        
        Returns:
            bool: True if 64-bit, False if 32-bit
        """
        return self.ei_class == 2

    @hybrid_property
    def address_size(self) -> int:
        """Get the address size in bytes for this ELF file.
        
        Returns:
            int: 8 bytes for 64-bit files, 4 bytes for 32-bit files
        """
        return 8 if self.is_64bit else 4


class Elf_ProgramHeaders(Base, RidMixIn):
    """ORM model for ELF program header (Elf_Phdr).
    
    Represents a loadable segment/program header. Program headers describe how the
    kernel should load the file into memory during program execution.
    
    Attributes:
        p_type (int): Segment type (PT_LOAD=1, PT_DYNAMIC=2, PT_INTERP=3, etc.)
        p_offset (int): Segment file offset
        p_vaddr (int): Segment virtual address
        p_paddr (int): Segment physical address
        p_filesz (int): Segment size in file
        p_memsz (int): Segment size in memory
        p_flags (int): Segment attribute flags (PF_X=1, PF_W=2, PF_R=4)
        p_align (int): Segment alignment constraint
    """

    p_type = StdBigInt()
    p_offset = StdBigInt()
    p_vaddr = StdBigInt()
    p_paddr = StdBigInt()
    p_filesz = StdBigInt()
    p_memsz = StdBigInt()
    p_flags = StdBigInt()
    p_align = StdBigInt()


class Elf_Section(Base, RidMixIn):
    """ORM model for ELF section header (Elf_Shdr).
    
    Represents a section within an ELF file. Sections contain the actual data and code:
    code (.text), initialized data (.data), uninitialized data (.bss), symbol tables,
    string tables, debug information, etc.
    
    Provides comprehensive flag checking via hybrid properties that work in both
    Python and SQL queries. Supports filtering by section type, flags, and content.
    
    Attributes:
        index (int): Sequential section index (unique)
        sh_name (int): Section name string table index
        sh_type (int): Section type (SHT_PROGBITS=1, SHT_SYMTAB=2, SHT_STRTAB=3, etc.)
        sh_flags (int): Section flags (SHF_WRITE=1, SHF_ALLOC=2, SHF_EXECINSTR=4, etc.)
        sh_addr (int): Section address in memory
        sh_offset (int): Section file offset
        sh_size (int): Section size in bytes
        sh_link (int): Link to related section
        sh_info (int): Additional section info
        sh_addralign (int): Section alignment requirement
        sh_entsize (int): Size of entry in section (for tables)
        section_name (str): Resolved section name (indexed for fast lookup)
        section_image (bytes): Raw section content
    """

    index = Column(types.Integer, unique=True)
    sh_name = StdBigInt()
    sh_type = StdBigInt()
    sh_flags = StdBigInt()
    sh_addr = StdBigInt()
    sh_offset = StdBigInt()
    sh_size = StdBigInt()
    sh_link = StdBigInt()
    sh_info = StdBigInt()
    sh_addralign = StdBigInt()
    sh_entsize = StdBigInt()

    section_name = Column(types.VARCHAR, index=True)
    section_image = Column(types.BLOB)

    @hybrid_property
    def is_debug(self) -> bool:
        """Check if section contains debug information.
        
        Returns:
            bool: True if section name starts with ".debug"
        """
        return self.section_name.starts_with(".debug")

    @hybrid_property
    def is_dwo(self) -> bool:
        """Check if section contains split debug information.
        
        Returns:
            bool: True if section name starts with ".dwo" (DWARF object files)
        """
        return self.section_name.starts_with(".dwo")

    @hybrid_property
    def has_content(self) -> bool:
        """Check if section has actual content.
        
        Returns:
            bool: True if section is not NOBITS/NULL and has non-zero size
        """
        return self.sh_type not in (
            defs.SectionType.SHT_NOBITS,
            defs.SectionType.SHT_NULL,
        ) and (self.sh_size > 0)

    @has_content.expression
    def has_content(self) -> Any:
        """SQL expression for checking if section has content.
        
        Returns:
            Any: SQLAlchemy expression for use in WHERE clauses
        """
        return and_(
            not_(self.sh_type.in_((defs.SectionType.SHT_NOBITS, defs.SectionType.SHT_NULL))),
            (self.sh_size > 0),
        )

    @hybrid_property
    def progbits(self) -> bool:
        """Check if section is PROGBITS type (code or data).
        
        Returns:
            bool: True if sh_type is SHT_PROGBITS
        """
        return self.sh_type == defs.SectionType.SHT_PROGBITS

    @hybrid_method
    def get_flags(self) -> int:
        """Get section flags.
        
        Returns:
            int: Raw section flags value (sh_flags)
        """
        return self.sh_flags

    @hybrid_method
    def test_flags(self, mask: int) -> bool:
        """Test if section flags match a bitmask.
        
        Args:
            mask: Bitmask to test against sh_flags
        
        Returns:
            bool: True if (sh_flags & mask) == mask
        """
        return self.get_flags() & mask == mask

    @test_flags.expression
    def test_flags(self, mask: int) -> Any:
        """SQL expression for testing section flags.
        
        Args:
            mask: Bitmask to test against sh_flags
        
        Returns:
            Any: SQLAlchemy expression for use in WHERE clauses
        """
        return self.get_flags().op("&")(mask) == mask

    @hybrid_property
    def section_type(self) -> defs.SectionType:
        """Get section type as enum.
        
        Returns:
            defs.SectionType: Enum representing the section type
        """
        return defs.SectionType(self.sh_type)

    @hybrid_property
    def section_display_name(self) -> str:
        """Get human-readable section type name.
        
        For processor-specific or OS-specific types, returns the offset from
        the base constant (e.g., "SHT_LOPROC + 0x00000010").
        
        Returns:
            str: Section type name or formatted offset for special types
        """
        sh_type = self.sh_type
        if sh_type > defs.SectionType.SHT_LOUSER.value:
            diff = sh_type - defs.SectionType.SHT_LOUSER.value
            return f"SHT_LOUSER + 0x{diff:08x}"
        elif sh_type > defs.SectionType.SHT_LOPROC.value:
            diff = sh_type - defs.SectionType.SHT_LOPROC.value
            return f"SHT_LOPROC + 0x{diff:08x}"
        else:
            return defs.SectionType(self.sh_type).name

    @hybrid_property
    def flag_writeable(self) -> bool:
        """Check if section is writeable.
        
        Returns:
            bool: True if SHF_WRITE flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_WRITE)

    @hybrid_property
    def flag_executable(self) -> bool:
        """Check if section is executable.
        
        Returns:
            bool: True if SHF_EXECINSTR flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_EXECINSTR)

    @hybrid_property
    def flag_alloc(self) -> bool:
        """Check if section occupies memory.
        
        Returns:
            bool: True if SHF_ALLOC flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_ALLOC)

    @hybrid_property
    def flag_merge(self) -> bool:
        """Check if section data can be merged.
        
        Returns:
            bool: True if SHF_MERGE flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_MERGE)

    @hybrid_property
    def flag_strings(self) -> bool:
        """Check if section contains null-terminated strings.
        
        Returns:
            bool: True if SHF_STRINGS flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_STRINGS)

    @hybrid_property
    def flag_info_link(self) -> bool:
        """Check if sh_info contains section link.
        
        Returns:
            bool: True if SHF_INFO_LINK flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_INFO_LINK)

    @hybrid_property
    def flag_link_order(self) -> bool:
        """Check if section order matters during linking.
        
        Returns:
            bool: True if SHF_LINK_ORDER flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_LINK_ORDER)

    @hybrid_property
    def flag_os_nonconforming(self) -> bool:
        """Check if section uses OS-specific semantics.
        
        Returns:
            bool: True if SHF_OS_NONCONFORMING flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_OS_NONCONFORMING)

    @hybrid_property
    def flag_group(self) -> bool:
        """Check if section is member of a group.
        
        Returns:
            bool: True if SHF_GROUP flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_GROUP)

    @hybrid_property
    def flag_tls(self) -> bool:
        """Check if section contains thread-local storage.
        
        Returns:
            bool: True if SHF_TLS flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_TLS)

    @hybrid_property
    def flag_ordered(self) -> bool:
        """Check if section ordering is significant (Solaris only).
        
        Returns:
            bool: True if SHF_ORDERED flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_ORDERED)

    @hybrid_property
    def flag_exclude(self) -> bool:
        """Check if section is excluded from linking (Solaris only).
        
        Returns:
            bool: True if SHF_EXCLUDE flag is set
        """
        return self.test_flags(defs.SectionFlags.SHF_EXCLUDE)


class Elf_Symbol(Base, RidMixIn):
    """ORM model for ELF symbol table entry (Elf_Sym).
    
    Represents a symbol (function, variable, label, etc.) in an ELF file.
    Symbol tables enable linking, relocation, debugging, and runtime symbol lookup.
    
    Provides extensive properties for checking symbol attributes and access rights.
    All 'st_*' attributes are raw values from symbol tables per the ELF specification;
    other attributes exist for convenience and resolved information.
    
    Attributes:
        st_name (int): Index into string table for symbol name
        st_value (int): Symbol value (address or offset, indexed for fast lookup)
        st_size (int): Size associated with symbol (e.g., function size)
        st_bind (int): Symbol binding (STB_LOCAL=0, STB_GLOBAL=1, STB_WEAK=2)
        st_type (int): Symbol type (STT_NOTYPE=0, STT_OBJECT=1, STT_FUNC=2, etc.)
        st_other (int): Symbol visibility and reserved bits
        st_shndx (int): Section header index (SHN_UNDEF=0, SHN_ABS=0xfff1, etc.)
        section_name (str): Resolved name of section containing symbol (indexed)
        symbol_name (str): Resolved symbol name from string table (indexed)
        access (int): Access/permission flags (indexed for fast lookup)
    """

    st_name = StdInteger()
    st_value = StdInteger(index=True)
    st_size = StdInteger()
    st_bind = StdInteger(index=True)
    st_type = StdInteger(index=True)
    st_other = StdInteger()
    st_shndx = StdInteger()

    section_name = Column(types.VARCHAR, index=True)
    symbol_name = Column(types.VARCHAR, index=True)
    access = StdInteger(index=True)

    @hybrid_property
    def hidden(self) -> bool:
        """Check if symbol is hidden or internal.
        
        Returns:
            bool: True if st_other is STV_HIDDEN or STV_INTERNAL
        """
        return self.st_other in (
            defs.SymbolVisibility.STV_HIDDEN,
            defs.SymbolVisibility.STV_INTERNAL,
        )

    @hidden.expression
    def hidden(self) -> Any:
        """SQL expression for checking if symbol is hidden.
        
        Returns:
            Any: SQLAlchemy expression for use in WHERE clauses
        """
        return self.st_other.in_((defs.SymbolVisibility.STV_HIDDEN, defs.SymbolVisibility.STV_INTERNAL))

    @hybrid_property
    def weak(self) -> bool:
        """Check if symbol is weak.
        
        Returns:
            bool: True if st_bind is STB_WEAK
        """
        return self.symbol_bind() == defs.SymbolBinding.STB_WEAK

    @hybrid_property
    def absolute(self) -> bool:
        """Check if symbol is absolute (not relative to a section).
        
        Returns:
            bool: True if st_shndx is SHN_ABS
        """
        return self.st_shndx == defs.SectionName.SHN_ABS

    @hybrid_property
    def undefined(self) -> bool:
        """Check if symbol is undefined (external reference).
        
        Returns:
            bool: True if st_shndx is SHN_UNDEF
        """
        return self.st_shndx == defs.SectionName.SHN_UNDEF

    @hybrid_property
    def local(self) -> bool:
        """Check if symbol is local.
        
        Returns:
            bool: True if st_bind is STB_LOCAL
        """
        return self.symbol_bind() == defs.SymbolBinding.STB_LOCAL

    @hybrid_property
    def global_(self) -> bool:
        """Check if symbol is global.
        
        Returns:
            bool: True if st_bind is STB_GLOBAL
        """
        return self.symbol_bind() == defs.SymbolBinding.STB_GLOBAL

    @hybrid_method
    def get_access(self) -> int:
        """Get symbol access flags.
        
        Returns:
            int: Raw access flags value
        """
        return self.access

    @hybrid_method
    def test_access(self, mask: int) -> bool:
        """Test if symbol access flags match a bitmask.
        
        Args:
            mask: Bitmask to test against access flags
        
        Returns:
            bool: True if (access & mask) == mask
        """
        return self.get_access() & mask == mask

    @test_access.expression
    def test_access(self, mask: int) -> Any:
        """SQL expression for testing symbol access flags.
        
        Args:
            mask: Bitmask to test against access flags
        
        Returns:
            Any: SQLAlchemy expression for use in WHERE clauses
        """
        return self.get_access().op("&")(mask) == mask

    @hybrid_property
    def writeable(self) -> bool:
        """Check if symbol is in a writeable section.
        
        Returns:
            bool: True if SHF_WRITE flag is set in access
        """
        return self.test_access(defs.SectionFlags.SHF_WRITE)

    @hybrid_property
    def executeable(self) -> bool:
        """Check if symbol is in an executable section.
        
        Returns:
            bool: True if SHF_EXECINSTR flag is set in access
        """
        return self.test_access(defs.SectionFlags.SHF_EXECINSTR)

    @hybrid_property
    def allocate(self) -> bool:
        """Check if symbol occupies memory.
        
        Returns:
            bool: True if SHF_ALLOC flag is set in access
        """
        return self.test_access(defs.SectionFlags.SHF_ALLOC)

    @hybrid_property
    def symbol_bind(self) -> defs.SymbolBinding:
        """Get symbol binding type as enum.
        
        Returns:
            defs.SymbolBinding: Enum representing symbol binding
        """
        return defs.SymbolBinding(self.st_bind)

    @hybrid_property
    def symbol_type(self) -> defs.SymbolType:
        """Get symbol type as enum.
        
        Returns:
            defs.SymbolType: Enum representing symbol type
        """
        return defs.SymbolType(self.st_type)


class Elf_Comment(Base, RidMixIn):
    """ORM model for ELF comment section entry.
    
    Stores text comments found in ELF files (typically from .comment sections).
    
    Attributes:
        text (str): Comment text content
    """

    text = Column(types.VARCHAR)


class Elf_Note(Base, RidMixIn):
    """ORM model for ELF note entry.
    
    Notes provide extensible metadata in ELF files for vendor-specific or
    architecture-specific information (e.g., build IDs, capabilities).
    
    Attributes:
        section_name (str): Name of section containing this note (unique)
        type (int): Note type identifier
        name (str): Note name (owner/vendor identifier)
        desc (str): Note description text
    """

    section_name = Column(types.VARCHAR, unique=True)
    type = StdInteger()
    name = Column(types.VARCHAR)
    desc = Column(types.VARCHAR)


class DIEAttribute(Base, RidMixIn):
    """ORM model for DWARF Debug Information Entry (DIE) attribute.
    
    Represents a single attribute (DW_AT_*) attached to a DIE. Attributes contain
    metadata about the DIE (e.g., name, type, location, size, etc.).
    
    Stores attribute names as integer enum values for performance. The _coerce_name
    validator allows flexible input (int, enum, or string name) which is normalized
    to an integer for storage.
    
    Attributes:
        name (int): Attribute tag/name as AttributeEncoding enum value (indexed)
        form (int): Attribute form (DW_FORM_*) indicating how value is encoded (indexed)
        raw_value (str): String representation of the attribute value
        entry_id (int): Foreign key to parent DebugInformationEntry
        entry (Relationship): Relationship to parent DebugInformationEntry
    """

    # Store attribute name (DW_AT_*) as integer enum (AttributeEncoding) for performance
    name = StdInteger(index=True)
    # Form of the attribute (DW_FORM_*), stored as integer enum for later interpretation
    form = StdInteger(index=True, nullable=True)
    raw_value = Column(types.VARCHAR)
    entry_id = Column(types.Integer, ForeignKey("debuginformationentry.rid"), index=True)
    entry = relationship("DebugInformationEntry", back_populates="attributes")

    @orm.validates("name")
    def _coerce_name(self, key: str, value: Any) -> int:
        """Accept attribute name as int, enum, or string and coerce to integer.
        
        Flexible validator that normalizes different input formats (integer,
        AttributeEncoding enum instance, or string name) to integer storage format.
        
        Args:
            key: Validator key name (always "name")
            value: Input value to coerce (int, enum, or string)
        
        Returns:
            int: Integer representation of attribute name
        """
        try:
            if isinstance(value, int):
                return value
            # enum instance or int-like
            try:
                return int(value)
            except Exception:
                pass
            # string name
            from objutils.dwarf.constants import AttributeEncoding as AttrEnc

            return int(AttrEnc[str(value)])
        except Exception:
            # Leave as-is if coercion fails; SQLite will accept, and map builder will handle
            return value

    @property
    def encoding_name(self) -> str:
        """Get attribute name as string regardless of internal storage.
        
        Exposes the attribute name in human-readable string format, converting
        from integer storage if needed.
        
        Returns:
            str: String name of the attribute
        """
        try:
            from objutils.dwarf.constants import AttributeEncoding as AttrEnc
        except Exception:
            AttrEnc = None
        v = getattr(self, "name", None)
        if isinstance(v, int) and AttrEnc is not None:
            try:
                return AttrEnc(v).name
            except Exception:
                return str(v)
        # enum-like or string
        try:
            return v.name  # enum
        except Exception:
            return str(v)


class DebugInformationEntry(Base, RidMixIn):
    """ORM model for DWARF Debug Information Entry (DIE).
    
    Represents a node in the DWARF debug information tree. DIEs describe source code
    constructs (functions, variables, types, scopes, etc.) and enable source-level debugging.
    
    Supports tree traversal through parent/children relationships. Uses validators to
    accept flexible tag input formats (integer, enum, or string name).
    
    Attributes:
        tag (int): DWARF tag (DW_TAG_*) as integer enum, indexed for fast queries
        offset (int): Byte offset of this DIE within its Compilation Unit, indexed
        cu_start (int): Start offset of the Compilation Unit this DIE belongs to, indexed
        parent_id (int): Foreign key to parent DIE, enables tree traversal
        attributes (list): List of DIEAttribute objects attached to this DIE
        parent (DebugInformationEntry): Parent DIE node (self-referential)
        children (list): List of child DIE nodes (self-referential, ordered by offset)
    """

    # Store DWARF Tag as integer enum value to reduce memory and speed up queries
    tag = StdInteger(index=True)
    # Offset of this DIE within the .debug_info section (CU-relative start used by DwarfProcessor)
    offset = Column(types.Integer, index=True)
    # Start offset of the Compilation Unit this DIE belongs to; used for ref form resolution
    cu_start = Column(types.Integer, index=True, nullable=True)
    # Parent DIE linkage for building a tree
    parent_id = Column(types.Integer, ForeignKey("debuginformationentry.rid"), index=True, nullable=True)

    # Relationships
    attributes = relationship("DIEAttribute", back_populates="entry", uselist=True)
    # Self-referential relationship for DIE tree
    parent = relationship(
        "DebugInformationEntry",
        remote_side=lambda: DebugInformationEntry.rid,
        back_populates="children",
        uselist=False,
        foreign_keys=[parent_id],
    )
    children = relationship(
        "DebugInformationEntry",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id],
        order_by="DebugInformationEntry.offset",
    )

    @orm.validates("tag")
    def _coerce_tag(self, key: str, value: Any) -> int:
        """Accept tag as int, enum, or string name and coerce to integer.
        
        Flexible validator that normalizes different input formats (integer,
        DWARF Tag enum instance, or string name) to integer storage format.
        
        Args:
            key: Validator key name (always "tag")
            value: Input value to coerce (int, enum, or string)
        
        Returns:
            int: Integer representation of DWARF tag
        """
        try:
            if isinstance(value, int):
                return value
            # enum instance or int-like
            try:
                return int(value)
            except Exception:
                pass
            # string name
            from objutils.dwarf.constants import Tag as DwarfTag

            return int(DwarfTag[str(value)])
        except Exception:
            # Leave as-is if coercion fails; SQLite will accept, and abbrev mapping will handle
            return value

    @property
    def abbrev(self) -> Any:
        """Get abbreviated representation of DIE tag for convenience.
        
        Returns a simple object with a tag property containing the string tag name,
        even though the database stores the tag as an integer. Enables convenient
        access to tag name without manual enum conversion.
        
        Returns:
            Any: Object with __str__/__repr__ returning Tag(name) format
        """

        class _Abbrev:
            """Abbreviated DIE tag wrapper exposing string tag name."""

            def __init__(self, tag_value: Any) -> None:
                """Initialize abbrev with tag value and convert to string name.
                
                Args:
                    tag_value: Integer, enum, or string tag value
                """
                # Expose string tag name for consumer code even though DB stores int
                try:
                    from objutils.dwarf.constants import Tag as DwarfTag
                except Exception:
                    DwarfTag = None
                if isinstance(tag_value, int) and DwarfTag is not None:
                    try:
                        self.tag = DwarfTag(tag_value).name
                    except Exception:
                        self.tag = str(tag_value)
                else:
                    # already a string or enum-like; best effort string
                    try:
                        self.tag = tag_value.name  # enum
                    except Exception:
                        self.tag = str(tag_value)

            def __str__(self) -> str:
                """Return string representation of tag.
                
                Returns:
                    str: Tag name in format "Tag(tagname)"
                """
                return f"Tag({self.tag})"

            __repr__ = __str__

        return _Abbrev(self.tag)

    @property
    def attributes_map(self) -> Dict[str, "DIEAttribute"]:
        """Get attributes as a dictionary keyed by attribute name.
        
        Lazily builds and caches a mapping of attribute names to DIEAttribute
        objects for convenient access by attribute name rather than iteration.
        
        Returns:
            Dict[str, DIEAttribute]: Dictionary mapping attribute names to their objects
        """
        cache = getattr(self, "_attributes_map_cache", None)
        if cache is None:

            def _attr_key(a: "DIEAttribute") -> str:
                """Normalize attribute key to string even if stored as integer enum.
                
                Args:
                    a: DIEAttribute object
                
                Returns:
                    str: Attribute name as string
                """
                # Normalize attribute key to string even if stored as integer enum
                try:
                    return a.encoding_name
                except Exception:
                    v = getattr(a, "name", None)
                    try:
                        return v.name  # enum-like
                    except Exception:
                        return str(v)

            cache = {_attr_key(attr): attr for attr in (self.attributes or [])}
            setattr(self, "_attributes_map_cache", cache)
        return cache

    def get_attribute(self, name: str) -> Optional["DIEAttribute"]:
        """Get a specific attribute by name.
        
        Args:
            name: Attribute name string (e.g., "DW_AT_name")
        
        Returns:
            Optional[DIEAttribute]: The attribute object, or None if not found
        """
        return self.attributes_map.get(name)


class DebugInformation(Base, RidMixIn):
    """ORM model for DWARF debug information collection.
    
    Container table for organizing DWARF debugging information. Currently serves
    as a placeholder for future expansion of debug metadata storage.
    """

    pass


class CompilationUnit(Base, RidMixIn):
    """ORM model for DWARF Compilation Unit (CU).
    
    Represents a compilation unit (single translation unit) within debug information.
    Currently serves as a placeholder for future expansion of CU-level metadata.
    """

    pass


def calculateCacheSize(value: int) -> int:
    """Convert cache size in bytes to SQLite PRAGMA format.
    
    SQLite PRAGMA CACHE_SIZE accepts negative values representing number of pages.
    This function converts a byte size to the appropriate negative page count.
    
    Args:
        value: Cache size in bytes
    
    Returns:
        int: Negative page count for PRAGMA CACHE_SIZE
    """
    return -(value // PAGE_SIZE)


REGEX_CACHE: Dict[str, Any] = {}


def regexer(value: Optional[str], expr: Optional[str]) -> int:
    """SQLite-compatible regex function for pattern matching.
    
    Used with SQLite's CREATE_FUNCTION to enable REGEXP operators in SQL queries.
    Caches compiled regex patterns for performance.
    
    Args:
        value: String to search (may be None)
        expr: Regex pattern to match (may be None)
    
    Returns:
        int: 1 if pattern matches, 0 otherwise
    """
    if value is None or expr is None:
        return 0
    pattern = REGEX_CACHE.get(expr)
    if pattern is None:
        pattern = re.compile(expr, re.UNICODE)
        REGEX_CACHE[expr] = pattern
    return 1 if pattern.search(value) else 0


@event.listens_for(Engine, "connect")
def set_sqlite3_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
    """Configure SQLite pragmas for optimal ELF database performance.
    
    Called automatically when SQLAlchemy connects to the SQLite database.
    Configures memory management, foreign keys, synchronization, and locking.
    
    Args:
        dbapi_connection: SQLite connection object
        connection_record: SQLAlchemy connection record
    
    Pragmas configured:
        - FOREIGN_KEYS: Enable referential integrity constraints
        - PAGE_SIZE: Match system page size for efficient I/O
        - CACHE_SIZE: Tune memory usage
        - SYNCHRONOUS: Disable disk sync for speed (assumes reliable filesystem)
        - LOCKING_MODE: Use exclusive locking for consistency
        - TEMP_STORE: Keep temporary data in memory
    """
    dbapi_connection.create_function("REGEXP", 2, regexer)
    cursor = dbapi_connection.cursor()
    # cursor.execute("PRAGMA jornal_mode=WAL")
    cursor.execute("PRAGMA FOREIGN_KEYS=ON")
    cursor.execute(f"PRAGMA PAGE_SIZE={PAGE_SIZE}")
    cursor.execute(f"PRAGMA CACHE_SIZE={calculateCacheSize(CACHE_SIZE * 1024 * 1024)}")
    cursor.execute("PRAGMA SYNCHRONOUS=OFF")  # FULL
    cursor.execute("PRAGMA LOCKING_MODE=EXCLUSIVE")  # NORMAL
    cursor.execute("PRAGMA TEMP_STORE=MEMORY")  # FILE
    cursor.close()


class Model:
    """Main database interface for ELF ORM operations.
    
    Manages SQLAlchemy engine, session, and database schema. Handles automatic
    database creation with .prgdb extension, schema initialization, and backward
    compatibility migrations.
    
    The Model class provides the primary interface for:
    - Creating/opening ELF analysis databases
    - Accessing ORM session for queries
    - Managing schema initialization and migration
    
    Example:
        >>> db = Model("firmware.elf.prgdb", debug=False)
        >>> header = db.session.query(Elf_Header).first()
        >>> sections = db.session.query(Elf_Section).all()
        >>> db.close()
    
    Attributes:
        dbname (str): Database file path (":memory:" or file path)
        _engine (Engine): SQLAlchemy engine
        _session (Session): SQLAlchemy session
        _metadata (Metadata): SQLAlchemy metadata
    """

    def __init__(self, filename: str = ":memory:", debug: bool = False) -> None:
        """Initialize ELF database model and create tables.
        
        Creates SQLite database file and initializes all ORM tables. Automatically
        runs schema migration for older databases to ensure compatibility.
        
        Args:
            filename: Database file path or ":memory:" (default: ":memory:")
                     File extension .prgdb is optional
            debug: Enable SQLAlchemy echo for SQL debugging (default: False)
        """
        if filename == ":memory:" or not filename:
            self.dbname = ":memory:"
        else:
            # if not filename.lower().endswith(DB_EXTENSION):
            #    self.dbname = f"{filename}.{DB_EXTENSION}"
            # else:
            self.dbname = filename

        self._engine = create_engine(
            f"sqlite:///{self.dbname}",
            echo=debug,
            connect_args={"detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES},
            native_datetime=True,
        )

        self._session = orm.Session(self._engine, autoflush=True, autocommit=False)

        self._metadata = Base.metadata
        Base.metadata.create_all(self.engine)
        # Ensure schema upgrades for older databases opened directly via Model
        self._ensure_schema()
        self.session.flush()
        self.session.commit()

    def _ensure_schema(self) -> None:
        """Ensure required columns and indexes exist for older databases.
        
        Adds missing columns and creates indexes with minimal changes without
        rebuilding the database. Uses ALTER TABLE and CREATE INDEX IF NOT EXISTS
        statements for safe, non-destructive schema migration.
        
        This method handles backward compatibility for databases created by
        older versions of objutils that lacked certain columns or indexes.
        
        Silently continues if inspection or ALTER operations fail, leaving
        the database in its existing state if migration is not possible.
        """
        try:
            from sqlalchemy import inspect as sa_inspect

            inspector = sa_inspect(self.engine)
            # Ensure debuginformationentry columns exist
            try:
                die_cols = {c["name"] for c in inspector.get_columns("debuginformationentry")}
            except Exception:
                die_cols = set()
            # Ensure dieattribute columns exist
            try:
                dia_cols = {c["name"] for c in inspector.get_columns("dieattribute")}
            except Exception:
                dia_cols = set()
            with self.engine.begin() as conn:
                # --- Columns ---
                if "offset" not in die_cols:
                    conn.execute(text('ALTER TABLE debuginformationentry ADD COLUMN "offset" INTEGER'))
                if "parent_id" not in die_cols:
                    conn.execute(text('ALTER TABLE debuginformationentry ADD COLUMN "parent_id" INTEGER'))
                if "cu_start" not in die_cols:
                    conn.execute(text('ALTER TABLE debuginformationentry ADD COLUMN "cu_start" INTEGER'))
                if "form" not in dia_cols:
                    conn.execute(text('ALTER TABLE dieattribute ADD COLUMN "form" INTEGER'))

                # --- Indexes ---
                try:
                    die_indexes = {i.get("name") for i in inspector.get_indexes("debuginformationentry")}
                except Exception:
                    die_indexes = set()
                try:
                    dia_indexes = {i.get("name") for i in inspector.get_indexes("dieattribute")}
                except Exception:
                    dia_indexes = set()

                # Critical for traversal speed: lookups by DIE.offset
                if "idx_die_offset" not in die_indexes:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_die_offset ON debuginformationentry ("offset")'))
                # Helpful for reference resolution across CUs
                if "idx_die_cu_start" not in die_indexes and "cu_start" in die_cols:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_die_cu_start ON debuginformationentry ("cu_start")'))
                # Helpful for parent/child traversal
                if "idx_die_parent_id" not in die_indexes and "parent_id" in die_cols:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_die_parent_id ON debuginformationentry ("parent_id")'))
                # Attribute-side foreign key lookups (speed attributes_map building)
                if "idx_dia_entry_id" not in dia_indexes:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_dia_entry_id ON dieattribute ("entry_id")'))
                # Optional filters by attribute name/form
                if "idx_dia_name" not in dia_indexes:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_dia_name ON dieattribute ("name")'))
                if "idx_dia_form" not in dia_indexes and "form" in dia_cols:
                    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_dia_form ON dieattribute ("form")'))
        except Exception:
            # Be permissive: if inspection or ALTER fails, leave as-is.
            pass

    def close(self) -> None:
        """Close database connection and dispose of engine.
        
        Closes the SQLAlchemy session and disposes of the engine, releasing
        all database connections and resources.
        """
        self.session.close()
        self._engine.dispose()

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine.
        
        Returns:
            Engine: SQLAlchemy database engine
        """
        return self._engine

    @property
    def session(self) -> Session:
        """Get the SQLAlchemy session.
        
        Returns:
            Session: SQLAlchemy ORM session for queries and operations
        """
        return self._session

    @property
    def metadata(self) -> Any:
        """Get the SQLAlchemy metadata.
        
        Returns:
            Any: SQLAlchemy metadata containing table definitions
        """
        return self._metadata
