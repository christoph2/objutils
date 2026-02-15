"""SQLAlchemy ORM models for PE/COFF data storage.

This module defines the database schema for storing parsed PE/COFF file information.
Uses SQLAlchemy ORM with SQLite backend for efficient querying and analysis.

Architecture:
    The ORM layer provides structured storage for PE file components:

    ```
    Model (Database)
      ├── Pe_Header (File metadata)
      │     ├── machine (CPU architecture)
      │     ├── number_of_sections
      │     ├── characteristics (flags)
      │     └── image_base, alignments
      │
      ├── Pe_Section (Code/data sections)
      │     ├── name (.text, .data, .rdata, etc.)
      │     ├── vaddr/vsize (virtual memory)
      │     ├── file_offset/size (file layout)
      │     └── characteristics (permissions)
      │
      └── Pe_Symbol (Symbol table)
            ├── name (function/variable name)
            ├── value (address/offset)
            ├── section_number
            └── storage_class (external/static)
    ```

Usage Example:
    ```python
    from objutils.pecoff.model import Model, Pe_Header, Pe_Section

    # Create in-memory database
    model = Model(":memory:")

    # Access database session
    with model.session() as session:
        # Query header
        header = session.query(Pe_Header).first()
        print(f"Machine: {header.machine}")
        print(f"Sections: {header.number_of_sections}")

        # Query sections
        sections = session.query(Pe_Section).all()
        for section in sections:
            print(f"{section.name}: {section.vsize} bytes @ {section.vaddr:#x}")

        # Find specific section
        text_section = session.query(Pe_Section).filter_by(name=".text").first()
        if text_section:
            print(f"Code section: {text_section.characteristics:#x}")

    model.close()
    ```

Integration with Parser:
    The PeParser class (from objutils.pecoff) populates these models:

    ```python
    from objutils.pecoff import PeParser

    # Parser automatically creates and populates database
    pe = PeParser("app.exe", verbose=False)

    # Access parsed data via ORM
    with pe.session as session:
        header = session.query(Pe_Header).first()
        # ... query as needed
    ```

Performance Optimizations:
    SQLite is configured with WAL (Write-Ahead Logging) mode and
    memory-based temporary storage for fast parsing of large PE files.

See Also:
    - objutils.pecoff: Main PE parser that uses these models
    - objutils.pecoff.defs: Constants for characteristics/flags
    - objutils.elf.model: Similar ORM structure for ELF files
"""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import Column, Integer, Numeric, String, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


Base = declarative_base()


def StdInteger(default=0, primary_key=False, unique=False, nullable=False, index=False):
    """Create standard integer column with common defaults.

    Helper function to reduce boilerplate when defining integer columns
    with consistent settings.

    Args:
        default: Default value for column (default: 0)
        primary_key: Whether column is primary key (default: False)
        unique: Whether column must be unique (default: False)
        nullable: Whether column can be NULL (default: False)
        index: Whether to create index on column (default: False)

    Returns:
        SQLAlchemy Column instance configured with specified options

    Example:
        ```python
        class MyModel(Base):
            id = StdInteger(primary_key=True)
            count = StdInteger(default=0, index=True)
        ```
    """
    return Column(Integer, primary_key=primary_key, unique=unique, nullable=nullable, index=index, default=default)


