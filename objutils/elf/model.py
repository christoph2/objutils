#!/usr/bin/env python

__version__ = "0.1.0"

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
from sqlalchemy.orm import declarative_base, declared_attr, relationship
from sqlalchemy.sql import func

from objutils.elf import defs

CACHE_SIZE = 4  # MB
PAGE_SIZE = mmap.PAGESIZE

DB_EXTENSION = ".prgdb"

Base = declarative_base()


class MixInBase:
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    def __repr__(self):
        columns = [c.name for c in self.__class__.__table__.c]
        result = []
        for name, value in [(n, getattr(self, n)) for n in columns]:
            if isinstance(value, str):
                result.append(f"{name} = {value!r}")
            else:
                result.append(f"{name} = {value}")
        return "{}({})".format(self.__class__.__name__, ", ".join(result))


class RidMixIn(MixInBase):
    rid = Column("rid", types.Integer, primary_key=True)


def StdInteger(default=0, primary_key=False, unique=False, nullable=False, index=False):
    return Column(
        types.INTEGER,
        default=default,
        nullable=nullable,  # PassiveDefault(str(default))
        primary_key=primary_key,
        unique=unique,
        index=index,
    )
    # types.INTEGER


def StdNumeric(default=0, primary_key=False, unique=False, nullable=False, index=False):
    return Column(
        types.NUMERIC(20, 0),
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
    )


def StdBigInt(default=0, primary_key=False, unique=False, nullable=False, index=False):
    return Column(
        types.INTEGER,
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
    )

    #  Column("id", types.BigInteger().with_variant(types.BigInteger, "sqlite"), primary_key=True)


def StdFloat(default=0.0, primary_key=False, unique=False, nullable=False):
    return Column(
        types.Integer,
        default=default,
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
    )


class Meta(Base, RidMixIn):
    hash_value = Column(types.VARCHAR)
    ts_created = Column(types.DateTime(timezone=True), server_default=func.now())


class Elf_Header(Base, RidMixIn):
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


class Elf_ProgramHeaders(Base, RidMixIn):
    p_type = StdBigInt()
    p_offset = StdBigInt()
    p_vaddr = StdBigInt()
    p_paddr = StdBigInt()
    p_filesz = StdBigInt()
    p_memsz = StdBigInt()
    p_flags = StdBigInt()
    p_align = StdBigInt()


class Elf_Section(Base, RidMixIn):
    """ """

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
    def is_debug(self):
        return self.section_name.starts_with(".debug")

    @hybrid_property
    def is_dwo(self):
        return self.section_name.starts_with(".dwo")

    @hybrid_property
    def has_content(self):
        return self.sh_type not in (
            defs.SectionType.SHT_NOBITS,
            defs.SectionType.SHT_NULL,
        ) and (self.sh_size > 0)

    @has_content.expression
    def has_content(self):
        return and_(
            not_(self.sh_type.in_((defs.SectionType.SHT_NOBITS, defs.SectionType.SHT_NULL))),
            (self.sh_size > 0),
        )

    @hybrid_method
    def get_flags(self):
        return self.sh_flags

    @hybrid_method
    def test_flags(self, mask):
        print("\ttest_flags", self.get_flags(), mask)
        return self.get_flags() & mask == mask

    @test_flags.expression
    def test_flags(self, mask):
        return self.get_flags().op("&")(mask) == mask

    @hybrid_property
    def section_type(self):
        return defs.SectionType(self.sh_type)

    @hybrid_property
    def section_display_name(self):
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
    def flag_writeable(self):
        return self.test_flags(defs.SectionFlags.SHF_WRITE)

    @hybrid_property
    def flag_executable(self):
        return self.test_flags(defs.SectionFlags.SHF_EXECINSTR)

    @hybrid_property
    def flag_alloc(self):
        return self.test_flags(defs.SectionFlags.SHF_ALLOC)

    @hybrid_property
    def flag_merge(self):
        return self.test_flags(defs.SectionFlags.SHF_MERGE)

    @hybrid_property
    def flag_strings(self):
        return self.test_flags(defs.SectionFlags.SHF_STRINGS)

    @hybrid_property
    def flag_info_link(self):
        return self.test_flags(defs.SectionFlags.SHF_INFO_LINK)

    @hybrid_property
    def flag_link_order(self):
        return self.test_flags(defs.SectionFlags.SHF_LINK_ORDER)

    @hybrid_property
    def flag_os_nonconforming(self):
        return self.test_flags(defs.SectionFlags.SHF_OS_NONCONFORMING)

    @hybrid_property
    def flag_group(self):
        return self.test_flags(defs.SectionFlags.SHF_GROUP)

    @hybrid_property
    def flag_tls(self):
        return self.test_flags(defs.SectionFlags.SHF_TLS)

    @hybrid_property
    def flag_ordered(self):  # Solaris only.
        return self.test_flags(defs.SectionFlags.SHF_ORDERED)

    @hybrid_property
    def flag_exclude(self):  # Solaris only.
        return self.test_flags(defs.SectionFlags.SHF_EXCLUDE)


