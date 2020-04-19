#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <github.com/Christoph2,
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

from functools import partial
import mmap
import re
import sqlite3

from sqlalchemy import (MetaData, schema, types, orm, event,
    create_engine, Column, ForeignKey, ForeignKeyConstraint, func,
    PassiveDefault, UniqueConstraint, CheckConstraint, select
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, with_polymorphic, validates

from objutils.elf import defs

Base = declarative_base()

class MixInBase(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        columns = [c.name for c in self.__class__.__table__.c]
        result = []
        for name, value in [(n, getattr(self, n)) for n in columns]:
            if isinstance(value, str):
                result.append("{} = '{}'".format(name, value))
            else:
                result.append("{} = {}".format(name, value))
        return "{}({})".format(self.__class__.__name__, ", ".join(result))


class RidMixIn(MixInBase):
    rid = Column("rid", types.Integer, primary_key = True)


def StdInteger(default = 0, primary_key = False, unique = False, nullable = False):
    return Column(types.Integer, default = default, nullable = nullable,    # PassiveDefault(str(default))
        primary_key = primary_key, unique = unique)

def StdFloat(default = 0.0, primary_key = False, unique = False, nullable = False):
    return Column(types.Integer, default = default, nullable = nullable,
        primary_key = primary_key, unique = unique)


class Elf_Section(Base, RidMixIn):
    """

    """
    index = Column(types.Integer, unique = True)
    sh_name = StdInteger()
    sh_type = StdInteger()
    sh_flags = StdInteger()
    sh_addr = StdInteger()
    sh_offset = StdInteger()
    sh_size = StdInteger()
    sh_link = StdInteger()
    sh_info = StdInteger()
    sh_addralign = StdInteger()
    sh_entsize = StdInteger()
    section_name = Column(types.VARCHAR, index = True)

    @hybrid_property
    def allocate(self):
        self.sh_type not in (SectionType.SHT_NOBITS, SectionType.SHT_NULL) and self.sh_size > 0


class Elf_Symbol(Base, RidMixIn):
    """

    """
    st_name = StdInteger()
    st_value = StdInteger()
    st_info = StdInteger()
    st_size = StdInteger()
    st_bind = StdInteger()
    st_type = StdInteger()
    st_other = StdInteger()
    st_shndx = StdInteger()
    section_name = Column(types.VARCHAR, index = True)
    symbol_name = Column(types.VARCHAR, index = True)

    @hybrid_property
    def hidden(self):
        return self.st_other in (defs.SymbolVisibility.STV_HIDDEN, defs.SymbolVisibility.STV_INTERNAL)


class Model(object):

    def __init__(self, debug = False):
        self._engine = create_engine("sqlite:///:memory:", echo = debug,
        connect_args={'detect_types': sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES},
        native_datetime = True)

        self._session = orm.Session(self._engine, autoflush = True, autocommit = False)

        self._metadata = Base.metadata
        Base.metadata.create_all(self.engine)
        print("*** TABLES:")
        for table in Base.metadata.tables:
            print(table, end = "\n\n")
        self.session.flush()
        self.session.commit()

    @property
    def engine(self):
        return self._engine

    @property
    def session(self):
        return self._session

    @property
    def metadata(self):
        return self._metadata

