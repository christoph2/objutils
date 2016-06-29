#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

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

import os
import enum

import objutils.elf as Elf
import objutils.elf.defs as defs
from objutils.elf import Reader
from optparse import OptionParser

import objutils.armabi as arm

def stVisibility(v):
    return v & 0x3

##
##
##

##
##def tbssSpecial(sectionHeader, segment):
##   return ((sectionHeader.sh_flags & defs.SHF_TLS) != 0 and sectionHeader.sh_type == defs.SHT_NOBITS and segment.p_type != defs.PT_TLS)
##
##def sectionSize(sectionHeader, segment):
##    return 0 if tbssSpecial(sectionHeader, segment) else sectionHeader.sh_size
##
##def sectionInSegment1(sectionHeader, segment, check_vma, strict):
##    hasOffset = False
##    validSegment = False
##    hasVMA = False
##    hasDynamicSize = False
##
##    validSegment =((sectionHeader.sh_flags & defs.SHF_TLS) != 0) and (segment.p_type == defs.PT_TLS or segment.p_type == defs.PT_GNU_RELRO \
##        or segment.p_type == defs.PT_LOAD) or \
##        ((sectionHeader.sh_flags & defs.SHF_TLS) == 0 and segment.p_type != defs.PT_TLS and segment.p_type != defs.PT_PHDR)
##    hasOffset = sectionHeader.sh_type == defs.SHT_NOBITS \
##        or (sectionHeader.sh_offset >= segment.p_offset \
##        and (not strict or (sectionHeader.sh_offset - segment.p_offset <= segment.p_filesz - 1)) \
##        and ((sectionHeader.sh_offset - segment.p_offset + sectionSize(sectionHeader, segment)) <= (segment.p_filesz)))
##    hasVMA = (not check_vma or (sectionHeader.sh_flags & defs.SHF_ALLOC) == 0 or (sectionHeader.sh_addr >= segment.p_vaddr \
##        and (not strict or (sectionHeader.sh_addr - segment.p_vaddr <= segment.p_memsz - 1)) \
##        and ((sectionHeader.sh_addr - segment.p_vaddr + sectionSize(sectionHeader, segment)) <= segment.p_memsz))
##    )
##    hasDynamicSize = (segment.p_type != defs.PT_DYNAMIC or sectionHeader.sh_size != 0 or segment.p_memsz == 0 \
##        or ((sectionHeader.sh_type == defs.SHT_NOBITS or (sectionHeader.sh_offset > segment.p_offset \
##        and (sectionHeader.sh_offset - segment.p_offset < segment.p_filesz))) \
##        and ((sectionHeader.sh_flags & defs.SHF_ALLOC) == 0 \
##        or (sectionHeader.sh_addr > segment.p_vaddr \
##        and (sectionHeader.sh_addr - segment.p_vaddr < segment.p_memsz)))) \
##    )
##
##    result = validSegment and hasOffset and hasVMA and hasDynamicSize
##    return result
##
##
##def sectionInSegment(sectionHeader, segment):
##    return sectionInSegment1(sectionHeader, segment, 1, 0)
##
##def sectioInSegmentStrict(sectionHeader, segment):
##    return sectionInSegment1(sectionHeader, segment, 1, 1)
##

##
##
##


