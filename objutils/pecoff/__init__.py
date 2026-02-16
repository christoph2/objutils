"""PE/COFF file parser for Windows executables and object files.

This module provides parsing and analysis of Portable Executable (PE) and
Common Object File Format (COFF) files, including Windows executables (.exe),
dynamic libraries (.dll), and object files (.obj).

Overview:
    The PE/COFF parser extracts:

    - **Headers**: DOS stub, COFF header, Optional header (PE32/PE32+)
    - **Sections**: Code (.text), data (.data), resources (.rsrc), etc.
    - **Symbols**: From COFF symbol table or PDB debug info
    - **Image creation**: Convert sections to objutils.Image for analysis

    ```
    PE File Structure:
    ┌──────────────────┐
    │ DOS Stub (MZ)    │  ← Legacy DOS compatibility
    ├──────────────────┤
    │ PE Signature     │  ← "PE\0\0" magic
    ├──────────────────┤
    │ COFF Header      │  ← Machine type, section count, characteristics
    ├──────────────────┤
    │ Optional Header  │  ← Entry point, image base, alignments
    │  PE32 / PE32+    │    (32-bit or 64-bit variant)
    ├──────────────────┤
    │ Section Headers  │  ← .text, .data, .rdata, .rsrc, etc.
    ├──────────────────┤
    │ Section Data     │
    │  .text (code)    │
    │  .data (data)    │
    │  .rsrc (res)     │
    │  ...             │
    └──────────────────┘
    ```

Architecture:
    **Two-Phase Parsing**:
    1. Validation: Check DOS/PE signatures
    2. Parsing: Extract headers, sections, symbols

    **Memory-Mapped I/O**: For efficient access to large PE files

    **SQLAlchemy Integration**: Optional database storage via model.Model

    **PDB Support**: Automatic debug symbol loading (Windows only)

Usage Examples:
    **Basic Parsing**:
    ```python
    from objutils.pecoff import PeParser

    # Parse Windows executable
    pe = PeParser("C:\\Windows\\System32\\kernel32.dll")

    # Access headers
    print(f"Machine: {pe.machine():#x}")
    print(f"Image base: {pe.image_base():#x}")
    print(f"Sections: {len(pe.sections)}")
    print(f"Symbols: {len(pe.symbols)}")

    # Enumerate sections
    for section in pe.sections:
        print(f"{section['name']:8s} @ {section['virtual_address']:#010x}")

    pe.close()
    ```

    **Image Creation**:
    ```python
    # Convert PE sections to objutils.Image
    img = pe.create_image(
        add_image_base=True,  # Use absolute addresses
        include_pattern=".text"  # Only code section
    )

    # Access binary data
    code = img.read(0x401000, 100)  # Read 100 bytes at address
    ```

    **With PDB Symbols**:
    ```python
    # Parse with PDB debug symbols (Windows only)
    pe = PeParser("app.exe", pdb_path=[".", "C:\\Symbols"])

    # Symbols now include PDB data if found
    for sym in pe.symbols:
        print(f"{sym['name']}: {sym['value']:#x}")
    ```

PE32 vs PE32+:
    The parser automatically detects 32-bit vs 64-bit executables:

    - **PE32** (32-bit): Magic 0x10B, 32-bit image_base
    - **PE32+** (64-bit): Magic 0x20B, 64-bit image_base

    Key differences:
    - Image base size: 4 bytes vs 8 bytes
    - Pointer size: 32-bit vs 64-bit
    - Base of data field: Present in PE32 only

Construct Structures:
    Binary parsing uses the `construct` library with these structures:

    - **CoffHeader**: Machine, section count, timestamp, characteristics
    - **OptionalHeaderPe32**: 32-bit entry point, image base, alignments
    - **OptionalHeaderPe32Plus**: 64-bit variant
    - **SectionHeader**: Section metadata (name, RVA, size, characteristics)
    - **CoffSymbol**: Symbol table entries

Integration:
    **With objutils.Image**:
    ```python
    img = pe.create_image()
    objutils.dump("ihex", "firmware.hex", img)
    ```

    **With ORM models**:
    ```python
    pe.create_db_on_demand()
    with pe.db.session() as session:
        header = session.query(model.Pe_Header).first()
        sections = session.query(model.Pe_Section).all()
    ```

Limitations:
    - PDB support requires Windows with dbghelp.dll
    - COFF symbol table often stripped in release builds
    - Data directories (imports/exports) not fully parsed
    - Relocations not processed

See Also:
    - objutils.pecoff.defs: Constants and characteristics flags
    - objutils.pecoff.model: SQLAlchemy ORM models
    - objutils.pecoff.pdb: PDB debug symbol integration
    - objutils.elf: Similar parser for ELF files
"""

