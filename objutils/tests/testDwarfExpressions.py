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

import objutils.dwarf.expressions as exp
import unittest


##
## Unittests.
##
class TestStack(unittest.TestCase):

    def setUp(self):
        self.stack = exp.Stack(8)

    def tearDown(self):
        delattr(self, 'stack')

    def testPushPop(self):
        values = [1, 2, 5, 9, 23, 42, 68, 99]

        for value in values:
            self.stack.push(value)
        result = []
        while self.stack.notEmpty():
            result.append(self.stack.pop())
        self.assertEqual(result, list(reversed(values)))

    def testRaisesUnderflowException(self):
        self.assertRaises(exp.StackUnderflowError, self.stack.pop)

    def testRaisesOverflowException(self):
        values = [1, 2, 5, 9, 23, 42, 68, 99]

        for value in values:
            self.stack.push(value)

        self.assertRaises(exp.StackOverflowError, self.stack.push, 101)

    def testGetSizeWorks(self):
        self.assertEqual(self.stack.size, 8)

    def testSizeIsReadonly(self):
        self.assertRaises(AttributeError, setattr, self.stack, 'size', 32)


class TestStackMachine(unittest.TestCase):

    def setUp(self):
        self.stackMachine = exp.StackMachine(8)

    def tearDown(self):
        delattr(self, 'stackMachine')

    def testStackMachineHasAStack(self):
        sm = getattr(self.stackMachine, 'stack', None)
        self.assertIsNotNone(sm)

    def testOpcodeInRange(self):
        rangeTuple = (exp.constants.DW_OP_lit0, exp.constants.DW_OP_lit31)

        self.assertTrue(self.stackMachine.opcodeInRange(exp.constants.DW_OP_lit0, rangeTuple))
        self.assertTrue(self.stackMachine.opcodeInRange(exp.constants.DW_OP_lit1, rangeTuple))
        self.assertTrue(self.stackMachine.opcodeInRange(exp.constants.DW_OP_lit31, rangeTuple))

    def testOpcodeNotInRange(self):
        rangeTuple = (exp.constants.DW_OP_lit0, exp.constants.DW_OP_lit31)

        self.assertFalse(self.stackMachine.opcodeInRange(exp.constants.DW_OP_ne, rangeTuple))
        self.assertFalse(self.stackMachine.opcodeInRange(exp.constants.DW_OP_reg0, rangeTuple))


class TestLiteralEncoding(unittest.TestCase):
    def setUp(self):
        self.literalEncoding = exp.LiteralEncoding()

    def tearDown(self):
        delattr(self, 'literalEncoding')

    def testIsInitializedToNone(self):
        self.assertIsNone(self.literalEncoding.value)

    def testCouldBeWritten(self):
        self.literalEncoding = 23
        self.assertEqual(self.literalEncoding, 23)


class TestUnsignedLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = exp.UnsignedLiteral(0)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), exp.LiteralEncoding))

    def testAtLeastOpLit0(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', exp.constants.DW_OP_lit0 - 1)

    def testAtMostOpLit31(self):
        self.assertRaises(ValueError, setattr, self.literal, 'value', exp.constants.DW_OP_lit31 + 1)


class TestAddressLiteral(unittest.TestCase):
    def setUp(self):
        self.literal = exp.AddressLiteral(16)

    def tearDown(self):
        delattr(self, 'literal')

    def testIsSubclassOfLiteralEncodig(self):
        self.assertTrue(issubclass(type(self.literal), exp.LiteralEncoding))

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


#class TestAddressLiteral(unittest.TestCase):
#    def setUp(self):
#        self.literal = exp.AddressLiteral(0)
#
#    def tearDown(self):
#        delattr(self, 'literal')
#
#    def testIsSubclassOfLiteralEncodig(self):
#        self.assertTrue(issubclass(type(self.literal), exp.LiteralEncoding))



def main():
    unittest.main()

if __name__ == '__main__':
    main()

