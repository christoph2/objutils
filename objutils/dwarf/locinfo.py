#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <github.com/Christoph2,
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

import functools

from objutils.dwarf import constants, encoding

NO_OPERANDS = (
    constants.DW_OP_reg0,
    constants.DW_OP_reg1,
    constants.DW_OP_reg2,
    constants.DW_OP_reg3,
    constants.DW_OP_reg4,
    constants.DW_OP_reg5,
    constants.DW_OP_reg6,
    constants.DW_OP_reg7,
    constants.DW_OP_reg8,
    constants.DW_OP_reg9,
    constants.DW_OP_reg10,
    constants.DW_OP_reg11,
    constants.DW_OP_reg12,
    constants.DW_OP_reg13,
    constants.DW_OP_reg14,
    constants.DW_OP_reg15,
    constants.DW_OP_reg16,
    constants.DW_OP_reg17,
    constants.DW_OP_reg18,
    constants.DW_OP_reg19,
    constants.DW_OP_reg20,
    constants.DW_OP_reg21,
    constants.DW_OP_reg22,
    constants.DW_OP_reg23,
    constants.DW_OP_reg24,
    constants.DW_OP_reg25,
    constants.DW_OP_reg26,
    constants.DW_OP_reg27,
    constants.DW_OP_reg28,
    constants.DW_OP_reg29,
    constants.DW_OP_reg30,
    constants.DW_OP_reg31,
    constants.DW_OP_deref,
    constants.DW_OP_dup,
    constants.DW_OP_drop,
    constants.DW_OP_over,
    constants.DW_OP_swap,
    constants.DW_OP_rot,
    constants.DW_OP_xderef,
    constants.DW_OP_abs,
    constants.DW_OP_and,
    constants.DW_OP_div,
    constants.DW_OP_minus,
    constants.DW_OP_mod,
    constants.DW_OP_mul,
    constants.DW_OP_neg,
    constants.DW_OP_not,
    constants.DW_OP_or,
    constants.DW_OP_plus,
    constants.DW_OP_shl,
    constants.DW_OP_shr,
    constants.DW_OP_shra,
    constants.DW_OP_xor,
    constants.DW_OP_eq,
    constants.DW_OP_ge,
    constants.DW_OP_gt,
    constants.DW_OP_le,
    constants.DW_OP_lt,
    constants.DW_OP_ne,
    constants.DW_OP_lit0,
    constants.DW_OP_lit1,
    constants.DW_OP_lit2,
    constants.DW_OP_lit3,
    constants.DW_OP_lit4,
    constants.DW_OP_lit5,
    constants.DW_OP_lit6,
    constants.DW_OP_lit7,
    constants.DW_OP_lit8,
    constants.DW_OP_lit9,
    constants.DW_OP_lit10,
    constants.DW_OP_lit11,
    constants.DW_OP_lit12,
    constants.DW_OP_lit13,
    constants.DW_OP_lit14,
    constants.DW_OP_lit15,
    constants.DW_OP_lit16,
    constants.DW_OP_lit17,
    constants.DW_OP_lit18,
    constants.DW_OP_lit19,
    constants.DW_OP_lit20,
    constants.DW_OP_lit21,
    constants.DW_OP_lit22,
    constants.DW_OP_lit23,
    constants.DW_OP_lit24,
    constants.DW_OP_lit25,
    constants.DW_OP_lit26,
    constants.DW_OP_lit27,
    constants.DW_OP_lit28,
    constants.DW_OP_lit29,
    constants.DW_OP_lit30,
    constants.DW_OP_lit31,
    constants.DW_OP_nop,
    constants.DW_OP_push_object_address,
    constants.DW_OP_form_tls_address,
    constants.DW_OP_call_frame_cfa,
    constants.DW_OP_stack_value,
)

SINGLE_BYTE = (
    constants.DW_OP_const1u,
    constants.DW_OP_const1s,
    constants.DW_OP_pick,
    constants.DW_OP_deref_size,
    constants.DW_OP_xderef_size,
)

DUAL_BYTES = (
    constants.DW_OP_const2u,
    constants.DW_OP_const2s,
    constants.DW_OP_skip,
    constants.DW_OP_bra,
    constants.DW_OP_call2,
)

FOUR_BYTES = (
    constants.DW_OP_const4u,
    constants.DW_OP_const4s,
    constants.DW_OP_call4,
    constants.DW_OP_call_ref, #  - 4 or 8 byte offset!!!
)

EIGHT_BYTES = (
    constants.DW_OP_const8u,
    constants.DW_OP_const8s,
)

SINGLE_ULEB = (
    constants.DW_OP_regx,
    constants.DW_OP_constu,
    constants.DW_OP_plus_uconst,
    constants.DW_OP_piece,
)