"""
static char *
get_machine_flags (unsigned e_flags, unsigned e_machine)
{
  static char buf[1024];

  buf[0] = '\0';
        case EM_BLACKFIN:
          if (e_flags & EF_BFIN_PIC)
            strcat (buf, ", PIC");

          if (e_flags & EF_BFIN_FDPIC)
            strcat (buf, ", FDPIC");

          if (e_flags & EF_BFIN_CODE_IN_L1)
            strcat (buf, ", code in L1");

          if (e_flags & EF_BFIN_DATA_IN_L1)
            strcat (buf, ", data in L1");

          break;

        case EM_CYGNUS_FRV:
          switch (e_flags & EF_FRV_CPU_MASK)
            {
            case EF_FRV_CPU_GENERIC:
              break;

            default:
              strcat (buf, ", fr???");
              break;

            case EF_FRV_CPU_FR300:
              strcat (buf, ", fr300");
              break;

            case EF_FRV_CPU_FR400:
              strcat (buf, ", fr400");
              break;
            case EF_FRV_CPU_FR405:
              strcat (buf, ", fr405");
              break;

            case EF_FRV_CPU_FR450:
              strcat (buf, ", fr450");
              break;

            case EF_FRV_CPU_FR500:
              strcat (buf, ", fr500");
              break;
            case EF_FRV_CPU_FR550:
              strcat (buf, ", fr550");
              break;

            case EF_FRV_CPU_SIMPLE:
              strcat (buf, ", simple");
              break;
            case EF_FRV_CPU_TOMCAT:
              strcat (buf, ", tomcat");
              break;
            }
          break;

        case EM_68K:
          if ((e_flags & EF_M68K_ARCH_MASK) == EF_M68K_M68000)
            strcat (buf, ", m68000");
          else if ((e_flags & EF_M68K_ARCH_MASK) == EF_M68K_CPU32)
            strcat (buf, ", cpu32");
          else if ((e_flags & EF_M68K_ARCH_MASK) == EF_M68K_FIDO)
            strcat (buf, ", fido_a");
          else
            {
              char const * isa = _("unknown");
              char const * mac = _("unknown mac");
              char const * additional = NULL;

              switch (e_flags & EF_M68K_CF_ISA_MASK)
                {
                case EF_M68K_CF_ISA_A_NODIV:
                  isa = "A";
                  additional = ", nodiv";
                  break;
                case EF_M68K_CF_ISA_A:
                  isa = "A";
                  break;
                case EF_M68K_CF_ISA_A_PLUS:
                  isa = "A+";
                  break;
                case EF_M68K_CF_ISA_B_NOUSP:
                  isa = "B";
                  additional = ", nousp";
                  break;
                case EF_M68K_CF_ISA_B:
                  isa = "B";
                  break;
                case EF_M68K_CF_ISA_C:
                  isa = "C";
                  break;
                case EF_M68K_CF_ISA_C_NODIV:
                  isa = "C";
                  additional = ", nodiv";
                  break;
                }
              strcat (buf, ", cf, isa ");
              strcat (buf, isa);
              if (additional)
                strcat (buf, additional);
              if (e_flags & EF_M68K_CF_FLOAT)
                strcat (buf, ", float");
              switch (e_flags & EF_M68K_CF_MAC_MASK)
                {
                case 0:
                  mac = NULL;
                  break;
                case EF_M68K_CF_MAC:
                  mac = "mac";
                  break;
                case EF_M68K_CF_EMAC:
                  mac = "emac";
                  break;
                case EF_M68K_CF_EMAC_B:
                  mac = "emac_b";
                  break;
                }
              if (mac)
                {
                  strcat (buf, ", ");
                  strcat (buf, mac);
                }
            }
          break;

        case EM_PPC:
          if (e_flags & EF_PPC_EMB)
            strcat (buf, ", emb");

          if (e_flags & EF_PPC_RELOCATABLE)
            strcat (buf, _(", relocatable"));

          if (e_flags & EF_PPC_RELOCATABLE_LIB)
            strcat (buf, _(", relocatable-lib"));
          break;

        case EM_V800:
          if ((e_flags & EF_RH850_ABI) == EF_RH850_ABI)
            strcat (buf, ", RH850 ABI");

          if (e_flags & EF_V800_850E3)
            strcat (buf, ", V3 architecture");

          if ((e_flags & (EF_RH850_FPU_DOUBLE | EF_RH850_FPU_SINGLE)) == 0)
            strcat (buf, ", FPU not used");

          if ((e_flags & (EF_RH850_REGMODE22 | EF_RH850_REGMODE32)) == 0)
            strcat (buf, ", regmode: COMMON");

          if ((e_flags & (EF_RH850_GP_FIX | EF_RH850_GP_NOFIX)) == 0)
            strcat (buf, ", r4 not used");

          if ((e_flags & (EF_RH850_EP_FIX | EF_RH850_EP_NOFIX)) == 0)
            strcat (buf, ", r30 not used");

          if ((e_flags & (EF_RH850_TP_FIX | EF_RH850_TP_NOFIX)) == 0)
            strcat (buf, ", r5 not used");

          if ((e_flags & (EF_RH850_REG2_RESERVE | EF_RH850_REG2_NORESERVE)) == 0)
            strcat (buf, ", r2 not used");

          for (e_flags &= 0xFFFF; e_flags; e_flags &= ~ (e_flags & - e_flags))
            {
              switch (e_flags & - e_flags)
                {
                case EF_RH850_FPU_DOUBLE: strcat (buf, ", double precision FPU"); break;
                case EF_RH850_FPU_SINGLE: strcat (buf, ", single precision FPU"); break;
                case EF_RH850_SIMD: strcat (buf, ", SIMD"); break;
                case EF_RH850_CACHE: strcat (buf, ", CACHE"); break;
                case EF_RH850_MMU: strcat (buf, ", MMU"); break;
                case EF_RH850_REGMODE22: strcat (buf, ", regmode:22"); break;
                case EF_RH850_REGMODE32: strcat (buf, ", regmode:23"); break;
                case EF_RH850_DATA_ALIGN8: strcat (buf, ", 8-byte alignment"); break;
                case EF_RH850_GP_FIX: strcat (buf, ", r4 fixed"); break;
                case EF_RH850_GP_NOFIX: strcat (buf, ", r4 free"); break;
                case EF_RH850_EP_FIX: strcat (buf, ", r30 fixed"); break;
                case EF_RH850_EP_NOFIX: strcat (buf, ", r30 free"); break;
                case EF_RH850_TP_FIX: strcat (buf, ", r5 fixed"); break;
                case EF_RH850_TP_NOFIX: strcat (buf, ", r5 free"); break;
                case EF_RH850_REG2_RESERVE: strcat (buf, ", r2 fixed"); break;
                case EF_RH850_REG2_NORESERVE: strcat (buf, ", r2 free"); break;
                default: break;
                }
            }
          break;

        case EM_V850:
        case EM_CYGNUS_V850:
          switch (e_flags & EF_V850_ARCH)
            {
            case E_V850E3V5_ARCH:
              strcat (buf, ", v850e3v5");
              break;
            case E_V850E2V3_ARCH:
              strcat (buf, ", v850e2v3");
              break;
            case E_V850E2_ARCH:
              strcat (buf, ", v850e2");
              break;
            case E_V850E1_ARCH:
              strcat (buf, ", v850e1");
              break;
            case E_V850E_ARCH:
              strcat (buf, ", v850e");
              break;
            case E_V850_ARCH:
              strcat (buf, ", v850");
              break;
            default:
              strcat (buf, _(", unknown v850 architecture variant"));
              break;
            }
          break;

        case EM_M32R:
        case EM_CYGNUS_M32R:
          if ((e_flags & EF_M32R_ARCH) == E_M32R_ARCH)
            strcat (buf, ", m32r");
          break;

        case EM_MIPS:
        case EM_MIPS_RS3_LE:
          if (e_flags & EF_MIPS_NOREORDER)
            strcat (buf, ", noreorder");

          if (e_flags & EF_MIPS_PIC)
            strcat (buf, ", pic");

          if (e_flags & EF_MIPS_CPIC)
            strcat (buf, ", cpic");

          if (e_flags & EF_MIPS_UCODE)
            strcat (buf, ", ugen_reserved");

          if (e_flags & EF_MIPS_ABI2)
            strcat (buf, ", abi2");

          if (e_flags & EF_MIPS_OPTIONS_FIRST)
            strcat (buf, ", odk first");

          if (e_flags & EF_MIPS_32BITMODE)
            strcat (buf, ", 32bitmode");

          switch ((e_flags & EF_MIPS_MACH))
            {
            case E_MIPS_MACH_3900: strcat (buf, ", 3900"); break;
            case E_MIPS_MACH_4010: strcat (buf, ", 4010"); break;
            case E_MIPS_MACH_4100: strcat (buf, ", 4100"); break;
            case E_MIPS_MACH_4111: strcat (buf, ", 4111"); break;
            case E_MIPS_MACH_4120: strcat (buf, ", 4120"); break;
            case E_MIPS_MACH_4650: strcat (buf, ", 4650"); break;
            case E_MIPS_MACH_5400: strcat (buf, ", 5400"); break;
            case E_MIPS_MACH_5500: strcat (buf, ", 5500"); break;
            case E_MIPS_MACH_SB1:  strcat (buf, ", sb1");  break;
            case E_MIPS_MACH_9000: strcat (buf, ", 9000"); break;
            case E_MIPS_MACH_LS2E: strcat (buf, ", loongson-2e"); break;
            case E_MIPS_MACH_LS2F: strcat (buf, ", loongson-2f"); break;
            case E_MIPS_MACH_LS3A: strcat (buf, ", loongson-3a"); break;
            case E_MIPS_MACH_OCTEON: strcat (buf, ", octeon"); break;
            case E_MIPS_MACH_OCTEON2: strcat (buf, ", octeon2"); break;
            case E_MIPS_MACH_XLR:  strcat (buf, ", xlr"); break;
            case 0:
            /* We simply ignore the field in this case to avoid confusion:
               MIPS ELF does not specify EF_MIPS_MACH, it is a GNU
               extension.  */
              break;
            default: strcat (buf, _(", unknown CPU")); break;
            }

          switch ((e_flags & EF_MIPS_ABI))
            {
            case E_MIPS_ABI_O32: strcat (buf, ", o32"); break;
            case E_MIPS_ABI_O64: strcat (buf, ", o64"); break;
            case E_MIPS_ABI_EABI32: strcat (buf, ", eabi32"); break;
            case E_MIPS_ABI_EABI64: strcat (buf, ", eabi64"); break;
            case 0:
            /* We simply ignore the field in this case to avoid confusion:
               MIPS ELF does not specify EF_MIPS_ABI, it is a GNU extension.
               This means it is likely to be an o32 file, but not for
               sure.  */
              break;
            default: strcat (buf, _(", unknown ABI")); break;
            }

          if (e_flags & EF_MIPS_ARCH_ASE_MDMX)
            strcat (buf, ", mdmx");

          if (e_flags & EF_MIPS_ARCH_ASE_M16)
            strcat (buf, ", mips16");

          if (e_flags & EF_MIPS_ARCH_ASE_MICROMIPS)
            strcat (buf, ", micromips");

          switch ((e_flags & EF_MIPS_ARCH))
            {
            case E_MIPS_ARCH_1: strcat (buf, ", mips1"); break;
            case E_MIPS_ARCH_2: strcat (buf, ", mips2"); break;
            case E_MIPS_ARCH_3: strcat (buf, ", mips3"); break;
            case E_MIPS_ARCH_4: strcat (buf, ", mips4"); break;
            case E_MIPS_ARCH_5: strcat (buf, ", mips5"); break;
            case E_MIPS_ARCH_32: strcat (buf, ", mips32"); break;
            case E_MIPS_ARCH_32R2: strcat (buf, ", mips32r2"); break;
            case E_MIPS_ARCH_64: strcat (buf, ", mips64"); break;
            case E_MIPS_ARCH_64R2: strcat (buf, ", mips64r2"); break;
            default: strcat (buf, _(", unknown ISA")); break;
            }
          break;

        case EM_SH:
          switch ((e_flags & EF_SH_MACH_MASK))
            {
            case EF_SH1: strcat (buf, ", sh1"); break;
            case EF_SH2: strcat (buf, ", sh2"); break;
            case EF_SH3: strcat (buf, ", sh3"); break;
            case EF_SH_DSP: strcat (buf, ", sh-dsp"); break;
            case EF_SH3_DSP: strcat (buf, ", sh3-dsp"); break;
            case EF_SH4AL_DSP: strcat (buf, ", sh4al-dsp"); break;
            case EF_SH3E: strcat (buf, ", sh3e"); break;
            case EF_SH4: strcat (buf, ", sh4"); break;
            case EF_SH5: strcat (buf, ", sh5"); break;
            case EF_SH2E: strcat (buf, ", sh2e"); break;
            case EF_SH4A: strcat (buf, ", sh4a"); break;
            case EF_SH2A: strcat (buf, ", sh2a"); break;
            case EF_SH4_NOFPU: strcat (buf, ", sh4-nofpu"); break;
            case EF_SH4A_NOFPU: strcat (buf, ", sh4a-nofpu"); break;
            case EF_SH2A_NOFPU: strcat (buf, ", sh2a-nofpu"); break;
            case EF_SH3_NOMMU: strcat (buf, ", sh3-nommu"); break;
            case EF_SH4_NOMMU_NOFPU: strcat (buf, ", sh4-nommu-nofpu"); break;
            case EF_SH2A_SH4_NOFPU: strcat (buf, ", sh2a-nofpu-or-sh4-nommu-nofpu"); break;
            case EF_SH2A_SH3_NOFPU: strcat (buf, ", sh2a-nofpu-or-sh3-nommu"); break;
            case EF_SH2A_SH4: strcat (buf, ", sh2a-or-sh4"); break;
            case EF_SH2A_SH3E: strcat (buf, ", sh2a-or-sh3e"); break;
            default: strcat (buf, _(", unknown ISA")); break;
            }

          if (e_flags & EF_SH_PIC)
            strcat (buf, ", pic");

          if (e_flags & EF_SH_FDPIC)
            strcat (buf, ", fdpic");
          break;

        case EM_SPARCV9:
          if (e_flags & EF_SPARC_32PLUS)
            strcat (buf, ", v8+");

          if (e_flags & EF_SPARC_SUN_US1)
            strcat (buf, ", ultrasparcI");

          if (e_flags & EF_SPARC_SUN_US3)
            strcat (buf, ", ultrasparcIII");

          if (e_flags & EF_SPARC_HAL_R1)
            strcat (buf, ", halr1");

          if (e_flags & EF_SPARC_LEDATA)
            strcat (buf, ", ledata");

          if ((e_flags & EF_SPARCV9_MM) == EF_SPARCV9_TSO)
            strcat (buf, ", tso");

          if ((e_flags & EF_SPARCV9_MM) == EF_SPARCV9_PSO)
            strcat (buf, ", pso");

          if ((e_flags & EF_SPARCV9_MM) == EF_SPARCV9_RMO)
            strcat (buf, ", rmo");
          break;

        case EM_PARISC:
          switch (e_flags & EF_PARISC_ARCH)
            {
            case EFA_PARISC_1_0:
              strcpy (buf, ", PA-RISC 1.0");
              break;
            case EFA_PARISC_1_1:
              strcpy (buf, ", PA-RISC 1.1");
              break;
            case EFA_PARISC_2_0:
              strcpy (buf, ", PA-RISC 2.0");
              break;
            default:
              break;
            }
          if (e_flags & EF_PARISC_TRAPNIL)
            strcat (buf, ", trapnil");
          if (e_flags & EF_PARISC_EXT)
            strcat (buf, ", ext");
          if (e_flags & EF_PARISC_LSB)
            strcat (buf, ", lsb");
          if (e_flags & EF_PARISC_WIDE)
            strcat (buf, ", wide");
          if (e_flags & EF_PARISC_NO_KABP)
            strcat (buf, ", no kabp");
          if (e_flags & EF_PARISC_LAZYSWAP)
            strcat (buf, ", lazyswap");
          break;

        case EM_PJ:
        case EM_PJ_OLD:
          if ((e_flags & EF_PICOJAVA_NEWCALLS) == EF_PICOJAVA_NEWCALLS)
            strcat (buf, ", new calling convention");

          if ((e_flags & EF_PICOJAVA_GNUCALLS) == EF_PICOJAVA_GNUCALLS)
            strcat (buf, ", gnu calling convention");
          break;

        case EM_IA_64:
          if ((e_flags & EF_IA_64_ABI64))
            strcat (buf, ", 64-bit");
          else
            strcat (buf, ", 32-bit");
          if ((e_flags & EF_IA_64_REDUCEDFP))
            strcat (buf, ", reduced fp model");
          if ((e_flags & EF_IA_64_NOFUNCDESC_CONS_GP))
            strcat (buf, ", no function descriptors, constant gp");
          else if ((e_flags & EF_IA_64_CONS_GP))
            strcat (buf, ", constant gp");
          if ((e_flags & EF_IA_64_ABSOLUTE))
            strcat (buf, ", absolute");
          if (elf_header.e_ident[EI_OSABI] == ELFOSABI_OPENVMS)
            {
              if ((e_flags & EF_IA_64_VMS_LINKAGES))
                strcat (buf, ", vms_linkages");
              switch ((e_flags & EF_IA_64_VMS_COMCOD))
                {
                case EF_IA_64_VMS_COMCOD_SUCCESS:
                  break;
                case EF_IA_64_VMS_COMCOD_WARNING:
                  strcat (buf, ", warning");
                  break;
                case EF_IA_64_VMS_COMCOD_ERROR:
                  strcat (buf, ", error");
                  break;
                case EF_IA_64_VMS_COMCOD_ABORT:
                  strcat (buf, ", abort");
                  break;
                default:
                  abort ();
                }
            }
          break;

        case EM_VAX:
          if ((e_flags & EF_VAX_NONPIC))
            strcat (buf, ", non-PIC");
          if ((e_flags & EF_VAX_DFLOAT))
            strcat (buf, ", D-Float");
          if ((e_flags & EF_VAX_GFLOAT))
            strcat (buf, ", G-Float");
          break;

        case EM_RX:
          if (e_flags & E_FLAG_RX_64BIT_DOUBLES)
            strcat (buf, ", 64-bit doubles");
          if (e_flags & E_FLAG_RX_DSP)
            strcat (buf, ", dsp");
          if (e_flags & E_FLAG_RX_PID)
            strcat (buf, ", pid");
          if (e_flags & E_FLAG_RX_ABI)
            strcat (buf, ", RX ABI");
          break;

        case EM_S390:
          if (e_flags & EF_S390_HIGH_GPRS)
            strcat (buf, ", highgprs");
          break;

        case EM_TI_C6000:
          if ((e_flags & EF_C6000_REL))
            strcat (buf, ", relocatable module");
          break;
        }
    }

  return buf;
}
"""

