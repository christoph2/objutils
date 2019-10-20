#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import enum
from objutils.elf import defs

# Processor specific flags for the ELF header e_flags field.
EF_ARM_RELEXEC          = 0x01
EF_ARM_HASENTRY         = 0x02
EF_ARM_INTERWORK        = 0x04
EF_ARM_APCS_26          = 0x08
EF_ARM_APCS_FLOAT       = 0x10
EF_ARM_PIC              = 0x20
EF_ARM_ALIGN8           = 0x40         # 8-bit structure alignment is in use.
EF_ARM_NEW_ABI          = 0x80
EF_ARM_OLD_ABI          = 0x100
EF_ARM_SOFT_FLOAT       = 0x200
EF_ARM_VFP_FLOAT        = 0x400
EF_ARM_MAVERICK_FLOAT   = 0x800

# Frame unwind information
PT_ARM_EXIDX            = defs.PT_LOPROC + 1

# Other constants defined in the ARM ELF spec. version B-01.
EF_ARM_SYMSARESORTED    = 0x04          # NB conflicts with EF_INTERWORK.
EF_ARM_DYNSYMSUSESEGIDX = 0x08          # NB conflicts with EF_APCS26.
EF_ARM_MAPSYMSFIRST     = 0x10          # NB conflicts with EF_APCS_FLOAT.
EF_ARM_EABIMASK         = 0xFF000000

# New constants defined in the ARM ELF spec. version XXX.
# Only valid in conjunction with EF_ARM_EABI_VER5.
EF_ARM_ABI_FLOAT_SOFT   = 0x200         # NB conflicts with EF_ARM_SOFT_FLOAT.
EF_ARM_ABI_FLOAT_HARD   = 0x400         # NB conflicts with EF_ARM_VFP_FLOAT.

# Constants defined in AAELF.
EF_ARM_BE8              = 0x00800000
EF_ARM_LE8              = 0x00400000

EF_ARM_EABI_UNKNOWN     = 0x00000000
EF_ARM_EABI_VER1        = 0x01000000
EF_ARM_EABI_VER2        = 0x02000000
EF_ARM_EABI_VER3        = 0x03000000
EF_ARM_EABI_VER4        = 0x04000000
EF_ARM_EABI_VER5        = 0x05000000

# Local aliases for some flags to match names used by COFF port.
F_INTERWORK             = EF_ARM_INTERWORK
F_APCS26                = EF_ARM_APCS_26
F_APCS_FLOAT            = EF_ARM_APCS_FLOAT
F_PIC                   = EF_ARM_PIC
F_SOFT_FLOAT            = EF_ARM_SOFT_FLOAT
F_VFP_FLOAT             = EF_ARM_VFP_FLOAT

# Additional symbol types for Thumb.
STT_ARM_TFUNC           = defs.STT_LOPROC   # A Thumb function.
STT_ARM_16BIT           = defs.STT_HIPROC   # A Thumb label.

# /* Additional section types.
SHT_ARM_EXIDX           = 0x70000001    # Section holds ARM unwind info.
SHT_ARM_PREEMPTMAP      = 0x70000002    # Section pre-emption details.
SHT_ARM_ATTRIBUTES      = 0x70000003    # Section holds attributes.
SHT_ARM_DEBUGOVERLAY    = 0x70000004    # Section holds overlay debug info.
SHT_ARM_OVERLAYSECTION  = 0x70000005    # Section holds GDB and overlay integration info.

# ARM-specific values for sh_flags.
SHF_ENTRYSECT           = 0x10000000    # Section contains an entry point.
SHF_COMDEF              = 0x80000000    # Section may be multiply defined in the input to a link step.

# ARM-specific program header flags.
PF_ARM_SB               = 0x10000000    # Segment contains the location addressed by the static base.
PF_ARM_PI               = 0x20000000    # Segment is position-independent.
PF_ARM_ABS              = 0x40000000    # Segment must be loaded at its base address.

