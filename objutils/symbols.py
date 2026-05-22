"""General symbol abstraction that works on top of DWARF, PDB, or whatsoever.

This module provides a format-neutral type system that can represent type information
from DWARF (ELF debug info), PDB (Windows debug info), or any other debug format.

The central abstraction for primitive types is :class:`TypeEncoding`, which replaces
the previous format-specific ``encoding: Any`` fields.  Two helper functions translate
format-specific values to :class:`TypeEncoding`:

- :func:`type_encoding_from_dwarf_ate` – converts a DWARF ``DW_ATE_*`` integer value
- :func:`type_encoding_from_pdb_bt`    – converts a PDB ``BasicType`` (``btXxx``) integer value
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, TypeAlias


# ---------------------------------------------------------------------------
# Format-neutral type encoding
# ---------------------------------------------------------------------------


class TypeKind(enum.Enum):
    """Fundamental type category, independent of any debug-format specifics.

    Groups:
        Basic:       VOID, BOOLEAN, ADDRESS, INTEGER, FLOAT
        Float ext.:  COMPLEX_FLOAT, IMAGINARY_FLOAT, DECIMAL_FLOAT
        Characters:  CHAR  (repertoire stored in :class:`CharEncoding`)
        Scaled:      FIXED, PACKED_DECIMAL, NUMERIC_STRING, EDITED
        Windows/COM: BCD, BIT, CURRENCY, DATE, VARIANT, HRESULT, BSTR
        Fallback:    UNKNOWN
    """

    VOID = "void"
    BOOLEAN = "boolean"
    ADDRESS = "address"
    INTEGER = "integer"
    FLOAT = "float"
    COMPLEX_FLOAT = "complex_float"
    IMAGINARY_FLOAT = "imaginary_float"
    DECIMAL_FLOAT = "decimal_float"
    CHAR = "char"
    FIXED = "fixed"
    PACKED_DECIMAL = "packed_decimal"
    NUMERIC_STRING = "numeric_string"
    EDITED = "edited"
    BCD = "bcd"
    BIT = "bit"
    CURRENCY = "currency"
    DATE = "date"
    VARIANT = "variant"
    HRESULT = "hresult"
    BSTR = "bstr"
    UNKNOWN = "unknown"


class Signedness(enum.Enum):
    """Sign property of a type.

    Attributes:
        SIGNED:          Explicitly signed (e.g. ``int``, ``signed char``).
        UNSIGNED:        Explicitly unsigned (e.g. ``unsigned int``, ``uint8_t``).
        NOT_APPLICABLE:  Signedness is semantically meaningless for this kind
                         (float, void, bool, unicode char, address, …).
        UNSPECIFIED:     Signedness is theoretically applicable but not yet
                         determined – e.g. plain ``char`` whose signedness is
                         implementation-defined in C.
    """

    SIGNED = "signed"
    UNSIGNED = "unsigned"
    NOT_APPLICABLE = "n/a"
    UNSPECIFIED = "unspecified"


class CharEncoding(enum.Enum):
    """Character repertoire / encoding, only meaningful when :attr:`TypeKind` is ``CHAR``.

    Attributes:
        UNSPECIFIED:  Byte-sized ``char`` without a specified encoding (C ``char``).
        ASCII:        ISO/IEC 646:1991 – Fortran ``ASCII`` kind; DWARF ``DW_ATE_ASCII``.
        UCS:          ISO/IEC 10646 UCS-4 – Fortran ``ISO_10646`` kind; DWARF ``DW_ATE_UCS``.
        UTF:          ISO/IEC 10646-1:1993 (general Unicode); DWARF ``DW_ATE_UTF``.
        UTF8:         UTF-8 – C23/C++20 ``char8_t`` (unsigned); PDB ``btChar8``.
        UTF16:        UTF-16 – C++11 ``char16_t``; PDB ``btChar16``.
        UTF32:        UTF-32 – C++11 ``char32_t``; PDB ``btChar32``.
        WIDE:         Platform-defined wide character ``wchar_t``; PDB ``btWChar``.
    """

    UNSPECIFIED = "unspecified"
    ASCII = "ascii"
    UCS = "ucs"
    UTF = "utf"
    UTF8 = "utf8"
    UTF16 = "utf16"
    UTF32 = "utf32"
    WIDE = "wide"


@dataclass(frozen=True)
class TypeEncoding:
    """Format-neutral encoding descriptor for a primitive type.

    Combines a :class:`TypeKind` with optional :class:`Signedness` and
    :class:`CharEncoding` qualifiers.  The dataclass is *frozen* so instances
    are hashable and can be used as dict or set keys.

    Args:
        kind:          Fundamental category of the type.
        signedness:    Sign property (defaults to :attr:`Signedness.NOT_APPLICABLE`).
        char_encoding: Character repertoire for ``CHAR`` types
                       (defaults to :attr:`CharEncoding.UNSPECIFIED`).

    Examples::

        >>> TypeEncoding(TypeKind.INTEGER, Signedness.SIGNED)
        TypeEncoding(kind=INTEGER, signedness=SIGNED, char_encoding=UNSPECIFIED)
        >>> TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.UTF16)
        TypeEncoding(kind=CHAR, signedness=NOT_APPLICABLE, char_encoding=UTF16)

    Use :func:`type_encoding_from_dwarf_ate` and :func:`type_encoding_from_pdb_bt`
    to construct instances from format-specific values.
    """

    kind: TypeKind
    signedness: Signedness = Signedness.NOT_APPLICABLE
    char_encoding: CharEncoding = CharEncoding.UNSPECIFIED

    # ------------------------------------------------------------------
    # Convenience predicates
    # ------------------------------------------------------------------

    def is_signed(self) -> bool:
        """Return ``True`` if the type is explicitly signed."""
        return self.signedness == Signedness.SIGNED

    def is_unsigned(self) -> bool:
        """Return ``True`` if the type is explicitly unsigned."""
        return self.signedness == Signedness.UNSIGNED

    def is_integer(self) -> bool:
        """Return ``True`` for integer kinds (signed or unsigned)."""
        return self.kind == TypeKind.INTEGER

    def is_float(self) -> bool:
        """Return ``True`` for any floating-point kind."""
        return self.kind in (TypeKind.FLOAT, TypeKind.COMPLEX_FLOAT, TypeKind.IMAGINARY_FLOAT, TypeKind.DECIMAL_FLOAT)

    def is_char(self) -> bool:
        """Return ``True`` for character types."""
        return self.kind == TypeKind.CHAR

    def is_void(self) -> bool:
        """Return ``True`` for the void type."""
        return self.kind == TypeKind.VOID

    def is_boolean(self) -> bool:
        """Return ``True`` for boolean types."""
        return self.kind == TypeKind.BOOLEAN

    def __str__(self) -> str:
        parts: list[str] = []
        if self.signedness not in (Signedness.NOT_APPLICABLE, Signedness.UNSPECIFIED):
            parts.append(self.signedness.value)
        parts.append(self.kind.value)
        if self.char_encoding != CharEncoding.UNSPECIFIED:
            parts.append(f"({self.char_encoding.value})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"TypeEncoding(kind={self.kind.name}, signedness={self.signedness.name}, "
            f"char_encoding={self.char_encoding.name})"
        )


# ---------------------------------------------------------------------------
# Conversion: DWARF DW_ATE_* → TypeEncoding
# ---------------------------------------------------------------------------

# Raw integer keys are the DW_ATE_* values from DWARF4 Table 5.1.
# HP vendor extensions (0x80–0x8B) are not listed here; they map to UNKNOWN.
_DWARF_ATE_MAP: dict[int, TypeEncoding] = {
    0x0:  TypeEncoding(TypeKind.VOID),                                                # void (compiler extension, not in spec)
    0x1:  TypeEncoding(TypeKind.ADDRESS, Signedness.NOT_APPLICABLE),                  # DW_ATE_address
    0x2:  TypeEncoding(TypeKind.BOOLEAN, Signedness.NOT_APPLICABLE),                  # DW_ATE_boolean
    0x3:  TypeEncoding(TypeKind.COMPLEX_FLOAT, Signedness.NOT_APPLICABLE),            # DW_ATE_complex_float
    0x4:  TypeEncoding(TypeKind.FLOAT, Signedness.NOT_APPLICABLE),                    # DW_ATE_float
    0x5:  TypeEncoding(TypeKind.INTEGER, Signedness.SIGNED),                          # DW_ATE_signed
    0x6:  TypeEncoding(TypeKind.CHAR, Signedness.SIGNED, CharEncoding.UNSPECIFIED),   # DW_ATE_signed_char
    0x7:  TypeEncoding(TypeKind.INTEGER, Signedness.UNSIGNED),                        # DW_ATE_unsigned
    0x8:  TypeEncoding(TypeKind.CHAR, Signedness.UNSIGNED, CharEncoding.UNSPECIFIED), # DW_ATE_unsigned_char
    0x9:  TypeEncoding(TypeKind.IMAGINARY_FLOAT, Signedness.NOT_APPLICABLE),          # DW_ATE_imaginary_float
    0xA:  TypeEncoding(TypeKind.PACKED_DECIMAL),                                      # DW_ATE_packed_decimal
    0xB:  TypeEncoding(TypeKind.NUMERIC_STRING),                                      # DW_ATE_numeric_string
    0xC:  TypeEncoding(TypeKind.EDITED),                                              # DW_ATE_edited
    0xD:  TypeEncoding(TypeKind.FIXED, Signedness.SIGNED),                            # DW_ATE_signed_fixed
    0xE:  TypeEncoding(TypeKind.FIXED, Signedness.UNSIGNED),                          # DW_ATE_unsigned_fixed
    0xF:  TypeEncoding(TypeKind.DECIMAL_FLOAT, Signedness.NOT_APPLICABLE),            # DW_ATE_decimal_float
    0x10: TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.UTF),   # DW_ATE_UTF  (char16_t / char32_t / u8 in C++)
    0x11: TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.UCS),   # DW_ATE_UCS  (Fortran ISO_10646)
    0x12: TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.ASCII), # DW_ATE_ASCII (Fortran ASCII kind)
}


def type_encoding_from_dwarf_ate(ate_value: int) -> TypeEncoding:
    """Convert a DWARF ``DW_ATE_*`` integer value to a :class:`TypeEncoding`.

    Args:
        ate_value: Raw ``DW_AT_encoding`` value (e.g. ``BaseTypeEncoding.signed`` = 5).

    Returns:
        Matching :class:`TypeEncoding`, or ``TypeEncoding(TypeKind.UNKNOWN)`` for
        unrecognised or vendor-extension values.

    Example::

        >>> from objutils.dwarf.constants import BaseTypeEncoding
        >>> type_encoding_from_dwarf_ate(int(BaseTypeEncoding.float))
        TypeEncoding(kind=FLOAT, signedness=NOT_APPLICABLE, char_encoding=UNSPECIFIED)
    """
    return _DWARF_ATE_MAP.get(int(ate_value), TypeEncoding(TypeKind.UNKNOWN))


# ---------------------------------------------------------------------------
# Conversion: PDB BasicType → TypeEncoding
# ---------------------------------------------------------------------------

# Raw integer keys are the btXxx values from Microsoft cvconst.h.
_PDB_BT_MAP: dict[int, TypeEncoding] = {
    0:  TypeEncoding(TypeKind.UNKNOWN),                                                # btNoType
    1:  TypeEncoding(TypeKind.VOID),                                                   # btVoid
    2:  TypeEncoding(TypeKind.CHAR, Signedness.UNSPECIFIED, CharEncoding.ASCII),       # btChar – plain C char (impl-defined signedness)
    3:  TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.WIDE),     # btWChar – wchar_t
    6:  TypeEncoding(TypeKind.INTEGER, Signedness.SIGNED),                             # btInt
    7:  TypeEncoding(TypeKind.INTEGER, Signedness.UNSIGNED),                           # btUInt
    8:  TypeEncoding(TypeKind.FLOAT, Signedness.NOT_APPLICABLE),                       # btFloat
    9:  TypeEncoding(TypeKind.BCD),                                                    # btBCD
    10: TypeEncoding(TypeKind.BOOLEAN, Signedness.NOT_APPLICABLE),                     # btBool
    13: TypeEncoding(TypeKind.INTEGER, Signedness.SIGNED),                             # btLong  (size captured in byte_size)
    14: TypeEncoding(TypeKind.INTEGER, Signedness.UNSIGNED),                           # btULong
    25: TypeEncoding(TypeKind.CURRENCY),                                               # btCurrency
    26: TypeEncoding(TypeKind.DATE),                                                   # btDate
    27: TypeEncoding(TypeKind.VARIANT),                                                # btVariant
    28: TypeEncoding(TypeKind.COMPLEX_FLOAT, Signedness.NOT_APPLICABLE),               # btComplex
    29: TypeEncoding(TypeKind.BIT),                                                    # btBit
    30: TypeEncoding(TypeKind.BSTR),                                                   # btBSTR
    31: TypeEncoding(TypeKind.HRESULT),                                                # btHresult
    32: TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.UTF16),    # btChar16 – char16_t (C++11)
    33: TypeEncoding(TypeKind.CHAR, Signedness.NOT_APPLICABLE, CharEncoding.UTF32),    # btChar32 – char32_t (C++11)
    34: TypeEncoding(TypeKind.CHAR, Signedness.UNSIGNED, CharEncoding.UTF8),           # btChar8  – char8_t (C++20, always unsigned)
}


def type_encoding_from_pdb_bt(bt_value: int) -> TypeEncoding:
    """Convert a PDB ``BasicType`` integer value to a :class:`TypeEncoding`.

    Args:
        bt_value: Raw ``BasicType`` value from dbghelp/cvconst.h
                  (e.g. ``BasicType.btFloat`` = 8).

    Returns:
        Matching :class:`TypeEncoding`, or ``TypeEncoding(TypeKind.UNKNOWN)`` for
        unrecognised values.

    Example::

        >>> from objutils.pecoff.pdb import BasicType
        >>> type_encoding_from_pdb_bt(int(BasicType.btFloat))
        TypeEncoding(kind=FLOAT, signedness=NOT_APPLICABLE, char_encoding=UNSPECIFIED)
    """
    return _PDB_BT_MAP.get(int(bt_value), TypeEncoding(TypeKind.UNKNOWN))


# ---------------------------------------------------------------------------
# Symbol / type dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PrimitiveType:
    """A primitive / base type.

    Attributes:
        name:      Type name as it appears in the source (e.g. ``"int``, ``"float"``).
        encoding:  Format-neutral :class:`TypeEncoding` describing how the value
                   is encoded and interpreted.
        byte_size: Storage size in bytes.
    """

    name: str
    encoding: TypeEncoding
    byte_size: int


@dataclass
class ArrayType:
    type: TypeInfo
    array_spec: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class TypeDefinition:
    name: str
    type: TypeInfo


@dataclass
class VolatileType:
    type: TypeInfo


@dataclass
class ConstantType:
    type: TypeInfo


@dataclass
class PointerType:
    type: TypeInfo


@dataclass
class ReferenceType:
    type: TypeInfo


@dataclass
class Enumerator:
    name: str
    value: int


@dataclass
class EnumerationType:
    """An enumeration type.

    Attributes:
        name:        Enumeration name.
        byte_size:   Storage size in bytes.
        encoding:    :class:`TypeEncoding` of the underlying integer type,
                     or ``None`` when not determinable.
        base_type:   Resolved underlying type (usually a :class:`PrimitiveType`).
        enumerators: List of named enumeration constants.
    """

    name: str
    byte_size: int
    encoding: TypeEncoding | None
    base_type: TypeInfo
    enumerators: list[Enumerator] = field(default_factory=list)


@dataclass
class UnspecifiedType:
    name: str


@dataclass
class StructMember:
    name: str
    type: TypeInfo
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
    type: TypeInfo
    offset: int
    accessibility: Any  # Accessibility
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
    alternatives: list[StructMember] = field(default_factory=list)


@dataclass
class SubroutineType:
    name: str
    prototyped: int
    return_type: TypeInfo
    parameters: list[TypeInfo] = field(default_factory=list)


@dataclass
class VariableType:
    name: str
    type: TypeInfo
    location: int
    size: int


@dataclass
class DataType:
    name: str
    value: Any
    type: TypeInfo
    datakind: Any


TypeInfo: TypeAlias = (
    PrimitiveType
    | ArrayType
    | TypeDefinition
    | VolatileType
    | ConstantType
    | PointerType
    | ReferenceType
    | EnumerationType
    | UnspecifiedType
    | StructureType
    | ClassType
    | UnionType
    | SubroutineType
)

# Backward-compatible alias (legacy typo retained intentionally).
TypeDefiniton = TypeDefinition