class PrintMode(enum.IntEnum):
    FULL_HEX    = 0
    LONG_HEX    = 1
    DEC_5       = 2
    PREFIX_HEX  = 3
    HEX         = 4
    DEC         = 5
    UNSIGNED    = 6

def printVMA(vma, mode):
    nc = 0
    if mode == PrintMode.FULL_HEX:
        print("0x", end ="")

"""
print_vma (bfd_vma vma, print_mode mode)
{
  int nc = 0;

  switch (mode)
    {
    case FULL_HEX:
      nc = printf ("0x");
      /* Drop through.  */

    case LONG_HEX:
#ifdef BFD64
      if (is_32bit_elf)
        return nc + printf ("%8.8" BFD_VMA_FMT "x", vma);
#endif
      printf_vma (vma);
      return nc + 16;

    case DEC_5:
      if (vma <= 99999)
        return printf ("%5" BFD_VMA_FMT "d", vma);
      /* Drop through.  */

    case PREFIX_HEX:
      nc = printf ("0x");
      /* Drop through.  */

    case HEX:
      return nc + printf ("%" BFD_VMA_FMT "x", vma);

    case DEC:
      return printf ("%" BFD_VMA_FMT "d", vma);

    case UNSIGNED:
      return printf ("%" BFD_VMA_FMT "u", vma);
    }
  return 0;
}
"""

