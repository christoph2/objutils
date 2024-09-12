#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <github.com/Christoph2,
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


from collections import namedtuple
from enum import IntEnum

from construct import (
    Byte,
    Bytes,
    Computed,
    CString,
    Int32ub,
    Int32ul,
    Struct,
    Switch,
    Tell,
    this,
)

from objutils.dwarf.encoding import ULEB


AttributeDescription = namedtuple("AttributeDescription", "tag value parameterType conv")


class Reader(IntEnum):
    """ """

    INT32 = 1
    CSTRING = 2
    ULEB = 3


Ident = {}

Tag_CPU_arch = {
    0: "Pre-v4",
    1: "ARM v4",
    2: "ARM v4T",
    3: "ARM v5T",
    4: "ARM v5TE",
    5: "ARM v5TEJ",
    6: "ARM v6",
    7: "ARM v6KZ",
    8: "ARM v6T2",
    9: "ARM v6K",
    10: "ARM v7",
    11: "ARM v6-M",
    12: "ARM v6S-M",
    13: "ARM v7E-M",
    14: "ARM v8",
}

Tag_CPU_arch_profile = {
    0x00: "Architecture profile is not applicable",
    0x41: "The application profile",
    0x52: "The real-time profile",
    0x4D: "The microcontroller profile",
    0x53: "Application or real-time profile",
}

Tag_ARM_ISA_use = {
    0: "The user did not permit this entity to use ARM instructions",
    1: "The user intended that this entity could use ARM instructions",
}

Tag_THUMB_ISA_use = {
    0: "The user did not permit this entity to use Thumb instructions",
    1: "The user permitted this entity to use 16-bit Thumb instructions (including BL)",
    2: "32-bit Thumb instructions were permitted",
}

Tag_FP_arch = {
    0: "The user did not permit this entity to use instructions requiring FP hardware ",
    1: "The user permitted use of instructions from v1 of the floating point (FP) ISA ",
    2: "Use of the v2 FP ISA was permitted (implies use of the v1 FP ISA) ",
    3: "Use of the v3 FP ISA was permitted (implies use of the v2 FP ISA) ",
    4: "Use of the v3 FP ISA was permitted, but only citing registers D0-D15, S0-S31 ",
    5: "Use of the v4 FP ISA was permitted (implies use of the non-vector v3 FP ISA) ",
    6: "Use of the v4 FP ISA was permitted, but only citing registers D0-D15, S0-S31 ",
    7: "Use of the ARM v8-A FP ISA was permitted ",
    8: "Use of the ARM v8-A FP ISA was permitted, but only citing registers D0-D15, S0-S31",
}

Tag_WMMX_arch = {
    0: "The user did not permit this entity to use WMMX",
    1: "The user permitted this entity to use WMMX v1",
    2: "The user permitted this entity to use WMMX v2",
}

Tag_Advanced_SIMD_arch = {
    0: "The user did not permit this entity to use the Advanced SIMD Architecture (Neon)",
    1: "Use of the Advanced SIMDv1 Architecture (Neon) was permitted",
    2: "Use of Advanced SIMDv2 Architecture (Neon) (with half-precision floating-point and fused MAC operations) was permitted",
    3: "Use of the ARM v8-A Advanced SIMD Architecture (Neon) was permitted",
    4: "Use of the ARM v8.1-A Advanced SIMD Architecture (Neon) was permitted",
}

Tag_FP_HP_extension = {
    0: "The user intended half-precision floating point instructions may be used if they exist "
    "in the available FP and ASIMD instruction sets as indicated by Tag_FP_arch and Tag_ASIMD_arch ",
    1: "Use of the optional half-precision extension to VFPv3/Advanced SIMDv1 was permitted",
}

Tag_CPU_unaligned_access = {
    0: "The user did not intend this entity to make unaligned data accesses",
    1: "The user intended that this entity might make v6-style unaligned data accesses",
}

Tag_T2EE_use = {
    0: "No use of T2EE extension was permitted, or no information is available",
    1: "Use of the T2EE extension was permitted",
}

Tag_Virtualization_use = {
    0: "No use of any virtualization extension was permitted, or no information available",
    1: "Use of the TrustZone extension was permitted",
    2: "Use of the virtualization extensions (HVC, ERET) were permitted",
    3: "Use of TrustZone and virtualization extensions were permitted",
}

