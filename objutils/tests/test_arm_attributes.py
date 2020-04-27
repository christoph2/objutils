
from objutils.elf.arm import attributes

ATMEL_SAMD21 = b"A'\x00\x00\x00aeabi\x00\x01\x1d\x00\x00\x00\x056S-M\x00\x06\x0c\x07M\t\x01\x12\x04\x14\x01\x15\x01\x17\x03\x18\x01\x1a\x01"
ARM_ATTRS1 = b'A,\x00\x00\x00aeabi\x00\x01"\x00\x00\x00\x05ARM v6K\x00\x06\t\x07M\x08\x01\t\x01\x12\x04\x14\x01\x15\x01\x17\x03\x18\x01\x1a\x01'

ARM_ATTRS2 = bytes.fromhex("4138000000616561626900012e00000005372d4100060a0741080109020a030c01110212041301140115011703180119011a021c0122012601")

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

"""
  Tag_CPU_name: "7-A"
  Tag_CPU_arch: v7
  Tag_CPU_arch_profile: Application
  Tag_ARM_ISA_use: Yes
  Tag_THUMB_ISA_use: Thumb-2
  Tag_FP_arch: VFPv3
  Tag_Advanced_SIMD_arch: NEONv1
  Tag_ABI_PCS_GOT_use: GOT-indirect
  Tag_ABI_PCS_wchar_t: 4
  Tag_ABI_FP_rounding: Needed
  Tag_ABI_FP_denormal: Needed
  Tag_ABI_FP_exceptions: Needed
  Tag_ABI_FP_number_model: IEEE 754
  Tag_ABI_align_needed: 8-byte
  Tag_ABI_align_preserved: 8-byte, except leaf SP
  Tag_ABI_enum_size: int
  Tag_ABI_VFP_args: VFP registers
  Tag_CPU_unaligned_access: v6
  Tag_ABI_FP_16bit_format: IEEE 754

"""

def test_arm_attrs2():
    res = attributes.parse(ARM_ATTRS2)
    assert len(res.keys()) == 1
    assert "aeabi" in res
    attrs = res['aeabi']
    assert len(attrs) == 19
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18 = attrs

    assert a0.tag == 5
    assert a0.tag_name == "Tag_CPU_name"
    assert a0.value == "7-A"
    assert a0.description == "7-A"

    assert a1.tag == 6
    assert a1.tag_name == "Tag_CPU_arch"
    assert a1.value == 10
    assert a1.description == "ARM v7"

    assert a2.tag == 7
    assert a2.tag_name == "Tag_CPU_arch_profile"
    assert a2.value == 65
    assert a2.description == "The application profile"

    assert a3.tag == 8
    assert a3.tag_name == "Tag_ARM_ISA_use"
    assert a3.value == 1
    assert a3.description == "The user intended that this entity could use ARM instructions"

    assert a4.tag == 9
    assert a4.tag_name == "Tag_THUMB_ISA_use"
    assert a4.value == 2
    assert a4.description == "32-bit Thumb instructions were permitted"

    assert a5.tag == 10
    assert a5.tag_name == "Tag_FP_arch"
    assert a5.value == 3
    assert a5.description == "Use of the v3 FP ISA was permitted (implies use of the v2 FP ISA) "

    assert a6.tag == 12
    assert a6.tag_name == "Tag_Advanced_SIMD_arch"
    assert a6.value == 1
    assert a6.description == "Use of the Advanced SIMDv1 Architecture (Neon) was permitted"

    assert a7.tag == 17
    assert a7.tag_name == "Tag_ABI_PCS_GOT_use"
    assert a7.value == 2
    assert a7.description == "The user permitted this entity to address imported data indirectly (e.g. via a GOT)"

    assert a8.tag == 18
    assert a8.tag_name == "Tag_ABI_PCS_wchar_t"
    assert a8.value == 4
    assert a8.description == "The user intended the size of wchar_t to be 4"

    assert a9.tag == 19
    assert a9.tag_name == "Tag_ABI_FP_rounding"
    assert a9.value == 1
    assert a9.description == "The user permitted this code to choose the IEEE 754 rounding mode at run time"

    assert a10.tag == 20
    assert a10.tag_name == "Tag_ABI_FP_denormal"
    assert a10.value == 1
    assert a10.description == "The user permitted this code to choose the IEEE 754 rounding mode at run time"

    assert a11.tag == 21
    assert a11.tag_name == "Tag_ABI_FP_exceptions"
    assert a11.value == 1
    assert a11.description == "The user permitted this code to check the IEEE 754 inexact exception"

    assert a12.tag == 23
    assert a12.tag_name == "Tag_ABI_FP_number_model"
    assert a12.value == 3
    assert a12.description == "The user permitted this code to use all the IEEE 754-defined FP encodings"

    assert a13.tag == 24
    assert a13.tag_name == "Tag_ABI_align_needed"
    assert a13.value == 1
    assert a13.description == "Code was permitted to depend on the 8-byte alignment of 8-byte data items"

    assert a14.tag == 25
    assert a14.tag_name == "Tag_ABI_align8_preserved"
    assert a14.value == 1
    assert a14.description == "Code was required to preserve 8-byte alignment of 8-byte data objects"

    assert a15.tag == 26
    assert a15.tag_name == "Tag_ABI_enum_size"
    assert a15.value == 2
    assert a15.description == "The user intended Enum containers to be 32-bit "

    assert a16.tag == 28
    assert a16.tag_name == "Tag_ABI_VFP_args"
    assert a16.value == 1
    assert a16.description == "The user intended FP parameter/result passing to conform to AAPCS, VFP variant"

    assert a17.tag == 34
    assert a17.tag_name == "Tag_CPU_unaligned_access"
    assert a17.value == 1
    assert a17.description == "The user intended that this entity might make v6-style unaligned data accesses"

    assert a18.tag == 38
    assert a18.tag_name == "Tag_ABI_FP_16bit_format"
    assert a18.value == 1
    assert a18.description == "Use of IEEE 754 (draft, November 2006) format 16-bit FP numbers was permitted "

