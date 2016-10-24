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

from objutils.dwarf import constants


class StackOverflowError(Exception): pass
class StackUnderflowError(Exception): pass

class Stack(list):
    def __init__(self, size):
        self._size = size

    def push(self, value):
        if len(self) == self.size:
            raise StackOverflowError()
        self.append(value)

    def pop(self):
        if len(self) == 0:
            raise StackUnderflowError()
        else:
            return super(Stack, self).pop(-1)

    def notEmpty(self):
        return len(self) > 0

    def _getSize(self):
        return self._size

    size = property(_getSize)


class LiteralEncoding(object):
    __slots__ = ['_value', '_maximum', '_minimum']

    def __init__(self, minimum = None, maximum = None, value = None):
        self._value = value
        self._minimum = minimum
        self._maximum = maximum

    def _setValue(self, value):
        if value < self._minimum:
            raise ValueError("Value must be at least '{0:d}'".format(self._minimum))
        elif value > self._maximum:
            raise ValueError("Value must be at most '{0:d}'".format(self._maximum))
        self._value = value

    def _getValue(self):
        return self._value

    value = property(_getValue, _setValue)


class UnsignedLiteral(LiteralEncoding):
    def __init__(self, value = None):
        super(UnsignedLiteral, self).__init__(constants.DW_OP_lit0, constants.DW_OP_lit31, value)


class AddressLiteral(LiteralEncoding):
    def __init__(self, width):
        self._width = width
        super(AddressLiteral, self).__init__(0, 2 ** width)

    def _getWidth(self):
        return self._width

    width = property(_getWidth)


class StackMachine(object):
    def __init__(self, stackSize = 256):
        self._stack = Stack(stackSize)

    def opcodeInRange(self, opcode, rangeTuple):
        rangeLo, rangeHi = rangeTuple

        return opcode in range(rangeLo, rangeHi + 1)

    def addr(self): pass
    def deref(self): pass
    def const1u(self): pass
    def const1s(self): pass
    def const2u(self): pass
    def const2s(self): pass
    def const4u(self): pass
    def const4s(self): pass
    def const8u(self): pass
    def const8s(self): pass
    def constu(self): pass
    def consts(self): pass
    def dup(self): pass
    def drop(self): pass
    def over(self): pass
    def pick(self): pass
    def swap(self): pass
    def rot(self): pass
    def xderef(self): pass
    def abs(self): pass
    def and_(self): pass
    def div(self): pass
    def minus(self): pass
    def mod(self): pass
    def mul(self): pass
    def neg(self): pass
    def not_(self): pass
    def or_(self): pass
    def plus(self): pass
    def plus_uconst(self): pass
    def shl(self): pass
    def shr(self): pass
    def shra(self): pass
    def xor(self): pass
    def skip(self): pass
    def bra(self): pass
    def eq(self): pass
    def ge(self): pass
    def gt(self): pass
    def le(self): pass
    def lt(self): pass
    def ne(self): pass
    def lit0(self): pass
    def lit1(self): pass
    def lit31(self): pass
    def reg0(self): pass
    def reg1(self): pass
    def reg31(self): pass
    def breg0(self): pass
    def breg1(self): pass
    def breg31(self): pass
    def regx(self): pass
    def fbreg(self): pass
    def bregx(self): pass
    def piece(self): pass
    def deref_size(self): pass
    def xderef_size(self): pass
    def nop(self): pass
    def push_object_address(self): pass
    def call2(self): pass
    def call4(self): pass
    def call_ref(self): pass
    def form_tls_address(self): pass
    def call_frame_cfa(self): pass
    def bit_piece(self): pass
    def implicit_value(self): pass
    def stack_value(self): pass

    @property
    def stack(self):
        return self._stack

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))

    def testMinimumAddress(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', -1)

    def testMaximumAddress(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', (2 ** 16) + 1)