Tag_MPextension_use = {
    0: "No use of ARM v7 MP extension was permitted, or no information available.",
    1: "Use of the ARM v7 MP extension was permitted.",
}

Tag_DIV_use = {
    0: "The user intended divide instructions may be used if they exist, or no explicit information recorded. "
    "This code was permitted to use SDIV and UDIV if the instructions are guaranteed present in the "
    "architecture, as indicated by Tag_CPU_arch and Tag_CPU_arch_profile.",
    1: "This code was explicitly not permitted to use SDIV or UDIV.",
    2: "This code was permitted to use SDIV and UDIV in the ARM and Thumb ISAs; the instructions are present "
    "as an optional architectural extension above the base architecture implied by Tag_CPU_arch and Tag_CPU_arch_profile.",
}

Tag_PCS_config = {
    0: "No standard configuration used, or no information recorded ",
    1: "Bare platform configuration ",
    2: "Linux application configuration ",
    3: "Linux DSO configuration ",
    4: "Palm OS 2004 configuration ",
    5: "Reserved to future Palm OS configuration ",
    6: "Symbian OS 2004 configuration ",
    7: "Reserved to future Symbian OS configuration",
}

Tag_ABI_PCS_R9_use = {
    0: "R9 used as V6 (just another callee-saved register, implied by omitting the tag) ",
    1: "R9 used as SB, a global Static Base register",
    2: "R9 used as a Thread Local Storage (TLS) pointer",
    3: "R9 not used at all by code associated with the attributed entity",
}

Tag_ABI_PCS_RW_data = {
    0: "RW static data was permitted to be addressed absolutely",
    1: "RW static data was only permitted to be addressed PC-relative",
    2: "RW static data was only permitted to be addressed SB-relative",
    3: "The user did not permit this entity to use RW static data",
}

Tag_ABI_PCS_RO_data = {
    0: "RO static data was permitted to be addressed absolutely",
    1: "RO static data was only permitted to be addressed PC-relative",
    2: "The user did not permit this entity to use RO static data",
}

Tag_ABI_PCS_GOT_use = {
    0: "The user did not permit this entity to import static data",
    1: "The user permitted this entity to address imported data directly",
    2: "The user permitted this entity to address imported data indirectly (e.g. via a GOT)",
}

Tag_ABI_PCS_wchar_t = {
    0: "The user prohibited the use of wchar_t when building this entity",
    2: "The user intended the size of wchar_t to be 2",
    4: "The user intended the size of wchar_t to be 4",
}

Tag_ABI_enum_size = {
    0: "The user prohibited the use of enums when building this entity ",
    1: "Enum values occupy the smallest container big enough to hold all their values ",
    2: "The user intended Enum containers to be 32-bit ",
    3: "The user intended that every enumeration visible across an ABI-complying interface "
    "contains a value needing 32 bits to encode it; other enums can be containerized",
}

Tag_ABI_align_needed = {
    0: "The user did not permit code to depend the alignment of 8-byte data or data with extended (> 8-byte) alignment",
    1: "Code was permitted to depend on the 8-byte alignment of 8-byte data items",
    2: "Code was permitted to depend on the 4-byte alignment of 8-byte data items",
    3: "Reserved",
    # n (in 4..12) Code was permitted to depend on the 8-byte alignment of 8-byte
    # data items and the alignment of data items having up to 2n-byte extended alignment
}

Tag_ABI_align_preserved = {
    0: "The user did not require code to preserve 8-byte alignment of 8-byte data objects",
    1: "Code was required to preserve 8-byte alignment of 8-byte data objects",
    2: "Code was required to preserve 8-byte alignment of 8-byte data objects and "
    "to ensure (SP MOD 8) = 0 at all instruction boundaries (not just at function calls)",
    3: "Reserved",
    # n (in 4..12) Code was required to preserve the alignments of case 2 and the
    # alignment of data items having up to 2n-byte extended alignment.
}

Tag_ABI_FP_rounding = {
    0: "The user intended this code to use the IEEE 754 round to nearest rounding mode",
    1: "The user permitted this code to choose the IEEE 754 rounding mode at run time",
}

