#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2024 by Christoph Schueler <cpu12.gems@googlemail.com>

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

##
## Stackmachine for DWARF expressions.
##

import io
from dataclasses import dataclass
from typing import Any, List

from construct import Array

from objutils.dwarf import constants


class Stack:

    def __init__(self):
        self._values: List[Any] = []

    def push(self, value: Any) -> None:
        self._values.append(value)

    def pop(self) -> Any:
        return self._values.pop()

    @property
    def tos(self) -> Any:
        return self._values[-1]

    @tos.setter
    def tos(self, value: Any) -> None:
        self._values[-1] = value

    def empty(self) -> bool:
        return len(self._values) == 0

    def __str__(self) -> str:
        return f"Stack({self._values!r})"


@dataclass
class EvaluationResult:
    pass


######################
######################
######################


class OperationBase:

    PARAMETERS = []
    ARRAY_SIZE = None

    @classmethod
    def set_readers(cls, readers):
        cls.readers = readers
        cls.native_address = readers.native_address
        cls.u8 = readers.u8
        cls.s8 = readers.s8
        cls.u16 = readers.u16
        cls.s16 = readers.s16
        cls.u32 = readers.u32
        cls.s32 = readers.s32
        cls.u64 = readers.u64
        cls.s64 = readers.s64
        cls.uleb = readers.uleb
        cls.sleb = readers.sleb
        cls.block1 = readers.block1
        cls.READERS = {
            "native_address": cls.native_address,
            "u8": cls.u8,
            "s8": cls.s8,
            "u16": cls.u16,
            "s16": cls.s16,
            "u32": cls.u32,
            "s32": cls.s32,
            "u64": cls.u64,
            "s64": cls.s64,
            "uleb": cls.uleb,
            "sleb": cls.sleb,
            "block1": cls.block1,
        }

    def parse(self, image):
        self.result = []
        self.data_block = None
        for type_name in self.PARAMETERS:
            reader = OperationBase.READERS[type_name]
            data = reader.parse_stream(image)
            self.result.append(data)
        if self.result and self.ARRAY_SIZE is not None:
            length = self.result[self.ARRAY_SIZE]
            self.data_block = Array(length, self.u8).parse_stream(image)
            print("*** DATA_BLOCK:", self.data_block)
            raise RuntimeError()

    @property
    def value(self):
        return

    def stack_op(self, stack):
        pass

    def __str__(self):
        if self.result:
            params = []
            for param in self.result:
                if param > 0:
                    params.append(f"0x{param:08x}")
                else:
                    params.append(f"{param}")
            return f"{self.DISPLAY_NAME}({', '.join(params)})"
        else:
            return f"{self.DISPLAY_NAME}()"

    __repr__ = __str__


class Addr(OperationBase):
    DISPLAY_NAME = "addr"
    PARAMETERS = ["native_address"]

    def stack_op(self, stack):
        value = self.result[0]
        stack.push(value)


class Deref(OperationBase):
    DISPLAY_NAME = "deref"


