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
    """
    Simple container whose attributes are populated with Construct parsers
    and helpers for reading DWARF fields.
    """

    pass




class DwarfReaders:

    def __init__(
        self,
        endianess: Endianess,
        address_size: int,
        strings: bytes = b"",
        line_strings: bytes = b"",
        *,
        enable_debug_log: bool = False,
    ) -> None:
        self._endianess = endianess
        self._address_size = address_size
        self._strings = strings
        self._line_strings = line_strings
        self._enable_debug_log = enable_debug_log

        #      Little    Big
        self._BASIC_READERS = {
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
        return self._endianess

    @property
    def address_size(self) -> int:
        return self._address_size

    @lru_cache(maxsize=64 * 1024)
    def dwarf_expression(self, form: constants.AttributeForm, expr: bytes) -> str:
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
