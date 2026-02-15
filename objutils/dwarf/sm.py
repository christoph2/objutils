#!/usr/bin/env python
# ruff: noqa: E402
# Imports come after module docstring (standard Python practice)

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

"""DWARF expression evaluator with stack machine architecture.

This module implements a complete stack machine for evaluating DWARF location
and attribute expressions. DWARF expressions are sequences of operations that
manipulate a stack to compute addresses, values, and other runtime information.

Architecture:
    The stack machine consists of:
    
    1. **Stack**: Simple stack data structure for operands
    2. **Operations**: Individual operation classes (150+ opcodes)
    3. **StackMachine**: Executor that decodes and runs expressions
    4. **Readers**: Binary data readers for operation parameters

DWARF Expression Types:
    - **Location expressions**: Compute variable/member addresses at runtime
    - **Simple locations**: Direct addresses (DW_OP_addr)
    - **Register locations**: Values in CPU registers (DW_OP_reg*)
    - **Register-relative**: Base register + offset (DW_OP_breg*)
    - **Composite locations**: Complex address calculations

Operation Categories:
    1. **Literals**: Push constants (DW_OP_lit*, DW_OP_const*, DW_OP_addr)
    2. **Arithmetic**: Add, subtract, multiply, divide, modulo
    3. **Bitwise**: AND, OR, XOR, shifts
    4. **Stack manipulation**: DUP, DROP, SWAP, PICK, OVER, ROT
    5. **Control flow**: Branch (DW_OP_bra), skip (DW_OP_skip)
    6. **Comparison**: Equal, less than, greater than, etc.
    7. **Register access**: Read CPU register values
    8. **Memory access**: Dereference pointers (DW_OP_deref)

Usage Example:
    ```python
    from objutils.dwarf.readers import DwarfReaders
    from objutils.dwarf.sm import StackMachine

    # Create readers for binary parsing
    readers = DwarfReaders(endianess=Endianess.Little, address_size=8)
    
    # Create and configure stack machine
    sm = StackMachine(readers)
    
    # Evaluate DWARF expression (as bytes)
    expr = b'\\x03\\x00\\x10\\x00\\x00\\x00\\x00\\x00\\x00'  # DW_OP_addr 0x1000
    result = sm.evaluate(expr)
    print(result)  # "addr(0x00001000)"
    ```

Advanced Example:
    ```python
    # Complex expression: breg5(offset) + const
    # DW_OP_breg5 <offset> DW_OP_plus_uconst <addend>
    expr = bytes([0x75, 0x10, 0x23, 0x20])  # breg5(16) + 32
    result = sm.evaluate(expr)
    # Result: "breg5(16); plus_uconst(32)"
    
    # Access final stack value
    final_value = sm.stack.tos if not sm.stack.empty() else None
    ```

Operation Parameter Types:
    Operations can have typed parameters read from the expression:
    - **native_address**: Address-sized integer (4 or 8 bytes)
    - **u8, u16, u32, u64**: Unsigned integers (fixed size)
    - **s8, s16, s32, s64**: Signed integers (fixed size)
    - **uleb**: Unsigned LEB128 (variable-length encoding)
    - **sleb**: Signed LEB128 (variable-length encoding)
    - **block1**: Byte block with 1-byte length prefix

Stack Machine Features:
    - Automatic opcode decoding from expression bytes
    - Parameter parsing based on operation definitions
    - Stack manipulation with proper error handling
    - Textual representation of expressions for debugging
    - Partial evaluation support (stops at undefined opcodes)

Implementation Pattern:
    Each DWARF operation is implemented as a class inheriting from OperationBase:
    
    ```python
    class Plus_Uconst(OperationBase):
        DISPLAY_NAME = "plus_uconst"
        PARAMETERS = ["uleb"]  # Read one ULEB parameter
        
        def stack_op(self, stack):
            # Pop value, add parameter, push result
            value = stack.pop()
            offset = self.result[0]  # Parameter value
            stack.push(value + offset)
    ```

DWARF Specification Reference:
    This implementation follows DWARF 4 specification, Section 2.5
    (Location Descriptions) and Section 2.6 (Location Expressions).

Limitations:
    - Not all 250+ DWARF operations are fully implemented
    - Some operations lack stack_op() implementations (placeholders)
    - Memory dereferencing operations require external context
    - Register values must be provided externally

See Also:
    - objutils.dwarf.constants: DWARF operation opcodes
    - objutils.dwarf.readers: Binary data readers
    - objutils.dwarf.traverser: Uses expressions for variable locations
"""

import io
from dataclasses import dataclass
from typing import Any

from construct import Array

from objutils.dwarf import constants