# /* Values for the Tag_CPU_arch EABI attribute.
TAG_CPU_ARCH_PRE_V4     = 0
TAG_CPU_ARCH_V4         = 1
TAG_CPU_ARCH_V4T        = 2
TAG_CPU_ARCH_V5T        = 3
TAG_CPU_ARCH_V5TE       = 4
TAG_CPU_ARCH_V5TEJ      = 5
TAG_CPU_ARCH_V6         = 6
TAG_CPU_ARCH_V6KZ       = 7
TAG_CPU_ARCH_V6T2       = 8
TAG_CPU_ARCH_V6K        = 9
TAG_CPU_ARCH_V7         = 10
TAG_CPU_ARCH_V6_M       = 11
TAG_CPU_ARCH_V6S_M      = 12
TAG_CPU_ARCH_V7E_M      = 13
TAG_CPU_ARCH_V8         = 14
MAX_TAG_CPU_ARCH        = 14
# Pseudo-architecture to allow objects to be compatible with the subset of
# armv4t and armv6-m.  This value should never be stored in object files.
TAG_CPU_ARCH_V4T_PLUS_V6_M  = (MAX_TAG_CPU_ARCH + 1)


class ElfArmRelocType(enum.IntEnum):

# AAELF official names and numbers.
    R_ARM_NONE =               0
    R_ARM_PC24 =               1   # deprecated
    R_ARM_ABS32 =              2
    R_ARM_REL32 =              3
    R_ARM_LDR_PC_G0 =          4
    R_ARM_ABS16 =              5
    R_ARM_ABS12 =              6
    R_ARM_THM_ABS5 =           7
    R_ARM_ABS8 =               8
    R_ARM_SBREL32 =            9
    R_ARM_THM_CALL =          10
    R_ARM_THM_PC8 =           11
    R_ARM_BREL_ADJ =          12
    R_ARM_TLS_DESC =          13
    R_ARM_THM_SWI8 =          14   # obsolete
    R_ARM_XPC25 =             15   # obsolete
    R_ARM_THM_XPC22 =         16   # obsolete
    R_ARM_TLS_DTPMOD32 =      17
    R_ARM_TLS_DTPOFF32 =      18
    R_ARM_TLS_TPOFF32 =       19
    R_ARM_COPY =              20   # Copy symbol at runtime.
    R_ARM_GLOB_DAT =          21   # Create GOT entry.
    R_ARM_JUMP_SLOT =         22   # Create PLT entry.
    R_ARM_RELATIVE =          23   # Adjust by program base.
    R_ARM_GOTOFF32 =          24   # 32 bit offset to GOT.
    R_ARM_BASE_PREL =         25   # 32 bit PC relative offset to GOT.
    R_ARM_GOT_BREL =          26   # 32 bit GOT entry.
    R_ARM_PLT32 =             27   # deprecated - 32 bit PLT address.
    R_ARM_CALL =              28
    R_ARM_JUMP24 =            29
    R_ARM_THM_JUMP24 =        30
    R_ARM_BASE_ABS =          31
    R_ARM_ALU_PCREL7_0 =      32   # obsolete
    R_ARM_ALU_PCREL15_8 =     33   # obsolete
    R_ARM_ALU_PCREL23_15 =    34   # obsolete
    R_ARM_LDR_SBREL_11_0 =    35   # deprecated, should have _NC suffix
    R_ARM_ALU_SBREL_19_12 =   36   # deprecated, should have _NC suffix
    R_ARM_ALU_SBREL_27_20 =   37   # deprecated, should have _CK suffix
    R_ARM_TARGET1 =           38
    R_ARM_SBREL31 =           39   # deprecated
    R_ARM_V4BX =              40
    R_ARM_TARGET2 =           41
    R_ARM_PREL31 =            42
    R_ARM_MOVW_ABS_NC =       43
    R_ARM_MOVT_ABS =          44
    R_ARM_MOVW_PREL_NC =      45
    R_ARM_MOVT_PREL =         46
    R_ARM_THM_MOVW_ABS_NC =   47
    R_ARM_THM_MOVT_ABS =      48
    R_ARM_THM_MOVW_PREL_NC =  49
    R_ARM_THM_MOVT_PREL =     50
    R_ARM_THM_JUMP19 =        51
    R_ARM_THM_JUMP6 =         52
    R_ARM_THM_ALU_PREL_11_0 = 53
    R_ARM_THM_PC12 =          54
    R_ARM_ABS32_NOI =         55
    R_ARM_REL32_NOI =         56
    R_ARM_ALU_PC_G0_NC =      57
    R_ARM_ALU_PC_G0 =         58
    R_ARM_ALU_PC_G1_NC =      59
    R_ARM_ALU_PC_G1 =         60
    R_ARM_ALU_PC_G2 =         61
    R_ARM_LDR_PC_G1 =         62
    R_ARM_LDR_PC_G2 =         63
    R_ARM_LDRS_PC_G0 =        64
    R_ARM_LDRS_PC_G1 =        65
    R_ARM_LDRS_PC_G2 =        66
    R_ARM_LDC_PC_G0 =         67
    R_ARM_LDC_PC_G1 =         68
    R_ARM_LDC_PC_G2 =         69
    R_ARM_ALU_SB_G0_NC =      70
    R_ARM_ALU_SB_G0 =         71
    R_ARM_ALU_SB_G1_NC =      72
    R_ARM_ALU_SB_G1 =         73
    R_ARM_ALU_SB_G2 =         74
    R_ARM_LDR_SB_G0 =         75
    R_ARM_LDR_SB_G1 =         76
    R_ARM_LDR_SB_G2 =         77
    R_ARM_LDRS_SB_G0 =        78
    R_ARM_LDRS_SB_G1 =        79
    R_ARM_LDRS_SB_G2 =        80
    R_ARM_LDC_SB_G0 =         81
    R_ARM_LDC_SB_G1 =         82
    R_ARM_LDC_SB_G2 =         83
    R_ARM_MOVW_BREL_NC =      84
    R_ARM_MOVT_BREL =         85
    R_ARM_MOVW_BREL =         86
    R_ARM_THM_MOVW_BREL_NC =  87
    R_ARM_THM_MOVT_BREL =     88
    R_ARM_THM_MOVW_BREL =     89
    R_ARM_TLS_GOTDESC =       90
    R_ARM_TLS_CALL =          91
    R_ARM_TLS_DESCSEQ =       92
    R_ARM_THM_TLS_CALL =      93
    R_ARM_PLT32_ABS =         94
    R_ARM_GOT_ABS =           95
    R_ARM_GOT_PREL =          96
    R_ARM_GOT_BREL12 =        97
    R_ARM_GOTOFF12 =          98
    R_ARM_GOTRELAX =          99
    R_ARM_GNU_VTENTRY =      100   # deprecated - old C++ abi
    R_ARM_GNU_VTINHERIT =    101   # deprecated - old C++ abi
    R_ARM_THM_JUMP11 =       102
    R_ARM_THM_JUMP8 =        103
    R_ARM_TLS_GD32 =         104
    R_ARM_TLS_LDM32 =        105
    R_ARM_TLS_LDO32 =        106
    R_ARM_TLS_IE32 =         107
    R_ARM_TLS_LE32 =         108
    R_ARM_TLS_LDO12 =        109
    R_ARM_TLS_LE12 =         110
    R_ARM_TLS_IE12GP =       111
    # 112 - 127 private range
    R_ARM_ME_TOO =           128   # obsolete
    R_ARM_THM_TLS_DESCSEQ =  129

    R_ARM_IRELATIVE =        160

    # Extensions?  R=read-only?
    R_ARM_RXPC25 =           249
    R_ARM_RSBREL32 =         250
    R_ARM_THM_RPC22 =        251
    R_ARM_RREL32 =           252
    R_ARM_RABS32 =           253
    R_ARM_RPC24 =            254
    R_ARM_RBASE =            255

    # Unofficial names for some of the relocs.
    R_ARM_GOTOFF =           R_ARM_GOTOFF32   # 32 bit offset to GOT.
    R_ARM_THM_PC22 =         R_ARM_THM_CALL
    R_ARM_THM_PC11 =         R_ARM_THM_JUMP11
    R_ARM_THM_PC9 =          R_ARM_THM_JUMP8

    # Relocs with both a different name, and (apparently) different meaning in
    # GNU usage.
    R_ARM_GOTPC =              R_ARM_BASE_PREL  # 32 bit PC relative offset to GOT.
    R_ARM_GOT32 =              R_ARM_GOT_BREL   # 32 bit GOT entry.
    R_ARM_ROSEGREL32 =         R_ARM_SBREL31    # ???
    R_ARM_AMP_VCALL9 =         R_ARM_BREL_ADJ   # Thumb-something.  Not used.

    R_ARM_max = 256