import io
import os
import typing
from pathlib import Path

from construct import Bytes, Int8ul, Int16ul, Int32ul, Int64ul, Struct

from objutils import Image, Section
from objutils.utils import create_memorymapped_fileview

from . import defs, model


try:
    from .pdb import pdb_symbols_for_pe  # type: ignore
except Exception:  # pragma: no cover
    pdb_symbols_for_pe = None  # type: ignore[assignment]


# ================================ Construct Structures ================================

# ================================ Construct Structures ================================

CoffHeader = Struct(
    "machine" / Int16ul,  # CPU architecture (defs.IMAGE_FILE_MACHINE_*)
    "number_of_sections" / Int16ul,  # Count of section headers
    "time_date_stamp" / Int32ul,  # Unix timestamp of file creation
    "pointer_to_symbol_table" / Int32ul,  # File offset to COFF symbol table (often 0)
    "number_of_symbols" / Int32ul,  # Count of symbols (often 0 in release builds)
    "size_of_optional_header" / Int16ul,  # Size of optional header (0 for .obj files)
    "characteristics" / Int16ul,  # File characteristics (defs.IMAGE_FILE_*)
)

OptionalHeaderPe32 = Struct(
    "magic" / Int16ul,  # 0x10B (PE32 = 32-bit)
    "major_linker_version" / Int8ul,  # Linker version
    "minor_linker_version" / Int8ul,
    "size_of_code" / Int32ul,  # Sum of all code section sizes
    "size_of_initialized_data" / Int32ul,  # Sum of initialized data sections
    "size_of_uninitialized_data" / Int32ul,  # Sum of .bss sections
    "address_of_entry_point" / Int32ul,  # RVA of entry point function
    "base_of_code" / Int32ul,  # RVA of code section start
    "base_of_data" / Int32ul,  # RVA of data section start (PE32 only)
    "image_base" / Int32ul,  # Preferred load address (32-bit)
    "section_alignment" / Int32ul,  # Section alignment in memory (typically 4KB)
    "file_alignment" / Int32ul,  # Section alignment in file (typically 512B)
)

OptionalHeaderPe32Plus = Struct(
    "magic" / Int16ul,  # 0x20B (PE32+ = 64-bit)
    "major_linker_version" / Int8ul,  # Linker version
    "minor_linker_version" / Int8ul,
    "size_of_code" / Int32ul,  # Sum of all code section sizes
    "size_of_initialized_data" / Int32ul,  # Sum of initialized data sections
    "size_of_uninitialized_data" / Int32ul,  # Sum of .bss sections
    "address_of_entry_point" / Int32ul,  # RVA of entry point function
    "base_of_code" / Int32ul,  # RVA of code section start
    "image_base" / Int64ul,  # Preferred load address (64-bit)
    "section_alignment" / Int32ul,  # Section alignment in memory (typically 4KB)
    "file_alignment" / Int32ul,  # Section alignment in file (typically 512B)
)