class ELFReader(object):

    def __init__(self):
        pass


    def printFileHeader(self, reader):
        if self.options.fileHeader:
            print("ELF Header:")
            print("  Magic:   " + ' '.join(["{0:02x}".format((ord(x))) for x in reader.header.magicBytes[:16]]) + " ")
            print("  Class:                             {0!s}".format((reader.header.elfClassAsString())))
            print("  Data:                              {0!s}".format(reader.header.elfDataEncodingAsString()))
            print("  Version:                           {0:d} {1!s}".format(reader.header.elfVersion, reader.header.getVersionAsString()))
            print("  OS/ABI:                            {0!s}".format((reader.header.getAbiNameAsString())))
            print("  ABI Version:                       {0:d}".format((reader.header.elfAbiVersion)))
            print("  Type:                              {0!s}".format(reader.header.getElfTypeAsString()))
            print("  Machine:                           {0!s}".format(reader.header.elfMachineName))
            print("  Version:                           0x%lx" % reader.header.elfVersion)
            print("  Entry point address:               0x{0:x}".format((reader.header.elfEntryPoint)))  #  (bytes into file)
            print("  Start of program headers:          {0:d} (bytes into file)".format((reader.header.elfProgramHeaderTableOffset)))
            print("  Start of section headers:          {0:d} (bytes into file)".format((reader.header.elfSectionHeaderTableOffset)))
            print("  Flags:                             0x%lx%s" % (reader.header.elfFlags, getMachineFlags(reader.header.elfFlags, reader.header.elfMachine)))
            print("  Size of this header:               %ld (bytes)" % (reader.header.elfEHSize))
            print("  Size of program headers:           %ld (bytes)" % (reader.header.elfPHTEntrySize))
            print("  Number of program headers:         %ld" % (reader.header.elfNumberOfPHs))
            if reader.sectionHeaders and reader.header.e_phnum == defs.PN_XNUM and reader.sectionHeaders[0].sh_info !=0:
                print(" (%ld)" % reader.section_headers[0].sh_info)
            print("  Size of section headers:           %ld (bytes)" % (reader.header.elfSHTEntrySize))
            print("  Number of section headers:         %ld" % (reader.header.elfNumberOfSHs))
            if reader.sectionHeaders and reader.header.e_shnum == defs.SHN_UNDEF:
                print(" (%ld)" % reader.section_headers[0].sh_size);
            print("  Section header string table index: %ld" % (reader.header.elfStringTableIndex))
            if reader.sectionHeaders and reader.header.e_shstrndx == defs.SHN_XINDEX:
                print(" ({0:d})".format(reader.header.section_headers[0].sh_link));
            elif reader.header.e_shstrndx != defs.SHN_UNDEF and reader.header.e_shstrndx > reader.header.e_shnum:
                print(" <corrupt: out of range>")

    def printProgramHeaders(self, reader):
        if self.reader.header.e_phnum == 0:
            if self.reader.header.e_phoff != 0:
                print("possibly corrupt ELF header - it has a non-zero program header offset, but no program headers")
            elif self.doSegments:
                print("\nThere are no program headers in this file.\n")
                #sys.exit(1) # TODO: Exception!
                return

        if self.doSegments and not self.doHeader:
            print("Elf file type is {0!s}".format(reader.header.getElfTypeAsString()))
            print("Entry point 0x{0:x}".format(reader.header.e_entry))
            print("There are {0:d} program headers, starting at offset {1:d}".format(reader.header.e_phnum, reader.header.e_phoff))
        elif not self.doSegments:
            return
        print
        print("Program Headers:")
        if not self.reader.header.is64Bit:
            print("  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align")
        elif self.options.wideScreen:
            print("  Type           Offset   VirtAddr           PhysAddr           FileSiz  MemSiz   Flg Align")
        else:
            print("  Type           Offset             VirtAddr           PhysAddr")
            print("                 FileSiz            MemSiz              Flags  Align")

        dynamicAddr = None
        dynamicSize = None

        for header in reader.programHeaders:
            if self.doSegments:
                flags=""
                if (header.phFlags & defs.PF_R) == defs.PF_R:
                    flags+='R'
                else:
                    flags+=' '
                if (header.phFlags & defs.PF_W) == defs.PF_W:
                    flags+='W'
                else:
                    flags+=' '
                if (header.phFlags & defs.PF_X) == defs.PF_X:
                    flags+='E'
                else:
                    flags+=' '
                if not self.reader.header.is64Bit:
                    print("  %-14.14s 0x%6.6lx 0x%8.8lx 0x%8.8lx 0x%5.5lx 0x%5.5lx %-3s %d" % (header.phTypeName,
                        header.phOffset, header.phVirtualAddress, header.phPhysicalAddress, header.phFileSize,
                        header.phMemSize,flags, header.phAlign
                    ))
                elif self.options.wideScreen:
                    print("  %-14.14s 0x%6.6lx 0x%16.16lx 0x%16.16lx 0x%6.6lx 0x%6.6lx %-3s %d" % (header.phTypeName,
                        header.phOffset, header.phVirtualAddress, header.phPhysicalAddress, header.phFileSize,
                        header.phMemSize,flags,header.phAlign
                    ))
                else:
                    print("  %-14.14s 0x%6.6lx 0x%16.16lx 0x%16.16lx" % (header.phTypeName, header.phOffset,
                        header.phVirtualAddress, header.phPhysicalAddress
                    ))
                    print("                 0x%16.16lx 0x%16.16lx %-3s %d" % (header.phFileSize, header.phMemSize,
                        flags, header.phAlign
                    ))
            if header.phType == defs.PT_DYNAMIC:
                if dynamicAddr:
                    raise TypeError("more than one dynamic segment")
                dynamicAddr = header.p_offset
                dynamicSize = header.p_filesz

                if reader.sectionHeaders:
                    dyn = reader.sectionHeaderByName('.dynamic')
                    if dyn:
                        #print "DYN-SH:", dyn
                        pass

                """
          if (section_headers != NULL)
            {
              Elf_Internal_Shdr * sec;

              sec = find_section (".dynamic");

              if (sec == NULL || sec->sh_size == 0)
                {
                  /* A corresponding .dynamic section is expected, but on
                     IA-64/OpenVMS it is OK for it to be missing.  */
                  if (!is_ia64_vms ())
                    error (_("no .dynamic section in the dynamic segment\n"));
                  break;
                }

              if (sec->sh_type == SHT_NOBITS)
                {
                  dynamic_size = 0;
                  break;
                }

              dynamic_addr = sec->sh_offset;
              dynamic_size = sec->sh_size;

              if (dynamic_addr < segment->p_offset
                  || dynamic_addr > segment->p_offset + segment->p_filesz)
                warn (_("the .dynamic section is not contained"
                        " within the dynamic segment\n"));
              else if (dynamic_addr > segment->p_offset)
                warn (_("the .dynamic section is not the first section"
                        " in the dynamic segment.\n"));
            }
                """
            elif header.phType == defs.PT_INTERP:
                if self.doSegments:
                    print("      [Requesting program interpreter: {0!s}]".format((header.image.strip())))

        if self.doSegments and reader.sectionHeaders:   # and reader.stringTable
            print("\n Section to Segment mapping:")
            print("  Segment Sections...")
            sectionsToSegments = reader.sectionsToSegments

            for idx, entry in enumerate(sectionsToSegments.values()):
                print("   {0:02d}     {1}".format(idx, " ".join([x.shName for x in entry])))

    def printSectionsHeaders(self, reader):
        if not self.reader.header.e_shnum:
            print("\nThere are no sections in this file.")
            return
        print
        if self.reader.header.e_shnum > 1:
            print("Section Headers:")
        else:
            print("Section Header:")

        if not self.reader.header.is64Bit:
            if self.doSectionDetails:
                print("  [Nr] Name")
                print("       Type            Addr     Off    Size   ES   Lk Inf Al")
            else:
                print("  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al")
        elif self.options.wideScreen:
            if self.doSectionDetails:
                print("  [Nr] Name")
                print("       Type            Address          Off    Size   ES   Lk Inf Al")
            else:
                print("  [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al")
        else:
            if self.doSectionDetails:
                print("  [Nr] Name")
                print("       Type              Address          Offset            Link")
                print("       Size              EntSize          Info              Align")
            else:
                print("  [Nr] Name              Type             Address           Offset")
                print("       Size              EntSize          Flags  Link  Info  Align")

        if self.doSectionDetails:
            print("       Flags")

        for idx, section in enumerate(reader.sectionHeaders):
            flags = ""
            flagsLong = []
            if (section.shFlags & defs.SHF_WRITE) == defs.SHF_WRITE:
                flags += 'W'
                flagsLong.append('WRITE')
            if (section.shFlags & defs.SHF_ALLOC) == defs.SHF_ALLOC:
                flags += 'A'
                flagsLong.append('ALLOC')
            if (section.shFlags & defs.SHF_EXECINSTR) == defs.SHF_EXECINSTR:
                flags += 'X'
                flagsLong.append('EXEC')
            if (section.shFlags & defs.SHF_MERGE) == defs.SHF_MERGE:
                flags += 'M'
                flagsLong.append('MERGE')
            if (section.shFlags & defs.SHF_STRINGS) == defs.SHF_STRINGS:
                flags += 'S'
                flagsLong.append('STRINGS')
            if (section.shFlags & defs.SHF_INFO_LINK) == defs.SHF_INFO_LINK:
                flags += 'I'
                flagsLong.append('INFO LINK')
            if (section.shFlags & defs.SHF_LINK_ORDER) == defs.SHF_LINK_ORDER:
                flags += 'L'
                flagsLong.append('LINK ORDER')
            if (section.shFlags & defs.SHF_GROUP) == defs.SHF_GROUP:
                flags += 'G'
                flagsLong.append('GROUP')
            if (section.shFlags & defs.SHF_TLS) == defs.SHF_TLS:
                flags += 'T'
                flagsLong.append('TLS')
            if (section.shFlags & defs.SHF_EXCLUDE) == defs.SHF_EXCLUDE:
                flags += 'E'
                flagsLong.append('EXCLUDE')
            if (section.shFlags & defs.SHF_ORDERED) == defs.SHF_ORDERED:
                flags += 'O'
                flagsLong.append('ORDERED')
            if (section.shFlags & defs.SHF_MASKOS) == defs.SHF_MASKOS:
                flags += 'o'
                flagsLong.append('MASKOS')
            if (section.shFlags & defs.SHF_MASKPROC) == defs.SHF_MASKPROC:
                flags += 'p'
                flagsLong.append('MASKPROC')
            if self.doSectionDetails:
                print("  [{0:2d}] {1}".format(idx, section.shName))
                if self.options.wideScreen:
                    print("       {0:<15}".format(section.shTypeName)),
                else:
                    print("       {0:<15.15}".format(section.shTypeName)),
            else:
                if self.options.wideScreen:
                    print("  [{0:2d}] {1:<17.17}{2:<15}".format(idx, section.shName, section.shTypeName)),
                else:
                    print("  [{0:2d}]  {1:<17.17}{2:<15.15}".format(idx, section.shName, section.shTypeName)),

            if not self.reader.header.is64Bit:
                linkToBig = ""
                print( "{0:08x} {1:06x} {2:06x} {3:02x}".format(section.shAddress, section.shOffset, section.shSize, section.shEntitySize)),
                if self.doSectionDetails:
                    print(" "),
                else:
                    print(" {0:3}".format(flags)),
                if section.shLink >= self.reader.header.e_shnum:
                    if self.reader.header.e_machine in (defs.ELFMachineType.EM_386, defs.ELFMachineType.EM_486,
                        defs.ELFMachineType.EM_X86_64, defs.ELFMachineType.EM_L1OM, defs.ELFMachineType.EM_K1OM,
                        defs.ELFMachineType.EM_OLD_SPARCV9, defs.ELFMachineType.EM_SPARC32PLUS, defs.ELFMachineType.EM_SPARCV9,
                        defs.ELFMachineType.EM_SPARC
                    ):
                        if section.shLink ==  defs.SHN_BEFORE:
                            linkToBig = "BEFORE"
                        elif section.shLink ==  defs.SHN_AFTER:
                            linkToBig = "AFTER"
                if self.doSectionDetails:
                    if linkToBig:
                        print("<{0}>".format(linkToBig)),
                    else:
                        print("{0:2d}".format(section.shLink)),
                    print("{0:3d} {1:2d}".format(section.shInfo, section.shAddressAlign))
                else:
                    print("{0:2d} {1:3d} {2:2d}".format(section.shLink, section.shInfo, section.shAddressAlign))
                #if (link_too_big && ! * link_too_big)
                #    warn (_("section %u: sh_link value of %u is larger than the number of sections\n"), i, section->sh_link);
            elif self.options.wideScreen:
                print("{0:016x} {1:06x} {2:06x} {3:02x}".format(section.shAddress, section.shOffset, section.shSize, section.shEntitySize)),
                if self.doSectionDetails:
                    print(" "),
                else:
                    print("{0:3}".format(flags))
                print("{0:2d} {1:3d} {2:2d}".format(section.shLink, section.shInfo, section.shAddressAlign))
            elif self.doSectionDetails:
                print("       {0:<15s}  {1:016x}  {2:016x}  {3:d}".format(section.shTypeName, section.shAddress, section.shOffset, section.shLink))
                print("       {0:016x} {1:016x}  {2:<16d}  {3:d}".format(section.shSize, section.shEntitySize, section.shInfo, section.shAddressAlign))
            else:
                print(" {0:016x}  {1:08x}".format(section.shAddress, section.shOffset))
                print("       {0:016x}  {1:016x}  {2:3s}".format(section.shSize, section.shEntitySize, flags)),
                print("    {0:2d}   {1:3d}     {2:d}".format(section.shLink, section.shInfo, section.shAddressAlign))
            if self.doSectionDetails:
                if self.reader.header.is64Bit:
                    print("       [{0:016x}]: {1}".format(section.shFlags, ', '.join(flagsLong)))
                else:
                    print("       [{0:08x}]: {1}".format(section.shFlags, ', '.join(flagsLong)))
        if not self.doSectionDetails:
            print("""Key to Flags:
  W (write), A (alloc), X (execute), M (merge), S (strings)
  I (info), L (link order), G (group), T (TLS), E (exclude), x (unknown)
  O (extra OS processing required) o (OS specific), p (processor specific)""")
        else:
            """      if (elf_header.e_machine == EM_X86_64
          || elf_header.e_machine == EM_L1OM
          || elf_header.e_machine == EM_K1OM)
            """