class MixInBase:
    """Base mixin providing common ORM functionality.

    Provides automatic table naming and string representation for all
    model classes.
    """

    @property
    def __tablename__(self) -> str:  # type: ignore[override]
        """Generate table name from class name.

        Returns:
            Lowercase class name as table name
        """
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Generate readable string representation.

        Returns:
            String like "ClassName(attr1=value1, attr2=value2)"
        """
        s = self.__class__.__name__ + "("
        s += ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__dict__ if not k.startswith("_"))
        s += ")"
        return s


class RidMixIn(MixInBase):
    """Mixin adding auto-increment primary key 'rid'.

    All PE models use this mixin to get a unique row identifier.
    """

    rid = StdInteger(primary_key=True)


class Pe_Header(Base, RidMixIn):
    """PE/COFF file header information.

    Stores metadata about the executable/DLL: target architecture,
    number of sections, timestamps, and file characteristics.

    Attributes:
        rid: Auto-increment primary key
        machine: CPU architecture (IMAGE_FILE_MACHINE_* constant)
        number_of_sections: Count of sections in file
        time_date_stamp: Unix timestamp of file creation
        characteristics: Bit flags (use defs.decode_characteristics())
        image_base: Preferred load address in memory
        section_alignment: Memory alignment for sections (typically 4KB)
        file_alignment: File offset alignment (typically 512 bytes)

    Example:
        ```python
        header = session.query(Pe_Header).first()
        if header.machine == defs.IMAGE_FILE_MACHINE_AMD64:
            print("64-bit x86 executable")
        print(f"Load address: {header.image_base:#x}")
        ```
    """

    __tablename__ = "pe_header"
    machine = StdInteger()
    number_of_sections = StdInteger()
    time_date_stamp = StdInteger()
    characteristics = StdInteger()
    image_base = Numeric()
    section_alignment = StdInteger()
    file_alignment = StdInteger()


class Pe_Section(Base, RidMixIn):
    """PE section (code/data region) information.

    Each section represents a contiguous memory region with specific
    permissions and content type (.text for code, .data for data, etc.).

    Attributes:
        rid: Auto-increment primary key
        name: Section name (max 8 chars, e.g., ".text", ".data", ".rdata")
        vaddr: Virtual address (where section loads in memory)
        vsize: Virtual size (size in memory, may be > file size)
        file_offset: Offset in PE file where section data starts
        size: Size of section data in file
        characteristics: Bit flags (permissions, content type)

    Common Sections:
        - .text: Executable code (IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ)
        - .data: Initialized writable data
        - .rdata: Read-only data (constants, strings)
        - .bss: Uninitialized data (not in file)
        - .rsrc: Resources (icons, dialogs, etc.)

    Example:
        ```python
        # Find executable code section
        text = session.query(Pe_Section).filter_by(name=".text").first()
        print(f"Code: {text.vsize} bytes @ {text.vaddr:#x}")

        # Check if section is writable
        if text.characteristics & defs.IMAGE_SCN_MEM_WRITE:
            print("WARNING: Code section is writable!")
        ```
    """

    __tablename__ = "pe_sections"
    name = Column(String(256), index=True)
    vaddr = StdInteger()
    vsize = StdInteger()
    file_offset = StdInteger()
    size = StdInteger()
    characteristics = StdInteger()


class Pe_Symbol(Base, RidMixIn):
    """PE symbol table entry (function/variable).

    Stores information about exported functions, imported functions,
    and internal symbols from the COFF symbol table or PDB debug info.

    Attributes:
        rid: Auto-increment primary key
        name: Symbol name (function/variable identifier)
        value: Address or offset (interpretation depends on section)
        section_number: Section index (1-based) or special value
        type: Symbol type (function, data, etc.)
        storage_class: External (exported) or static (internal)

    Note:
        Most PE files have stripped symbol tables. Use PDB files
        for comprehensive symbol information.

    Example:
        ```python
        # Find exported functions
        exports = session.query(Pe_Symbol).filter(
            Pe_Symbol.storage_class == defs.IMAGE_SYM_CLASS_EXTERNAL
        ).all()

        for symbol in exports:
            print(f"{symbol.name} @ {symbol.value:#x}")
        ```
    """

    __tablename__ = "pe_symbols"
    name = Column(String(512), index=True)
    value = StdInteger()
    section_number = StdInteger()
    type = StdInteger()
    storage_class = StdInteger()


def set_sqlite3_pragmas(dbapi_connection, connection_record):
    """Configure SQLite for optimal performance.

    Sets pragmas to improve parsing speed:
    - Disable synchronous writes (faster, less safe)
    - Enable WAL (Write-Ahead Logging) mode
    - Large cache size for better performance
    - Memory-based temporary storage

    Args:
        dbapi_connection: SQLite database connection
        connection_record: SQLAlchemy connection record (unused)

    Note:
        These settings prioritize speed over durability. Acceptable for
        parsing (read-only after initial load), but use with caution for
        write-heavy applications.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA synchronous = OFF")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA cache_size = 100000")
        cursor.execute("PRAGMA temp_store = MEMORY")
    finally:
        cursor.close()


class Model:
    """Database model manager for PE/COFF data.

    Creates and manages SQLite database with PE tables. Provides
    session context manager for queries.

    Attributes:
        _engine: SQLAlchemy engine
        _Session: Session factory

    Example:
        ```python
        # In-memory database (discarded when closed)
        model = Model(":memory:")

        # Persistent database file
        model = Model("analysis.db")

        # Query data
        with model.session() as session:
            headers = session.query(Pe_Header).all()
            # ... perform queries

        # Clean up
        model.close()
        ```
    """

    def __init__(self, filename: str = ":memory:", debug: bool = False):
        """Initialize database with PE schema.

        Args:
            filename: Database file path or ":memory:" for in-memory DB
            debug: Enable SQL query logging (default: False)
        """
        self._engine = create_engine(f"sqlite:///{filename}", echo=debug)

        # sqlite pragmas
        event.listen(self._engine, "connect", set_sqlite3_pragmas)  # type: ignore[arg-type]

        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def close(self):
        """Close database and release resources.

        Should be called when done using the database to ensure
        proper cleanup.
        """
        self._engine.dispose()

    def engine(self) -> Engine:
        """Get SQLAlchemy engine for advanced use cases.

        Returns:
            SQLAlchemy Engine instance
        """
        return self._engine

    @contextmanager
    def session(self) -> Session:
        """Context manager for database sessions.

        Yields:
            SQLAlchemy Session for queries

        Example:
            ```python
            with model.session() as session:
                result = session.query(Pe_Header).first()
            # Session automatically closed
            ```
        """
        ses = self._Session()
        try:
            yield ses
        finally:
            ses.close()
