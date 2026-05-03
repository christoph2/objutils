import unittest
from objutils.dwarf.readers import DwarfReaders, Endianess
from objutils.dwarf.sm import StackMachine


class TestStackMachine(unittest.TestCase):
    def setUp(self):
        self.readers = DwarfReaders(Endianess.Little, 4)
        self.sm = StackMachine(self.readers.readers)

    def test_plus_uconst_basic(self):
        # Push 10 (DW_OP_lit10 = 0x3a), then DW_OP_plus_uconst 5 (0x23 0x05)
        expr = b"\x3a\x23\x05"
        result = self.sm.evaluate(expr)
        self.assertEqual(result.representation, "lit10(); plus_uconst(0x00000005)")
        self.assertEqual(result.value.value, 15)

    def test_plus_uconst_empty_stack(self):
        # DW_OP_plus_uconst 0 (0x23 0x00) with empty stack
        # Sollte 0 + 0 = 0 ergeben (statt Crash)
        expr = b"\x23\x00"
        result = self.sm.evaluate(expr)
        self.assertEqual(result.representation, "plus_uconst(0)")
        self.assertEqual(result.value.value, 0)

    def test_arithmetic(self):
        # lit10 (0x3a), lit3 (0x33), plus (0x22) -> 13
        expr = b"\x3a\x33\x22"
        result = self.sm.evaluate(expr)
        self.assertEqual(result.representation, "lit10(); lit3(); plus()")
        self.assertEqual(result.value.value, 13)

    def test_const_type(self):
        # DW_OP_const_type (0xa4), type_offset (uleb 0x12), size (1), value (0x42)
        expr = b"\xa4\x12\x01\x42"
        result = self.sm.evaluate(expr)
        self.assertIn("const_type", result.representation)
        self.assertEqual(result.value.value, 0x42)
        self.assertEqual(result.value.type_offset, 0x12)

    def test_multiple_ops(self):
        # GNU entry value test cases from original file
        # DW_OP_GNU_entry_value (0xf3), uleb 1 (0x01), DW_OP_reg1 (0x51)
        # Note: stack_op for these might not be fully implemented but parsing should work
        expr = b"\xf3\x01\x51"
        result = self.sm.evaluate(expr)
        self.assertIn("GNU_entry_value", result.representation)
        self.assertIn("reg1", result.representation)

    def test_unknown_opcode(self):
        # 0x00 ist DW_OP_addr (unkorrekt, da Parameter fehlen, aber Opcode existiert)
        # 0x23 ist DW_OP_plus_uconst
        # Wir testen einen wirklich unbekannten Opcode
        expr = b"\xfe"
        result = self.sm.evaluate(expr)
        self.assertEqual(result.representation, "<unk>(0xfe)")
        self.assertIsNone(result.value)


if __name__ == "__main__":
    unittest.main()