##
##            print("""Key to Flags:
##  W (write), A (alloc), X (execute), M (merge), S (strings), l (large)
##  I (info), L (link order), G (group), T (TLS), E (exclude), x (unknown)
##  O (extra OS processing required) o (OS specific), p (processor specific)""")
##

    def printSymbols(self):
        if not self.reader.header.is64Bit:
            pass
        else:
            pass

        for section in self.reader.sectionHeaders:
            if section.shType in (defs.SHT_SYMTAB,defs.SHT_DYNSYM):
                if section.sh_entsize == 0:
                    print("Symbol table {0} has a sh_entsize of zero!".format(section.shName))
                    continue

                print("\nSymbol table '{0}' contains {1} entries:".format(section.shName, section.numEntries))

                if not self.reader.header.is64Bit:
                    print("   Num:    Value  Size Type    Bind   Vis      Ndx Name")

                else:
                    print("   Num:    Value          Size Type    Bind   Vis      Ndx Name")

                for idx, (_, symbol) in enumerate(section.symbols.items()):
                    print("{0:6d}: {1:016x} {2:5d} {3:<7} {4:<6} {5:<7}".format(idx, symbol.st_value, symbol.st_size,
                        getSymbolType(symbol.st_info & 0x0f), getSymbolBinding(symbol.st_info >> 4), getSymbolVisibility(symbol.st_other))
                    ),
                    if (symbol.st_other ^ stVisibility (symbol.st_other)):
                        print(" [{0}] ".format(get_symbol_other(symbol.st_other ^ stVisibility(symbol.st_other))))

                    print(" {0:4} {1:25.25}".format(getSymbolIndexType(self.reader.header, symbol.st_shndx),
                        self.reader.getString(section.shLink, symbol.st_name))
                    )

                    #print_symbol (25, psym->st_name < strtab_size ? strtab + psym->st_name : _("<corrupt>"));

                    #print(" [0:<4]".format(getSymbolIndexType(header, symbol.st_shndx)))

                    #print "%s" % (self.reader.getString(section.shLink, symbol.st_name),)
                    #print "0x%08x 0x%08x %-7s %-6s " %(symbol.st_value,symbol.st_size,
                    #    getSymbolType(symbol.st_info & 0x0f), getSymbolBinding(symbol.st_info >> 4)),
                    #sectionName = Elf.getSpecialSectionName(symbol.st_shndx)
                    #if sectionName:
                    #    print "%-8s" % (sectionName,)
                    #else:
                    #    print "0x%08x " % (symbol.st_shndx)
                    #,symbol.st_info,symbol.st_value,symbol.st_shndx,symbol.st_other

    def run(self):
        usage = "Usage: readelf.py [options] <elf-file>"

        options=[]
        args=[]

        self.doSegments = False
        self.doHeader = False
        self.doSectionDetails = False

        op = OptionParser(usage = usage,version = "%prog " + __version__, description = "Display information about the contents of ELF format files")
        op.add_option('-H', '--file-header', help = "Display the ELF file header", dest = "fileHeader", action = "store_true", default = False)
        op.add_option('-l', '--program-headers', help = 'Display the program headers', dest = 'pogramHeaders', action = "store_true", default = False)

        op.add_option('-W', '--wide', help = 'Allow output width to exceed 80 characters', dest = 'wideScreen', action = "store_true", default = False)

        op.add_option('-t', '--section-details', help = "Display the section details", dest = "sectionDetails", action = "store_true", default = False)
        op.add_option('-s', '--symbols', help = "Display the symbol table", dest = "doSymbols", action = "store_true", default = False)
        op.add_option('-S', '--section-headers', help = "Display the sections' header", dest = "sectionHeaders",  action = "store_true", default = False)


        """
    Usage: readelf <option(s)> elf-file(s)
     Display information about the contents of ELF format files
     Options are:
      -a --all               Equivalent to: -h -l -S -s -r -d -V -A -I
      -h --file-header       Display the ELF file header
      -l --program-headers   Display the program headers
         --segments          An alias for --program-headers
      -S --section-headers   Display the sections' header
         --sections          An alias for --section-headers
      -g --section-groups    Display the section groups
      -t --section-details   Display the section details
      -e --headers           Equivalent to: -h -l -S
      -s --syms              Display the symbol table
         --symbols           An alias for --syms
      --dyn-syms             Display the dynamic symbol table
      -n --notes             Display the core notes (if present)
      -r --relocs            Display the relocations (if present)
      -u --unwind            Display the unwind info (if present)
      -d --dynamic           Display the dynamic section (if present)
      -V --version-info      Display the version sections (if present)
      -A --arch-specific     Display architecture specific information (if any)
      -c --archive-index     Display the symbol/file index in an archive
      -D --use-dynamic       Use the dynamic section info when displaying symbols
      -x --hex-dump=<number|name>
                             Dump the contents of section <number|name> as bytes
      -p --string-dump=<number|name>
                             Dump the contents of section <number|name> as strings
      -R --relocated-dump=<number|name>
                             Dump the contents of section <number|name> as relocated bytes
      -w[lLiaprmfFsoRt] or
      --debug-dump[=rawline,=decodedline,=info,=abbrev,=pubnames,=aranges,=macro,=frames,
                   =frames-interp,=str,=loc,=Ranges,=pubtypes,
                   =gdb_index,=trace_info,=trace_abbrev,=trace_aranges,
                   =addr,=cu_index]
                             Display the contents of DWARF2 debug sections
      --dwarf-depth=N        Do not display DIEs at depth N or greater
      --dwarf-start=N        Display DIEs starting with N, at the same depth
                             or deeper
      -I --histogram         Display histogram of bucket list lengths
      -W --wide              Allow output width to exceed 80 characters
      @<file>                Read options from <file>
      -H --help              Display this information
      -v --version           Display the version number of readelf

    """

        (options, args) = op.parse_args()
        filename = args[0]

        if options.fileHeader:
            self.doHeader = True
        if options.pogramHeaders:
            self.doSegments = True
        if options.sectionDetails:
            self.doSectionDetails = True

        self.options = options
        self.reader = Reader(filename)
        #self.reader = Reader(file(filename, "rb"))
        self.printFileHeader(self.reader)
        if options.sectionHeaders:
            self.printSectionsHeaders(self.reader)
        if options.pogramHeaders:
            self.printProgramHeaders(self.reader)
        if options.doSymbols:
            self.printSymbols()

        #printELFInfo(filename)
        """
        reader=Reader(file(f, "rb"))
        printHeader(reader)
        printProgramHeaders(reader)

def printELFInfo(f):
    reader = Reader(file(f, "rb"))

    printHeader(reader)
    printProgramHeaders(reader)
    printSectionsHeaders(reader)

        """

