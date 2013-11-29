#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2013 by Christoph Schueler <github.com/Christoph2,
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

import constants

import unittest

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
            raise ValueError("Value must be at least '%u'" % self._minimum)
        elif value > self._maximum:
            raise ValueError("Value must be at most '%u'" % self._maximum)
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

    def _getStack(self):
        return self._stack

    stack = property(_getStack)


##
## Unittests.
##
class TestStack(unittest.TestCase):
    def setUp(self):
        self.stack = Stack(8)

    def tearDown(self):
        delattr(self, 'stack')

    def testPushPop(self):
        values = [1, 2, 5, 9, 23, 42, 68, 99]

        for value in values:
            self.stack.push(value)
        result = []
        while self.stack.notEmpty():
            result.append(self.stack.pop())
        self.assertEquals(result, list(reversed(values)))

    def testRaisesUnderflowException(self):
        self.assertRaises(StackUnderflowError, self.stack.pop)

    def testRaisesOverflowException(self):
        values = [1, 2, 5, 9, 23, 42, 68, 99]

        for value in values:
            self.stack.push(value)

        self.assertRaises(StackOverflowError, self.stack.push, 101)

    def testGetSizeWorks(self):
        self.assertEquals(self.stack.size, 8)

    def testSizeIsReadonly(self):
        self.assertRaises(AttributeError, setattr, self.stack, 'size', 32)


class TestStackMachine(unittest.TestCase):
    def setUp(self):
        self.stackMachine = StackMachine(8)

    def tearDown(self):
        delattr(self, 'stackMachine')

    def testStackMachineHasAStack(self):
        sm = getattr(self.stackMachine, 'stack', None)
        self.assertIsNotNone(sm)

    def testOpcodeInRange(self):
        rangeTuple = (constants.DW_OP_lit0, constants.DW_OP_lit31)

        self.assertTrue(self.stackMachine.opcodeInRange(constants.DW_OP_lit0, rangeTuple))
        self.assertTrue(self.stackMachine.opcodeInRange(constants.DW_OP_lit1, rangeTuple))
        self.assertTrue(self.stackMachine.opcodeInRange(constants.DW_OP_lit31, rangeTuple))

    def testOpcodeNotInRange(self):
        rangeTuple = (constants.DW_OP_lit0, constants.DW_OP_lit31)

        self.assertFalse(self.stackMachine.opcodeInRange(constants.DW_OP_ne, rangeTuple))
        self.assertFalse(self.stackMachine.opcodeInRange(constants.DW_OP_reg0, rangeTuple))


class TestLiteralEncoding(unittest.TestCase):
    def setUp(self):
        self.literalEncoding = LiteralEncoding()

    def tearDown(self):
        delattr(self, 'literalEncoding')

    def testIsInitializedToNone(self):
        self.assertIsNone(self.literalEncoding.value)

    def testCouldBeWritten(self):
        self.literalEncoding = 23
        self.assertEquals(self.literalEncoding, 23)


class TestUnsignedLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = UnsignedLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))

    def testAtLeastOpLit0(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', constants.DW_OP_lit0 - 1)

    def testAtMostOpLit31(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', constants.DW_OP_lit31 + 1)


class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = AddressLiteral(16)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))

    def testMinimumAddress(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', -1)

    def testMaximumAddress(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', (2 ** 16) + 1)

"""
3.  DW_OP_const1u, DW_OP_const2u, DW_OP_const4u, DW_OP_const8u
    The single operand of a DW_OP_constnu operation provides a 1, 2, 4, or 8-byte unsigned
    integer constant, respectively.
4.  DW_OP_const1s , DW_OP_const2s, DW_OP_const4s, DW_OP_const8s
    The single operand of a DW_OP_constns operation provides a 1, 2, 4, or 8-byte signed
    integer constant, respectively.
5.  DW_OP_constu
    The single operand of the DW_OP_constu operation provides an unsigned LEB128 integer
    constant.
6.  DW_OP_consts
    The single operand of the DW_OP_consts operation provides a signed LEB128 integer
    constant.
"""



"""
class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = AddressLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))
class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = AddressLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))
class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = AddressLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))
class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = AddressLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), LiteralEncoding))

"""

def main():
    unittest.main()

if __name__ == '__main__':
    main()