def decodeARMMachineFlags(flags):
    result = ''
    unknown = False
    eabi = flags  & EF_ARM_EABIMASK
    flags &= ~EF_ARM_EABIMASK

    if flags & EF_ARM_RELEXEC:
        result += ", relocatable0 executable"
        flags &= ~ EF_ARM_RELEXEC

    if flags & EF_ARM_HASENTRY:
        result += ", has entry point"
        flags &= ~ EF_ARM_HASENTRY

    if eabi == EF_ARM_EABI_VER1:
        result += ", Version1 EABI"
        while flags:
            flag = flags & -flags
            flags &= ~ flag
            if flag == EF_ARM_SYMSARESORTED:
                result += ", sorted symbol tables"
            else:
                unknown = True
    elif eabi == EF_ARM_EABI_VER2:
        result += ", Version2 EABI"
        while flags:
            flag = flags & -flags
            flags &= ~ flag
            if flag == EF_ARM_SYMSARESORTED:    # Conflicts with EF_ARM_INTERWORK.
                result += ", sorted symbol tables"
            elif flsg == EF_ARM_DYNSYMSUSESEGIDX:
                result += ", dynamic symbols use segment index"
            elif flag == EF_ARM_MAPSYMSFIRST:
                result += ", mapping symbols precede others"
            else:
                unknown = True
    elif eabi == EF_ARM_EABI_VER3:
        result += ", Version3 EABI"
    elif eabi == EF_ARM_EABI_VER4:
        result += ", Version4 EABI"
        while flags:
            flag = flags & -flags
            flags &= ~ flag
            if flag == EF_ARM_BE8:
                result += ", BE8"
            elif flag == EF_ARM_LE8:
                result += ", LE8"
            else:
                unknown = True
    elif eabi == EF_ARM_EABI_VER5:
        result += ", Version5 EABI"
        while flags:
            flag = flags & -flags
            flags &= ~ flag
            if flag == EF_ARM_BE8:
                result += ", BE8"
            elif flag == EF_ARM_LE8:
                result += ", LE8"
            elif flag == EF_ARM_ABI_FLOAT_SOFT: # Conflicts with EF_ARM_SOFT_FLOAT.
                result += ", soft-float ABI"
            elif flag == EF_ARM_ABI_FLOAT_HARD: # Conflicts with EF_ARM_VFP_FLOAT.
                result += ", hard-float ABI"
            else:
                unknown = True
    elif eabi == EF_ARM_EABI_UNKNOWN:
        result += ", GNU EABI"
        while flags:
            flag = flags & -flags
            flags &= ~ flag
            if flag == EF_ARM_INTERWORK:
                result += ", interworking enabled"
            elif flag == EF_ARM_APCS_26:
                result += ", uses APCS/26"
            elif flag == EF_ARM_APCS_FLOAT:
                result += ", uses APCS/float"
            elif flag == EF_ARM_PIC:
                result += ", position independent"
            elif flag == EF_ARM_ALIGN8:
                result += ", 8 bit structure alignment"
            elif flag == EF_ARM_NEW_ABI:
                result += ", uses new ABI"
            elif flag == EF_ARM_OLD_ABI:
                result += ", uses old ABI"
            elif flag == EF_ARM_SOFT_FLOAT:
                result += ", software FP"
            elif flag == EF_ARM_VFP_FLOAT:
                result += ", VFP"
            elif flag == EF_ARM_MAVERICK_FLOAT:
                result += ", Maverick FP"
            else:
                unknwown = True

    else:
        result += ", <unrecognized EABI>"
        if flags:
            unknown = True
    if unknown:
        result += ", <unknown>"
    return result