SINGLE_SLEB = (
    constants.DW_OP_consts,
    constants.DW_OP_breg0,
    constants.DW_OP_breg1,
    constants.DW_OP_breg2,
    constants.DW_OP_breg3,
    constants.DW_OP_breg4,
    constants.DW_OP_breg5,
    constants.DW_OP_breg6,
    constants.DW_OP_breg7,
    constants.DW_OP_breg8,
    constants.DW_OP_breg9,
    constants.DW_OP_breg10,
    constants.DW_OP_breg11,
    constants.DW_OP_breg12,
    constants.DW_OP_breg13,
    constants.DW_OP_breg14,
    constants.DW_OP_breg15,
    constants.DW_OP_breg16,
    constants.DW_OP_breg17,
    constants.DW_OP_breg18,
    constants.DW_OP_breg19,
    constants.DW_OP_breg20,
    constants.DW_OP_breg21,
    constants.DW_OP_breg22,
    constants.DW_OP_breg23,
    constants.DW_OP_breg24,
    constants.DW_OP_breg25,
    constants.DW_OP_breg26,
    constants.DW_OP_breg27,
    constants.DW_OP_breg28,
    constants.DW_OP_breg29,
    constants.DW_OP_breg30,
    constants.DW_OP_breg31,
    constants.DW_OP_fbreg,
)

ULEB128_FOLLOWED_BY_SLEB128 = (
    constants.DW_OP_bregx,
)

ULEB128_FOLLOWED_BY_ULEB128 = (
    constants.DW_OP_bit_piece,
)

ULEB128_FOLLOWED_BY_BLOCK = (
    constants.DW_OP_implicit_value,
)

MACHINE_WORD = (
    constants.DW_OP_addr,
)

class Operation(object):

    def __init__(self, opcode, operands):
        self._operands = list([operands])
        self._opcode = opcode

    def _getOperands(self):
        return self._operands

    def _getOpcode(self):
        return self._opcode

    def __str__(self):
        operands = ', '.join([str(o) for o in self.operands])
        if operands == '[]':
            return "<Operation %s>" % (constants.OPERATION_MAP[self.opcode], )
        else:
            return "<Operation %s(%s)>" % (constants.OPERATION_MAP[self.opcode], operands)

    __repr__ = __str__

    opcode = property(_getOpcode)
    operands = property(_getOperands)


class Dissector(object):

    def __init__(self, block, wordSize):
        self.block = block
        self.idx = 0
        self.wordSize = wordSize
        self._cache = {}

    def run(self):
        if isinstance(self.block, list):
            result = []
            while self.block:
                opcode = self.block.pop(0)
                decoder = self.lookupDecoder(opcode)
                try:
                    result.append(Operation(opcode, decoder(self)))
                except TypeError as e:
                    print("*** EXECPTION: %s" % e)
            return result
        else:
            return self.block   # TODO: Nur bis zu entgültigen Klärung!!!

    def lookupDecoder(self, opcode):
        result = None
        if opcode == 0x58:
            pass
        if opcode in self._cache:
            result = self._cache[opcode]
        else:
            for enc, func in self.ENCODINGS.items():
                if opcode in enc:
                    if enc == NO_OPERANDS:
                        pass
                    result = func
                    self._cache[opcode] = func
                    break
        if result is None:
            pass
        return result

    def readByte(self):
        return self.slice(1)

    def readDualBytes(self):
        return self.arrayToNumber(self.slice(2))

    def readFourBytes(self):
        return self.arrayToNumber(self.slice(4))

    def readEightByte(self):
        return self.arrayToNumber(self.slice(8))

    def readSingleULeb(self):
        length = self.getLEBLength()
        arr = self.slice(length)
        res = encoding.decodeULEB(arr)
        return res

    def readSingleSLeb(self):
        length = self.getLEBLength()
        arr = self.slice(length)
        res = encoding.decodeSLEB(arr)
        return res

    def readULebFollowedBySLeb(self):
        uleb = self.readSingleULeb()
        sleb = self.readSingleSLeb()
        return (uleb, sleb)

    def readULebFollowedByULeb(self):
        uleb1 = self.readSingleULeb()
        uleb2 = self.readSingleULeb()
        return (uleb1, uleb2)

    def readULebFollowedByBlock(self):
        length = self.readSingleULeb()
        block = self.slice(length)
        return (uleb, block)

    def readMachineWord(self):
        return self.arrayToNumber(self.slice(self.wordSize))

    def void(self):
        return []

    def getLEBLength(self):
        for idx, bval in enumerate(self.block, 1):
             if bval & 0x80 == 0:
                 break
        return idx

    def slice(self, length):
        arr =  self.block[ : length]
        if len(arr) != length:
            return None
        self.block = self.block[ length : ]
        return arr

    def arrayToNumber(self, arr):
        return functools.reduce(lambda x, y: (x * 256) + y, arr)

    ENCODINGS = {NO_OPERANDS : void, SINGLE_BYTE: readByte, DUAL_BYTES: readDualBytes, FOUR_BYTES: readFourBytes,
        EIGHT_BYTES: readEightByte, SINGLE_ULEB: readSingleULeb, SINGLE_SLEB: readSingleSLeb,
        ULEB128_FOLLOWED_BY_SLEB128: readULebFollowedBySLeb, ULEB128_FOLLOWED_BY_ULEB128: readULebFollowedByULeb,
        ULEB128_FOLLOWED_BY_BLOCK: readULebFollowedByBlock, MACHINE_WORD: readMachineWord
    }

##
##d=Dissector([0x03, 0x00, 0x00, 0x40,0x39], 4)
##result = d.run()
##for r in result:
##    print r
##
##def getLEB(values):
##    for idx, bval in enumerate(values, 1):
##         if bval & 0x80 == 0:
##             break
##    return values[ : idx], idx
##
##
##leb, endIndex = getLEB([199, 155, 127])
##
##

