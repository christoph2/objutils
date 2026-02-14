from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import Column, Integer, Numeric, String, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


Base = declarative_base()


def StdInteger(default=0, primary_key=False, unique=False, nullable=False, index=False):
    return Column(Integer, primary_key=primary_key, unique=unique, nullable=nullable, index=index, default=default)


class MixInBase:
    @property
    def __tablename__(self) -> str:  # type: ignore[override]
        return self.__class__.__name__

    def __repr__(self) -> str:
        s = self.__class__.__name__ + "("
        s += ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__dict__ if not k.startswith("_"))
        s += ")"
        return s


class RidMixIn(MixInBase):
    rid = StdInteger(primary_key=True)


class Pe_Header(Base, RidMixIn):
    __tablename__ = "pe_header"
    machine = StdInteger()
    number_of_sections = StdInteger()
    time_date_stamp = StdInteger()
    characteristics = StdInteger()
    image_base = Numeric()
    section_alignment = StdInteger()
    file_alignment = StdInteger()


class Pe_Section(Base, RidMixIn):
    __tablename__ = "pe_sections"
    name = Column(String(256), index=True)
    vaddr = StdInteger()
    vsize = StdInteger()
    file_offset = StdInteger()
    size = StdInteger()
    characteristics = StdInteger()


class Pe_Symbol(Base, RidMixIn):
    __tablename__ = "pe_symbols"
    name = Column(String(512), index=True)
    value = StdInteger()
    section_number = StdInteger()
    type = StdInteger()
    storage_class = StdInteger()


def set_sqlite3_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA synchronous = OFF")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA cache_size = 100000")
        cursor.execute("PRAGMA temp_store = MEMORY")
    finally:
        cursor.close()


class Model:
    def __init__(self, filename: str = ":memory:", debug: bool = False):
        self._engine = create_engine(f"sqlite:///{filename}", echo=debug)

        # sqlite pragmas
        event.listen(self._engine, "connect", set_sqlite3_pragmas)  # type: ignore[arg-type]

        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def close(self):
        self._engine.dispose()

    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session(self) -> Session:
        ses = self._Session()
        try:
            yield ses
        finally:
            ses.close()