class Stack:
    """Simple LIFO stack for DWARF expression evaluation.

    Provides basic stack operations for the DWARF stack machine.
    Stores arbitrary Python values (integers, addresses, etc.).

    Attributes:
        _values: Internal list storing stack contents (private)

    Example:
        ```python
        stack = Stack()
        stack.push(42)
        stack.push(10)
        result = stack.pop()  # 10
        top = stack.tos       # 42
        stack.tos = 100       # Modify top without pop/push
        ```
    """

    def __init__(self):
        """Initialize empty stack."""
        self._values: list[Any] = []

    def push(self, value: Any) -> None:
        """Push value onto stack.

        Args:
            value: Value to push (typically int or address)
        """
        self._values.append(value)

    def pop(self) -> Any:
        """Pop and return top value from stack.

        Returns:
            Top stack value

        Raises:
            IndexError: If stack is empty
        """
        return self._values.pop()

    @property
    def tos(self) -> Any:
        """Get top-of-stack value without popping.

        Returns:
            Top stack value

        Raises:
            IndexError: If stack is empty
        """
        return self._values[-1]

    @tos.setter
    def tos(self, value: Any) -> None:
        """Set top-of-stack value without popping.

        Args:
            value: New value for top of stack

        Raises:
            IndexError: If stack is empty
        """
        self._values[-1] = value

    def get_at(self, index: int) -> Any:
        """Get value at index from top of stack.

        Args:
            index: Index from top (0 = top, 1 = second, etc.)

        Returns:
            Value at specified index

        Raises:
            IndexError: If index out of range

        Example:
            >>> stack = Stack()
            >>> stack.push(10)  # bottom
            >>> stack.push(20)
            >>> stack.push(30)  # top
            >>> stack.get_at(0)  # 30 (top)
            30
            >>> stack.get_at(1)  # 20
            20
            >>> stack.get_at(2)  # 10
            10
        """
        return self._values[-(index + 1)]

    def empty(self) -> bool:
        """Check if stack is empty.

        Returns:
            True if stack has no values, False otherwise
        """
        return len(self._values) == 0

    def __str__(self) -> str:
        """Return string representation of stack contents."""
        return f"Stack({self._values!r})"


@dataclass
class EvaluationResult:
    """Result of DWARF expression evaluation.

    Placeholder for future expansion. Could contain:
    - Final stack state
    - Expression interpretation
    - Error information
    - Location type (memory, register, etc.)
    """

    pass


######################
## Operation Classes ##
######################


class OperationBase:
    """Base class for all DWARF expression operations.

    Each DWARF operation (DW_OP_*) is represented by a subclass that:
    1. Defines parameters to read from expression bytes
    2. Implements stack manipulation logic
    3. Provides textual representation

    Class Attributes:
        PARAMETERS: List of parameter type names to read (e.g., ["uleb", "s16"])
        ARRAY_SIZE: Index of parameter containing array length (or None)
        DISPLAY_NAME: Human-readable operation name for string representation
        readers: Binary data readers (set via set_readers class method)
        READERS: Dict mapping type names to reader instances

    Instance Attributes:
        result: List of parsed parameter values
        data_block: Optional byte array for block operations

    Subclass Pattern:
        ```python
        class MyOp(OperationBase):
            DISPLAY_NAME = "my_op"
            PARAMETERS = ["uleb", "u16"]  # Read ULEB then U16

            def stack_op(self, stack):
                # Implement stack manipulation
                param1 = self.result[0]
                param2 = self.result[1]
                stack.push(param1 + param2)
        ```

    Parameter Types:
        - native_address: Address-sized int (4 or 8 bytes depending on arch)
        - u8, u16, u32, u64: Unsigned fixed-size integers
        - s8, s16, s32, s64: Signed fixed-size integers
        - uleb: Unsigned LEB128 variable-length encoding
        - sleb: Signed LEB128 variable-length encoding
        - block1: Byte block with 1-byte length prefix

    Note:
        Operations without stack_op() implementation are placeholders.
        Some complex operations (branches, derefs) require additional context.
    """

    PARAMETERS = []
    ARRAY_SIZE = None

    @classmethod
    def set_readers(cls, readers):
        """Configure binary readers for all operation classes.

        Must be called once before parsing expressions to set up
        architecture-specific readers (endianness, address size).

        Args:
            readers: DwarfReaders instance with configured parsers

        Note:
            This sets class-level attributes used by all operations.
        """
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
        """Parse operation parameters from byte stream.

        Reads parameter values according to PARAMETERS list.
        Handles optional array data blocks if ARRAY_SIZE is set.

        Args:
            image: Binary stream positioned after opcode byte

        Note:
            Parsed values are stored in self.result list.
            Array data is stored in self.data_block.
        """
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
        """Get operation value (reserved for future use)."""
        return

    def stack_op(self, stack):
        """Execute operation's effect on the stack.

        Subclasses override this to implement their specific stack manipulation.

        Args:
            stack: Stack instance to manipulate

        Note:
            Default implementation does nothing (no-op).
            Operations that modify the stack must override this.
        """
        pass

    def __str__(self):
        """Return textual representation of operation with parameters.

        Format: "op_name(param1, param2, ...)"
        Hex format for positive values, decimal for negative.
        """
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


##################################
## Literal/Constant Operations  ##
##################################


class Addr(OperationBase):
    """DW_OP_addr: Push absolute address onto stack.

    Parameters:
        native_address: Address value (4 or 8 bytes depending on architecture)

    Stack Effect: [] -> [address]
    """

    DISPLAY_NAME = "addr"
    PARAMETERS = ["native_address"]

    def stack_op(self, stack):
        value = self.result[0]
        stack.push(value)


