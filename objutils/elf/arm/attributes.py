#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

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


from collections import namedtuple, OrderedDict
from io import BytesIO
from pprint import pprint
import unittest
import struct

import enum

## elf TODO: parsedSections  (ARM.Attributes, Notes, etc) as oppossed to blobs, like .text.


Attribute = namedtuple("Attribute", "tag value parameterType conv")

ARM_ATTRS = b'A,\x00\x00\x00aeabi\x00\x01"\x00\x00\x00\x05ARM v6K\x00\x06\t\x07M\x08\x01\t\x01\x12\x04\x14\x01\x15\x01\x17\x03\x18\x01\x1a\x01'

CCA = b'C2.06\x00\x058-A.32\x00\x06\n\x07A\x08\x01\t\x02\n\x05\x0c\x02\x11\x01\x12\x02\x14\x02\x17\x01\x18\x01\x19\x01\x1a\x01\x1c\x01\x1e\x03"\x01$\x01B\x01D\x03F\x01,'


Ident = {}

Tag_CPU_arch = {
    0:  "Pre-v4",
    1:  "ARM v4",
    2:  "ARM v4T",
    3:  "ARM v5T",
    4:  "ARM v5TE",
    5:  "ARM v5TEJ",
    6:  "ARM v6",
    7:  "ARM v6KZ",
    8:  "ARM v6T2",
    9:  "ARM v6K",
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

Tag_ARM_ISA_use =  {
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
    0: "The user intended half-precision floating point instructions may be used if they exist in the available FP and ASIMD instruction sets as indicated by Tag_FP_arch and Tag_ASIMD_arch ",
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
    0: "The user intended divide instructions may be used if they exist, or no explicit information recorded. This code was permitted to use SDIV and UDIV if the instructions are guaranteed present in the architecture, as indicated by Tag_CPU_arch and Tag_CPU_arch_profile.",
    1: "This code was explicitly not permitted to use SDIV or UDIV.",
    2: "This code was permitted to use SDIV and UDIV in the ARM and Thumb ISAs; the instructions are present as an optional architectural extension above the base architecture implied by Tag_CPU_arch and Tag_CPU_arch_profile.",
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
    3: "The user intended that every enumeration visible across an ABI-complying interface contains a value needing 32 bits to encode it; other enums can be containerized",
}

Tag_ABI_align_needed = {
    0: "The user did not permit code to depend the alignment of 8-byte data or data with extended (> 8-byte) alignment",
    1: "Code was permitted to depend on the 8-byte alignment of 8-byte data items",
    2: "Code was permitted to depend on the 4-byte alignment of 8-byte data items",
    3: "Reserved",
    #n (in 4..12) Code was permitted to depend on the 8-byte alignment of 8-byte data items and the alignment of data items having up to 2n-byte extended alignment
}

Tag_ABI_align_preserved = {
    0: "The user did not require code to preserve 8-byte alignment of 8-byte data objects",
    1: "Code was required to preserve 8-byte alignment of 8-byte data objects",
    2: "Code was required to preserve 8-byte alignment of 8-byte data objects and to ensure (SP MOD 8) = 0 at all instruction boundaries (not just at function calls)",
    3: "Reserved",
    #n (in 4..12) Code was required to preserve the alignments of case 2 and the alignment of data items having up to 2n-byte extended alignment.
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
    0: " The user intended that this code should not use floating point numbers ",
    1: " The user permitted this code to use IEEE 754 format normal numbers only ",
    2: " The user permitted numbers, infinities, and one quiet NaN (see [RTABI]) ",
    3: " The user permitted this code to use all the IEEE 754-defined FP encodings",
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
    1:  Attribute("Tag_File", 1, "uint32", Ident),
    2:  Attribute("Tag_Section", 2, "uint32", Ident),
    3:  Attribute("Tag_Symbol", 3, "uint32", Ident),
    4:  Attribute("Tag_CPU_raw_name", 4, "ntbs", Ident),
    5:  Attribute("Tag_CPU_name", 5, "ntbs", Ident),
    6:  Attribute("Tag_CPU_arch", 6, "uleb128", Tag_CPU_arch),
    7:  Attribute("Tag_CPU_arch_profile", 7, "uleb128", Tag_CPU_arch_profile),
    8:  Attribute("Tag_ARM_ISA_use", 8, "uleb128", Tag_ARM_ISA_use),
    9:  Attribute("Tag_THUMB_ISA_use", 9, "uleb128", Tag_THUMB_ISA_use),
    10: Attribute("Tag_FP_arch", 10, "uleb128", Tag_FP_arch),
    11: Attribute("Tag_WMMX_arch", 11, "uleb128", Tag_WMMX_arch),
    12: Attribute("Tag_Advanced_SIMD_arch", 12, "uleb128", Tag_Advanced_SIMD_arch),
    13: Attribute("Tag_PCS_config", 13, "uleb128", Tag_PCS_config),
    14: Attribute("Tag_ABI_PCS_R9_use",  14, "uleb128", Tag_ABI_PCS_R9_use),
    15: Attribute("Tag_ABI_PCS_RW_data", 15, "uleb128",Tag_ABI_PCS_RW_data),
    16: Attribute("Tag_ABI_PCS_RO_data", 16, "uleb128", Tag_ABI_PCS_RO_data),
    17: Attribute("Tag_ABI_PCS_GOT_use", 17, "uleb128", Tag_ABI_PCS_GOT_use),
    18: Attribute("Tag_ABI_PCS_wchar_t", 18, "uleb128", Tag_ABI_PCS_wchar_t),
    19: Attribute("Tag_ABI_FP_rounding", 19, "uleb128", Tag_ABI_FP_rounding),
    20: Attribute("Tag_ABI_FP_denormal", 20, "uleb128", Tag_ABI_FP_rounding),
    21: Attribute("Tag_ABI_FP_exceptions", 21, "uleb128", Tag_ABI_FP_exceptions),
    22: Attribute("Tag_ABI_FP_user_exceptions", 22, "uleb128", Tag_ABI_FP_user_exceptions),
    23: Attribute("Tag_ABI_FP_number_model", 23, "uleb128", Tag_ABI_FP_number_model),
    24: Attribute("Tag_ABI_align_needed", 24, "uleb128", Tag_ABI_align_needed),
    25: Attribute("Tag_ABI_align8_preserved", 25, "uleb128", Tag_ABI_align_preserved),
    26: Attribute("Tag_ABI_enum_size", 26, "uleb128", Tag_ABI_enum_size),
    27: Attribute("Tag_ABI_HardFP_use", 27, "uleb128", Tag_ABI_HardFP_use),
    28: Attribute("Tag_ABI_VFP_args", 28, "uleb128", Tag_ABI_VFP_args),
    29: Attribute("Tag_ABI_WMMX_args", 29, "uleb128", Tag_ABI_WMMX_args),
    30: Attribute("Tag_ABI_optimization_goals", 30, "uleb128", Tag_ABI_optimization_goals),
    31: Attribute("Tag_ABI_FP_optimization_goals", 31, "uleb128", Tag_ABI_FP_optimization_goals),
    32: Attribute("Tag_compatibility", 32, "ntbs", Ident),
    34: Attribute("Tag_CPU_unaligned_access", 34, "uleb128", Tag_CPU_unaligned_access),
    36: Attribute("Tag_FP_HP_extension (was Tag_VFP_HP_extension)",  36, "uleb128", Tag_FP_HP_extension),
    38: Attribute("Tag_ABI_FP_16bit_format", 38, "uleb128", Tag_ABI_FP_16bit_format),
    42: Attribute("Tag_MPextension_use", 42, "uleb128", Tag_MPextension_use),
    44: Attribute("Tag_DIV_use", 44, "uleb128", Tag_DIV_use),
    64: Attribute("Tag_nodefaults", 64, "uleb128", Ident),
    65: Attribute("Tag_also_compatible_with", 65, "ntbs", Ident),
    67: Attribute("Tag_conformance", 67, "ntbs", Ident),
    66: Attribute("Tag_T2EE_use", 66, "uleb128", Tag_T2EE_use),
    68: Attribute("Tag_Virtualization_use", 68, "uleb128", Tag_Virtualization_use),
    70: Attribute("Tag_MPextension_use", 70, "uleb128", Tag_MPextension_use),
}


class PrematureEndOfSectionError(Exception): pass
class MalformedStructureError(Exception): pass


class ArmAttributes(object):

    def __init__(self, attrs, endianess = "<"):
        print(len(attrs))
        #version = ord(attrs[0])
        version = attrs[0]
        print("VERSION:", version)
        self.idx = 0
        self.version = version
        self.endianess = endianess
        self.blob = attrs[1 : ]
        print("BLOB", self.blob)
        self.attrs = OrderedDict()
        self.sections = self._splitSections(self.blob)
        pprint(self.attrs)

    ###############################
    def uleb128(self):
        result = 0
        shift = 0
        idx = 0
        for bval in self.next():
            bval = ord(bval)
            result |= ((bval & 0x7f) << shift)
            idx += 1
            if bval & 0x80 == 0:
                break
            shift += 7
        return result

    def ntbs(self):
        result = []
        while True:
            octet = self.next()
            if octet != '\x00':
                result.append(octet)
            else:
                break
        return ''.join(result)

    def uint32(self):
        result = struct.unpack("{}L".format(self.endianess), self.next(4))[0]
        return result
    ###############################


    def next(self, count = 1):
        """
        """
        data = self.blob[self.idx : self.idx + count]
        print("CHUNK", data)
        self.idx += count
        return data


    def pos(self):
        #return self.blob.tell()
        return self.idx

    def _splitSections(self, attrs):
        ctr = 0
        while attrs:
            size = self.uint32()
            vendor = self.ntbs()
            print("SV", size, vendor)
            break
            self.attrs.setdefault(vendor, OrderedDict())
            print(size, vendor)
            self._splitSubSections(vendor)
            if self.pos() >= size:
                break
            ctr += 1
            if ctr > 64:
                break

    def _splitSubSections(self, key):
        tag = self.next()
        size = self.uint32()
        start = self.pos()
        print(size)
        ctr = 0
        while True:
            attr = self.uleb128()
            attr = ATTRIBUTES[attr]
            value = self.FUNCTIONS[attr.parameterType](self)
            attrValue = attr.conv.get(value, value)
            pos = self.pos() + 5
            print("{0} ==> {1} [{2}]  <{3}>".format(attr.tag, value, attrValue, pos - start))
            self.attrs[key][attr.tag] = value
            if pos - start >= size:
                break
            ctr += 1
            if ctr > 64:
                break

    FUNCTIONS = {
        "ntbs": ntbs,
        "uleb128": uleb128,
        "uint32": uint32,
    }



attrs = ArmAttributes(ARM_ATTRS)

class TestAttrs(unittest.TestCase):

    def testVersion(self):
        self.assertEqual(ARM_ATTRS[0], 'A')

    def testSizeMatches(self):
        pass


class VerifyAttributes(unittest.TestCase):

    def testParameterTypes(self):
        for att in ATTRIBUTES.values():
            self.assertIn(att.parameterType, ("uint32", "ntbs", "uleb128"))

    def testConsitentNumbering(self):
        for num, att in ATTRIBUTES.items():
            self.assertEqual(num, att.value)



unittest.main()


"""
** Section #10 '.ARM.attributes' (SHT_ARM_ATTRIBUTES)
    Size   : 89 bytes

    'aeabi' file build attributes:
    0x000000:   43 32 2e 30 36 00 05 38 2d 41 2e 33 32 00 06 0a    C2.06..8-A.32...
    0x000010:   07 41 08 01 09 02 0a 05 0c 02 11 01 12 02 14 02    .A..............
    0x000020:   17 01 18 01 19 01 1a 01 1c 01 1e 03 22 01 24 01    ............".$.
    0x000030:   42 01 44 03 46 01 2c 02                            B.D.F.,.
        Tag_conformance = "2.06"
        Tag_CPU_name = "8-A.32"
        Tag_CPU_arch = ARM v7 (=10)
        Tag_CPU_arch_profile = The application profile 'A' (e.g. for Cortex A8) (=65)
        Tag_ARM_ISA_use = ARM instructions were permitted to be used (=1)
        Tag_THUMB_ISA_use = Thumb2 instructions were permitted (implies Thumb instructions permitted) (=2)
        Tag_VFP_arch = VFPv4 instructions were permitted (implies VFPv3 instructions were permitted) (=5)
        Tag_NEON_arch = Use of Advanced SIMD Architecture version 2 was permitted (=2)
        Tag_ABI_PCS_GOT_use = Data are imported directly (=1)
        Tag_ABI_PCS_wchar_t = Size of wchar_t is 2 (=2)
        Tag_ABI_FP_denormal = This code was permitted to require that the sign of a flushed-to-zero number be preserved in the sign of 0 (=2)
        Tag_ABI_FP_number_model = This code was permitted to use only IEEE 754 format FP numbers (=1)
        Tag_ABI_align8_needed = Code was permitted to depend on the 8-byte alignment of 8-byte data items (=1)
        Tag_ABI_align8_preserved = Code was required to preserve 8-byte alignment of 8-byte data objects (=1)
        Tag_ABI_enum_size = Enum values occupy the smallest container big enough to hold all values (=1)
        Tag_ABI_VFP_args = FP parameter/result passing conforms to the VFP variant of the AAPCS (=1)
        Tag_ABI_optimization_goals = Optimized for small size, but speed and debugging illusion preserved (=3)
        Tag_CPU_unaligned_access = The producer was permitted to generate architecture v6-style unaligned data accesses (=1)
        Tag_VFP_HP_extension = The producer was permitted to use the VFPv3/Advanced SIMD optional half-precision extension (=1)
        Tag_T2EE_use = Use of the T2EE extension was permitted (=1)
        Tag_Virtualization_use = Use of TrustZone and virtualization extensions was permitted (=3)
        Tag_MPextension_use = Use of the ARM v7 MP extension was permitted (=1)
        Tag_v7DIV_use = Code was permitted to use SDIV and UDIV; code is intended to execute on a CPU conforming to architecture v7 with the integer division extension (=2)

    'ARM' file build attributes:
    0x000000:   12 01 16 01
"""