class Elf_Symbol(Base, RidMixIn):
    """

    Attributes
    ----------
    All attributes prefixed with 'st_' are raw values from symboltables (please refer to ELF specification);
    all other exist for your convenience.

    section_name: str

    symbol_name: str

    hidden: bool

    weak: bool

    undefined: bool
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
    def hidden(self):
        return self.st_other in (
            defs.SymbolVisibility.STV_HIDDEN,
            defs.SymbolVisibility.STV_INTERNAL,
        )

    @hidden.expression
    def hidden(self):
        return self.st_other.in_((defs.SymbolVisibility.STV_HIDDEN, defs.SymbolVisibility.STV_INTERNAL))

    @hybrid_property
    def weak(self):
        return self.symbol_bind() == defs.SymbolBinding.STB_WEAK

    @hybrid_property
    def absolute(self):
        return self.st_shndx == defs.SectionName.SHN_ABS

    @hybrid_property
    def undefined(self):
        return self.st_shndx == defs.SectionName.SHN_UNDEF

    @hybrid_property
    def local(self):
        return self.symbol_bind() == defs.SymbolBinding.STB_LOCAL

    @hybrid_property
    def global_(self):
        return self.symbol_bind() == defs.SymbolBinding.STB_GLOBAL

    @hybrid_method
    def get_access(self):
        return self.access

    @hybrid_method
    def test_access(self, mask):
        return self.get_access() & mask == mask

    @test_access.expression
    def test_access(self, mask):
        return self.get_access().op("&")(mask) == mask

    @hybrid_property
    def writeable(self):
        return self.test_access(defs.SectionFlags.SHF_WRITE)

    @hybrid_property
    def executeable(self):
        return self.test_access(defs.SectionFlags.SHF_EXECINSTR)

    @hybrid_property
    def allocate(self):
        return self.test_access(defs.SectionFlags.SHF_ALLOC)

    @hybrid_property
    def symbol_bind(self):
        return defs.SymbolBinding(self.st_bind)

    @hybrid_property
    def symbol_type(self):
        return defs.SymbolType(self.st_type)


class Elf_Comment(Base, RidMixIn):
    """ """

    text = Column(types.VARCHAR)


class Elf_Note(Base, RidMixIn):
    """ """

    section_name = Column(types.VARCHAR, unique=True)
    type = StdInteger()
    name = Column(types.VARCHAR)
    desc = Column(types.VARCHAR)


class DIEAttribute(Base, RidMixIn):
    # Store attribute name (DW_AT_*) as integer enum (AttributeEncoding) for performance
    name = StdInteger(index=True)
    # Form of the attribute (DW_FORM_*), stored as integer enum for later interpretation
    form = StdInteger(index=True, nullable=True)
    raw_value = Column(types.VARCHAR)
    # Keep DB column for backward compatibility; if None, we compute lazily on access
    display_value = Column(types.VARCHAR, nullable=True)
    entry_id = Column(types.Integer, ForeignKey("debuginformationentry.rid"), index=True)
    entry = relationship("DebugInformationEntry", back_populates="attributes")

    @orm.validates("name")
    def _coerce_name(self, key, value):
        """Accept attribute name as int, enum, or string and coerce to integer for storage."""
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
    def encoding_name(self):
        """Expose attribute name as string, regardless of integer storage."""
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

    # ----- Display value computation with caching -----
    def _compute_display_value(self):
        try:
            from objutils.dwarf import constants as c
        except Exception:
            return str(self.raw_value)

        # Normalize helpers
        def to_int(v):
            try:
                return int(v)
            except Exception:
                return None

        enc = None
        try:
            enc = c.AttributeEncoding(self.name)
        except Exception:
            pass
        frm = None
        try:
            frm = c.AttributeForm(self.form) if self.form is not None else None
        except Exception:
            pass

        raw = self.raw_value

        # Location-like attributes
        if enc in (
                getattr(c.AttributeEncoding, "location", None),
                getattr(c.AttributeEncoding, "GNU_call_site_value", None),
                getattr(c.AttributeEncoding, "frame_base", None),
                getattr(c.AttributeEncoding, "GNU_call_site_target", None),
                getattr(c.AttributeEncoding, "vtable_elem_location", None),
                getattr(c.AttributeEncoding, "data_member_location", None),
                getattr(c.AttributeEncoding, "return_addr", None),
        ):
            if frm in (
                    getattr(c.AttributeForm, "DW_FORM_exprloc", None),
                    getattr(c.AttributeForm, "DW_FORM_block", None),
                    getattr(c.AttributeForm, "DW_FORM_block1", None),
                    getattr(c.AttributeForm, "DW_FORM_block2", None),
                    getattr(c.AttributeForm, "DW_FORM_block4", None),
                    getattr(c.AttributeForm, "DW_FORM_implicit_const", None),
            ):
                # We cannot run the DWARF stack machine here; present as hex bytes for performance.
                if isinstance(raw, (bytes, bytearray)):
                    return raw.hex()
                # Strings like "b'..'" or iterables of ints
                try:
                    if isinstance(raw, str) and raw.startswith("b'"):
                        # best effort: eval-safe removal
                        hexed = raw.encode("latin1", "ignore")
                        return hexed.hex()
                except Exception:
                    pass
                return str(raw)
            else:
                ival = to_int(raw)
                if ival is not None:
                    return f"0x{ival:08x}"
                return str(raw)

        # Encoded attributes mapped to enums (language, accessibility, etc.)
        try:
            ENCODED_MAP = {
                c.AttributeEncoding.decimal_sign: c.DecimalSign,
                c.AttributeEncoding.endianity: c.Endianity,
                c.AttributeEncoding.accessibility: c.Accessibility,
                c.AttributeEncoding.visibility: c.Visibility,
                c.AttributeEncoding.virtuality: c.Virtuality,
                c.AttributeEncoding.language: c.Languages,
                c.AttributeEncoding.identifier_case: c.IdentifierCase,
                c.AttributeEncoding.calling_convention: c.CallingConvention,
                c.AttributeEncoding.inline: c.Inline,
                c.AttributeEncoding.ordering: c.Ordering,
                c.AttributeEncoding.discr_list: c.DiscriminantDescriptor,
                c.AttributeEncoding.defaulted: c.Defaulted,
            }
            if enc in ENCODED_MAP:
                ival = to_int(raw)
                if ival is not None and ival in ENCODED_MAP[enc].__members__.values():
                    try:
                        name = ENCODED_MAP[enc](ival).name
                        return f"{name} (0x{ival:08x})"
                    except Exception:
                        return f"0x{ival:08x}"
        except Exception:
            pass

        # References
        if frm in (
                getattr(c.AttributeForm, "DW_FORM_ref1", None),
                getattr(c.AttributeForm, "DW_FORM_ref2", None),
                getattr(c.AttributeForm, "DW_FORM_ref4", None),
                getattr(c.AttributeForm, "DW_FORM_ref8", None),
                getattr(c.AttributeForm, "DW_FORM_ref_udata", None),
        ):
            ival = to_int(raw)
            base = getattr(self.entry, "cu_start", None)
            if ival is not None:
                if base is not None:
                    try:
                        ival += int(base)
                    except Exception:
                        pass
                return f"0x{ival:08x}"
            return str(raw)
        if frm == getattr(c.AttributeForm, "DW_FORM_ref_addr", None):
            ival = to_int(raw)
            if ival is not None:
                return f"0x{ival:08x}"
            return str(raw)

        # Default: best-effort string
        return raw if isinstance(raw, str) else str(raw)

    def get_display_value(self):
        # If column is set, use it; otherwise compute and cache per-instance
        dv = getattr(self, "display_value", None)
        if dv not in (None, ""):
            return dv
        cached = getattr(self, "_display_value_cache", None)
        if cached is not None:
            return cached
        dv = self._compute_display_value()
        setattr(self, "_display_value_cache", dv)
        return dv


class DebugInformationEntry(Base, RidMixIn):
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
    )
    children = relationship(
        "DebugInformationEntry",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    @orm.validates("tag")
    def _coerce_tag(self, key, value):
        """Accept tag as int, enum, or string name and coerce to integer for storage."""
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
    def abbrev(self):
        class _Abbrev:
            def __init__(self, tag_value):
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
                return f"Tag({self.tag})"

            __repr__ = __str__

        return _Abbrev(self.tag)

    @property
    def attributes_map(self):
        cache = getattr(self, "_attributes_map_cache", None)
        if cache is None:

            def _attr_key(a):
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

    def get_attribute(self, name: str):
        return self.attributes_map.get(name)


class DebugInformation(Base, RidMixIn):
    pass
    # die_map: dict[int, DebugInformationEntry]
    # die_entries: List[DebugInformationEntry]


class CompilationUnit(Base, RidMixIn):
    pass


def calculateCacheSize(value):
    return -(value // PAGE_SIZE)


REGEX_CACHE = {}


def regexer(value: str, expr: str):
    if value is None or expr is None:
        return 0
    pattern = REGEX_CACHE.get(expr)
    if pattern is None:
        pattern = re.compile(expr, re.UNICODE)
        REGEX_CACHE[expr] = pattern
    return 1 if pattern.search(value) else 0


@event.listens_for(Engine, "connect")
def set_sqlite3_pragmas(dbapi_connection, connection_record):
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


"""
class A2LDatabase(object):
    def __init__(self, filename, debug=False, logLevel="INFO"):
        if filename == ":memory:":
            self.dbname = ""
        else:
            if not filename.lower().endswith(DB_EXTENSION):
                self.dbname = "{}.{}".format(filename, DB_EXTENSION)
            else:
                self.dbname = filename
        self._engine = create_engine(
            "sqlite:///{}".format(self.dbname),
            echo=debug,
            connect_args={"detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES},
            native_datetime=True,
        )

        self._session = orm.Session(self._engine, autoflush=False, autocommit=False)
        self._metadata = Base.metadata
        # loadInitialData(Node)
        Base.metadata.create_all(self.engine)
        meta = MetaData(schema_version=CURRENT_SCHEMA_VERSION)
        self.session.add(meta)
        self.session.flush()
        self.session.commit()
        self._closed = False
"""


class Model:
    def __init__(self, filename: str = ":memory:", debug: bool = False):
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

    def _ensure_schema(self):
        """Ensure required columns and critical indexes exist for older databases.
        Adds missing columns and creates indexes with minimal changes without rebuilding the DB.
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
                    conn.execute(
                        text('CREATE INDEX IF NOT EXISTS idx_die_cu_start ON debuginformationentry ("cu_start")'))
                # Helpful for parent/child traversal
                if "idx_die_parent_id" not in die_indexes and "parent_id" in die_cols:
                    conn.execute(
                        text('CREATE INDEX IF NOT EXISTS idx_die_parent_id ON debuginformationentry ("parent_id")'))
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

    def close(self):
        self.session.close()
        self._engine.dispose()

    @property
    def engine(self):
        return self._engine

    @property
    def session(self):
        return self._session

    @property
    def metadata(self):
        return self._metadata