SYMBOL_BINDINGS={
    defs.STB_LOCAL   : "LOCAL",
    defs.STB_GLOBAL  : "GLOBAL",
    defs.STB_WEAK    : "WEAK",
}

def getSymbolBinding(value):
    if defs.STB_LOCAL<= value <=defs.STB_WEAK:
        return SYMBOL_BINDINGS[value]
    elif defs.STB_LOPROC<= value <=defs.STB_HIPROC:
        return "PROC"
    else:
        return "UNK"

SYMBOL_TYPES={
    defs.STT_NOTYPE  : "NOTYPE",
    defs.STT_OBJECT  : "OBJECT",
    defs.STT_FUNC    : "FUNC",
    defs.STT_SECTION : "SECTION",
    defs.STT_FILE    : "FILE"
}

def getSymbolType(value):
    if defs.STT_NOTYPE <= value <= defs.STT_FILE:
        return SYMBOL_TYPES[value]
    elif defs.STT_LOPROC <= value <= defs.STT_HIPROC:
        return "PROC"
    else:
        return "UNKNOWN"


def getSymbolVisibility(visibility):
    if visibility == defs.STV_DEFAULT:
        return "DEFAULT"
    elif visibility == defs.STV_INTERNAL:
        return "INTERNAL"
    elif visibility == defs.STV_HIDDEN:
        return "HIDDEN"
    elif visibility == defs.STV_PROTECTED:
        return "PROTECTED"
    else:
        pass    # TODO: raise TypeError()!


