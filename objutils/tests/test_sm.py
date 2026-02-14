TESTS = [
    bytes([0xF3, 0x01, 0x51]),  # (DW_OP_GNU_entry_value: (DW_OP_reg1 (r1)))
    bytes([0x78, 0x00, 0x74, 0x00, 0x22]),  # (DW_OP_breg8 (r8): 0; DW_OP_breg4 (r4): 0; DW_OP_plus)
    bytes([0x76, 0x00, 0x74, 0x00, 0x1C]),  # (DW_OP_breg6 (r6): 0; DW_OP_breg4 (r4): 0; DW_OP_minus)
    bytes([0xF3, 0x01, 0x50, 0x23, 0x34]),  # (DW_OP_GNU_entry_value: (DW_OP_reg0 (r0)); DW_OP_plus_uconst: 52)
]

"""
pprint(TESTS)

from objutils.dwarf.sm import readers

readers = Readers()

sm = StackMachine(readers)

for test in TESTS:
    print(sm.evaluate(test))
"""