class Const1U(OperationBase):

    DISPLAY_NAME = "const1u"
    PARAMETERS = ["u8"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const1S(OperationBase):
    DISPLAY_NAME = "const1s"
    PARAMETERS = ["s8"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const2U(OperationBase):
    DISPLAY_NAME = "const2u"
    PARAMETERS = ["u16"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const2S(OperationBase):
    DISPLAY_NAME = "const2s"
    PARAMETERS = ["s16"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const4U(OperationBase):
    DISPLAY_NAME = "const4u"
    PARAMETERS = ["u32"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const4S(OperationBase):
    DISPLAY_NAME = "const4s"
    PARAMETERS = ["s32"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const8U(OperationBase):
    DISPLAY_NAME = "const8u"
    PARAMETERS = ["u64"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const8S(OperationBase):
    DISPLAY_NAME = "const8s"
    PARAMETERS = ["s64"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Constu(OperationBase):
    DISPLAY_NAME = "constu"
    PARAMETERS = ["uleb"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Consts(OperationBase):
    DISPLAY_NAME = "consts"
    PARAMETERS = ["sleb"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Dup(OperationBase):
    DISPLAY_NAME = "dup"


class Drop(OperationBase):
    DISPLAY_NAME = "drop"


class Over(OperationBase):
    DISPLAY_NAME = "over"


class Pick(OperationBase):
    DISPLAY_NAME = "pick"
    PARAMETERS = ["u8"]


class Swap(OperationBase):
    DISPLAY_NAME = "swap"


class Rot(OperationBase):
    DISPLAY_NAME = "rot"


class Xderef(OperationBase):
    DISPLAY_NAME = "xderef"


class Abs(OperationBase):
    DISPLAY_NAME = "abs"


class And_(OperationBase):
    DISPLAY_NAME = "and_"


class Div(OperationBase):
    DISPLAY_NAME = "div"


class Minus(OperationBase):
    DISPLAY_NAME = "minus"


class Mod(OperationBase):
    DISPLAY_NAME = "mod"


class Mul(OperationBase):
    DISPLAY_NAME = "mul"


class Neg(OperationBase):
    DISPLAY_NAME = "neg"


class Not_(OperationBase):
    DISPLAY_NAME = "not_"


class Or_(OperationBase):
    DISPLAY_NAME = "or_"


class Plus(OperationBase):
    DISPLAY_NAME = "plus"


class Plus_Uconst(OperationBase):
    DISPLAY_NAME = "plus_uconst"
    PARAMETERS = ["uleb"]


class Shl(OperationBase):
    DISPLAY_NAME = "shl"


class Shr(OperationBase):
    DISPLAY_NAME = "shr"


class Shra(OperationBase):
    DISPLAY_NAME = "shra"


class Xor(OperationBase):
    DISPLAY_NAME = "xor"


class Bra(OperationBase):
    DISPLAY_NAME = "bra"
    PARAMETERS = ["s16"]


class Eq(OperationBase):
    DISPLAY_NAME = "eq"


class Ge(OperationBase):
    DISPLAY_NAME = "ge"


class Gt(OperationBase):
    DISPLAY_NAME = "gt"


class Le(OperationBase):
    DISPLAY_NAME = "le"


class Lt(OperationBase):
    DISPLAY_NAME = "lt"


class Ne(OperationBase):
    DISPLAY_NAME = "ne"


class Skip(OperationBase):
    DISPLAY_NAME = "skip"
    PARAMETERS = ["s16"]


class Lit0(OperationBase):

    DISPLAY_NAME = "lit0"

    def stack_op(self, stack):
        stack.push(0)


class Lit1(OperationBase):

    DISPLAY_NAME = "lit1"

    def stack_op(self, stack):
        stack.push(1)


class Lit2(OperationBase):

    DISPLAY_NAME = "lit2"

    def stack_op(self, stack):
        stack.push(2)


class Lit3(OperationBase):

    DISPLAY_NAME = "lit3"

    def stack_op(self, stack):
        stack.push(3)


class Lit4(OperationBase):

    DISPLAY_NAME = "lit4"

    def stack_op(self, stack):
        stack.push(4)


class Lit5(OperationBase):

    DISPLAY_NAME = "lit5"

    def stack_op(self, stack):
        stack.push(5)


class Lit6(OperationBase):

    DISPLAY_NAME = "lit6"

    def stack_op(self, stack):
        stack.push(6)


class Lit7(OperationBase):

    DISPLAY_NAME = "lit7"

    def stack_op(self, stack):
        stack.push(7)


class Lit8(OperationBase):

    DISPLAY_NAME = "lit8"

    def stack_op(self, stack):
        stack.push(8)


class Lit9(OperationBase):

    DISPLAY_NAME = "lit9"

    def stack_op(self, stack):
        stack.push(9)


class Lit10(OperationBase):

    DISPLAY_NAME = "lit10"

    def stack_op(self, stack):
        stack.push(10)


class Lit11(OperationBase):

    DISPLAY_NAME = "lit11"

    def stack_op(self, stack):
        stack.push(11)


class Lit12(OperationBase):

    DISPLAY_NAME = "lit12"

    def stack_op(self, stack):
        stack.push(12)


class Lit13(OperationBase):

    DISPLAY_NAME = "lit13"

    def stack_op(self, stack):
        stack.push(13)


class Lit14(OperationBase):

    DISPLAY_NAME = "lit14"

    def stack_op(self, stack):
        stack.push(14)


class Lit15(OperationBase):

    DISPLAY_NAME = "lit15"

    def stack_op(self, stack):
        stack.push(15)


class Lit16(OperationBase):

    DISPLAY_NAME = "lit16"

    def stack_op(self, stack):
        stack.push(16)


class Lit17(OperationBase):

    DISPLAY_NAME = "lit17"

    def stack_op(self, stack):
        stack.push(17)


class Lit18(OperationBase):

    DISPLAY_NAME = "lit18"

    def stack_op(self, stack):
        stack.push(18)


class Lit19(OperationBase):

    DISPLAY_NAME = "lit19"

    def stack_op(self, stack):
        stack.push(19)


class Lit20(OperationBase):

    DISPLAY_NAME = "lit20"

    def stack_op(self, stack):
        stack.push(20)


class Lit21(OperationBase):

    DISPLAY_NAME = "lit21"

    def stack_op(self, stack):
        stack.push(21)


class Lit22(OperationBase):

    DISPLAY_NAME = "lit22"

    def stack_op(self, stack):
        stack.push(22)


class Lit23(OperationBase):

    DISPLAY_NAME = "lit23"

    def stack_op(self, stack):
        stack.push(23)


class Lit24(OperationBase):

    DISPLAY_NAME = "lit24"

    def stack_op(self, stack):
        stack.push(24)


class Lit25(OperationBase):

    DISPLAY_NAME = "lit25"

    def stack_op(self, stack):
        stack.push(25)


class Lit26(OperationBase):

    DISPLAY_NAME = "lit26"

    def stack_op(self, stack):
        stack.push(26)


class Lit27(OperationBase):

    DISPLAY_NAME = "lit27"

    def stack_op(self, stack):
        stack.push(27)


class Lit28(OperationBase):

    DISPLAY_NAME = "lit28"

    def stack_op(self, stack):
        stack.push(28)


class Lit29(OperationBase):

    DISPLAY_NAME = "lit29"

    def stack_op(self, stack):
        stack.push(29)


class Lit30(OperationBase):

    DISPLAY_NAME = "lit30"

    def stack_op(self, stack):
        stack.push(30)


class Lit31(OperationBase):

    DISPLAY_NAME = "lit31"

    def stack_op(self, stack):
        stack.push(31)


class Reg0(OperationBase):

    DISPLAY_NAME = "reg0"


class Reg1(OperationBase):
    DISPLAY_NAME = "reg1"


class Reg2(OperationBase):
    DISPLAY_NAME = "reg2"


class Reg3(OperationBase):
    DISPLAY_NAME = "reg3"


class Reg4(OperationBase):
    DISPLAY_NAME = "reg4"


class Reg5(OperationBase):
    DISPLAY_NAME = "reg5"


class Reg6(OperationBase):
    DISPLAY_NAME = "reg6"


class Reg7(OperationBase):
    DISPLAY_NAME = "reg7"


class Reg8(OperationBase):
    DISPLAY_NAME = "reg8"


class Reg9(OperationBase):
    DISPLAY_NAME = "reg9"


class Reg10(OperationBase):
    DISPLAY_NAME = "reg10"


class Reg11(OperationBase):
    DISPLAY_NAME = "reg11"


class Reg12(OperationBase):
    DISPLAY_NAME = "reg12"


class Reg13(OperationBase):
    DISPLAY_NAME = "reg13"


class Reg14(OperationBase):
    DISPLAY_NAME = "reg14"


class Reg15(OperationBase):
    DISPLAY_NAME = "reg15"


class Reg16(OperationBase):
    DISPLAY_NAME = "reg16"


class Reg17(OperationBase):
    DISPLAY_NAME = "reg17"


class Reg18(OperationBase):
    DISPLAY_NAME = "reg18"


class Reg19(OperationBase):
    DISPLAY_NAME = "reg19"


class Reg20(OperationBase):
    DISPLAY_NAME = "reg20"


class Reg21(OperationBase):
    DISPLAY_NAME = "reg21"


class Reg22(OperationBase):
    DISPLAY_NAME = "reg22"


class Reg23(OperationBase):
    DISPLAY_NAME = "reg23"


class Reg24(OperationBase):
    DISPLAY_NAME = "reg24"


class Reg25(OperationBase):
    DISPLAY_NAME = "reg25"


class Reg26(OperationBase):
    DISPLAY_NAME = "reg26"


class Reg27(OperationBase):
    DISPLAY_NAME = "reg27"


class Reg28(OperationBase):
    DISPLAY_NAME = "reg28"


class Reg29(OperationBase):
    DISPLAY_NAME = "reg29"


class Reg30(OperationBase):
    DISPLAY_NAME = "reg30"


class Reg31(OperationBase):
    DISPLAY_NAME = "reg31"


class Breg0(OperationBase):
    DISPLAY_NAME = "breg0"
    PARAMETERS = ["sleb"]


class Breg1(OperationBase):
    DISPLAY_NAME = "breg1"
    PARAMETERS = ["sleb"]


class Breg2(OperationBase):
    DISPLAY_NAME = "breg2"
    PARAMETERS = ["sleb"]


class Breg3(OperationBase):
    DISPLAY_NAME = "breg3"
    PARAMETERS = ["sleb"]


class Breg4(OperationBase):
    DISPLAY_NAME = "breg4"
    PARAMETERS = ["sleb"]


class Breg5(OperationBase):
    DISPLAY_NAME = "breg5"
    PARAMETERS = ["sleb"]


class Breg6(OperationBase):
    DISPLAY_NAME = "breg6"
    PARAMETERS = ["sleb"]


class Breg7(OperationBase):
    DISPLAY_NAME = "breg7"
    PARAMETERS = ["sleb"]


class Breg8(OperationBase):
    DISPLAY_NAME = "breg8"
    PARAMETERS = ["sleb"]


class Breg9(OperationBase):
    DISPLAY_NAME = "breg9"
    PARAMETERS = ["sleb"]


class Breg10(OperationBase):
    DISPLAY_NAME = "breg10"
    PARAMETERS = ["sleb"]


class Breg11(OperationBase):
    DISPLAY_NAME = "breg11"
    PARAMETERS = ["sleb"]


class Breg12(OperationBase):
    DISPLAY_NAME = "breg12"
    PARAMETERS = ["sleb"]


class Breg13(OperationBase):
    DISPLAY_NAME = "breg13"
    PARAMETERS = ["sleb"]


class Breg14(OperationBase):
    DISPLAY_NAME = "breg14"
    PARAMETERS = ["sleb"]


class Breg15(OperationBase):
    DISPLAY_NAME = "breg15"
    PARAMETERS = ["sleb"]


class Breg16(OperationBase):
    DISPLAY_NAME = "breg16"
    PARAMETERS = ["sleb"]


class Breg17(OperationBase):
    DISPLAY_NAME = "breg17"
    PARAMETERS = ["sleb"]


class Breg18(OperationBase):
    DISPLAY_NAME = "breg18"
    PARAMETERS = ["sleb"]


class Breg19(OperationBase):
    DISPLAY_NAME = "breg19"
    PARAMETERS = ["sleb"]


class Breg20(OperationBase):
    DISPLAY_NAME = "breg20"
    PARAMETERS = ["sleb"]


class Breg21(OperationBase):
    DISPLAY_NAME = "breg21"
    PARAMETERS = ["sleb"]


class Breg22(OperationBase):
    DISPLAY_NAME = "breg22"
    PARAMETERS = ["sleb"]


class Breg23(OperationBase):
    DISPLAY_NAME = "breg23"
    PARAMETERS = ["sleb"]


class Breg24(OperationBase):
    DISPLAY_NAME = "breg24"
    PARAMETERS = ["sleb"]


class Breg25(OperationBase):
    DISPLAY_NAME = "breg25"
    PARAMETERS = ["sleb"]


class Breg26(OperationBase):
    DISPLAY_NAME = "breg26"
    PARAMETERS = ["sleb"]


class Breg27(OperationBase):
    DISPLAY_NAME = "breg27"
    PARAMETERS = ["sleb"]


class Breg28(OperationBase):
    DISPLAY_NAME = "breg28"
    PARAMETERS = ["sleb"]


class Breg29(OperationBase):
    DISPLAY_NAME = "breg29"
    PARAMETERS = ["sleb"]


class Breg30(OperationBase):
    DISPLAY_NAME = "breg30"
    PARAMETERS = ["sleb"]


class Breg31(OperationBase):
    DISPLAY_NAME = "breg31"
    PARAMETERS = ["sleb"]


class Regx(OperationBase):
    DISPLAY_NAME = "regx"
    PARAMETERS = ["uleb"]


class Fbreg(OperationBase):
    DISPLAY_NAME = "fbreg"
    PARAMETERS = ["sleb"]


class Bregx(OperationBase):
    DISPLAY_NAME = "bregx"
    PARAMETERS = ["uleb", "sleb"]


class Piece(OperationBase):
    DISPLAY_NAME = "piece"
    PARAMETERS = ["uleb"]


class Deref_Size(OperationBase):
    DISPLAY_NAME = "deref_size"
    PARAMETERS = ["u8"]


class Xderef_Size(OperationBase):
    DISPLAY_NAME = "xderef_size"
    PARAMETERS = ["u8"]


class Nop(OperationBase):
    DISPLAY_NAME = "nop"


class Push_Object_Address(OperationBase):
    DISPLAY_NAME = "push_object_address"


class Call2(OperationBase):
    DISPLAY_NAME = "call2"
    PARAMETERS = ["u16"]


class Call4(OperationBase):
    DISPLAY_NAME = "call4"
    PARAMETERS = ["u32"]


class Call_Ref(OperationBase):
    DISPLAY_NAME = "call_ref"
    PARAMETERS = ["native_address"]


class Form_Tls_Address(OperationBase):
    DISPLAY_NAME = "form_tls_address"


class Call_Frame_Cfa(OperationBase):
    DISPLAY_NAME = "call_frame_cfa"


class Bit_Piece(OperationBase):
    DISPLAY_NAME = "bit_piece"
    PARAMETERS = ["uleb", "uleb"]


class Implicit_Value(OperationBase):
    DISPLAY_NAME = "implicit_value"
    PARAMETERS = ["uleb"]


class Stack_Value(OperationBase):
    DISPLAY_NAME = "stack_value"


class Implicit_Pointer(OperationBase):
    DISPLAY_NAME = "implicit_pointer"
    PARAMETERS = ["native_address", "sleb"]


class Addrx(OperationBase):
    DISPLAY_NAME = "addrx"
    PARAMETERS = ["uleb"]


class Constx(OperationBase):
    DISPLAY_NAME = "constx"
    PARAMETERS = ["uleb"]


class Entry_Value(OperationBase):
    DISPLAY_NAME = "entry_value"
    PARAMETERS = ["uleb"]


class Const_Type(OperationBase):
    DISPLAY_NAME = "const_type"
    PARAMETERS = ["uleb", "u8"]


class Regval_Type(OperationBase):
    DISPLAY_NAME = "regval_type"
    PARAMETERS = ["uleb", "uleb"]


class Deref_Type(OperationBase):
    DISPLAY_NAME = "deref_type"
    PARAMETERS = ["u8", "uleb"]


class Xderef_Type(OperationBase):
    DISPLAY_NAME = "xderef_type"
    PARAMETERS = ["u8", "uleb"]


class Convert(OperationBase):
    DISPLAY_NAME = "convert"
    PARAMETERS = ["uleb"]


class Reinterpret(OperationBase):
    DISPLAY_NAME = "reinterpret"
    PARAMETERS = ["uleb"]


class Lo_User(OperationBase):
    DISPLAY_NAME = "lo_user"


class Hi_User(OperationBase):
    DISPLAY_NAME = "hi_user"


class Gnu_Push_Tls_Address(OperationBase):
    DISPLAY_NAME = "GNU_push_tls_address"


class Gnu_Uninit(OperationBase):
    DISPLAY_NAME = "GNU_uninit"


class Gnu_Encoded_Addr(OperationBase):
    DISPLAY_NAME = "GNU_encoded_addr"


class Gnu_Implicit_Pointer(OperationBase):
    DISPLAY_NAME = "GNU_implicit_pointer"


class Gnu_Entry_Value(OperationBase):
    DISPLAY_NAME = "GNU_entry_value"
    PARAMETERS = ["uleb"]


class Gnu_Const_Type(OperationBase):
    DISPLAY_NAME = "GNU_const_type"
    PARAMETERS = ["uleb", "u8"]  # , "block1"


class Gnu_Regval_Type(OperationBase):
    DISPLAY_NAME = "GNU_regval_type"
    PARAMETERS = ["uleb", "uleb"]


class Gnu_Deref_Type(OperationBase):
    DISPLAY_NAME = "GNU_deref_type"
    PARAMETERS = ["u8", "uleb"]


class Gnu_Convert(OperationBase):
    DISPLAY_NAME = "GNU_convert"
    PARAMETERS = ["uleb"]


class Gnu_Reinterpret(OperationBase):
    DISPLAY_NAME = "GNU_reinterpret"
    PARAMETERS = ["uleb"]


class Gnu_Parameter_Ref(OperationBase):
    DISPLAY_NAME = "GNU_parameter_ref"
    PARAMETERS = ["native_address"]


class Gnu_Addr_Index(OperationBase):
    DISPLAY_NAME = "GNU_addr_index"


class Gnu_Const_Index(OperationBase):
    DISPLAY_NAME = "GNU_const_index"


class Hp_Unknown(OperationBase):
    DISPLAY_NAME = "HP_unknown"


class Hp_Is_Value(OperationBase):
    DISPLAY_NAME = "HP_is_value"


class Hp_Fltconst4(OperationBase):
    DISPLAY_NAME = "HP_fltconst4"


class Hp_Fltconst8(OperationBase):
    DISPLAY_NAME = "HP_fltconst8"


class Hp_Mod_Range(OperationBase):
    DISPLAY_NAME = "HP_mod_range"


class Hp_Unmod_Range(OperationBase):
    DISPLAY_NAME = "HP_unmod_range"


class Hp_Tls(OperationBase):
    DISPLAY_NAME = "HP_tls"


class Gi_Omp_Thread_Num(OperationBase):
    DISPLAY_NAME = "GI_omp_thread_num"


OP_MAP = {
    constants.Operation.addr: Addr,
    constants.Operation.deref: Deref,
    constants.Operation.const1u: Const1U,
    constants.Operation.const1s: Const1S,
    constants.Operation.const2u: Const2U,
    constants.Operation.const2s: Const2S,
    constants.Operation.const4u: Const4U,
    constants.Operation.const4s: Const4S,
    constants.Operation.const8u: Const8U,
    constants.Operation.const8s: Const8S,
    constants.Operation.constu: Constu,
    constants.Operation.consts: Consts,
    constants.Operation.dup: Dup,
    constants.Operation.drop: Drop,
    constants.Operation.over: Over,
    constants.Operation.pick: Pick,
    constants.Operation.swap: Swap,
    constants.Operation.rot: Rot,
    constants.Operation.xderef: Xderef,
    constants.Operation.abs: Abs,
    constants.Operation.and_: And_,
    constants.Operation.div: Div,
    constants.Operation.minus: Minus,
    constants.Operation.mod: Mod,
    constants.Operation.mul: Mul,
    constants.Operation.neg: Neg,
    constants.Operation.not_: Not_,
    constants.Operation.or_: Or_,
    constants.Operation.plus: Plus,
    constants.Operation.plus_uconst: Plus_Uconst,
    constants.Operation.shl: Shl,
    constants.Operation.shr: Shr,
    constants.Operation.shra: Shra,
    constants.Operation.xor: Xor,
    constants.Operation.bra: Bra,
    constants.Operation.eq: Eq,
    constants.Operation.ge: Ge,
    constants.Operation.gt: Gt,
    constants.Operation.le: Le,
    constants.Operation.lt: Lt,
    constants.Operation.ne: Ne,
    constants.Operation.skip: Skip,
    constants.Operation.lit0: Lit0,
    constants.Operation.lit1: Lit1,
    constants.Operation.lit2: Lit2,
    constants.Operation.lit3: Lit3,
    constants.Operation.lit4: Lit4,
    constants.Operation.lit5: Lit5,
    constants.Operation.lit6: Lit6,
    constants.Operation.lit7: Lit7,
    constants.Operation.lit8: Lit8,
    constants.Operation.lit9: Lit9,
    constants.Operation.lit10: Lit10,
    constants.Operation.lit11: Lit11,
    constants.Operation.lit12: Lit12,
    constants.Operation.lit13: Lit13,
    constants.Operation.lit14: Lit14,
    constants.Operation.lit15: Lit15,
    constants.Operation.lit16: Lit16,
    constants.Operation.lit17: Lit17,
    constants.Operation.lit18: Lit18,
    constants.Operation.lit19: Lit19,
    constants.Operation.lit20: Lit20,
    constants.Operation.lit21: Lit21,
    constants.Operation.lit22: Lit22,
    constants.Operation.lit23: Lit23,
    constants.Operation.lit24: Lit24,
    constants.Operation.lit25: Lit25,
    constants.Operation.lit26: Lit26,
    constants.Operation.lit27: Lit27,
    constants.Operation.lit28: Lit28,
    constants.Operation.lit29: Lit29,
    constants.Operation.lit30: Lit30,
    constants.Operation.lit31: Lit31,
    constants.Operation.reg0: Reg0,
    constants.Operation.reg1: Reg1,
    constants.Operation.reg2: Reg2,
    constants.Operation.reg3: Reg3,
    constants.Operation.reg4: Reg4,
    constants.Operation.reg5: Reg5,
    constants.Operation.reg6: Reg6,
    constants.Operation.reg7: Reg7,
    constants.Operation.reg8: Reg8,
    constants.Operation.reg9: Reg9,
    constants.Operation.reg10: Reg10,
    constants.Operation.reg11: Reg11,
    constants.Operation.reg12: Reg12,
    constants.Operation.reg13: Reg13,
    constants.Operation.reg14: Reg14,
    constants.Operation.reg15: Reg15,
    constants.Operation.reg16: Reg16,
    constants.Operation.reg17: Reg17,
    constants.Operation.reg18: Reg18,
    constants.Operation.reg19: Reg19,
    constants.Operation.reg20: Reg20,
    constants.Operation.reg21: Reg21,
    constants.Operation.reg22: Reg22,
    constants.Operation.reg23: Reg23,
    constants.Operation.reg24: Reg24,
    constants.Operation.reg25: Reg25,
    constants.Operation.reg26: Reg26,
    constants.Operation.reg27: Reg27,
    constants.Operation.reg28: Reg28,
    constants.Operation.reg29: Reg29,
    constants.Operation.reg30: Reg30,
    constants.Operation.reg31: Reg31,
    constants.Operation.breg0: Breg0,
    constants.Operation.breg1: Breg1,
    constants.Operation.breg2: Breg2,
    constants.Operation.breg3: Breg3,
    constants.Operation.breg4: Breg4,
    constants.Operation.breg5: Breg5,
    constants.Operation.breg6: Breg6,
    constants.Operation.breg7: Breg7,
    constants.Operation.breg8: Breg8,
    constants.Operation.breg9: Breg9,
    constants.Operation.breg10: Breg10,
    constants.Operation.breg11: Breg11,
    constants.Operation.breg12: Breg12,
    constants.Operation.breg13: Breg13,
    constants.Operation.breg14: Breg14,
    constants.Operation.breg15: Breg15,
    constants.Operation.breg16: Breg16,
    constants.Operation.breg17: Breg17,
    constants.Operation.breg18: Breg18,
    constants.Operation.breg19: Breg19,
    constants.Operation.breg20: Breg20,
    constants.Operation.breg21: Breg21,
    constants.Operation.breg22: Breg22,
    constants.Operation.breg23: Breg23,
    constants.Operation.breg24: Breg24,
    constants.Operation.breg25: Breg25,
    constants.Operation.breg26: Breg26,
    constants.Operation.breg27: Breg27,
    constants.Operation.breg28: Breg28,
    constants.Operation.breg29: Breg29,
    constants.Operation.breg30: Breg30,
    constants.Operation.breg31: Breg31,
    constants.Operation.regx: Regx,
    constants.Operation.fbreg: Fbreg,
    constants.Operation.bregx: Bregx,
    constants.Operation.piece: Piece,
    constants.Operation.deref_size: Deref_Size,
    constants.Operation.xderef_size: Xderef_Size,
    constants.Operation.nop: Nop,
    constants.Operation.push_object_address: Push_Object_Address,
    constants.Operation.call2: Call2,
    constants.Operation.call4: Call4,
    constants.Operation.call_ref: Call_Ref,
    constants.Operation.form_tls_address: Form_Tls_Address,
    constants.Operation.call_frame_cfa: Call_Frame_Cfa,
    constants.Operation.bit_piece: Bit_Piece,
    constants.Operation.implicit_value: Implicit_Value,
    constants.Operation.stack_value: Stack_Value,
    constants.Operation.implicit_pointer: Implicit_Pointer,
    constants.Operation.addrx: Addrx,
    constants.Operation.constx: Constx,
    constants.Operation.entry_value: Entry_Value,
    constants.Operation.const_type: Const_Type,
    constants.Operation.regval_type: Regval_Type,
    constants.Operation.deref_type: Deref_Type,
    constants.Operation.xderef_type: Xderef_Type,
    constants.Operation.convert: Convert,
    constants.Operation.reinterpret: Reinterpret,
    constants.Operation.lo_user: Lo_User,
    constants.Operation.hi_user: Hi_User,
    constants.Operation.GNU_push_tls_address: Gnu_Push_Tls_Address,
    constants.Operation.GNU_uninit: Gnu_Uninit,
    constants.Operation.GNU_encoded_addr: Gnu_Encoded_Addr,
    constants.Operation.GNU_implicit_pointer: Gnu_Implicit_Pointer,
    constants.Operation.GNU_entry_value: Gnu_Entry_Value,
    constants.Operation.GNU_const_type: Gnu_Const_Type,
    constants.Operation.GNU_regval_type: Gnu_Regval_Type,
    constants.Operation.GNU_deref_type: Gnu_Deref_Type,
    constants.Operation.GNU_convert: Gnu_Convert,
    constants.Operation.GNU_reinterpret: Gnu_Reinterpret,
    constants.Operation.GNU_parameter_ref: Gnu_Parameter_Ref,
    constants.Operation.GNU_addr_index: Gnu_Addr_Index,
    constants.Operation.GNU_const_index: Gnu_Const_Index,
    constants.Operation.HP_unknown: Hp_Unknown,
    constants.Operation.HP_is_value: Hp_Is_Value,
    constants.Operation.HP_fltconst4: Hp_Fltconst4,
    constants.Operation.HP_fltconst8: Hp_Fltconst8,
    constants.Operation.HP_mod_range: Hp_Mod_Range,
    constants.Operation.HP_unmod_range: Hp_Unmod_Range,
    +constants.Operation.HP_tls: Hp_Tls,
    constants.Operation.GI_omp_thread_num: Gi_Omp_Thread_Num,
}

######################
######################
######################


class StackMachine:

    def __init__(self, readers):
        self.stack = Stack()
        OperationBase.set_readers(readers)

    def evaluate(self, expr: bytes):
        OPs = constants.Operation

        image = io.BytesIO(expr)
        result: list[str] = []
        while True:
            data = image.read(1)
            if data == b"":
                break
            opcode_num = data[0]
            try:
                opcode = OPs(opcode_num)
            except ValueError:
                print(f"Opcode not found {opcode_num!r}")
                opcode_name = "<unk>"
            else:
                opcode_name = opcode.name  # noqa: F841
            op_klass = OP_MAP.get(opcode_num)
            if op_klass:
                operation = op_klass()
                operation.parse(image)
                result.append(str(operation))
                operation.stack_op(self.stack)
        return "; ".join(result)