Tag_ABI_FP_denormal = {
    0: "The user built this code knowing that denormal numbers might be flushed to (+) zero",
    1: "The user permitted this code to depend on IEEE 754 denormal numbers",
    2: "The user permitted this code to depend on the sign of a flushed-to-zero number being preserved in the sign of 0",
}

Tag_ABI_FP_exceptions = {
    0: "The user intended that this code should not check for inexact results",
    1: "The user permitted this code to check the IEEE 754 inexact exception",
}

Tag_ABI_FP_user_exceptions = {
    0: "The user intended that this code should not enable or use IEEE user exceptions",
    1: "The user permitted this code to enables and use IEEE 754 user exceptions",
}

Tag_ABI_FP_number_model = {
    0: "The user intended that this code should not use floating point numbers ",
    1: "The user permitted this code to use IEEE 754 format normal numbers only ",
    2: "The user permitted numbers, infinities, and one quiet NaN (see [RTABI]) ",
    3: "The user permitted this code to use all the IEEE 754-defined FP encodings",
}

Tag_ABI_FP_16bit_format = {
    0: "The user intended that this entity should not use 16-bit floating point numbers ",
    1: "Use of IEEE 754 (draft, November 2006) format 16-bit FP numbers was permitted ",
    2: "Use of VFPv3/Advanced SIMD alternative format 16-bit FP numbers was permitted",
}

Tag_ABI_HardFP_use = {
    0: "The user intended that FP use should be implied by Tag_FP_arch",
    1: "The user intended this code to execute on the single-precision variant derived from Tag_FP_arch",
    2: "Reserved",
    3: "The user intended that FP use should be implied by Tag_FP_arch (Note: This is a deprecated duplicate of the default encoded by 0)",
}

Tag_ABI_VFP_args = {
    0: "The user intended FP parameter/result passing to conform to AAPCS, base variant",
    1: "The user intended FP parameter/result passing to conform to AAPCS, VFP variant",
    2: "The user intended FP parameter/result passing to conform to tool chain-specific conventions",
    3: "Code is compatible with both the base and VFP variants; the user did not permit non-variadic functions to pass FP parameters/results",
}

Tag_ABI_WMMX_args = {
    0: "The user intended WMMX parameter/result passing conform to the AAPCS, base variant",
    1: "The user intended WMMX parameter/result passing conform to Intels WMMX conventions",
    2: "The user intended WMMX parameter/result passing conforms to tool chain-specific conventions",
}

Tag_ABI_optimization_goals = {
    0: "No particular optimization goals, or no information recorded",
    1: "Optimized for speed, but small size and good debug illusion preserved",
    2: "Optimized aggressively for speed, small size and debug illusion sacrificed",
    3: "Optimized for small size, but speed and debugging illusion preserved",
    4: "Optimized aggressively for small size, speed and debug illusion sacrificed",
    5: "Optimized for good debugging, but speed and small size preserved",
    6: "Optimized for best debugging illusion, speed and small size sacrificed",
}

Tag_ABI_FP_optimization_goals = {
    0: "No particular FP optimization goals, or no information recorded",
    1: "Optimized for speed, but small size and good accuracy preserved",
    2: "Optimized aggressively for speed, small size and accuracy sacrificed",
    3: "Optimized for small size, but speed and accuracy preserved",
    4: "Optimized aggressively for small size, speed and accuracy sacrificed",
    5: "Optimized for accuracy, but speed and small size preserved",
    6: "Optimized for best accuracy, speed and small size sacrificed",
}


