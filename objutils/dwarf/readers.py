"""DWARF Data Readers and Stack Machine Support.

This module provides high-level interfaces for reading DWARF attribute values
with appropriate binary encodings. DwarfReaders encapsulates encoding selection
and provides a unified interface for parsing various DWARF data types.

Reader Pattern:
    DwarfReaders maintains a Readers container with attributes for each supported
    encoding type (u8, s16, uleb, block1, cstring_utf8, etc.). The appropriate reader
    is selected based on the endianness and address size of the debug information.

Stack Machine Integration:
    Includes integration with StackMachine for evaluating DWARF expressions and
    location descriptions (DW_FORM_exprloc, DW_FORM_block*, etc.).

Usage:
    Create a DwarfReaders instance with target architecture parameters, then use
    the readers attribute or stack_machine for decoding debug information.

Example:
    >>> from objutils.dwarf.encoding import Endianess
    >>> readers = DwarfReaders(Endianess.Little, 8)
    >>> value = readers.readers.uleb.parse(data)

Copyright (C) 2010-2025 by Christoph Schueler
"""

from dataclasses import dataclass
from functools import lru_cache

from construct import (
    CString,
    Int8sl,
    Int8ul,
    Int16sb,
    Int16sl,
    Int16ub,
    Int16ul,
    Int32sb,
    Int32sl,
    Int32ub,
    Int32ul,
    Int64sb,
    Int64sl,
    Int64ub,
    Int64ul,
)

from objutils.dwarf import constants
from objutils.dwarf.encoding import (
    SLEB,
    ULEB,
    Address,
    Block1,
    Block2b,
    Block2l,
    Block4b,
    Block4l,
    BlockUleb,
    Endianess,
    StrP,
)
from objutils.dwarf.sm import StackMachine


@dataclass
class Readers:
    """Container for DWARF data readers.

    A simple dataclass whose attributes are dynamically populated with Construct
    parsers for different DWARF encoding formats. Attributes are set based on
    architecture endianness and address size.

    Typical attributes include:
        u8, s8, u16, s16, u32, s32, u64, s64: Fixed-width integer readers.
        uleb, sleb: Variable-length integer readers.
        block1, block2, block4, block_uleb: Block data readers.
        native_address: Target-specific address reader.
        cstring_ascii, cstring_utf8: Null-terminated string readers.
        strp, line_strp: String pointer readers.
    """

    pass


class DwarfReaders:
    """High-Level DWARF Data Reader Interface.

    Provides architecture-aware readers for parsing DWARF debug information.
    Selects appropriate binary encodings based on target endianness and address size.

    Attributes:
        readers: Readers container with encoding-specific parser instances.
        stack_machine: StackMachine for evaluating DWARF expressions.
    """

    def __init__(
        self,
        endianess: Endianess,
        address_size: int,
        strings: bytes = b"",
        line_strings: bytes = b"",
        *,
        enable_debug_log: bool = False,
    ) -> None:
        """Initialize DWARF readers for specific target architecture.

        Args:
            endianess: Target byte order (Endianess.Little or Endianess.Big).
            address_size: Address width in bytes (1, 2, 4, or 8).
            strings: Complete debug_str section (for string pointer resolution).
            line_strings: Complete debug_line_str section (for line string resolution).
            enable_debug_log: Enable debug logging (default: False).
        """
        self._endianess = endianess
        self._address_size = address_size
        self._strings = strings
        self._line_strings = line_strings
        self._enable_debug_log = enable_debug_log

        #      Little    Big
        self._BASIC_READERS: dict[str, tuple] = {
            "u8": (Int8ul, Int8ul),
            "s8": (Int8sl, Int8sl),
            "u16": (Int16ul, Int16ub),
            "s16": (Int16sl, Int16sb),
            "u32": (Int32ul, Int32ub),
            "s32": (Int32sl, Int32sb),
            "u64": (Int64ul, Int64ub),
            "s64": (Int64sl, Int64sb),
            "block2": (Block2l, Block2b),
            "block4": (Block4l, Block4b),
        }

        self.readers = Readers()

        # Core encodings
        self.readers.native_address = Address(self._address_size, self._endianess)
        self.readers.uleb = ULEB
        self.readers.sleb = SLEB
        self.readers.block1 = Block1
        self.readers.block_uleb = BlockUleb
        self.readers.cstring_ascii = CString(encoding="ascii")
        self.readers.cstring_utf8 = CString(encoding="utf8")
        self.readers.strp = StrP(self._strings, self._endianess)
        self.readers.line_strp = StrP(self._line_strings, self._endianess)

        idx = 0 if self._endianess == Endianess.Little else 1
        for name, variants in self._BASIC_READERS.items():
            setattr(self.readers, name, variants[idx])

        # Stack-Maschine für DWARF-Ausdrücke
        self.stack_machine = StackMachine(self.readers)

    @property
    def endianess(self) -> Endianess:
        """Get target byte order."""
        return self._endianess

    @property
    def address_size(self) -> int:
        """Get target address width in bytes."""
        return self._address_size

    @lru_cache(maxsize=64 * 1024)
    def dwarf_expression(self, form: constants.AttributeForm, expr: bytes) -> str:
        """Evaluate DWARF expression or location description.

        Interprets DWARF expressions (DW_OP_* operations) and converts them to
        human-readable format. Handles both location descriptions and constant values.

        Args:
            form: Attribute form identifying the expression type.
            expr: Raw expression bytes to evaluate.

        Returns:
            String representation of the expression or value.

        Raises:
            NotImplementedError: If form type is unsupported.
        """
        if form in (
            constants.AttributeForm.DW_FORM_exprloc,
            constants.AttributeForm.DW_FORM_block,
            constants.AttributeForm.DW_FORM_block1,
            constants.AttributeForm.DW_FORM_block2,
            constants.AttributeForm.DW_FORM_block4,
        ):
            return self.stack_machine.evaluate(expr)
        elif form in (
            constants.AttributeForm.DW_FORM_data1,
            constants.AttributeForm.DW_FORM_data2,
            constants.AttributeForm.DW_FORM_data4,
            constants.AttributeForm.DW_FORM_data8,
            constants.AttributeForm.DW_FORM_data16,
        ):
            return f"0x{int(expr):08x}"
        elif form == constants.AttributeForm.DW_FORM_udata:
            return ULEB.parse(expr)
        elif form == constants.AttributeForm.DW_FORM_sdata:
            return SLEB.parse(expr)
        elif form in (constants.AttributeForm.DW_FORM_sec_offset, constants.AttributeForm.DW_FORM_loclistx):
            return f"0x{int(expr):08x}"
        else:
            print("Unsupported DWARF expression form:", form, list(expr))
            raise NotImplementedError(f"Unsupported DWARF expression form: {form}")