class Deref(OperationBase):
    """DW_OP_deref: Dereference address at top of stack.

    Pops address, reads value at that address, pushes result.
    Requires external memory context (not fully implemented).

    Stack Effect: [address] -> [value]
    """

    DISPLAY_NAME = "deref"


class Const1U(OperationBase):
    """DW_OP_const1u: Push 1-byte unsigned constant.

    Parameters:
        u8: Unsigned 8-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const1u"
    PARAMETERS = ["u8"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const1S(OperationBase):
    """DW_OP_const1s: Push 1-byte signed constant.

    Parameters:
        s8: Signed 8-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const1s"
    PARAMETERS = ["s8"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const2U(OperationBase):
    """DW_OP_const2u: Push 2-byte unsigned constant.

    Parameters:
        u16: Unsigned 16-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const2u"
    PARAMETERS = ["u16"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const2S(OperationBase):
    """DW_OP_const2s: Push 2-byte signed constant.

    Parameters:
        s16: Signed 16-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const2s"
    PARAMETERS = ["s16"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const4U(OperationBase):
    """DW_OP_const4u: Push 4-byte unsigned constant.

    Parameters:
        u32: Unsigned 32-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const4u"
    PARAMETERS = ["u32"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const4S(OperationBase):
    """DW_OP_const4s: Push 4-byte signed constant.

    Parameters:
        s32: Signed 32-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const4s"
    PARAMETERS = ["s32"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const8U(OperationBase):
    """DW_OP_const8u: Push 8-byte unsigned constant.

    Parameters:
        u64: Unsigned 64-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const8u"
    PARAMETERS = ["u64"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Const8S(OperationBase):
    """DW_OP_const8s: Push 8-byte signed constant.

    Parameters:
        s64: Signed 64-bit value

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "const8s"
    PARAMETERS = ["s64"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Constu(OperationBase):
    """DW_OP_constu: Push unsigned LEB128 constant.

    Parameters:
        uleb: Unsigned variable-length integer

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "constu"
    PARAMETERS = ["uleb"]

    def stack_op(self, stack):
        stack.push(self.result[0])


class Consts(OperationBase):
    """DW_OP_consts: Push signed LEB128 constant.

    Parameters:
        sleb: Signed variable-length integer

    Stack Effect: [] -> [value]
    """

    DISPLAY_NAME = "consts"
    PARAMETERS = ["sleb"]

    def stack_op(self, stack):
        stack.push(self.result[0])


#################################
## Stack Manipulation Operations ##
#################################


class Dup(OperationBase):
    """DW_OP_dup: Duplicate top stack value.

    Stack Effect: [a] -> [a, a]
    """

    DISPLAY_NAME = "dup"

    def stack_op(self, stack):
        a = stack.pop()
        stack.push(a)
        stack.push(a)


class Drop(OperationBase):
    """DW_OP_drop: Pop and discard top stack value.

    Stack Effect: [a] -> []
    """

    DISPLAY_NAME = "drop"

    def stack_op(self, stack):
        stack.pop()


class Over(OperationBase):
    """DW_OP_over: Copy second stack value to top.

    Stack Effect: [a, b] -> [a, b, a]
    """

    DISPLAY_NAME = "over"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a)
        stack.push(b)
        stack.push(a)


class Pick(OperationBase):
    """DW_OP_pick: Copy nth stack value to top.

    Parameters:
        u8: Index of value to copy (0 = top)

    Stack Effect: [a, b, c, ...] -> [a, b, c, ..., value_at_index]
    """

    DISPLAY_NAME = "pick"
    PARAMETERS = ["u8"]

    def stack_op(self, stack):
        index = self.result[0]
        value = stack.get_at(index)
        stack.push(value)


class Swap(OperationBase):
    """DW_OP_swap: Swap top two stack values.

    Stack Effect: [a, b] -> [b, a]
    """

    DISPLAY_NAME = "swap"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(b)
        stack.push(a)


class Rot(OperationBase):
    """DW_OP_rot: Rotate top three stack values.

    Stack Effect: [a, b, c] -> [b, c, a]
    """

    DISPLAY_NAME = "rot"

    def stack_op(self, stack):
        c = stack.pop()
        b = stack.pop()
        a = stack.pop()
        stack.push(b)
        stack.push(c)
        stack.push(a)


class Xderef(OperationBase):
    """DW_OP_xderef: Extended dereference (with address space).

    Pops address space ID and address, dereferences.
    Requires external memory context.

    Stack Effect: [address_space, address] -> [value]
    """

    DISPLAY_NAME = "xderef"


#############################
## Arithmetic Operations   ##
#############################


class Abs(OperationBase):
    """DW_OP_abs: Absolute value of top stack value.

    Stack Effect: [a] -> [|a|]
    """

    DISPLAY_NAME = "abs"

    def stack_op(self, stack):
        a = stack.pop()
        stack.push(abs(a))


class And_(OperationBase):
    """DW_OP_and: Bitwise AND of top two values.

    Stack Effect: [a, b] -> [a & b]
    """

    DISPLAY_NAME = "and_"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a & b)


class Div(OperationBase):
    """DW_OP_div: Signed division of top two values.

    Stack Effect: [a, b] -> [a / b]
    """

    DISPLAY_NAME = "div"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a // b)


class Minus(OperationBase):
    """DW_OP_minus: Subtraction of top two values.

    Stack Effect: [a, b] -> [a - b]
    """

    DISPLAY_NAME = "minus"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a - b)


class Mod(OperationBase):
    """DW_OP_mod: Modulo of top two values.

    Stack Effect: [a, b] -> [a % b]
    """

    DISPLAY_NAME = "mod"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a % b)


class Mul(OperationBase):
    """DW_OP_mul: Multiplication of top two values.

    Stack Effect: [a, b] -> [a * b]
    """

    DISPLAY_NAME = "mul"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a * b)


class Neg(OperationBase):
    """DW_OP_neg: Negation of top stack value.

    Stack Effect: [a] -> [-a]
    """

    DISPLAY_NAME = "neg"

    def stack_op(self, stack):
        a = stack.pop()
        stack.push(-a)


class Not_(OperationBase):
    """DW_OP_not: Bitwise NOT of top stack value.

    Stack Effect: [a] -> [~a]
    """

    DISPLAY_NAME = "not_"

    def stack_op(self, stack):
        a = stack.pop()
        stack.push(~a)


class Or_(OperationBase):
    """DW_OP_or: Bitwise OR of top two values.

    Stack Effect: [a, b] -> [a | b]
    """

    DISPLAY_NAME = "or_"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a | b)


class Plus(OperationBase):
    """DW_OP_plus: Addition of top two values.

    Stack Effect: [a, b] -> [a + b]
    """

    DISPLAY_NAME = "plus"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a + b)


class Plus_Uconst(OperationBase):
    """DW_OP_plus_uconst: Add unsigned constant to top value.

    Parameters:
        uleb: Unsigned constant to add

    Stack Effect: [a] -> [a + constant]

    Note:
        This is commonly used for struct member offsets.
    """

    DISPLAY_NAME = "plus_uconst"
    PARAMETERS = ["uleb"]

    def stack_op(self, stack):
        a = stack.pop()
        constant = self.result[0]
        stack.push(a + constant)


class Shl(OperationBase):
    """DW_OP_shl: Shift left.

    Stack Effect: [value, shift_amount] -> [value << shift_amount]
    """

    DISPLAY_NAME = "shl"

    def stack_op(self, stack):
        shift = stack.pop()
        value = stack.pop()
        stack.push(value << shift)


class Shr(OperationBase):
    """DW_OP_shr: Logical shift right.

    Stack Effect: [value, shift_amount] -> [value >> shift_amount]
    """

    DISPLAY_NAME = "shr"

    def stack_op(self, stack):
        shift = stack.pop()
        value = stack.pop()
        stack.push(value >> shift)


class Shra(OperationBase):
    """DW_OP_shra: Arithmetic shift right (sign-extending).

    Stack Effect: [value, shift_amount] -> [value >> shift_amount]
    """

    DISPLAY_NAME = "shra"

    def stack_op(self, stack):
        shift = stack.pop()
        value = stack.pop()
        # Python's >> is arithmetic for negative numbers
        stack.push(value >> shift)


class Xor(OperationBase):
    """DW_OP_xor: Bitwise XOR of top two values.

    Stack Effect: [a, b] -> [a ^ b]
    """

    DISPLAY_NAME = "xor"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(a ^ b)


#############################
## Control Flow Operations ##
#############################


class Bra(OperationBase):
    """DW_OP_bra: Conditional branch.

    Parameters:
        s16: Signed offset to branch to (if TOS != 0)

    Stack Effect: [condition] -> []

    Note:
        Branches are not fully implemented (require expression rewriting).
    """

    DISPLAY_NAME = "bra"
    PARAMETERS = ["s16"]


class Eq(OperationBase):
    """DW_OP_eq: Test equality.

    Stack Effect: [a, b] -> [a == b ? 1 : 0]
    """

    DISPLAY_NAME = "eq"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a == b else 0)


class Ge(OperationBase):
    """DW_OP_ge: Test greater-than-or-equal.

    Stack Effect: [a, b] -> [a >= b ? 1 : 0]
    """

    DISPLAY_NAME = "ge"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a >= b else 0)


class Gt(OperationBase):
    """DW_OP_gt: Test greater-than.

    Stack Effect: [a, b] -> [a > b ? 1 : 0]
    """

    DISPLAY_NAME = "gt"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a > b else 0)


class Le(OperationBase):
    """DW_OP_le: Test less-than-or-equal.

    Stack Effect: [a, b] -> [a <= b ? 1 : 0]
    """

    DISPLAY_NAME = "le"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a <= b else 0)


class Lt(OperationBase):
    """DW_OP_lt: Test less-than.

    Stack Effect: [a, b] -> [a < b ? 1 : 0]
    """

    DISPLAY_NAME = "lt"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a < b else 0)


class Ne(OperationBase):
    """DW_OP_ne: Test inequality.

    Stack Effect: [a, b] -> [a != b ? 1 : 0]
    """

    DISPLAY_NAME = "ne"

    def stack_op(self, stack):
        b = stack.pop()
        a = stack.pop()
        stack.push(1 if a != b else 0)


class Skip(OperationBase):
    """DW_OP_skip: Unconditional branch.

    Parameters:
        s16: Signed offset to skip to

    Note:
        Branches are not fully implemented.
    """

    DISPLAY_NAME = "skip"
    PARAMETERS = ["s16"]


###############################
## Literal Integer Operations ##
##      (DW_OP_lit0-31)      ##
###############################
# These push small constants (0-31) without parameters


class Lit0(OperationBase):
    """DW_OP_lit0: Push literal 0. Stack Effect: [] -> [0]"""

    DISPLAY_NAME = "lit0"

    def stack_op(self, stack):
        stack.push(0)


class Lit1(OperationBase):
    """DW_OP_lit1: Push literal 1. Stack Effect: [] -> [1]"""

    DISPLAY_NAME = "lit1"

    def stack_op(self, stack):
        stack.push(1)


class Lit2(OperationBase):
    """DW_OP_lit2: Push literal 2. Stack Effect: [] -> [2]"""

    DISPLAY_NAME = "lit2"

    def stack_op(self, stack):
        stack.push(2)


class Lit3(OperationBase):
    """DW_OP_lit3: Push literal 3. Stack Effect: [] -> [3]"""

    DISPLAY_NAME = "lit3"

    def stack_op(self, stack):
        stack.push(3)


class Lit4(OperationBase):
    """DW_OP_lit4: Push literal 4. Stack Effect: [] -> [4]"""

    DISPLAY_NAME = "lit4"

    def stack_op(self, stack):
        stack.push(4)


class Lit5(OperationBase):
    """DW_OP_lit5: Push literal 5. Stack Effect: [] -> [5]"""

    DISPLAY_NAME = "lit5"

    def stack_op(self, stack):
        stack.push(5)


class Lit6(OperationBase):
    """DW_OP_lit6: Push literal 6. Stack Effect: [] -> [6]"""

    DISPLAY_NAME = "lit6"

    def stack_op(self, stack):
        stack.push(6)


class Lit7(OperationBase):
    """DW_OP_lit7: Push literal 7. Stack Effect: [] -> [7]"""

    DISPLAY_NAME = "lit7"

    def stack_op(self, stack):
        stack.push(7)


class Lit8(OperationBase):
    """DW_OP_lit8: Push literal 8. Stack Effect: [] -> [8]"""

    DISPLAY_NAME = "lit8"

    def stack_op(self, stack):
        stack.push(8)


class Lit9(OperationBase):
    """DW_OP_lit9: Push literal 9. Stack Effect: [] -> [9]"""

    DISPLAY_NAME = "lit9"

    def stack_op(self, stack):
        stack.push(9)


class Lit10(OperationBase):
    """DW_OP_lit10: Push literal 10. Stack Effect: [] -> [10]"""

    DISPLAY_NAME = "lit10"

    def stack_op(self, stack):
        stack.push(10)


class Lit11(OperationBase):
    """DW_OP_lit11: Push literal 11. Stack Effect: [] -> [11]"""

    DISPLAY_NAME = "lit11"

    def stack_op(self, stack):
        stack.push(11)


class Lit12(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit12"

    def stack_op(self, stack):
        stack.push(12)


class Lit13(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit13"

    def stack_op(self, stack):
        stack.push(13)


class Lit14(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit14"

    def stack_op(self, stack):
        stack.push(14)


class Lit15(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit15"

    def stack_op(self, stack):
        stack.push(15)


class Lit16(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit16"

    def stack_op(self, stack):
        stack.push(16)


class Lit17(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit17"

    def stack_op(self, stack):
        stack.push(17)


class Lit18(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit18"

    def stack_op(self, stack):
        stack.push(18)


class Lit19(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit19"

    def stack_op(self, stack):
        stack.push(19)


class Lit20(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit20"

    def stack_op(self, stack):
        stack.push(20)


class Lit21(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit21"

    def stack_op(self, stack):
        stack.push(21)


class Lit22(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit22"

    def stack_op(self, stack):
        stack.push(22)


class Lit23(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit23"

    def stack_op(self, stack):
        stack.push(23)


class Lit24(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit24"

    def stack_op(self, stack):
        stack.push(24)


class Lit25(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit25"

    def stack_op(self, stack):
        stack.push(25)


class Lit26(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit26"

    def stack_op(self, stack):
        stack.push(26)


class Lit27(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit27"

    def stack_op(self, stack):
        stack.push(27)


class Lit28(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit28"

    def stack_op(self, stack):
        stack.push(28)


class Lit29(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit29"

    def stack_op(self, stack):
        stack.push(29)


class Lit30(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit30"

    def stack_op(self, stack):
        stack.push(30)


class Lit31(OperationBase):
    """DW_OP_lit12-31: Push literals 12-31."""

    DISPLAY_NAME = "lit31"

    def stack_op(self, stack):
        stack.push(31)


######################################
## Register Operations (DW_OP_reg*) ##
##  Read register value onto stack  ##
######################################
# Note: These require external register context (not fully implemented)


class Reg0(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg0"


class Reg1(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg1"


class Reg2(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg2"


class Reg3(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg3"


class Reg4(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg4"


class Reg5(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg5"


class Reg6(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg6"


class Reg7(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg7"


class Reg8(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg8"


class Reg9(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg9"


class Reg10(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg10"


class Reg11(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg11"


class Reg12(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg12"


class Reg13(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg13"


class Reg14(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg14"


class Reg15(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg15"


class Reg16(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg16"


class Reg17(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg17"


class Reg18(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg18"


class Reg19(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg19"


class Reg20(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg20"


class Reg21(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg21"


class Reg22(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg22"


class Reg23(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg23"


class Reg24(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg24"


class Reg25(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg25"


class Reg26(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg26"


class Reg27(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg27"


class Reg28(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg28"


class Reg29(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg29"


class Reg30(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg30"


class Reg31(OperationBase):
    """DW_OP_reg0-31: Push register values. Stack Effect: [] -> [reg_value]"""

    DISPLAY_NAME = "reg31"


##############################################
## Base Register Operations (DW_OP_breg*) ##
##  Push register + offset to stack        ##
##############################################
# Note: These require external register context (not fully implemented)


class Breg0(OperationBase):
    """DW_OP_breg0-31: Push register + offset.

    Parameters: sleb (offset). Stack Effect: [] -> [reg + offset]
    """

    DISPLAY_NAME = "breg0"
    PARAMETERS = ["sleb"]


class Breg1(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg1"
    PARAMETERS = ["sleb"]


class Breg2(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg2"
    PARAMETERS = ["sleb"]


class Breg3(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg3"
    PARAMETERS = ["sleb"]


class Breg4(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg4"
    PARAMETERS = ["sleb"]


class Breg5(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg5"
    PARAMETERS = ["sleb"]


class Breg6(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg6"
    PARAMETERS = ["sleb"]


class Breg7(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg7"
    PARAMETERS = ["sleb"]


class Breg8(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg8"
    PARAMETERS = ["sleb"]


class Breg9(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg9"
    PARAMETERS = ["sleb"]


class Breg10(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg10"
    PARAMETERS = ["sleb"]


class Breg11(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg11"
    PARAMETERS = ["sleb"]


class Breg12(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg12"
    PARAMETERS = ["sleb"]


class Breg13(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg13"
    PARAMETERS = ["sleb"]


class Breg14(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg14"
    PARAMETERS = ["sleb"]


class Breg15(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg15"
    PARAMETERS = ["sleb"]


class Breg16(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg16"
    PARAMETERS = ["sleb"]


class Breg17(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg17"
    PARAMETERS = ["sleb"]


class Breg18(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg18"
    PARAMETERS = ["sleb"]


class Breg19(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg19"
    PARAMETERS = ["sleb"]


class Breg20(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg20"
    PARAMETERS = ["sleb"]


class Breg21(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg21"
    PARAMETERS = ["sleb"]


class Breg22(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg22"
    PARAMETERS = ["sleb"]


class Breg23(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg23"
    PARAMETERS = ["sleb"]


class Breg24(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg24"
    PARAMETERS = ["sleb"]


class Breg25(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg25"
    PARAMETERS = ["sleb"]


class Breg26(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg26"
    PARAMETERS = ["sleb"]


class Breg27(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg27"
    PARAMETERS = ["sleb"]


class Breg28(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg28"
    PARAMETERS = ["sleb"]


class Breg29(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg29"
    PARAMETERS = ["sleb"]


class Breg30(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg30"
    PARAMETERS = ["sleb"]


class Breg31(OperationBase):
    """DW_OP_breg0-31: Push register + offset. Stack Effect: [] -> [reg + offset]"""

    DISPLAY_NAME = "breg31"
    PARAMETERS = ["sleb"]


class Regx(OperationBase):
    """DW_OP_regx: Push value of register N (parameter). Stack Effect: [] -> [reg[N]]"""

    DISPLAY_NAME = "regx"
    PARAMETERS = ["uleb"]


class Fbreg(OperationBase):
    """DW_OP_fbreg: Push frame base + offset. Stack Effect: [] -> [frame_base + offset]"""

    DISPLAY_NAME = "fbreg"
    PARAMETERS = ["sleb"]


class Bregx(OperationBase):
    """DW_OP_bregx: Push register N + offset. Stack Effect: [] -> [reg[N] + offset]"""

    DISPLAY_NAME = "bregx"
    PARAMETERS = ["uleb", "sleb"]


class Piece(OperationBase):
    """DW_OP_piece: Describe piece of composite location. Stack Effect: [address] -> []"""

    DISPLAY_NAME = "piece"
    PARAMETERS = ["uleb"]


class Deref_Size(OperationBase):
    """DW_OP_deref_size: Dereference N bytes. Stack Effect: [address] -> [value]"""

    DISPLAY_NAME = "deref_size"
    PARAMETERS = ["u8"]


class Xderef_Size(OperationBase):
    """DW_OP_xderef_size: Extended deref N bytes. Stack Effect: [addr_space, address] -> [value]"""

    DISPLAY_NAME = "xderef_size"
    PARAMETERS = ["u8"]


class Nop(OperationBase):
    """DW_OP_nop: No operation. Stack Effect: [] -> []"""

    DISPLAY_NAME = "nop"


class Push_Object_Address(OperationBase):
    """DW_OP_push_object_address: Push address of current object. Stack Effect: [] -> [address]"""

    DISPLAY_NAME = "push_object_address"


class Call2(OperationBase):
    """DW_OP_call2: Call subroutine at DIE offset (2 bytes). Stack Effect: varies"""

    DISPLAY_NAME = "call2"
    PARAMETERS = ["u16"]


class Call4(OperationBase):
    """DW_OP_call4: Call subroutine at DIE offset (4 bytes). Stack Effect: varies"""

    DISPLAY_NAME = "call4"
    PARAMETERS = ["u32"]


class Call_Ref(OperationBase):
    """DW_OP_call_ref: Call subroutine at DIE reference. Stack Effect: varies"""

    DISPLAY_NAME = "call_ref"
    PARAMETERS = ["native_address"]


class Form_Tls_Address(OperationBase):
    """DW_OP_form_tls_address: Form TLS address. Stack Effect: [offset] -> [tls_address]"""

    DISPLAY_NAME = "form_tls_address"


class Call_Frame_Cfa(OperationBase):
    """DW_OP_call_frame_cfa: Push CFA (Canonical Frame Address). Stack Effect: [] -> [cfa]"""

    DISPLAY_NAME = "call_frame_cfa"


class Bit_Piece(OperationBase):
    """DW_OP_bit_piece: Describe bit piece of composite location. Stack Effect: [value] -> []"""

    DISPLAY_NAME = "bit_piece"
    PARAMETERS = ["uleb", "uleb"]


class Implicit_Value(OperationBase):
    """DW_OP_implicit_value: Value is embedded in expression. Stack Effect: [] -> [value]"""

    DISPLAY_NAME = "implicit_value"
    PARAMETERS = ["uleb"]


class Stack_Value(OperationBase):
    """DW_OP_stack_value: Top of stack is value (not address). Stack Effect: [value] -> [value]"""

    DISPLAY_NAME = "stack_value"


class Implicit_Pointer(OperationBase):
    """DW_OP_implicit_pointer: Pointer to DIE + offset. Stack Effect: [] -> [pointer]"""

    DISPLAY_NAME = "implicit_pointer"
    PARAMETERS = ["native_address", "sleb"]


class Addrx(OperationBase):
    """DW_OP_addrx: Push address from .debug_addr. Stack Effect: [] -> [address]"""

    DISPLAY_NAME = "addrx"
    PARAMETERS = ["uleb"]


class Constx(OperationBase):
    """DW_OP_constx: Push constant from .debug_addr. Stack Effect: [] -> [constant]"""

    DISPLAY_NAME = "constx"
    PARAMETERS = ["uleb"]


class Entry_Value(OperationBase):
    """DW_OP_entry_value: Value at function entry. Stack Effect: varies"""

    DISPLAY_NAME = "entry_value"
    PARAMETERS = ["uleb"]


class Const_Type(OperationBase):
    """DW_OP_const_type: Typed constant value. Stack Effect: [] -> [value]"""

    DISPLAY_NAME = "const_type"
    PARAMETERS = ["uleb", "u8"]


class Regval_Type(OperationBase):
    """DW_OP_regval_type: Typed register value. Stack Effect: [] -> [value]"""

    DISPLAY_NAME = "regval_type"
    PARAMETERS = ["uleb", "uleb"]


class Deref_Type(OperationBase):
    """DW_OP_deref_type: Typed dereference. Stack Effect: [address] -> [typed_value]"""

    DISPLAY_NAME = "deref_type"
    PARAMETERS = ["u8", "uleb"]


class Xderef_Type(OperationBase):
    """DW_OP_xderef_type: Typed extended dereference. Stack Effect: [addr_space, address] -> [typed_value]"""

    DISPLAY_NAME = "xderef_type"
    PARAMETERS = ["u8", "uleb"]


class Convert(OperationBase):
    """DW_OP_convert: Convert value to different type. Stack Effect: [value] -> [converted_value]"""

    DISPLAY_NAME = "convert"
    PARAMETERS = ["uleb"]


class Reinterpret(OperationBase):
    """DW_OP_reinterpret: Reinterpret value as different type. Stack Effect: [value] -> [reinterpreted_value]"""

    DISPLAY_NAME = "reinterpret"
    PARAMETERS = ["uleb"]


##################################
## Vendor-Specific Extensions  ##
##################################


class Lo_User(OperationBase):
    """DW_OP_lo_user: Start of user-defined operation range."""

    DISPLAY_NAME = "lo_user"


class Hi_User(OperationBase):
    """DW_OP_hi_user: End of user-defined operation range."""

    DISPLAY_NAME = "hi_user"


# GNU Extensions
class Gnu_Push_Tls_Address(OperationBase):
    """GNU extension: Push TLS address."""

    DISPLAY_NAME = "GNU_push_tls_address"


class Gnu_Uninit(OperationBase):
    """GNU extension: Mark variable as uninitialized."""

    DISPLAY_NAME = "GNU_uninit"


class Gnu_Encoded_Addr(OperationBase):
    """GNU extension: Encoded address."""

    DISPLAY_NAME = "GNU_encoded_addr"


class Gnu_Implicit_Pointer(OperationBase):
    """GNU extension: Implicit pointer."""

    DISPLAY_NAME = "GNU_implicit_pointer"


class Gnu_Entry_Value(OperationBase):
    """GNU extension: Value at function entry."""

    DISPLAY_NAME = "GNU_entry_value"
    PARAMETERS = ["uleb"]


class Gnu_Const_Type(OperationBase):
    """GNU extension: Typed constant."""

    DISPLAY_NAME = "GNU_const_type"
    PARAMETERS = ["uleb", "u8"]  # , "block1"


class Gnu_Regval_Type(OperationBase):
    """GNU extension: Typed register value."""

    DISPLAY_NAME = "GNU_regval_type"
    PARAMETERS = ["uleb", "uleb"]


class Gnu_Deref_Type(OperationBase):
    """GNU extension: Typed dereference."""

    DISPLAY_NAME = "GNU_deref_type"
    PARAMETERS = ["u8", "uleb"]


class Gnu_Convert(OperationBase):
    """GNU extension: Convert value type."""

    DISPLAY_NAME = "GNU_convert"
    PARAMETERS = ["uleb"]


class Gnu_Reinterpret(OperationBase):
    """GNU extension: Reinterpret value type."""

    DISPLAY_NAME = "GNU_reinterpret"
    PARAMETERS = ["uleb"]


class Gnu_Parameter_Ref(OperationBase):
    """GNU extension: Reference to parameter."""

    DISPLAY_NAME = "GNU_parameter_ref"
    PARAMETERS = ["native_address"]


class Gnu_Addr_Index(OperationBase):
    """GNU extension: Address table index."""

    DISPLAY_NAME = "GNU_addr_index"


class Gnu_Const_Index(OperationBase):
    """GNU extension: Constant table index."""

    DISPLAY_NAME = "GNU_const_index"


# HP Extensions
class Hp_Unknown(OperationBase):
    """HP extension: Unknown operation."""

    DISPLAY_NAME = "HP_unknown"


class Hp_Is_Value(OperationBase):
    """HP extension: Is value."""

    DISPLAY_NAME = "HP_is_value"


class Hp_Fltconst4(OperationBase):
    """HP extension: 4-byte float constant."""

    DISPLAY_NAME = "HP_fltconst4"


class Hp_Fltconst8(OperationBase):
    """HP extension: 8-byte float constant."""

    DISPLAY_NAME = "HP_fltconst8"


class Hp_Mod_Range(OperationBase):
    """HP extension: Modified range."""

    DISPLAY_NAME = "HP_mod_range"


class Hp_Unmod_Range(OperationBase):
    """HP extension: Unmodified range."""

    DISPLAY_NAME = "HP_unmod_range"


class Hp_Tls(OperationBase):
    """HP extension: TLS support."""

    DISPLAY_NAME = "HP_tls"


class Gi_Omp_Thread_Num(OperationBase):
    """GI extension: OpenMP thread number."""

    DISPLAY_NAME = "GI_omp_thread_num"


# Opcode-to-class mapping dictionary
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
    constants.Operation.PGI_omp_thread_num: Gi_Omp_Thread_Num,
}

######################
######################
######################


class StackMachine:
    """DWARF expression stack machine evaluator.

    Evaluates DWARF expressions by executing stack operations. Each expression
    is a bytecode sequence that manipulates a stack to compute addresses or values.

    Attributes:
        stack: Stack instance for operation execution
        readers: DwarfReaders instance for parameter parsing

    Example:
        >>> from objutils.dwarf.readers import DwarfReaders
        >>> readers = DwarfReaders(4, '<')  # 32-bit little-endian
        >>> sm = StackMachine(readers)
        >>> # Expression: DW_OP_lit5, DW_OP_lit3, DW_OP_plus
        >>> result = sm.evaluate(b'\\x35\\x33\\x22')  # Push 5, push 3, add
        >>> print(result)
        lit5; lit3; plus

    Note:
        Not all operations are fully implemented (e.g., deref requires memory context,
        reg* operations require register context).
    """

    def __init__(self, readers):
        """Initialize stack machine.

        Args:
            readers: DwarfReaders instance for parsing operation parameters
        """
        self.stack = Stack()
        OperationBase.set_readers(readers)

    def evaluate(self, expr: bytes):
        """Evaluate DWARF expression bytecode.

        Args:
            expr: Bytecode sequence of DWARF operations

        Returns:
            String representation of executed operations (semicolon-separated)

        Example:
            >>> # DW_OP_addr <address> = push address
            >>> sm.evaluate(b'\\x03\\x00\\x10\\x00\\x00')  # addr 0x1000
            'addr(0x1000)'
        """
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
