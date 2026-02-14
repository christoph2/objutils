import io
import os
import struct
import typing
from pathlib import Path

from construct import Bytes, Int8ul, Int16ul, Int32ul, Int64ul, PaddedString, Struct

from objutils import Image, Section
from objutils.utils import create_memorymapped_fileview

from . import defs, model


try:
    from .pdb import pdb_symbols_for_pe  # type: ignore
except Exception:  # pragma: no cover
    pdb_symbols_for_pe = None  # type: ignore[assignment]


CoffHeader = Struct(
    "machine" / Int16ul,
    "number_of_sections" / Int16ul,
    "time_date_stamp" / Int32ul,
    "pointer_to_symbol_table" / Int32ul,
    "number_of_symbols" / Int32ul,
    "size_of_optional_header" / Int16ul,
    "characteristics" / Int16ul,
)

OptionalHeaderPe32 = Struct(
    "magic" / Int16ul,
    "major_linker_version" / Int8ul,
    "minor_linker_version" / Int8ul,
    "size_of_code" / Int32ul,
    "size_of_initialized_data" / Int32ul,
    "size_of_uninitialized_data" / Int32ul,
    "address_of_entry_point" / Int32ul,
    "base_of_code" / Int32ul,
    "base_of_data" / Int32ul,
    "image_base" / Int32ul,
    "section_alignment" / Int32ul,
    "file_alignment" / Int32ul,
)

OptionalHeaderPe32Plus = Struct(
    "magic" / Int16ul,
    "major_linker_version" / Int8ul,
    "minor_linker_version" / Int8ul,
    "size_of_code" / Int32ul,
    "size_of_initialized_data" / Int32ul,
    "size_of_uninitialized_data" / Int32ul,
    "address_of_entry_point" / Int32ul,
    "base_of_code" / Int32ul,
    "image_base" / Int64ul,
    "section_alignment" / Int32ul,
    "file_alignment" / Int32ul,
)

SectionHeader = Struct(
    "name_raw" / Bytes(8),
    "virtual_size" / Int32ul,
    "virtual_address" / Int32ul,
    "size_of_raw_data" / Int32ul,
    "pointer_to_raw_data" / Int32ul,
    "pointer_to_relocations" / Int32ul,
    "pointer_to_linenumbers" / Int32ul,
    "number_of_relocations" / Int16ul,
    "number_of_linenumbers" / Int16ul,
    "characteristics" / Int32ul,
)

CoffSymbol = Struct(
    "name_raw" / Bytes(8),
    "value" / Int32ul,
    "section_number" / Int16ul,
    "type" / Int16ul,
    "storage_class" / Int8ul,
    "number_of_aux_symbols" / Int8ul,
)


class PeParser:
    """
    Minimal Portable Executable (PE/COFF) parser providing:
    - Headers (DOS, COFF, Optional)
    - Sections (name, RVA, size, file offset, characteristics)
    - COFF symbols (if present — typical for .obj or special images)
    - Image creation API similar to objutils.elf.ElfParser.create_image

    Notes:
      - For image section addresses we use VirtualAddress (RVA). Optional header's ImageBase
        is added to the section addresses by default when creating the image, matching
        how ELF uses VMA for sections.
    """

    def __init__(self, filename: str | os.PathLike, *, pdb_path: list[str | os.PathLike] | None = None):
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
        self._mm = create_memorymapped_fileview(self._path)
        self._f = io.BytesIO(self._mm)
        self._parse()

    def close(self) -> None:
        try:
            if self._f:
                self._f.close()
        finally:
            self._f = None
            self._mm = None

    # -------------------------------- Parsing --------------------------------
    def _parse(self) -> None:
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
        string_table_start = f.tell()
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
        return None if self.coff_header is None else self.coff_header.get("machine")

    def image_base(self) -> int:
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
        """
        Build an Image from file sections.
        - If add_image_base is True, addresses are image_base + VirtualAddress; else RVAs.
        - include/exclude patterns are simple substring tests on section names.
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
