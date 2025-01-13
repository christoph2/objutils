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

from sqlalchemy import Column, ForeignKey, and_, create_engine, event, not_, orm, types
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


"""
class SLBigInteger(BigInteger):
    pass

@compiles(SLBigInteger, 'sqlite')
def bi_c(element, compiler, **kw):
    return "INTEGER"

@compiles(SLBigInteger)
def bi_c(element, compiler, **kw):
    return compiler.visit_BIGINT(element, **kw)


table = Table(
    "my_table", metadata,
    Column("id", SLBigInteger(), primary_key=True)
)
"""


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
    name = Column(types.VARCHAR)
    raw_value = Column(types.VARCHAR)
    display_value = Column(types.VARCHAR)
    entry_id = Column(types.Integer, ForeignKey("debuginformationentry.rid"))
    entry = relationship("DebugInformationEntry", back_populates="attributes")


class DebugInformationEntry(Base, RidMixIn):
    tag = Column(types.VARCHAR)
    attributes = relationship("DIEAttribute", back_populates="entry", uselist=True)


class DebugInformation(Base, RidMixIn):
    pass
    # die_map: dict[int, DebugInformationEntry]
    # die_entries: List[DebugInformationEntry]


class CompilationUnit(Base, RidMixIn):
    pass


"""
@dataclass
class DIEAttribute:
    raw_value: Any
    display_value: str

    def toJSON(self):
        print("Hello!?")


@dataclass
class DebugInformationEntry:
    name: str
    attributes: List = field(default_factory=list)
    children: List = field(default_factory=list)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


@dataclass
class DebugInformation:
    die_map: dict[int, DebugInformationEntry]
    die_entries: List[DebugInformationEntry]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
"""


def calculateCacheSize(value):
    return -(value // PAGE_SIZE)


REGEXER_CACHE = {}


def regexer(value, expr):
    if not REGEXER_CACHE.get(expr):
        REGEXER_CACHE[expr] = re.compile(expr, re.UNICODE)
    re_expr = REGEXER_CACHE[expr]
    return re_expr.match(value) is not None


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
        self.session.flush()
        self.session.commit()

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