ATTRIBUTES = {
    1: AttributeDescription("Tag_File", 1, Reader.INT32, Ident),
    2: AttributeDescription("Tag_Section", 2, Reader.INT32, Ident),
    3: AttributeDescription("Tag_Symbol", 3, Reader.INT32, Ident),
    4: AttributeDescription("Tag_CPU_raw_name", 4, Reader.CSTRING, Ident),
    5: AttributeDescription("Tag_CPU_name", 5, Reader.CSTRING, Ident),
    6: AttributeDescription("Tag_CPU_arch", 6, Reader.ULEB, Tag_CPU_arch),
    7: AttributeDescription("Tag_CPU_arch_profile", 7, Reader.ULEB, Tag_CPU_arch_profile),
    8: AttributeDescription("Tag_ARM_ISA_use", 8, Reader.ULEB, Tag_ARM_ISA_use),
    9: AttributeDescription("Tag_THUMB_ISA_use", 9, Reader.ULEB, Tag_THUMB_ISA_use),
    10: AttributeDescription("Tag_FP_arch", 10, Reader.ULEB, Tag_FP_arch),
    11: AttributeDescription("Tag_WMMX_arch", 11, Reader.ULEB, Tag_WMMX_arch),
    12: AttributeDescription("Tag_Advanced_SIMD_arch", 12, Reader.ULEB, Tag_Advanced_SIMD_arch),
    13: AttributeDescription("Tag_PCS_config", 13, Reader.ULEB, Tag_PCS_config),
    14: AttributeDescription("Tag_ABI_PCS_R9_use", 14, Reader.ULEB, Tag_ABI_PCS_R9_use),
    15: AttributeDescription("Tag_ABI_PCS_RW_data", 15, Reader.ULEB, Tag_ABI_PCS_RW_data),
    16: AttributeDescription("Tag_ABI_PCS_RO_data", 16, Reader.ULEB, Tag_ABI_PCS_RO_data),
    17: AttributeDescription("Tag_ABI_PCS_GOT_use", 17, Reader.ULEB, Tag_ABI_PCS_GOT_use),
    18: AttributeDescription("Tag_ABI_PCS_wchar_t", 18, Reader.ULEB, Tag_ABI_PCS_wchar_t),
    19: AttributeDescription("Tag_ABI_FP_rounding", 19, Reader.ULEB, Tag_ABI_FP_rounding),
    20: AttributeDescription("Tag_ABI_FP_denormal", 20, Reader.ULEB, Tag_ABI_FP_rounding),
    21: AttributeDescription("Tag_ABI_FP_exceptions", 21, Reader.ULEB, Tag_ABI_FP_exceptions),
    22: AttributeDescription("Tag_ABI_FP_user_exceptions", 22, Reader.ULEB, Tag_ABI_FP_user_exceptions),
    23: AttributeDescription("Tag_ABI_FP_number_model", 23, Reader.ULEB, Tag_ABI_FP_number_model),
    24: AttributeDescription("Tag_ABI_align_needed", 24, Reader.ULEB, Tag_ABI_align_needed),
    25: AttributeDescription("Tag_ABI_align8_preserved", 25, Reader.ULEB, Tag_ABI_align_preserved),
    26: AttributeDescription("Tag_ABI_enum_size", 26, Reader.ULEB, Tag_ABI_enum_size),
    27: AttributeDescription("Tag_ABI_HardFP_use", 27, Reader.ULEB, Tag_ABI_HardFP_use),
    28: AttributeDescription("Tag_ABI_VFP_args", 28, Reader.ULEB, Tag_ABI_VFP_args),
    29: AttributeDescription("Tag_ABI_WMMX_args", 29, Reader.ULEB, Tag_ABI_WMMX_args),
    30: AttributeDescription("Tag_ABI_optimization_goals", 30, Reader.ULEB, Tag_ABI_optimization_goals),
    31: AttributeDescription("Tag_ABI_FP_optimization_goals", 31, Reader.ULEB, Tag_ABI_FP_optimization_goals),
    32: AttributeDescription("Tag_compatibility", 32, Reader.CSTRING, Ident),
    34: AttributeDescription("Tag_CPU_unaligned_access", 34, Reader.ULEB, Tag_CPU_unaligned_access),
    36: AttributeDescription(
        "Tag_FP_HP_extension (was Tag_VFP_HP_extension)",
        36,
        Reader.ULEB,
        Tag_FP_HP_extension,
    ),
    38: AttributeDescription("Tag_ABI_FP_16bit_format", 38, Reader.ULEB, Tag_ABI_FP_16bit_format),
    42: AttributeDescription("Tag_MPextension_use", 42, Reader.ULEB, Tag_MPextension_use),
    44: AttributeDescription("Tag_DIV_use", 44, Reader.ULEB, Tag_DIV_use),
    64: AttributeDescription("Tag_nodefaults", 64, Reader.ULEB, Ident),
    65: AttributeDescription("Tag_also_compatible_with", 65, Reader.CSTRING, Ident),
    67: AttributeDescription("Tag_conformance", 67, Reader.CSTRING, Ident),
    66: AttributeDescription("Tag_T2EE_use", 66, Reader.ULEB, Tag_T2EE_use),
    68: AttributeDescription("Tag_Virtualization_use", 68, Reader.ULEB, Tag_Virtualization_use),
    70: AttributeDescription("Tag_MPextension_use", 70, Reader.ULEB, Tag_MPextension_use),
}