SectionHeader = Struct(
    "name_raw" / Bytes(8),  # Section name (null-padded, max 8 chars)
    "virtual_size" / Int32ul,  # Size in memory (may be > file size)
    "virtual_address" / Int32ul,  # RVA where section loads
    "size_of_raw_data" / Int32ul,  # Size of section data in file
    "pointer_to_raw_data" / Int32ul,  # File offset to section data
    "pointer_to_relocations" / Int32ul,  # File offset to relocations (object files)
    "pointer_to_linenumbers" / Int32ul,  # File offset to line numbers (deprecated)
    "number_of_relocations" / Int16ul,  # Count of relocations (object files)
    "number_of_linenumbers" / Int16ul,  # Count of line numbers (deprecated)
    "characteristics" / Int32ul,  # Section flags (defs.IMAGE_SCN_*)
)

CoffSymbol = Struct(
    "name_raw" / Bytes(8),  # Symbol name or string table offset
    "value" / Int32ul,  # Address or offset value
    "section_number" / Int16ul,  # Section index (1-based) or special value
    "type" / Int16ul,  # Symbol type (function, data, etc.)
    "storage_class" / Int8ul,  # Storage class (external, static, etc.)
    "number_of_aux_symbols" / Int8ul,  # Count of auxiliary symbol records
)