def getSymbolIndexType(header, _type):

    buf = ""

    if _type == defs.SHN_UNDEF:
        buf = "UND"
    elif _type == defs.SHN_ABS:
        buf = "ABS"
    elif _type == defs.SHN_COMMON:
        buf = "COM"
    else:
        if _type == defs.SHN_IA_64_ANSI_COMMON:
            pass
        else:
            buf = "{0:3d}".format(_type)
        """
          if (type == SHN_IA_64_ANSI_COMMON
              && elf_header.e_machine == EM_IA_64   # elfMachine    /   ELFMachineType
              && elf_header.e_ident[EI_OSABI] == ELFOSABI_HPUX) # elfOsAbi
            return "ANSI_COM";
          else if ((elf_header.e_machine == EM_X86_64
                    || elf_header.e_machine == EM_L1OM
                    || elf_header.e_machine == EM_K1OM)
                   && type == SHN_X86_64_LCOMMON)
            return "LARGE_COM";
          else if ((type == SHN_MIPS_SCOMMON
                    && elf_header.e_machine == EM_MIPS)
                   || (type == SHN_TIC6X_SCOMMON
                       && elf_header.e_machine == EM_TI_C6000))
            return "SCOM";
          else if (type == SHN_MIPS_SUNDEFINED
                   && elf_header.e_machine == EM_MIPS)
            return "SUND";
          else if (type >= SHN_LOPROC && type <= SHN_HIPROC)
            sprintf (buff, "PRC[0x%04x]", type & 0xffff);
          else if (type >= SHN_LOOS && type <= SHN_HIOS)
            sprintf (buff, "OS [0x%04x]", type & 0xffff);
          else if (type >= SHN_LORESERVE)
            sprintf (buff, "RSV[0x%04x]", type & 0xffff);
          else if (type >= elf_header.e_shnum)
            sprintf (buff, "bad section index[%3d]", type);
          else
            sprintf (buff, "%3d", type);
          break;
        """
    return buf


def printInfoData(reader):
    for header in [x for x in reader.sectionHeaders if x.shType == defs.SHT_NOTE]:
        img=header.image


def printRelocationData(reader):
    for header in [x for x in reader.sectionHeaders if x.shType in (defs.SHT_REL, defs.SHT_RELA)]:
        if header.shType == defs.SHT_REL:
            entrySize = defs.ELF_RELOCATION_SIZE
        else:
            entrySize = defs.ELF_RELOCATION_A_SIZE

        img = header.image
        numEntries = len(header.image) / entrySize



def main():
    reader = ELFReader()
    reader.run()

if __name__=='__main__':
    main()