"""
ADI         Analog Devices
acle        Reserved for use by Arm C Language Extensions.
aeabi       Reserved to the ABI for the Arm Architecture (EABI pseudo-vendor)
AnonXyz
anonXyz     Reserved to private experiments by the Xyz vendor. Guaranteed not to clash with any registered vendor name.
ARM Arm     Ltd (Note: the company, not the processor).
cxa         C++ ABI pseudo-vendor
FSL         Freescale Semiconductor Inc.
GHS         Green Hills Systems
gnu         GNU compilers and tools (Free Software Foundation)
iar         IAR Systems
icc         ImageCraft Creations Inc (ImageCraft C Compiler)
intel       Intel Corporation
ixs         Intel Xscale
llvm        The LLVM/Clang projects
PSI         PalmSource Inc.
RAL         Rowley Associates Ltd
SEGGER      SEGGER Microcontroller GmbH
somn        SOMNIUM Technologies Limited.
TASKING     Altium Ltd.
TI          TI Inc.
tls         Reserved for use in thread-local storage routines.
WRS         Wind River Systems.
"""

"""
<format-version>
    [ <section-length> "vendor-name"
        [ <file-tag> <size> <attribute>*
        | <section-tag> <size> <section-number>* 0 <attribute>*
        | <symbol-tag> <size> <symbol-number>* 0 <attribute>*
        ]+
]*
"""


class Attribute:
    def __init__(self, tag, tag_name, value, description=None):
        self.tag = tag
        self.tag_name = tag_name
        self.value = value
        if description is None:
            self.description = value

    def __repr__(self):
        return "Attribute(tag = {}, tag_name = {}, value = {}, description = {})".format(
            self.tag, self.tag_name, self.value, self.description
        )


def parse(buffer, byteorder="<"):
    """
    Parameters
    ----------
    buffer: bytes-like

    byteorder: char
        "<": Little-endian
        ">": Big-endian

    Returns
    -------
    dict
        key: Vendor name
        values: list of attributes
    """
    Integer = Int32ul if byteorder == "<" else Int32ub
    Section = Struct(
        "len" / Integer,
        "vendor" / CString(encoding="ascii"),
        "_pos" / Tell,
        "data" / Bytes(this.len - this._pos),
    )
    SubSectionHeader = Struct(
        "tag" / Byte,
        "len" / Integer,
        "_pos" / Tell,
        "data" / Bytes(this.len - this._pos),
    )

    RawAttribute = Struct(
        "tag" / ULEB,
        "parameterType" / Computed(lambda ctx: ATTRIBUTES[ctx.tag].parameterType),
        "name" / Computed(lambda ctx: ATTRIBUTES[ctx.tag].tag),
        "_conv" / Computed(lambda ctx: ATTRIBUTES[ctx.tag].conv),
        "value"
        / Switch(
            this.parameterType,
            {
                Reader.INT32: Integer,
                Reader.ULEB: ULEB,
                Reader.CSTRING: CString(encoding="ascii"),
            },
        ),
        "pos" / Tell,
    )
    i = 1
    length = len(buffer)
    result = {}
    while True:
        section = Section.parse(buffer[i:])
        if section.vendor not in result:
            result[section.vendor] = []
        i += section.len
        res = SubSectionHeader.parse(section.data)
        j = 0
        while j < len(res.data):
            attr = RawAttribute.parse(res.data[j:])
            r = Attribute(attr.tag, attr.name, attr.value)
            if attr._conv != Ident:
                r.description = attr._conv[attr.value]
            result[section.vendor].append(r)
            j += attr.pos
        if i >= length:
            break
    return result
