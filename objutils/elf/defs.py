#!/usr/bin/env python
"""ELF (Executable and Linkable Format) definitions module.

This module contains comprehensive definitions for the ELF file format, including:

- **File Type Definitions**: ELF file types (relocatable, executable, shared objects, core dumps)
- **Machine Architecture Types**: Support for 100+ processor architectures (x86, ARM, AVR, MIPS, etc.)
- **Section Definitions**: Section types, flags, and special section indices
- **Symbol Table Definitions**: Symbol bindings, types, and visibility attributes
- **Program Headers**: Segment types and flags for program loading
- **Data Classes**: Machine-specific data structures (AVR, ARM) for architecture details
- **Constants**: Magic numbers, version identifiers, and format strings

The module provides type-safe enumerations for all ELF constants following the official
ELF specification (System V ABI, ARM EABI, AVR EABI, etc.). All enumerations use IntEnum
for compatibility with C-style integer constants.

Key Classes:
    ELFType: ELF file type identifiers
    ELFMachineType: Machine/processor architecture identifiers
    ELFClass: 32-bit vs 64-bit architecture
    SectionType: Section type identifiers
    SectionFlags: Section attribute flags
    SymbolBinding: Symbol binding types (local, global, weak)
    SymbolType: Symbol types (function, object, section, etc.)
    ProgramHeader: Program segment types

Data Classes:
    MachineData: Base class for machine-specific data
    AvrMachineData: AVR-specific machine data and flags
    ArmMachineData: ARM-specific machine data and EABI flags

References:
    - ELF Specification: http://www.sco.com/developers/gabi/
    - ARM EABI: https://github.com/ARM-software/abi-aa
    - AVR EABI: http://ww1.microchip.com/downloads/en/AppNotes/doc1455.pdf
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import struct
from collections import namedtuple


ELF_MAGIC = b"\x7fELF"

EI_NIDENT = 16  # Size of e_ident[].
HDR_FMT32 = "HHIIIIIHHHHHH"
HDR_FMT64 = "HHIQQQIHHHHHH"


Elf32_Ehdr = namedtuple(
    "Elf32_Ehdr",
    """e_type e_machine e_version e_entry e_phoff e_shoff e_flags e_ehsize
                        e_phentsize e_phnum e_shentsize e_shnum e_shstrndx""",
)


class ELFType(enum.IntEnum):
    """ELF file type identifiers.
    
    Defines the object file type identifying what kind of ELF file this is.
    The file type determines how the ELF file should be interpreted and used.
    
    Attributes:
        ET_NONE: No file type (unknown or invalid)
        ET_REL: Relocatable file (object file, .o)
        ET_EXEC: Executable file (standalone program)
        ET_DYN: Shared object file (dynamic library, .so)
        ET_CORE: Core dump file (process memory snapshot)
        ET_NUM: Number of defined standard types
        ET_LOOS: OS-specific range start (0xFE00)
        ET_HIOS: OS-specific range end (0xFEFF)
        ET_LOPROC: Processor-specific range start (0xFF00)
        ET_HIPROC: Processor-specific range end (0xFFFF)
    """
    ET_NONE = 0
    " No file type"
    ET_REL = 1
    " Relocatable file"
    ET_EXEC = 2
    " Executable file"
    ET_DYN = 3
    " Shared object file"
    ET_CORE = 4
    " Core file"
    ET_NUM = 5
    "Number of defined types"
    ET_LOOS = 0xFE00
    "Operating system-specific"
    ET_HIOS = 0xFEFF
    "Operating system-specific"
    ET_LOPROC = 0xFF00
    " Processor-specific"
    ET_HIPROC = 0xFFFF
    "Processor-specific"


ELF_TYPE_NAMES = {
    ELFType.ET_NONE: "No file type",
    ELFType.ET_REL: "Relocatable file",
    ELFType.ET_EXEC: "Executable file",
    ELFType.ET_DYN: "Shared object file",
    ELFType.ET_CORE: "Core file",
}


class ELFMachineType(enum.IntEnum):
    """ELF machine (processor architecture) type identifiers.
    
    Identifies the target processor architecture for the ELF file. This extensive
    enumeration covers over 100 processor architectures including modern and legacy
    systems, embedded microcontrollers, DSPs, and specialized processors.
    
    The values are standardized by the ELF specification and various processor
    vendors. Architecture-specific behavior and relocations are defined by the
    corresponding processor supplement to the ELF specification.
    
    Common architectures include:
        - x86: EM_386 (Intel 80386)
        - x86-64: EM_X86_64 (AMD/Intel 64-bit)
        - ARM: EM_ARM (32-bit ARM)
        - AVR: EM_AVR (Atmel AVR 8-bit)
        - MIPS: EM_MIPS
        - PowerPC: EM_PPC, EM_PPC64
        - SPARC: EM_SPARC, EM_SPARCV9
    
    Note: Some values are reserved or obsolete but maintained for compatibility.
    """
    EM_NONE = 0  # No machine.
    EM_M32 = 1  # AT&T WE 32100.
    EM_SPARC = 2  # SPARC.
    EM_386 = 3  # Intel 80386.
    EM_68K = 4  # Motorola 68000.
    EM_88K = 5  # Motorola 88000.

    """
    RESERVED 6 Reserved for future use
    """

    EM_860 = 7  # Intel 80860.
    EM_MIPS = 8  # MIPS I Architecture.
    EM_S370 = 9  # IBM System/370 Processor.
    EM_MIPS_RS3_LE = 10  # MIPS RS3000 Little-endian.

    """
    RESERVED 11-14 Reserved for future use
    """

    EM_PARISC = 15  # Hewlett-Packard PA-RISC.
    RESERVED = 16  # Reserved for future use.
    EM_VPP500 = 17  # Fujitsu VPP500.
    EM_SPARC32PLUS = 18  # Enhanced instruction set SPARC.
    EM_960 = 19  # Intel 80960.
    EM_PPC = 20  # PowerPC.
    EM_PPC64 = 21  # 64-bit PowerPC.
    EM_S390 = 22  # IBM S390.
    EM_SPU = 23  # Sony/Toshiba/IBM SPU.

    """
    RESERVED 24-35 Reserved for future use
    """

    EM_V800 = 36  # NEC V800.
    EM_FR20 = 37  # Fujitsu FR20.
    EM_RH32 = 38  # TRW RH-32.
    EM_RCE = 39  # Motorola RCE.
    EM_ARM = 40  # Advanced RISC Machines ARM.
    EM_ALPHA = 41  # Digital Alpha.
    EM_SH = 42  # Hitachi SH.
    EM_SPARCV9 = 43  # SPARC Version 9.
    EM_TRICORE = 44  # Siemens Tricore embedded processor.
    EM_ARC = 45  # Argonaut RISC Core, Argonaut Technologies Inc.
    EM_H8_300 = 46  # Hitachi H8/300.
    EM_H8_300H = 47  # Hitachi H8/300H.
    EM_H8S = 48  # Hitachi H8S.
    EM_H8_500 = 49  # Hitachi H8/500.
    EM_IA_64 = 50  # Intel IA-64 processor architecture.
    EM_MIPS_X = 51  # Stanford MIPS-X.
    EM_COLDFIRE = 52  # Motorola ColdFire.
    EM_68HC12 = 53  # Motorola M68HC12.    # could also be 0x4D12 (s. HC12EABI)
    EM_MMA = 54  # Fujitsu MMA Multimedia Accelerator.
    EM_PCP = 55  # Siemens PCP.
    EM_NCPU = 56  # Sony nCPU embedded RISC processor.
    EM_NDR1 = 57  # Denso NDR1 microprocessor.
    EM_STARCORE = 58  # Motorola Star*Core processor.
    EM_ME16 = 59  # Toyota ME16 processor.
    EM_ST100 = 60  # STMicroelectronics ST100 processor.
    EM_TINYJ = 61  # Advanced Logic Corp. TinyJ embedded processor family.
    EM_X86_64 = 62  # Advanced Micro Devices X86-64.
    EM_PDSP = 63  # Sony DSP Processor.
    EM_PDP10 = 64  # DEC PDP-10
    EM_PDP11 = 65  # DEC PDP-11
    EM_FX66 = 66  # Siemens FX66 microcontroller.
    EM_ST9PLUS = 67  # STMicroelectronics ST9+ 8/16 bit microcontroller.
    EM_ST7 = 68  # STMicroelectronics ST7 8-bit microcontroller.
    EM_68HC16 = 69  # Motorola MC68HC16 Microcontroller.
    EM_68HC11 = 70  # Motorola MC68HC11 Microcontroller.
    EM_68HC08 = 71  # Motorola MC68HC08 Microcontroller.
    EM_68HC05 = 72  # Motorola MC68HC05 Microcontroller.
    EM_SVX = 73  # Silicon Graphics SVx.
    EM_ST19 = 74  # STMicroelectronics ST19 8-bit microcontroller.
    EM_VAX = 75  # Digital VAX.
    EM_CRIS = 76  # Axis Communications 32-bit embedded processor.
    EM_JAVELIN = 77  # Infineon Technologies 32-bit embedded processor.
    EM_FIREPATH = 78  # Element 14 64-bit DSP Processor.
    EM_ZSP = 79  # LSI Logic 16-bit DSP Processor.
    EM_MMIX = 80  # Donald Knuth's educational 64-bit processor.
    EM_HUANY = 81  # Harvard University machine-independent object files .
    EM_PRISM = 82  # SiTera Prism.
    EM_AVR = 83  # Atmel AVR 8-bit microcontroller.
    EM_FR30 = 84  # Fujitsu FR30.
    EM_D10V = 85  # Mitsubishi D10V.
    EM_D30V = 86  # Mitsubishi D30V.
    EM_V850 = 87  # NEC v850.
    EM_M32R = 88  # Mitsubishi M32R.
    EM_MN10300 = 89  # Matsushita MN10300.
    EM_MN10200 = 90  # Matsushita MN10200.
    EM_PJ = 91  # picoJava.
    EM_OPENRISC = 92  # OpenRISC 32-bit embedded processor.
    EM_ARC_A5 = 93  # ARC Cores Tangent-A5.
    EM_XTENSA = 94  # Tensilica Xtensa Architecture.
    EM_VIDEOCORE = 95  # Alphamosaic VideoCore processor.
    EM_TMM_GPP = 96  # Thompson Multimedia General Purpose Processor.
    EM_NS32K = 97  # National Semiconductor 32000 series.
    EM_TPC = 98  # Tenor Network TPC processor.
    EM_SNP1K = 99  # Trebia SNP 1000 processor.
    EM_ST200 = 100  # STMicroelectronics ST200 microcontroller.
    EM_IP2K = 101  # Ubicom IP2022 micro controller.
    EM_MAX = 102  # MAX Processor.
    EM_CR = 103  # National Semiconductor CompactRISC.
    EM_F2MC16 = 104  # Fujitsu F2MC16.
    EM_MSP430 = 105  # TI msp430 micro controller.
    EM_BLACKFIN = 106  # ADI Blackfin.
    EM_SE_C33 = 107  # S1C33 Family of Seiko Epson processors.
    EM_SEP = 108  # Sharp embedded microprocessor.
    EM_ARCA = 109  # Arca RISC Microprocessor.
    EM_UNICORE = 110  # Microprocessor series from PKU-Unity Ltd. and MPRC of Peking University.
    EM_EXCESS = 111  # eXcess: 16/32/64-bit configurable embedded CPU.
    EM_DXP = 112  # Icera Semiconductor Inc. Deep Execution Processor.
    EM_ALTERA_NIOS2 = 113  # Altera Nios II soft-core processor.
    EM_CRX = 114  # National Semiconductor CRX.
    EM_XGATE = 115  # Motorola XGATE embedded processor.
    EM_C166 = 116  # Infineon C16x/XC16x processor.
    EM_M16C = 117  # Renesas M16C series microprocessors.
    EM_DSPIC30F = 118  # Microchip Technology dsPIC30F Digital Signal Controller.
    EM_CE = 119  # Freescale Communication Engine RISC core.
    EM_M32C = 120  # Renesas M32C series microprocessors.
    EM_TSK3000 = 131  # Altium TSK3000 core.
    EM_RS08 = 132  # Freescale RS08 embedded processor.
    EM_ECOG2 = 134  # Cyan Technology eCOG2 microprocessor.
    EM_SCORE = 135  # Sunplus Score.
    EM_SCORE7 = 135  # Sunplus S+core7 RISC processor.
    EM_DSP24 = 136  # New Japan Radio (NJR) 24-bit DSP Processor.
    EM_VIDEOCORE3 = 137  # Broadcom VideoCore III processor.
    EM_LATTICEMICO32 = 138  # RISC processor for Lattice FPGA architecture.
    EM_SE_C17 = 139  # Seiko Epson C17 family.
    EM_TI_C6000 = 140  # Texas Instruments TMS320C6000 DSP family.
    EM_TI_C2000 = 141  # Texas Instruments TMS320C2000 DSP family.
    EM_TI_C5500 = 142  # Texas Instruments TMS320C55x DSP family.
    EM_TI_ARP32 = 143  # Texas Instruments App. Specific RISC
    EM_TI_PRU = 144  # Texas Instruments PRU I/O processor

    EM_MMDSP_PLUS = 160  # STMicroelectronics 64bit VLIW Data Signal Processor.
    EM_CYPRESS_M8C = 161  # Cypress M8C microprocessor.
    EM_R32C = 162  # Renesas R32C series microprocessors.
    EM_TRIMEDIA = 163  # NXP Semiconductors TriMedia architecture family.
    EM_QDSP6 = 164  # QUALCOMM DSP6 Processor.
    EM_I8051 = 165  # Intel 8051 and variants.
    EM_STXP7X = 166  # STMicroelectronics STxP7x family.
    EM_NDS32 = 167  # Andes Technology compact code size embedded RISC processor family.
    EM_ECOG1 = 168  # Cyan Technology eCOG1X family.
    EM_ECOG1X = 168  # Cyan Technology eCOG1X family.
    EM_MAXQ30 = 169  # Dallas Semiconductor MAXQ30 Core Micro-controllers.
    EM_XIMO16 = 170  # New Japan Radio (NJR) 16-bit DSP Processor.
    EM_MANIK = 171  # M2000 Reconfigurable RISC Microprocessor.
    EM_CRAYNV2 = 172  # Cray Inc. NV2 vector architecture.
    EM_RX = 173  # Renesas RX family.
    EM_METAG = 174  # Imagination Technologies META processor architecture.
    EM_MCST_ELBRUS = 175  # MCST Elbrus general purpose hardware architecture.
    EM_ECOG16 = 176  # Cyan Technology eCOG16 family.
    EM_CR16 = 177  # National Semiconductor CompactRISC 16-bit processor.
    EM_ETPU = 178  # Freescale Extended Time Processing Unit.
    EM_SLE9X = 179  # Infineon Technologies SLE9X core.
    EM_L1OM = 180  # Intel L1OM.
    EM_AARCH64 = 183
    EM_AVR32 = 185  # Atmel Corporation 32-bit microprocessor family.
    EM_STM8 = 186  # STMicroeletronics STM8 8-bit microcontroller.
    EM_TILE64 = 187  # Tilera TILE64 multicore architecture family.
    EM_TILEPRO = 188  # Tilera TILEPro multicore architecture family.
    EM_MICROBLAZE = 189  # Xilinx MicroBlaze 32-bit RISC soft processor core.
    EM_CUDA = 190  # NVIDIA CUDA architecture.
    EM_TILEGX = 191  # Tilera TILE-Gx
    EM_AVR_OLD = 0x1057  # AVR magic number.  Written in the absense of an ABI.
    EM_MSP430_OLD = 0x1059  # MSP430 magic number.  Written in the absense of everything.
    EM_MT = 0x2530  # Morpho MT.   Written in the absense of an ABI.
    EM_CYGNUS_FR30 = 0x3330  # FR30 magic number - no EABI available.
    EM_OPENRISC_OLD = 0x3426  # OpenRISC magic number.  Written in the absense of an ABI.
    EM_DLX = 0x5AA5  # DLX magic number.  Written in the absense of an ABI.
    EM_CYGNUS_FRV = 0x5441  # FRV magic number - no EABI available??.
    EM_XC16X = 0x4688  # Infineon Technologies 16-bit microcontroller with C166-V2 core.
    EM_NEC_V850 = 0x723E  # V850ES/FJ3 /w NEC compiler.
    EM_CYGNUS_D10V = 0x7650  # D10V backend magic number.  Written in the absence of an ABI.
    EM_CYGNUS_D30V = 0x7676  # D30V backend magic number.  Written in the absence of an ABI.
    EM_IP2K_OLD = 0x8217  # Ubicom IP2xxx;   Written in the absense of an ABI.
    EM_OR32 = 0x8472  # (Deprecated) Temporary number for the OpenRISC processor.
    EM_CYGNUS_POWERPC = 0x9025  # Cygnus PowerPC ELF backend.  Written in the absence of an ABI.
    EM_ALPHA_NO_ABI = 0x9026  # Alpha backend magic number.  Written in the absence of an ABI.
    EM_CYGNUS_M32R = 0x9041  # Cygnus M32R ELF backend.  Written in the absence of an ABI.
    EM_CYGNUS_V850 = 0x9080  # V850 backend magic number.  Written in the absense of an ABI.
    EM_S390_OLD = 0xA390  # old S/390 backend magic number. Written in the absence of an ABI.
    EM_XTENSA_OLD = 0xABC7  # Old, unofficial value for Xtensa.
    EM_XSTORMY16 = 0xAD45
    EM_CYGNUS_MN10300 = 0xBEEF  # mn10200 and mn10300 backend magic numbers. Written in the absense of an ABI.
    EM_COOLRISC_C816 = 0xC816  # Raisonance CoolRISC C816.
    EM_CYGNUS_MN10200 = 0xDEAD
    EM_M32C_OLD = 0xFEB0  # Renesas M32C and M16C.
    EM_IQ2000 = 0xFEBA  # Vitesse IQ2000.
    EM_NIOS32 = 0xFEBB  # NIOS magic number - no EABI available.
    EM_CYGNUS_MEP = 0xF00D  # Toshiba MeP
    EM_MOXIE = 0xFEED  # Moxie
    EM_MICROBLAZE_OLD = 0xBAAB  # Old MicroBlaze
    EM_ADAPTEVA_EPIPHANY = 0x1223  # Adapteva's Epiphany architecture.


ELF_MACHINE_NAMES = {
    ELFMachineType.EM_NONE: "No machine",
    ELFMachineType.EM_M32: "AT&T WE 32100",
    ELFMachineType.EM_SPARC: "SPARC",
    ELFMachineType.EM_386: "Intel 80386",
    ELFMachineType.EM_68K: "Motorola 68000",
    ELFMachineType.EM_88K: "Motorola 88000",
    ELFMachineType.EM_860: "Intel 80860",
    ELFMachineType.EM_MIPS: "MIPS I Architecture",
    ELFMachineType.EM_S370: "IBM System/370 Processor",
    ELFMachineType.EM_MIPS_RS3_LE: "MIPS RS3000 Little-endian",
    ELFMachineType.EM_PARISC: "Hewlett-Packard PA-RISC",
    ELFMachineType.RESERVED: "Reserved for future use",
    ELFMachineType.EM_VPP500: "Fujitsu VPP500",
    ELFMachineType.EM_SPARC32PLUS: "Enhanced instruction set SPARC",
    ELFMachineType.EM_960: "Intel 80960",
    ELFMachineType.EM_PPC: "PowerPC",
    ELFMachineType.EM_PPC64: "PowerPC64",
    ELFMachineType.EM_S390: "IBM S390",
    ELFMachineType.EM_SPU: "Sony/Toshiba/IBM SPU",
    ELFMachineType.EM_V800: "Renesas V850 (using RH850 ABI)",
    ELFMachineType.EM_FR20: "Fujitsu FR20",
    ELFMachineType.EM_RH32: "TRW RH-32",
    ELFMachineType.EM_RCE: "Motorola RCE",
    ELFMachineType.EM_ARM: "ARM",
    ELFMachineType.EM_ALPHA: "Digital Alpha",
    ELFMachineType.EM_SH: "Hitachi SH",
    ELFMachineType.EM_SPARCV9: "SPARC Version 9",
    ELFMachineType.EM_TRICORE: "Siemens Tricore embedded processor",
    ELFMachineType.EM_ARC: "Argonaut RISC Core, Argonaut Technologies Inc",
    ELFMachineType.EM_H8_300: "Hitachi H8/300",
    ELFMachineType.EM_H8_300H: "Hitachi H8/300H",
    ELFMachineType.EM_H8S: "Hitachi H8S",
    ELFMachineType.EM_H8_500: "Hitachi H8/500",
    ELFMachineType.EM_IA_64: "Intel IA-64 processor architecture",
    ELFMachineType.EM_MIPS_X: "Stanford MIPS-X",
    ELFMachineType.EM_COLDFIRE: "Motorola ColdFire",
    ELFMachineType.EM_68HC12: "Motorola MC68HC12 Microcontroller",
    ELFMachineType.EM_MMA: "Fujitsu MMA Multimedia Accelerator",
    ELFMachineType.EM_PCP: "Siemens PCP",
    ELFMachineType.EM_NCPU: "Sony nCPU embedded RISC processor",
    ELFMachineType.EM_NDR1: "Denso NDR1 microprocessor",
    ELFMachineType.EM_STARCORE: "Motorola Star*Core processor",
    ELFMachineType.EM_ME16: "Toyota ME16 processor",
    ELFMachineType.EM_ST100: "STMicroelectronics ST100 processor",
    ELFMachineType.EM_TINYJ: "Advanced Logic Corp. TinyJ embedded processor family",
    ELFMachineType.EM_X86_64: "Advanced Micro Devices X86-64",
    ELFMachineType.EM_PDSP: "Sony DSP Processor",
    ELFMachineType.EM_PDP10: "DEC PDP-10",
    ELFMachineType.EM_PDP11: "DEC PDP-11",
    ELFMachineType.EM_FX66: "Siemens FX66 microcontroller",
    ELFMachineType.EM_ST9PLUS: "STMicroelectronics ST9+ 8/16 bit microcontroller",
    ELFMachineType.EM_ST7: "STMicroelectronics ST7 8-bit microcontroller",
    ELFMachineType.EM_68HC16: "Motorola MC68HC16 Microcontroller",
    ELFMachineType.EM_68HC11: "Motorola MC68HC11 Microcontroller",
    ELFMachineType.EM_68HC08: "Motorola MC68HC08 Microcontroller",
    ELFMachineType.EM_68HC05: "Motorola MC68HC05 Microcontroller",
    ELFMachineType.EM_SVX: "Silicon Graphics SVx",
    ELFMachineType.EM_ST19: "STMicroelectronics ST19 8-bit microcontroller",
    ELFMachineType.EM_VAX: "Digital VAX",
    ELFMachineType.EM_CRIS: "Axis Communications 32-bit embedded processor",
    ELFMachineType.EM_JAVELIN: "Infineon Technologies 32-bit embedded processor",
    ELFMachineType.EM_FIREPATH: "Element 14 64-bit DSP Processor",
    ELFMachineType.EM_ZSP: "LSI Logic 16-bit DSP Processor",
    ELFMachineType.EM_MMIX: "Donald Knuth's educational 64-bit processor",
    ELFMachineType.EM_HUANY: "Harvard University machine-independent object files",
    ELFMachineType.EM_PRISM: "SiTera Prism",
    ELFMachineType.EM_AVR: "Atmel AVR 8-bit microcontroller",
    ELFMachineType.EM_FR30: "Fujitsu FR30",
    ELFMachineType.EM_D10V: "Mitsubishi D10V",
    ELFMachineType.EM_D30V: "Mitsubishi D30V",
    ELFMachineType.EM_V850: "NEC v850",
    ELFMachineType.EM_M32R: "Mitsubishi M32R",
    ELFMachineType.EM_MN10300: "Matsushita MN10300",
    ELFMachineType.EM_MN10200: "Matsushita MN10200",
    ELFMachineType.EM_PJ: "picoJava",
    ELFMachineType.EM_OPENRISC: "OpenRISC 32-bit embedded processor",
    ELFMachineType.EM_ARC_A5: "ARC Cores Tangent-A5",
    ELFMachineType.EM_XTENSA: "Tensilica Xtensa Architecture",
    ELFMachineType.EM_VIDEOCORE: "Alphamosaic VideoCore processor",
    ELFMachineType.EM_TMM_GPP: "Thompson Multimedia General Purpose Processor",
    ELFMachineType.EM_NS32K: "National Semiconductor 32000 series",
    ELFMachineType.EM_TPC: "Tenor Network TPC processor",
    ELFMachineType.EM_SNP1K: "Trebia SNP 1000 processor",
    ELFMachineType.EM_ST200: "STMicroelectronics ST200 microcontroller",
    ELFMachineType.EM_IP2K: "Ubicom IP2022 micro controller",
    ELFMachineType.EM_MAX: "MAX Processor",
    ELFMachineType.EM_CR: "National Semiconductor CompactRISC",
    ELFMachineType.EM_F2MC16: "Fujitsu F2MC16",
    ELFMachineType.EM_MSP430: "TI msp430 micro controller",
    ELFMachineType.EM_BLACKFIN: "ADI Blackfin",
    ELFMachineType.EM_SE_C33: "S1C33 Family of Seiko Epson processors",
    ELFMachineType.EM_SEP: "Sharp embedded microprocessor",
    ELFMachineType.EM_ARCA: "Arca RISC Microprocessor",
    ELFMachineType.EM_UNICORE: "Microprocessor series from PKU-Unity Ltd. and MPRC of Peking University",
    ELFMachineType.EM_EXCESS: "eXcess: 16/32/64-bit configurable embedded CPU",
    ELFMachineType.EM_DXP: "Icera Semiconductor Inc. Deep Execution Processor",
    ELFMachineType.EM_ALTERA_NIOS2: "Altera Nios II soft-core processor",
    ELFMachineType.EM_CRX: "National Semiconductor CRX",
    ELFMachineType.EM_XGATE: "Motorola XGATE embedded processor",
    ELFMachineType.EM_C166: "Infineon Technologies xc16x",
    ELFMachineType.EM_M16C: "Renesas M16C series microprocessors",
    ELFMachineType.EM_DSPIC30F: "Microchip Technology dsPIC30F Digital Signal Controller",
    ELFMachineType.EM_CE: "Freescale Communication Engine RISC core",
    ELFMachineType.EM_M32C: "Renesas M32C series microprocessors",
    ELFMachineType.EM_TSK3000: "Altium TSK3000 core",
    ELFMachineType.EM_RS08: "Freescale RS08 embedded processor",
    ELFMachineType.EM_ECOG2: "Cyan Technology eCOG2 microprocessor",
    ELFMachineType.EM_SCORE: "Sunplus Score",
    ELFMachineType.EM_SCORE7: "Sunplus S+core7 RISC processor",
    ELFMachineType.EM_DSP24: "New Japan Radio (NJR) 24-bit DSP Processor",
    ELFMachineType.EM_VIDEOCORE3: "Broadcom VideoCore III processor",
    ELFMachineType.EM_LATTICEMICO32: "RISC processor for Lattice FPGA architecture",
    ELFMachineType.EM_SE_C17: "Seiko Epson C17 family",
    ELFMachineType.EM_TI_C6000: "Texas Instruments TMS320C6000 DSP family",
    ELFMachineType.EM_TI_C2000: "Texas Instruments TMS320C2000 DSP family",
    ELFMachineType.EM_TI_C5500: "Texas Instruments TMS320C55x DSP family",
    ELFMachineType.EM_TI_ARP32: "Texas Instruments App. Specific RISC",
    ELFMachineType.EM_TI_PRU: "Texas Instruments PRU I/O processor",
    ELFMachineType.EM_MMDSP_PLUS: "STMicroelectronics 64bit VLIW Data Signal Processor",
    ELFMachineType.EM_CYPRESS_M8C: "Cypress M8C microprocessor",
    ELFMachineType.EM_R32C: "Renesas R32C series microprocessors",
    ELFMachineType.EM_TRIMEDIA: "NXP Semiconductors TriMedia architecture family",
    ELFMachineType.EM_QDSP6: "QUALCOMM DSP6 Processor",
    ELFMachineType.EM_I8051: "Intel 8051 and variants",
    ELFMachineType.EM_STXP7X: "STMicroelectronics STxP7x family",
    ELFMachineType.EM_NDS32: "Andes Technology compact code size embedded RISC processor family",
    ELFMachineType.EM_ECOG1: "Cyan Technology eCOG1X family",
    ELFMachineType.EM_ECOG1X: "Cyan Technology eCOG1X family",
    ELFMachineType.EM_MAXQ30: "Dallas Semiconductor MAXQ30 Core Micro-controllers",
    ELFMachineType.EM_XIMO16: "New Japan Radio (NJR) 16-bit DSP Processor",
    ELFMachineType.EM_MANIK: "M2000 Reconfigurable RISC Microprocessor",
    ELFMachineType.EM_CRAYNV2: "Cray Inc. NV2 vector architecture",
    ELFMachineType.EM_RX: "Renesas RX family",
    ELFMachineType.EM_METAG: "Imagination Technologies META processor architecture",
    ELFMachineType.EM_MCST_ELBRUS: "MCST Elbrus general purpose hardware architecture",
    ELFMachineType.EM_ECOG16: "Cyan Technology eCOG16 family",
    ELFMachineType.EM_CR16: "National Semiconductor CompactRISC 16-bit processor",
    ELFMachineType.EM_ETPU: "Freescale Extended Time Processing Unit",
    ELFMachineType.EM_SLE9X: "Infineon Technologies SLE9X core",
    ELFMachineType.EM_L1OM: "Intel L1OM",
    ELFMachineType.EM_AARCH64: "AArch64",
    ELFMachineType.EM_AVR32: "Atmel Corporation 32-bit microprocessor family",
    ELFMachineType.EM_STM8: "STMicroeletronics STM8 8-bit microcontroller",
    ELFMachineType.EM_TILE64: "Tilera TILE64 multicore architecture family",
    ELFMachineType.EM_TILEPRO: "Tilera TILEPro multicore architecture family",
    ELFMachineType.EM_MICROBLAZE: "Xilinx MicroBlaze 32-bit RISC soft processor core",
    ELFMachineType.EM_TILEGX: "Tilera TILE-Gx",
    ELFMachineType.EM_CUDA: "NVIDIA CUDA architecture",
    ELFMachineType.EM_AVR_OLD: "AVR",
    ELFMachineType.EM_MSP430_OLD: "MSP430",
    ELFMachineType.EM_MT: "Morpho MT",
    ELFMachineType.EM_CYGNUS_FR30: "Cygnus FR30",
    ELFMachineType.EM_OPENRISC_OLD: "OpenRISC",
    ELFMachineType.EM_DLX: "DLX",
    ELFMachineType.EM_CYGNUS_FRV: "Cygnus FRV",
    ELFMachineType.EM_XC16X: "Infineon C166-V2 core",
    ELFMachineType.EM_NEC_V850: "V850ES/FJ3 (NEC compiler)",
    ELFMachineType.EM_CYGNUS_D10V: "Cygnus D10V",
    ELFMachineType.EM_CYGNUS_D30V: "Cygnus D30V",
    ELFMachineType.EM_IP2K_OLD: "Ubicom IP2xxx",
    ELFMachineType.EM_OR32: "OpenRISC 32",
    ELFMachineType.EM_CYGNUS_POWERPC: "Cygnus PowerPC",
    ELFMachineType.EM_ALPHA_NO_ABI: "Alpha",
    ELFMachineType.EM_CYGNUS_M32R: "Cygnus M32R",
    ELFMachineType.EM_CYGNUS_V850: "Cygnus V850",
    ELFMachineType.EM_S390_OLD: "S/390",
    ELFMachineType.EM_XTENSA_OLD: "Xtensa",
    ELFMachineType.EM_XSTORMY16: "Xstormy16",
    ELFMachineType.EM_CYGNUS_MN10300: "Cygnus mn10200 or mn10300",
    ELFMachineType.EM_COOLRISC_C816: "CoolRISC C816",
    ELFMachineType.EM_CYGNUS_MN10200: "Cygnus mn10200",
    ELFMachineType.EM_M32C_OLD: "Renesas M32C or M16C.",
    ELFMachineType.EM_IQ2000: "Vitesse IQ2000.",
    ELFMachineType.EM_NIOS32: "NIOS",
    ELFMachineType.EM_CYGNUS_MEP: "Toshiba MeP",
    ELFMachineType.EM_MOXIE: "Moxie",
    ELFMachineType.EM_MICROBLAZE_OLD: "Old MicroBlaze",
    ELFMachineType.EM_ADAPTEVA_EPIPHANY: "Adapteva Epiphany",
}


class AVRMachineType(enum.IntEnum):
    """AVR microcontroller architecture sub-types.
    
    Defines specific AVR architecture variants used in the ELF flags field.
    Each variant represents a different AVR instruction set and feature set.
    These values are defined by the AVR EABI specification.
    
    Attributes:
        E_AVR_MACH_AVR1: AVR1 architecture (basic instruction set)
        E_AVR_MACH_AVR2: AVR2 architecture
        E_AVR_MACH_AVR3: AVR3 architecture  
        E_AVR_MACH_AVR4: AVR4 architecture
        E_AVR_MACH_AVR5: AVR5 architecture
        E_AVR_MACH_AVR6: AVR6 architecture
        E_AVR_MACH_AVR25: AVR25 architecture
        E_AVR_MACH_AVR31: AVR31 architecture
        E_AVR_MACH_AVR35: AVR35 architecture
        E_AVR_MACH_AVR51: AVR51 architecture
        E_AVR_MACH_AVRTINY: AVR Tiny architecture (reduced instruction set)
        E_AVR_MACH_XMEGA1: AVR XMEGA1 architecture
        E_AVR_MACH_XMEGA2: AVR XMEGA2 architecture
        E_AVR_MACH_XMEGA3: AVR XMEGA3 architecture
        E_AVR_MACH_XMEGA4: AVR XMEGA4 architecture
        E_AVR_MACH_XMEGA5: AVR XMEGA5 architecture
        E_AVR_MACH_XMEGA6: AVR XMEGA6 architecture
        E_AVR_MACH_XMEGA7: AVR XMEGA7 architecture
    """
    E_AVR_MACH_AVR1 = 1
    E_AVR_MACH_AVR2 = 2
    E_AVR_MACH_AVR3 = 3
    E_AVR_MACH_AVR4 = 4
    E_AVR_MACH_AVR5 = 5
    E_AVR_MACH_AVR6 = 6
    E_AVR_MACH_AVR25 = 25
    E_AVR_MACH_AVR31 = 31
    E_AVR_MACH_AVR35 = 35
    E_AVR_MACH_AVR51 = 51
    E_AVR_MACH_AVRTINY = 100
    E_AVR_MACH_XMEGA1 = 101
    E_AVR_MACH_XMEGA2 = 102
    E_AVR_MACH_XMEGA3 = 103
    E_AVR_MACH_XMEGA4 = 104
    E_AVR_MACH_XMEGA5 = 105
    E_AVR_MACH_XMEGA6 = 106
    E_AVR_MACH_XMEGA7 = 107


AVRMachineTypeNames = {
    AVRMachineType.E_AVR_MACH_AVR1: "avr:1",
    AVRMachineType.E_AVR_MACH_AVR2: "avr:2",
    AVRMachineType.E_AVR_MACH_AVR3: "avr:3",
    AVRMachineType.E_AVR_MACH_AVR4: "avr:4",
    AVRMachineType.E_AVR_MACH_AVR5: "avr:5",
    AVRMachineType.E_AVR_MACH_AVR6: "avr:6",
    AVRMachineType.E_AVR_MACH_AVR25: "avr:25",
    AVRMachineType.E_AVR_MACH_AVR31: "avr:31",
    AVRMachineType.E_AVR_MACH_AVR35: "avr:35",
    AVRMachineType.E_AVR_MACH_AVR51: "avr:51",
    AVRMachineType.E_AVR_MACH_AVRTINY: "avr:100",
    AVRMachineType.E_AVR_MACH_XMEGA1: "avr:101",
    AVRMachineType.E_AVR_MACH_XMEGA2: "avr:102",
    AVRMachineType.E_AVR_MACH_XMEGA3: "avr:103",
    AVRMachineType.E_AVR_MACH_XMEGA4: "avr:104",
    AVRMachineType.E_AVR_MACH_XMEGA5: "avr:105",
    AVRMachineType.E_AVR_MACH_XMEGA6: "avr:106",
    AVRMachineType.E_AVR_MACH_XMEGA7: "avr:107",
}

EF_AVR_MACH = 0x7F
EF_AVR_LINKRELAX_PREPARED = 0x80

# Old ABI (ie GNU pre EABI).  These are deprecated.
EF_ARM_RELEXEC = 0x01
EF_ARM_INTERWORK = 0x04
EF_ARM_APCS_26 = 0x08
EF_ARM_APCS_FLOAT = 0x10
EF_ARM_PIC = 0x20
EF_ARM_ALIGN8 = 0x40  # 8-bit structure alignment is in use.
EF_ARM_NEW_ABI = 0x80
EF_ARM_OLD_ABI = 0x100
EF_ARM_SOFT_FLOAT = 0x200
EF_ARM_VFP_FLOAT = 0x400
EF_ARM_MAVERICK_FLOAT = 0x800

# Old ARM ELF spec. version B-01.  Mostly deprecated.
EF_ARM_SYMSARESORTED = 0x04  # NB conflicts with EF_INTERWORK.
EF_ARM_DYNSYMSUSESEGIDX = 0x08  # NB conflicts with EF_APCS26.
EF_ARM_MAPSYMSFIRST = 0x10  # NB conflicts with EF_APCS_FLOAT.

# New constants defined in the ARM ELF spec. version XXX (AAELF).
# Only valid in conjunction with EF_ARM_EABI_VER5.
EF_ARM_ABI_FLOAT_SOFT = 0x200  # NB conflicts with EF_ARM_SOFT_FLOAT.
EF_ARM_ABI_FLOAT_HARD = 0x400  # NB conflicts with EF_ARM_VFP_FLOAT.

# Constants defined in AAELF.
EF_ARM_BE8 = 0x00800000
EF_ARM_LE8 = 0x00400000

EF_ARM_EABIMASK = 0xFF000000
EF_ARM_EABIMASK_COM = 0x00FFFFFF

EF_ARM_EABI_UNKNOWN = 0x00000000
EF_ARM_EABI_VER1 = 0x01000000
EF_ARM_EABI_VER2 = 0x02000000
EF_ARM_EABI_VER3 = 0x03000000
EF_ARM_EABI_VER4 = 0x04000000
EF_ARM_EABI_VER5 = 0x05000000


class MachineData:
    """Base class for machine-specific ELF data.
    
    Provides a common interface for extracting and presenting machine-specific
    information from ELF file headers. Subclasses implement architecture-specific
    flag interpretation and formatting.
    
    Attributes:
        type_name: Short machine type name (e.g., "ARM", "AVR")
        type_value: Numeric machine type value from ELFMachineType
        machine_name: Full descriptive machine name
        flags: Machine-specific flags from ELF header
    """

    type_name: str = "???"
    type_value: int = -1
    machine_name: str = "<unknown>"

    def __init__(self, machine_code: int, flags: int) -> None:
        """Initialize machine data from ELF header values.
        
        Args:
            machine_code: Machine type code from ELF header (e_machine)
            flags: Machine-specific flags from ELF header (e_flags)
        """
        self.flags = flags
        try:
            ELFMachineType(machine_code)
        except Exception:
            self.type_name = "???"
            self.type_value = -1
            self.machine_name = "<unknown>"
        else:
            machine = ELFMachineType(machine_code)
            self.type_name = machine.name[3:]  # get rid of 'EM_'.
            self.type_value = machine.value
            self.machine_name = ELF_MACHINE_NAMES.get(self.type_value, "<unknown>")

    def specific(self) -> list[str]:
        """Extract machine-specific flag information.
        
        Returns:
            List of human-readable strings describing machine-specific flags.
            Base implementation returns empty list.
        """
        return []

    def __str__(self) -> str:
        """Format machine data as human-readable string.
        
        Returns:
            Formatted string with type, machine name, and specific flags.
        """
        spec = self.specific()
        if spec:
            return f'{self.type_name!s} [{self.machine_name!s}] [{", ".join(spec)}]'
        else:
            return f"{self.type_name!s} [{self.machine_name!s}]"

    __repr__ = __str__


class AvrMachineData(MachineData):
    """AVR-specific machine data and flag interpretation.
    
    Extracts and formats AVR architecture-specific information from ELF flags,
    including the specific AVR sub-architecture variant and linker relaxation status.
    Follows the AVR EABI specification for flag interpretation.
    """

    def specific(self) -> list[str]:
        """Extract AVR-specific flags.
        
        Returns:
            List containing AVR architecture variant and optional features like
            link-relax preparation.
        """
        flags = self.flags & EF_AVR_MACH
        result = []
        if flags in AVRMachineTypeNames:
            result.append(AVRMachineTypeNames[flags])
        else:
            result.append("avr:<unknown>")
        if flags & EF_AVR_LINKRELAX_PREPARED:
            result.append("link-relax")
        return result


class ArmMachineData(MachineData):
    """ARM-specific machine data and EABI flag interpretation.
    
    Extracts and formats ARM architecture-specific information from ELF flags,
    including EABI version and ARM-specific attributes like relocatable executable
    and position-independent code flags. Follows the ARM EABI specification.
    """

    def specific(self) -> list[str]:
        """Extract ARM-specific flags.
        
        Returns:
            List of ARM-specific features extracted from e_flags.
            Currently returns empty list (implementation placeholder).
        """
        eabi = self.flags & EF_ARM_EABIMASK
        flags = self.flags = self.flags & EF_ARM_EABIMASK_COM
        result = []

        if flags & EF_ARM_RELEXEC:
            result.append("relocatable executable")
            flags = flags & (~EF_ARM_RELEXEC & 0xFFFFFFFF)
        if flags & EF_ARM_PIC:
            result.append("position independent")
            flags = flags & (~EF_ARM_PIC & 0xFFFFFFFF)
        """

        """
        result = []
        return result


MACHINE_DATA = {
    ELFMachineType.EM_AVR: AvrMachineData,
    ELFMachineType.EM_ARM: ArmMachineData,
}


EV_NONE = 0  # Invalid version.
EV_CURRENT = 1  # Current version.


##
## Offsets into file header.
##
EI_MAG0 = 0  # File identification.
EI_MAG1 = 1  # File identification.
EI_MAG2 = 2  # File identification.
EI_MAG3 = 3  # File identification.
EI_CLASS = 4  # File class.
EI_DATA = 5  # Data encoding.
EI_VERSION = 6  # File version.
EI_PAD = 7  # Start of padding bytes.
EI_OSABI = 7  # Operating system/ABI identification.
EI_ABIVERSION = 8  # ABI version.
# EI_NIDENT       = 16     # Size of e_ident[] - defined above.


class ELFClass(enum.IntEnum):
    """ELF file class (32-bit vs 64-bit architecture).
    
    Identifies whether the ELF file is for 32-bit or 64-bit architecture.
    This affects the size of addresses, offsets, and various data structures.
    
    Attributes:
        ELFCLASSNONE: Invalid/unknown class
        ELFCLASS32: 32-bit architecture (4-byte addresses)
        ELFCLASS64: 64-bit architecture (8-byte addresses)
    """
    ELFCLASSNONE = 0  # Invalid class.
    ELFCLASS32 = 1  # 32-bit objects.
    ELFCLASS64 = 2  # 64-bit objects.


ELF_CLASS_NAMES = {
    ELFClass.ELFCLASSNONE: "Invalid class",
    ELFClass.ELFCLASS32: "32-bit objects",
    ELFClass.ELFCLASS64: "64-bit objects",
}


class ELFDataEncoding(enum.IntEnum):
    """ELF data encoding (byte order/endianness).
    
    Specifies the byte ordering used for multi-byte data in the ELF file.
    This applies to all numeric fields in headers and data structures.
    
    Attributes:
        ELFDATANONE: Invalid/unknown data encoding
        ELFDATA2LSB: Little-endian (least significant byte first)
        ELFDATA2MSB: Big-endian (most significant byte first)
    """
    ELFDATANONE = 0  # Invalid data encoding.
    ELFDATA2LSB = 1  # Little-Endian.
    ELFDATA2MSB = 2  # Big-Endian.


ELF_BYTE_ORDER_NAMES = {
    ELFDataEncoding.ELFDATANONE: "Invalid data encoding",
    ELFDataEncoding.ELFDATA2LSB: "Little-Endian",
    ELFDataEncoding.ELFDATA2MSB: "Big-Endian",
}


class ELFAbiType(enum.IntEnum):
    """ELF OS/ABI type identifiers.
    
    Identifies the operating system and ABI to which the ELF file is targeted.
    This allows OS-specific interpretation of certain fields and sections.
    
    Multiple operating systems and embedded ABIs are supported. Most general-purpose
    Unix systems use ELFOSABI_NONE (System V ABI). Embedded systems may use
    ELFOSABI_STANDALONE.
    
    Attributes:
        ELFOSABI_NONE: UNIX System V ABI (generic/portable)
        ELFOSABI_HPUX: HP-UX operating system
        ELFOSABI_NETBSD: NetBSD
        ELFOSABI_GNU: GNU/Linux (also aliased as ELFOSABI_LINUX)
        ELFOSABI_LINUX: Alias for ELFOSABI_GNU
        ELFOSABI_SOLARIS: Solaris
        ELFOSABI_AIX: IBM AIX
        ELFOSABI_IRIX: SGI IRIX
        ELFOSABI_FREEBSD: FreeBSD
        ELFOSABI_TRU64: Compaq TRU64 UNIX
        ELFOSABI_MODESTO: Novell Modesto
        ELFOSABI_OPENBSD: OpenBSD
        ELFOSABI_OPENVMS: OpenVMS
        ELFOSABI_NSK: HP Non-Stop Kernel
        ELFOSABI_AROS: AROS
        ELFOSABI_FENIXOS: FenixOS
        ELFOSABI_C6000_ELFABI: TMS320C6000 bare-metal (also ARM AEABI)
        ELFOSABI_C6000_LINUX: TMS320C6000 Linux
        ELFOSABI_ARM: ARM architecture
        ELFOSABI_STANDALONE: Standalone/embedded (no OS)
    """
    ELFOSABI_NONE = 0  # UNIX System V ABI
    ELFOSABI_HPUX = 1  # HP-UX operating system
    ELFOSABI_NETBSD = 2  # NetBSD
    ELFOSABI_GNU = 3  # GNU
    ELFOSABI_LINUX = 3  # Alias for ELFOSABI_GNU
    ELFOSABI_SOLARIS = 6  # Solaris
    ELFOSABI_AIX = 7  # AIX
    ELFOSABI_IRIX = 8  # IRIX
    ELFOSABI_FREEBSD = 9  # FreeBSD
    ELFOSABI_TRU64 = 10  # TRU64 UNIX
    ELFOSABI_MODESTO = 11  # Novell Modesto
    ELFOSABI_OPENBSD = 12  # OpenBSD
    ELFOSABI_OPENVMS = 13  # OpenVMS
    ELFOSABI_NSK = 14  # Hewlett-Packard Non-Stop Kernel
    ELFOSABI_AROS = 15  # AROS
    ELFOSABI_FENIXOS = 16  # FenixOS
    ELFOSABI_C6000_ELFABI = 64  # Bare-metal TMS320C6000; alt:  ELFOSABI_ARM_AEABI
    ELFOSABI_C6000_LINUX = 65  # Linux TMS320C6000
    ELFOSABI_ARM = 97  # ARM
    ELFOSABI_STANDALONE = 255  # Standalone (embedded) application


##
##
##   ELF Sections.
##
##

SEC_FMT32 = "IIIIIIIIII"
ELF_SECTION_SIZE32 = struct.calcsize(SEC_FMT32)

SEC_FMT64 = "IIQQQQIIQQ"
ELF_SECTION_SIZE64 = struct.calcsize(SEC_FMT64)

Elf_Shdr = namedtuple(
    "Elf_Shdr",
    """sh_name sh_type sh_flags sh_addr sh_offset sh_size
    sh_link sh_info sh_addralign sh_entsize""",
)


class SectionName(enum.IntEnum):
    """ELF special section index values.
    
    Defines special section indices that have specific meanings beyond regular
    section references. These are used in symbol table entries and other contexts
    to indicate special section relationships.
    
    Attributes:
        SHN_UNDEF: Undefined/missing section reference
        SHN_LORESERVE: Start of reserved index range
        SHN_LOPROC: Start of processor-specific section indices
        SHN_BEFORE: Section ordered before all others (Solaris)
        SHN_AFTER: Section ordered after all others (Solaris)
        SHN_HIPROC: End of processor-specific section indices
        SHN_LOOS: Start of OS-specific section indices
        SHN_HIOS: End of OS-specific section indices
        SHN_ABS: Absolute symbols (not affected by relocation)
        SHN_COMMON: Common block symbols (unallocated C externals)
        SHN_XINDEX: Extended section index (actual index in separate table)
        SHN_HIRESERVE: End of reserved index range
    """
    SHN_UNDEF = 0
    # SHN_UNDEF This value marks an undefined, missing, irrelevant, or otherwise
    # meaningless section reference. For example, a symbol "defined'' relative to
    # section number SHN_UNDEF is an undefined symbol.

    SHN_LORESERVE = 0xFF00
    # This value specifies the lower bound of the range of reserved indexes
    SHN_LOPROC = 0xFF00
    SHN_BEFORE = 0xFF00
    # Order section before all others (Solaris).
    SHN_AFTER = 0xFF01
    # Order section after all others (Solaris).
    SHN_HIPROC = 0xFF1F
    # SHN_LOPROC through SHN_HIPROC: Values in this inclusive range are reserved for
    # processor-specific semantics.
    SHN_LOOS = 0xFF20
    # Start of OS-specific
    SHN_HIOS = 0xFF3F
    # End of OS-specific
    SHN_ABS = 0xFFF1
    # SHN_ABS This value specifies absolute values for the corresponding reference. For
    # example, symbols defined relative to section number SHN_ABS have
    # absolute values and are not affected by relocation.
    SHN_COMMON = 0xFFF2
    # SHN_COMMON Symbols defined relative to this section are common symbols, such as
    # FORTRAN COMMON or unallocated C external variables.
    SHN_XINDEX = 0xFFFF
    # Index is in extra table.
    SHN_HIRESERVE = 0xFFFF
    # SHN_HIRESERVE This value specifies the upper bound of the range of reserved indexes.
    # The system reserves indexes between SHN_LORESERVE and SHN_HIRESERVE, inclusive;
    # the values do not reference the section header table.That is, the section header
    # table does not contain entries for the  reserved indexes.

    SHN_IA_64_ANSI_COMMON = 0xFF00
    # This section only used by HP-UX, The HP linker gives weak symbols
    # precedence over regular common symbols.  We want common to override
    # weak.  Using this common instead of SHN_COMMON does that.


SpecialSections = {v: k for k, v in SectionName.__members__.items()}


def special_section_name(ndx: int) -> str:
    """Convert section index to special section name if applicable.
    
    Args:
        ndx: Section index value
        
    Returns:
        Section name string if index is a special section, otherwise string
        representation of the numeric index.
    """
    if ndx in SpecialSections:
        return SectionName(ndx).name
    else:
        return str(ndx)


class SectionType(enum.IntEnum):
    """ELF section type identifiers.
    
    Defines the type/purpose of each section in the ELF file. Section types
    determine how the linker and loader interpret the section contents.
    
    Common types include program data (PROGBITS), symbol tables (SYMTAB, DYNSYM),
    string tables (STRTAB), relocation entries (REL, RELA), and uninitialized
    data (NOBITS for .bss sections).
    
    GNU-specific extensions (SHT_GNU_*) provide additional functionality like
    GNU-style hash tables and version information.
    
    Processor-specific types are defined in the range SHT_LOPROC to SHT_HIPROC.
    """

    SHT_NULL = 0  # Section header table entry unused.
    SHT_PROGBITS = 1  # Program data.
    SHT_SYMTAB = 2  # Symbol table.
    SHT_STRTAB = 3  # String table.
    SHT_RELA = 4  # Relocation entries with addends.
    SHT_HASH = 5  # Symbol hash table.
    SHT_DYNAMIC = 6  # Dynamic linking information.
    SHT_NOTE = 7  # Notes.
    SHT_NOBITS = 8  # Program space with no data (bss).
    SHT_REL = 9  # Relocation entries, no addends.
    SHT_SHLIB = 10  # Reserved.
    SHT_DYNSYM = 11  # Dynamic linker symbol table.
    SHT_INIT_ARRAY = 14  # Array of constructors.
    SHT_FINI_ARRAY = 15  # Array of destructors.
    SHT_PREINIT_ARRAY = 16  # Array of pre-constructors.
    SHT_GROUP = 17  # Section group.
    SHT_SYMTAB_SHNDX = 18  # Extended section indeces.
    SHT_NUM = 19  # Number of defined types.
    SHT_LOOS = 0x60000000  # Start OS-specific.
    SHT_GNU_INCREMENTAL_INPUTS = 0x6FFF4700  # incremental build data
    SHT_GNU_ATTRIBUTES = 0x6FFFFFF5  # Object attributes.
    SHT_GNU_HASH = 0x6FFFFFF6  # GNU-style hash table.
    SHT_GNU_LIBLIST = 0x6FFFFFF7  # Prelink library list
    SHT_CHECKSUM = 0x6FFFFFF8  # Checksum for DSO content.
    SHT_LOSUNW = 0x6FFFFFFA  # Sun-specific low bound.
    SHT_SUNW_move = 0x6FFFFFFA
    SHT_SUNW_COMDAT = 0x6FFFFFFB
    SHT_SUNW_syminfo = 0x6FFFFFFC
    SHT_GNU_verdef = 0x6FFFFFFD  # Version definition section.
    SHT_GNU_verneed = 0x6FFFFFFE  # Version needs section.
    SHT_GNU_versym = 0x6FFFFFFF  # Version symbol table.
    SHT_HISUNW = 0x6FFFFFFF  # Sun-specific high bound.
    SHT_HIOS = 0x6FFFFFFF  # End OS-specific type.
    SHT_LOPROC = 0x70000000  # Start of processor-specific.

    SHT_ARM_EXIDX = 0x70000001  # Section holds ARM unwind info.
    SHT_ARM_PREEMPTMAP = 0x70000002  # Section pre-emption details.
    SHT_ARM_ATTRIBUTES = 0x70000003  # Section holds attributes.
    SHT_ARM_DEBUGOVERLAY = 0x70000004  # Section holds overlay debug info.
    SHT_ARM_OVERLAYSECTION = 0x70000005  # Section holds GDB and overlay integration info.

    SHT_HIPROC = 0x7FFFFFFF  # End of processor-specific.
    SHT_LOUSER = 0x80000000  # Start of application-specific.
    SHT_HIUSER = 0xFFFFFFFF  # End of application-specific.


class SectionFlags(enum.IntEnum):
    """ELF section attribute flags.
    
    Defines section attributes that control how sections are processed by the
    linker and loader. Flags can be combined using bitwise OR.
    
    Key flags include:
        - Memory attributes: WRITE, ALLOC, EXECINSTR
        - Optimization hints: MERGE, STRINGS
        - Grouping: GROUP, LINK_ORDER
        - Thread-local storage: TLS
        - Compression: COMPRESSED
    
    Attributes:
        SHF_WRITE: Section is writable at runtime
        SHF_ALLOC: Section occupies memory during execution
        SHF_EXECINSTR: Section contains executable instructions
        SHF_MERGE: Section data may be merged to eliminate duplicates
        SHF_STRINGS: Section contains null-terminated strings
        SHF_INFO_LINK: sh_info field contains section header table index
        SHF_LINK_ORDER: Special ordering requirements apply
        SHF_OS_NONCONFORMING: Non-standard OS-specific processing required
        SHF_GROUP: Section is member of a section group
        SHF_TLS: Section holds thread-local storage
        SHF_COMPRESSED: Section data is compressed
        SHF_MASKOS: Mask for OS-specific flags
        SHF_MASKPROC: Mask for processor-specific flags
        SHF_ORDERED: Special ordering requirement (Solaris)
        SHF_EXCLUDE: Section excluded unless referenced (Solaris)
    """
    SHF_WRITE = 0x1  # Writeable.
    SHF_ALLOC = 0x2  # Occupies memory during execution
    SHF_EXECINSTR = 0x4  # Executable.

    SHF_MERGE = 16  # Might be merged
    SHF_STRINGS = 32  # Contains nul-terminated strings
    SHF_INFO_LINK = 64  # `sh_info' contains SHT index
    SHF_LINK_ORDER = 128  # Preserve order after combining
    SHF_OS_NONCONFORMING = 256  # Non-standard OS specific handling required
    SHF_GROUP = 512  # Section is member of a group.
    SHF_TLS = 1024  # Section hold thread-local data.
    SHF_COMPRESSED = 2048  # Section with compressed data.

    SHF_MASKOS = 0x0FF00000  # OS-specific.
    SHF_MASKPROC = 0xF0000000  # Processor-specific.

    SHF_ORDERED = 1073741824  # Special ordering requirement (Solaris).
    SHF_EXCLUDE = 2147483648  # Section is excluded unless referenced or allocated (Solaris).


##
##
##   ELF Symbol Table.
##
##

SYMTAB_FMT32 = "IIIBBH"
SYMTAB_FMT64 = "IBBHQQ"

Elf32_Sym = namedtuple("Elf_Sym", "st_name st_value st_size st_info st_other st_shndx")
Elf64_Sym = namedtuple("Elf_Sym", "st_name st_info st_other st_shndx st_value st_size")

ELF32_SYM_TABLE_SIZE = struct.calcsize(SYMTAB_FMT32)
ELF64_SYM_TABLE_SIZE = struct.calcsize(SYMTAB_FMT64)

STN_UNDEF = 0


class SymbolBinding(enum.IntEnum):
    """ELF symbol binding types.
    
    Defines the linkage and visibility scope of symbols in the symbol table.
    The binding determines how symbols are resolved during linking.
    
    Attributes:
        STB_LOCAL: Local symbols (not visible outside object file, like C static)
        STB_GLOBAL: Global symbols (visible to all object files)
        STB_WEAK: Weak symbols (can be overridden by global symbols)
        STB_GNU_UNIQUE: GNU extension - symbol is unique in namespace
        STB_LOPROC: Start of processor-specific binding types
        STB_HIPROC: End of processor-specific binding types
    """
    STB_LOCAL = 0  # i.e. `static`
    STB_GLOBAL = 1
    STB_WEAK = 2
    STB_GNU_UNIQUE = 10  # Symbol is unique in namespace.

    STB_LOPROC = 13
    STB_HIPROC = 15


class SymbolType(enum.IntEnum):
    """ELF symbol type identifiers.
    
    Defines the type/category of symbols in the symbol table. The type indicates
    what kind of entity the symbol represents.
    
    Attributes:
        STT_NOTYPE: Symbol type not specified
        STT_OBJECT: Symbol is a data object (variable, array, etc.)
        STT_FUNC: Symbol is a function or executable code
        STT_SECTION: Symbol associated with a section
        STT_FILE: Symbol gives source file name
        STT_COMMON: Symbol labels an uninitialized common block
        STT_TLS: Symbol specifies thread-local storage entity
        STT_RELC: Complex relocation expression
        STT_SRELC: Signed complex relocation expression
        STT_GNU_IFUNC: GNU indirect function (resolved at runtime)
        STT_LOPROC: Start of processor-specific types
        STT_HIPROC: End of processor-specific types
    """
    STT_NOTYPE = 0
    STT_OBJECT = 1
    STT_FUNC = 2
    STT_SECTION = 3
    STT_FILE = 4
    STT_COMMON = 5
    STT_TLS = 6
    STT_RELC = 8  # Complex relocation expression.
    STT_SRELC = 9  # Signed Complex relocation expression.
    STT_GNU_IFUNC = 10  # Symbol is an indirect code object.
    STT_LOPROC = 13
    STT_HIPROC = 15


class SymbolVisibility(enum.IntEnum):
    """ELF symbol visibility specification.
    
    Defines symbol visibility encoded in the st_other field. Controls whether
    symbols are visible across module boundaries and preemption rules.
    
    Attributes:
        STV_DEFAULT: Default visibility (globally visible, can be preempted)
        STV_INTERNAL: Processor-specific hidden class
        STV_HIDDEN: Symbol not visible in other modules
        STV_PROTECTED: Visible but not preemptible (references bind locally)
    """

    STV_DEFAULT = 0  # Default symbol visibility rules
    STV_INTERNAL = 1  # Processor specific hidden class
    STV_HIDDEN = 2  # Sym unavailable in other modules
    STV_PROTECTED = 3  # Not preemptible, not exported


##
##
##   ELF Program Header
##
class ProgramHeader(enum.IntEnum):
    """ELF program header (segment) type identifiers.
    
    Defines the types of segments in program headers, which describe how to
    load and execute the program. Segments may overlap with sections and
    define memory layout at runtime.
    
    Attributes:
        PT_NULL: Unused program header entry
        PT_LOAD: Loadable segment (mapped into memory)
        PT_DYNAMIC: Dynamic linking information
        PT_INTERP: Path to program interpreter (dynamic linker)
        PT_NOTE: Auxiliary/note information
        PT_SHLIB: Reserved (unspecified semantics)
        PT_PHDR: Location and size of program header table
        PT_TLS: Thread-local storage segment
        PT_NUM: Number of defined standard types
        PT_LOOS: Start of OS-specific segment types
        PT_GNU_EH_FRAME: GCC exception handling frame header
        PT_GNU_STACK: Stack executability flags
        PT_GNU_RELRO: Segment becomes read-only after relocation
        PT_GNU_PROPERTY: GNU property segment
        PT_LOSUNW: Sun-specific low bound
        PT_SUNWBSS: Sun-specific BSS segment
        PT_SUNWSTACK: Sun-specific stack segment
        PT_HISUNW: Sun-specific high bound
        PT_HIOS: End of OS-specific segment types
        PT_LOPROC: Start of processor-specific segment types
        PT_HIPROC: End of processor-specific segment types
    """
    PT_NULL = 0  # Program header table entry unused.
    PT_LOAD = 1  # Loadable program segment.
    PT_DYNAMIC = 2  # Dynamic linking information.
    PT_INTERP = 3  # Program interpreter.
    PT_NOTE = 4  # Auxiliary information.
    PT_SHLIB = 5  # Reserved.
    PT_PHDR = 6  # Entry for header table itself.
    PT_TLS = 7  # Thread-local storage segment
    PT_NUM = 8  # Number of defined types
    PT_LOOS = 0x60000000  # Start of OS-specific
    PT_GNU_EH_FRAME = 0x6474E550  # GCC .eh_frame_hdr segment
    PT_GNU_STACK = 0x6474E551  # Indicates stack executability
    PT_GNU_RELRO = 0x6474E552  # Read-only after relocation
    PT_GNU_PROPERTY = 0x6474E553  # GNU property

    PT_LOSUNW = 0x6FFFFFFA
    PT_SUNWBSS = 0x6FFFFFFA  # Sun Specific segment
    PT_SUNWSTACK = 0x6FFFFFFB  # Stack segment
    PT_HISUNW = 0x6FFFFFFF
    PT_HIOS = 0x6FFFFFFF  # End of OS-specific
    PT_LOPROC = 0x70000000  # Start of processor-specific.
    PT_ARM_EXIDX = PT_LOPROC + 1  # Frame unwind information
    PT_HIPROC = 0x7FFFFFFF  # End of processor-specific


def program_header_name(tp: int) -> str:
    """Get the name of a program header type.
    
    Args:
        tp: Program header type value
        
    Returns:
        Program header type name without the "PT_" prefix.
    """
    return ProgramHeader(tp).name[3:]


PF_X = 0x1  # Execute.
PF_W = 0x2  # Write.
PF_R = 0x4  # Read.
PF_MASKPROC = 0xF0000000  # Unspecified.

PN_XNUM = 0xFFFF  # Extended numbering.


def program_header_flags_name(flg: int) -> str:
    """Format program header flags as readable string.
    
    Converts numeric program header flags to a human-readable format showing
    read, write, and execute permissions.
    
    Args:
        flg: Program header flags value
        
    Returns:
        String in "RWX" format where each letter indicates the presence of
        Read, Write, or eXecute permission. Absent permissions shown as "-".
        Example: "R-X" means readable and executable but not writable.
    """
    result = []

    if flg & PF_R == PF_R:
        result.append("R")
    else:
        result.append("-")
    if flg & PF_W == PF_W:
        result.append("W")
    else:
        result.append("-")
    if flg & PF_X == PF_X:
        result.append("X")
    else:
        result.append("-")
    return "".join(result)


class NoteSegmentDescriptorCore(enum.IntEnum):
    """ELF note segment descriptor types for core files.
    
    Defines the types of note segments that can appear in core dump files.
    These notes contain various process state information captured during
    core dump creation.
    
    Core file notes include register states, process info, task structures,
    and platform-specific data. Values are standardized across Unix systems
    for core file portability.
    
    Attributes:
        NT_PRSTATUS: Process status (prstatus struct)
        NT_FPREGSET: Floating point registers (fpregset struct)
        NT_PRPSINFO: Process info (prpsinfo struct)
        NT_PRXREG: Processor extended registers
        NT_TASKSTRUCT: Task structure
        NT_PLATFORM: Platform string from sysinfo
        NT_AUXV: Auxiliary vector
        NT_GWINDOWS: SPARC register windows
        NT_ASRS: Ancillary state registers
        NT_PSTATUS: Process status (pstatus struct)
        NT_PSINFO: Process info (psinfo struct)
        NT_PRCRED: Process credentials
        NT_UTSNAME: System name info (utsname struct)
        NT_LWPSTATUS: Lightweight process status
        NT_LWPSINFO: Lightweight process info
        NT_PRFPXREG: Floating point extended registers
        NT_PRXFPREG: User FP extended registers
        NT_PPC_VMX: PowerPC Altivec/VMX registers
    """

    NT_PRSTATUS = 1  # prstatus struct.
    NT_FPREGSET = 2  # fpregset struct.
    NT_PRPSINFO = 3  # prpsinfo struct.
    NT_PRXREG = 4  # prxregset struct.
    NT_TASKSTRUCT = 4  # task structure.
    NT_PLATFORM = 5  # String from sysinfo(SI_PLATFORM).
    NT_AUXV = 6  # auxv array.
    NT_GWINDOWS = 7  # gwindows struct.
    NT_ASRS = 8  # asrset struct.
    NT_PSTATUS = 10  # pstatus struct.
    NT_PSINFO = 13  # psinfo struct.
    NT_PRCRED = 14  # prcred struct.
    NT_UTSNAME = 15  # utsname struct.
    NT_LWPSTATUS = 16  # lwpstatus struct.
    NT_LWPSINFO = 17  # lwpinfo struct.
    NT_PRFPXREG = 20  # fprxregset struct.
    NT_PRXFPREG = 0x46E62B7F  # user_fxsr_struct.
    NT_PPC_VMX = 0x100  # PowerPC Altivec/VMX registers.
    NT_PPC_SPE = 0x101  # PowerPC SPE/EVR registers.
    NT_PPC_VSX = 0x102  # PowerPC VSX registers.
    NT_386_TLS = 0x200  # i386 TLS slots (struct user_desc).
    NT_386_IOPERM = 0x201  # x86 io permission bitmap (1=deny).
    NT_X86_XSTATE = 0x202  # x86 extended state using xsave.


class NoteSegmentDescriptorObject(enum.IntEnum):
    """ELF note segment descriptor types for object files.
    
    Defines note segment types that appear in regular object files (not core dumps).
    These notes contain metadata about the object file such as version information.
    
    Attributes:
        NT_VERSION: Contains version string information
    """

    NT_VERSION = 1  # Contains a version string.


BYTEORDER_PREFIX = {
    ELFDataEncoding.ELFDATA2LSB: "<",  # Little-Endian.
    ELFDataEncoding.ELFDATA2MSB: ">",  # Big-Endian.
}