class PeParser:
    """Parser for PE/COFF executables and object files.

    Parses Windows Portable Executable (PE) and Common Object File Format (COFF)
    files, extracting headers, sections, and symbols. Provides convenient API
    for converting sections to objutils.Image format.

    The parser supports:
    - PE32 (32-bit) and PE32+ (64-bit) executables
    - Windows .exe and .dll files
    - COFF .obj object files
    - PDB debug symbol integration (Windows only)

    Attributes:
        dos_header: DOS header dictionary (e_lfanew offset)
        coff_header: COFF header dictionary (machine, sections, characteristics)
        optional_header: Optional header dictionary (image_base, entry_point, alignments)
        sections: List of section dictionaries (name, vaddr, size, characteristics)
        symbols: List of symbol dictionaries (name, value, section, type)
        db: Optional SQLAlchemy database model for querying

    Example:
        ```python
        # Parse executable
        pe = PeParser("app.exe")

        # Access headers
        print(f"Machine: {pe.machine():#x}")
        print(f"Image base: {pe.image_base():#x}")

        # Create image from sections
        img = pe.create_image(include_pattern=".text")

        # Clean up
        pe.close()
        ```

    Note:
        The parser uses memory-mapped I/O for efficient access to large files.
        Always call close() when done to release resources.
    """

    def __init__(self, filename: str | os.PathLike, *, pdb_path: list[str | os.PathLike] | None = None):
        """Initialize parser and parse PE/COFF file.

        Opens the file, validates PE/COFF signatures, and parses headers,
        sections, and symbols. Automatically attempts to load PDB symbols
        if COFF symbol table is empty.

        Args:
            filename: Path to PE/COFF file (.exe, .dll, .obj)
            pdb_path: Optional list of directories to search for PDB files
                     (Windows only, requires dbghelp.dll)

        Raises:
            ValueError: If file is not a valid PE/COFF file (missing MZ or PE signatures)
            FileNotFoundError: If file does not exist

        Example:
            ```python
            # Basic parsing
            pe = PeParser("kernel32.dll")

            # With PDB symbol search paths
            pe = PeParser("app.exe", pdb_path=[".", "C:\\Symbols"])
            ```
        """
        self._path = Path(filename)
        self._pdb_path = pdb_path or []
        self._mm = None
        self._f = None

        # Parsed structures
        self.dos_header: dict[str, int] | None = None
        self.coff_header: dict[str, int] | None = None
        self.optional_header: dict[str, int] | None = None
        self.sections: list[dict[str, typing.Any]] = []
        self.symbols: list[dict[str, typing.Any]] = []

        # DB model
        self.db: model.Model | None = None

        self._open_and_parse()

    # ----------------------------- File Handling -----------------------------
    def _open_and_parse(self) -> None:
        """Open file with memory-mapping and trigger parsing."""
        self._mm = create_memorymapped_fileview(self._path)
        self._f = io.BytesIO(self._mm)
        self._parse()

    def close(self) -> None:
        """Close file and release memory-mapped resources.

        Should be called when done with the parser to ensure proper cleanup.

        Example:
            ```python
            pe = PeParser("app.exe")
            try:
                # Use parser
                img = pe.create_image()
            finally:
                pe.close()
            ```
        """
        try:
            if self._f:
                self._f.close()
        finally:
            self._f = None
            self._mm = None

    # -------------------------------- Parsing --------------------------------
    def _parse(self) -> None:
        """Parse PE/COFF file structure.

        Validates signatures and extracts:
        1. DOS header (MZ signature, PE offset)
        2. PE signature (PE\0\0)
        3. COFF header (machine, sections, characteristics)
        4. Optional header (PE32/PE32+, image_base, entry_point)
        5. Section headers (name, RVA, size, characteristics)
        6. COFF symbol table (if present)
        7. PDB symbols (if COFF symbols absent and PDB available)

        Raises:
            ValueError: If DOS or PE signatures are invalid
        """
        f = self._f
        assert f is not None

        # DOS header
        f.seek(0)
        mz = f.read(2)
        if mz != b"MZ":
            raise ValueError("Not a PE/COFF file: missing MZ header")
        f.seek(0x3C)
        e_lfanew = Int32ul.parse_stream(f)
        self.dos_header = {"e_lfanew": e_lfanew}

        # PE signature
        f.seek(e_lfanew)
        sig = f.read(4)
        if sig != defs.PE_SIGNATURE:
            raise ValueError("Not a PE/COFF file: missing PE\0\0 signature")

        # COFF header
        coff_hdr = CoffHeader.parse_stream(f)
        self.coff_header = {
            "machine": coff_hdr.machine,
            "number_of_sections": coff_hdr.number_of_sections,
            "time_date_stamp": coff_hdr.time_date_stamp,
            "pointer_to_symbol_table": coff_hdr.pointer_to_symbol_table,
            "number_of_symbols": coff_hdr.number_of_symbols,
            "size_of_optional_header": coff_hdr.size_of_optional_header,
            "characteristics": coff_hdr.characteristics,
        }
        number_of_sections = coff_hdr.number_of_sections
        size_of_optional_header = coff_hdr.size_of_optional_header

        # Optional header (PE32 or PE32+)
        self.optional_header = {}
        if size_of_optional_header:
            start = f.tell()
            magic = Int16ul.parse_stream(f)
            is_pe32_plus = magic == defs.OPTIONAL_HDR_MAGIC_PE32_PLUS
            is_pe32 = magic == defs.OPTIONAL_HDR_MAGIC_PE32
            if not (is_pe32 or is_pe32_plus):
                # Uncommon but possible: COFF only (e.g., .obj)
                f.seek(start)
            else:
                # We'll parse only fields relevant for image mapping
                f.seek(start)
                if is_pe32:
                    hdr = OptionalHeaderPe32.parse_stream(f)
                    self.optional_header.update(
                        {
                            "magic": hdr.magic,
                            "image_base": hdr.image_base,
                            "section_alignment": hdr.section_alignment,
                            "file_alignment": hdr.file_alignment,
                            "address_of_entry_point": hdr.address_of_entry_point,
                        }
                    )
                else:  # PE32+
                    hdr = OptionalHeaderPe32Plus.parse_stream(f)
                    self.optional_header.update(
                        {
                            "magic": hdr.magic,
                            "image_base": hdr.image_base,
                            "section_alignment": hdr.section_alignment,
                            "file_alignment": hdr.file_alignment,
                            "address_of_entry_point": hdr.address_of_entry_point,
                        }
                    )

            # Jump to end of optional header exactly
            f.seek(start + size_of_optional_header)

        # Section table
        self.sections = []
        for i in range(number_of_sections):
            section_hdr = SectionHeader.parse_stream(f)
            # name may be slash + offset into string table for long names in OBJ; in PE, usually inline
            name = section_hdr.name_raw.rstrip(b"\x00").decode("latin1", errors="ignore")
            self.sections.append(
                {
                    "name": name,
                    "virtual_size": section_hdr.virtual_size,
                    "virtual_address": section_hdr.virtual_address,
                    "size_of_raw_data": section_hdr.size_of_raw_data,
                    "pointer_to_raw_data": section_hdr.pointer_to_raw_data,
                    "characteristics": section_hdr.characteristics,
                }
            )

        # Symbols (COFF symbol table) if present
        self.symbols = []
        if self.coff_header["pointer_to_symbol_table"] and self.coff_header["number_of_symbols"]:
            self._parse_coff_symbols()
        # If no COFF symbols, try PDB symbols via dbghelp (best effort)
        if not self.symbols and pdb_symbols_for_pe:
            try:
                # pdb_file = str(self._pdb_path) if self._pdb_path else str(self._path)
                # self.symbols = pdb_symbols_for_pe(pdb_file)  # type: ignore[misc]
                self.symbols = pdb_symbols_for_pe(self._path, self._pdb_path)  # type: ignore[misc]
            except Exception as e:
                # Best-effort only; ignore if PDB not available
                print(f"Failed to retrieve PDB symbols: {e}")

    def _parse_coff_symbols(self) -> None:
        """Parse COFF symbol table and string table.

        COFF symbol table follows section data and contains function/variable
        symbols. Each symbol is 18 bytes. Symbol names are either inline (8 bytes)
        or referenced via string table offset.

        String Table Format:
            Immediately after symbol table:
            - First 4 bytes: Total size of string table (including size field)
            - Remaining bytes: Null-terminated strings

        Symbol Name Resolution:
            - If first 4 bytes are non-zero: Inline name (max 8 chars)
            - If first 4 bytes are zero: Last 4 bytes are offset into string table

        Note:
            Most release builds have stripped symbol tables (pointer_to_symbol_table == 0).
            Use PDB files for comprehensive symbol information.
        """
        f = self._f
        assert f is not None
        ptr = self.coff_header["pointer_to_symbol_table"]
        count = self.coff_header["number_of_symbols"]
        f.seek(ptr)
        # Immediately following the symbol table is the string table: first 4 bytes is its size
        # We'll first read raw bytes then a view for names resolution
        start_symtab = ptr
        symrec_size = 18
        f.seek(start_symtab + symrec_size * count)
        strtab_size = Int32ul.parse_stream(f) if count else 0
        if strtab_size >= 4:
            strtab = f.read(strtab_size - 4)
        else:
            strtab = b""

        def get_name(name8: bytes) -> str:
            # If first 4 bytes are zero, last 4 are offset into string table
            if name8[:4] == b"\x00\x00\x00\x00":
                off = Int32ul.parse(name8[4:8])
                if off and off < len(strtab):
                    end = strtab.find(b"\x00", off)
                    if end == -1:
                        end = len(strtab)
                    return strtab[off:end].decode("latin1", errors="ignore")
                return ""
            return name8.rstrip(b"\x00").decode("latin1", errors="ignore")

        f.seek(start_symtab)
        i = 0
        while i < count:
            rec = f.read(symrec_size)
            if len(rec) < symrec_size:
                break
            symbol = CoffSymbol.parse(rec)
            name8 = symbol.name_raw
            name = get_name(name8)
            self.symbols.append(
                {
                    "name": name,
                    "value": symbol.value,
                    "section_number": symbol.section_number,
                    "type": symbol.type,
                    "storage_class": symbol.storage_class,
                }
            )
            # Skip aux records
            if symbol.number_of_aux_symbols:
                f.seek(symbol.number_of_aux_symbols * symrec_size, io.SEEK_CUR)
                i += symbol.number_of_aux_symbols
            i += 1

    # ------------------------------- Public API -------------------------------
    def machine(self) -> int | None:
        """Get CPU architecture type.

        Returns:
            Machine type constant (defs.IMAGE_FILE_MACHINE_*) or None if no COFF header

        Common Values:
            - 0x014c: IMAGE_FILE_MACHINE_I386 (x86 32-bit)
            - 0x8664: IMAGE_FILE_MACHINE_AMD64 (x86-64)
            - 0x01c0: IMAGE_FILE_MACHINE_ARM (ARM)
            - 0xaa64: IMAGE_FILE_MACHINE_ARM64 (ARM 64-bit)

        Example:
            ```python
            from objutils.pecoff import defs

            if pe.machine() == defs.IMAGE_FILE_MACHINE_AMD64:
                print("64-bit x86 executable")
            ```
        """
        return None if self.coff_header is None else self.coff_header.get("machine")

    def image_base(self) -> int:
        """Get preferred load address for the image.

        Returns:
            Image base address (default: 0 if no optional header)

        Note:
            - Windows loader attempts to load PE at this address
            - If unavailable, relocations are applied
            - Typical values: 0x400000 (32-bit exe), 0x140000000 (64-bit exe)
            - DLLs typically use 0x10000000 or dynamic base

        Example:
            ```python
            base = pe.image_base()
            print(f"Preferred load address: {base:#x}")
            ```
        """
        if self.optional_header and "image_base" in self.optional_header:
            return int(self.optional_header["image_base"])  # type: ignore[return-value]
        return 0

    def create_image(
        self,
        *,
        join: bool = True,
        add_image_base: bool = True,
        include_pattern: str = "",
        exclude_pattern: str = "",
        callback: typing.Optional[typing.Callable[[Section], None]] = None,
    ) -> Image:
        """Build objutils.Image from PE sections.

        Converts PE file sections to objutils.Image format for analysis,
        hexdump, or conversion to other formats.

        Args:
            join: Merge consecutive sections with adjacent addresses (default: True)
            add_image_base: Add image_base to RVAs for absolute addresses (default: True)
                           If False, uses relative virtual addresses (RVAs)
            include_pattern: Only include sections with this substring in name
                            (default: "" = include all)
            exclude_pattern: Exclude sections with this substring in name
                            (default: "" = exclude none)
            callback: Optional function called for each section: callback("section", sec)

        Returns:
            objutils.Image containing section data with addresses

        Example:
            ```python
            # All sections with absolute addresses
            img = pe.create_image()

            # Only code section, relative addresses
            img = pe.create_image(
                add_image_base=False,
                include_pattern=".text"
            )

            # Exclude debug sections
            img = pe.create_image(exclude_pattern=".debug")

            # With callback
            def on_section(typ, sec):
                print(f"Added {sec.name}: {len(sec.data)} bytes")

            img = pe.create_image(callback=on_section)

            # Convert to Intel HEX
            objutils.dump("ihex", "firmware.hex", img)
            ```

        Note:
            - Sections with size_of_raw_data == 0 are skipped (e.g., .bss)
            - Section addresses are VirtualAddress (RVA) + ImageBase
            - This matches how objutils.elf creates images from sections
        """
        f = self._f
        assert f is not None
        sections = []
        img_base = self.image_base() if add_image_base else 0
        for s in self.sections:
            name = s["name"]
            if include_pattern and include_pattern not in name:
                continue
            if exclude_pattern and exclude_pattern in name:
                continue
            size = s["size_of_raw_data"]
            if size == 0:
                continue
            off = s["pointer_to_raw_data"]
            f.seek(off)
            data = f.read(size)
            start_addr = img_base + s["virtual_address"]
            sec = Section(
                start_address=start_addr,
                data=data,
                name=name,
            )
            if callback:
                callback("section", sec)
            sections.append(sec)
        return Image(sections=sections, join=join)

    # ------------------------------- DB Helpers -------------------------------
    def create_db_on_demand(self) -> None:
        """Create and populate SQLAlchemy database with parsed data.

        Creates in-memory SQLite database with:
        - Pe_Header: File metadata
        - Pe_Section: All sections
        - Pe_Symbol: All symbols

        The database can be queried using SQLAlchemy ORM:

        Example:
            ```python
            pe = PeParser("app.exe")
            pe.create_db_on_demand()

            # Query database
            with pe.db.session() as session:
                # Get header
                header = session.query(model.Pe_Header).first()
                print(f"Machine: {header.machine:#x}")

                # Find sections
                text_section = session.query(model.Pe_Section).filter_by(
                    name=".text"
                ).first()

                # Query symbols
                exports = session.query(model.Pe_Symbol).filter(
                    model.Pe_Symbol.storage_class == defs.IMAGE_SYM_CLASS_EXTERNAL
                ).all()
            ```

        Note:
            Database is created only once. Subsequent calls do nothing.
            Uses model.Model for database management.
        """
        if self.db is not None:
            return
        self.db = model.Model()
        # Populate
        with self.db.session() as ses:
            # Header
            hdr = model.Pe_Header(
                machine=self.coff_header.get("machine", 0) if self.coff_header else 0,
                number_of_sections=self.coff_header.get("number_of_sections", 0) if self.coff_header else 0,
                time_date_stamp=self.coff_header.get("time_date_stamp", 0) if self.coff_header else 0,
                characteristics=self.coff_header.get("characteristics", 0) if self.coff_header else 0,
                image_base=self.optional_header.get("image_base", 0) if self.optional_header else 0,
                section_alignment=self.optional_header.get("section_alignment", 0) if self.optional_header else 0,
                file_alignment=self.optional_header.get("file_alignment", 0) if self.optional_header else 0,
            )
            ses.add(hdr)

            # Sections
            for s in self.sections:
                ses.add(
                    model.Pe_Section(
                        name=s["name"],
                        vaddr=s["virtual_address"],
                        vsize=s["virtual_size"],
                        file_offset=s["pointer_to_raw_data"],
                        size=s["size_of_raw_data"],
                        characteristics=s["characteristics"],
                    )
                )

            # Symbols
            for sym in self.symbols:
                ses.add(
                    model.Pe_Symbol(
                        name=sym["name"],
                        value=int(sym.get("value", 0)),
                        section_number=sym["section_number"],
                        type=int(sym.get("type", 0)),
                        storage_class=int(sym.get("storage_class", 0)),
                    )
                )
            ses.commit()


class SectionAPI:
    def __init__(self, parent: PeParser):
        self.parent = parent

    def fetch(self, name_pattern: str | None = None) -> list[model.Pe_Section]:
        self.parent.create_db_on_demand()
        assert self.parent.db is not None
        with self.parent.db.session() as ses:
            q = ses.query(model.Pe_Section)
            if name_pattern:
                q = q.filter(model.Pe_Section.name.like(f"%{name_pattern}%"))
            return q.order_by(model.Pe_Section.vaddr).all()


class SymbolAPI:
    def __init__(self, parent: PeParser):
        self.parent = parent

    def fetch(self, name_pattern: str | None = None) -> list[model.Pe_Symbol]:
        self.parent.create_db_on_demand()
        assert self.parent.db is not None
        with self.parent.db.session() as ses:
            q = ses.query(model.Pe_Symbol)
            if name_pattern:
                q = q.filter(model.Pe_Symbol.name.like(f"%{name_pattern}%"))
            return q.order_by(model.Pe_Symbol.value).all()


__all__ = [
    "PeParser",
    "SectionAPI",
    "SymbolAPI",
]
