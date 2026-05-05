"""
General symbol abstraction that works on top of DWARF, PDB, or whatsoever.

"""

from dataclasses import dataclass, field
from typing import Any

@dataclass
class PrimitiveType:
    name: str
    encoding: Any   # BaseTypeEncoding
    byte_size: int


@dataclass
class ArrayType:
    type: PrimitiveType
    array_spec: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class TypeDefiniton:
    name: str
    type: PrimitiveType


@dataclass
class VolatileType:
    type: PrimitiveType


@dataclass
class ConstantType:
    type: PrimitiveType


@dataclass
class PointerType:
    type: PrimitiveType


@dataclass
class Enumerator:
    name: str
    value: int


@dataclass
class EnumerationType:
    name: str
    byte_size: int
    encoding: Any # BaseTypeEncoding
    base_type: PrimitiveType
    enumerators: list[Enumerator] = field(default_factory=list)


@dataclass
class UnspecifiedType:
    name: str


@dataclass
class StructMember:
    name: str
    type: PrimitiveType
    offset: int


@dataclass
class StructureType:
    name: str
    byte_size: int
    member: list[StructMember] = field(default_factory=list)


@dataclass
class ClassMember:
    name: str
    linkage_name: str
    type: PrimitiveType
    offset: int
    accessibility: Any #  Accessibility
    external: bool


@dataclass
class ClassType:
    name: str
    byte_size: int
    member: list[ClassMember] = field(default_factory=list)


@dataclass
class UnionType:
    name: str
    byte_size: int
    alternatives: list[PrimitiveType] = field(default_factory=list)


@dataclass
class SubroutineType:
    name: str
    prototyped: int
    parameters: list[PrimitiveType] = field(default_factory=list)


@dataclass
class VariableType:
    name: str
    type: PrimitiveType
    location: int
