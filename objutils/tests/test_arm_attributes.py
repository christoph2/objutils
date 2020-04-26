
from objutils.elf.arm import attributes

ATMEL_SAMD21 = b"A'\x00\x00\x00aeabi\x00\x01\x1d\x00\x00\x00\x056S-M\x00\x06\x0c\x07M\t\x01\x12\x04\x14\x01\x15\x01\x17\x03\x18\x01\x1a\x01"
ARM_ATTRS = b'A,\x00\x00\x00aeabi\x00\x01"\x00\x00\x00\x05ARM v6K\x00\x06\t\x07M\x08\x01\t\x01\x12\x04\x14\x01\x15\x01\x17\x03\x18\x01\x1a\x01'

"""
Attribute Section: aeabi
File Attributes
  Tag_CPU_name: "6S-M"
  Tag_CPU_arch: v6S-M
  Tag_CPU_arch_profile: Microcontroller
  Tag_THUMB_ISA_use: Thumb-1
  Tag_ABI_PCS_wchar_t: 4
  Tag_ABI_FP_denormal: Needed
  Tag_ABI_FP_exceptions: Needed
  Tag_ABI_FP_number_model: IEEE 754
  Tag_ABI_align_needed: 8-byte
  Tag_ABI_enum_size: small
"""

