/*
 * Copyright (c) 2009-2010 Christoph Schueler <chris@konnex-tools.de,
                                               cpu12.gems@googlemail.com>.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products
 *    derived from this software without specific prior written permission
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
 * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
#if !defined(__ELF_H)
#define __ELF_H

#include "StdTypes.h"

/*
**
**
**  Reference:
**  ----------
**  Tool Interface Standard (TIS)
**  Executable and Linking Format (ELF) Specification Version 1.2
**  
*/

/*                  Name                Size    Align   Purpose                     */
/* ================================================================================ */
typedef uint32_t    Elf32_Addr;     /*  4       4       Unsigned program address    */
typedef uint16_t    Elf32_Half;     /*  2       2       Unsigned medium integer     */
typedef uint32_t    Elf32_Off;      /*  4       4       Unsigned file offset        */
typedef int32_t     Elf32_Sword;    /*  4       4       Signed large integer        */
typedef uint32_t    Elf32_Word;     /*  4       4       Unsigned large integer      */
/*                  unsigned char       1       1       Unsigned small integer      */


/*
** 
**  ELF Header.
**
*/
#define EI_NIDENT       ((uint8_t)16)       /* Size of e_ident[].       */

#pragma pack(1)
typedef struct tagElf32_Ehdr {
    uint8_t     e_ident[EI_NIDENT];
    Elf32_Half  e_type;
    Elf32_Half  e_machine;
    Elf32_Word  e_version;
    Elf32_Addr  e_entry;
    Elf32_Off   e_phoff;
    Elf32_Off   e_shoff;
    Elf32_Word  e_flags;
    Elf32_Half  e_ehsize;
    Elf32_Half  e_phentsize;
    Elf32_Half  e_phnum;
    Elf32_Half  e_shentsize;
    Elf32_Half  e_shnum;
    Elf32_Half  e_shstrndx;
} Elf32_Ehdr;
#pragma pack()

#define ELF_HEADER_SIZE (sizeof(Elf32_Ehdr))

STATIC_ASSERT((ELF_HEADER_SIZE==52),"size of 'Elf32_Ehdr' must be 52 bytes.");


#define ELF_IDENT(hptr,ofs)         ((hptr)->e_ident[(ofs)])
    #define ELF_MAG0(hptr)          (ELF_IDENT((hptr),EI_MAG0))
    #define ELF_MAG1(hptr)          (ELF_IDENT((hptr),EI_MAG1))
    #define ELF_MAG2(hptr)          (ELF_IDENT((hptr),EI_MAG2))
    #define ELF_MAG3(hptr)          (ELF_IDENT((hptr),EI_MAG3))
    #define ELF_CLASS(hptr)         (ELF_IDENT((hptr),EI_CLASS))
    #define ELF_DATA(hptr)          (ELF_IDENT((hptr),EI_DATA))
    #define ELF_VERSION(hptr)       (ELF_IDENT((hptr),EI_VERSION))
    #define ELF_PAD(hptr)           (ELF_IDENT((hptr),EI_PAD))
    #define ELF_OSABI(hptr)         (ELF_IDENT((hptr),EI_OSABI))
    #define ELF_ABIVERSION(hptr)    (ELF_IDENT((hptr),EI_ABIVERSION))
    #define ELF_NIDENT(hptr)        (ELF_IDENT((hptr),EI_NIDENT))

#define ELF_TYPE(hptr)              ((hptr)->e_type)
#define ELF_MACHINE(hptr)           ((hptr)->e_machine)
#define ELF_VER(hptr)               ((hptr)->e_version)
#define ELF_ENTRY(hptr)             ((hptr)->e_entry)
#define ELF_PHOFF(hptr)             ((hptr)->e_phoff)
#define ELF_SHOFF(hptr)             ((hptr)->e_shoff)
#define ELF_FLAGS(hptr)             ((hptr)->e_flags)
#define ELF_EHSIZE(hptr)            ((hptr)->e_ehsize)
#define ELF_PHENTSIZE(hptr)         ((hptr)->e_phentsize)
#define ELF_PHNUM(hptr)             ((hptr)->e_phnum)
#define ELF_SHENTSIZE(hptr)         ((hptr)->e_shentsize)
#define ELF_SHNUM(hptr)             ((hptr)->e_shnum)
#define ELF_SHSTRNDX(hptr)          ((hptr)->e_shstrndx)


#define ET_NONE         ((Elf32_Half)0)     /* No file type.            */
#define ET_REL          ((Elf32_Half)1)     /* Relocatable file.        */
#define ET_EXEC         ((Elf32_Half)2)     /* Executable file.         */
#define ET_DYN          ((Elf32_Half)3)     /* Shared object file.      */
#define ET_CORE         ((Elf32_Half)4)     /* Core file.               */
#if 0
#define ET_LOPROC   ((Elf32_Half)0xff00)    /* Processor-specific.      */
#define ET_HIPROC   ((Elf32_Half)0xffff)    /* Processor-specific.      */
#endif

#define ELF_IS_EXECUTABLE(hdr)  (ELF_TYPE((hdr))==ET_EXEC || ELF_TYPE((hdr))==ET_DYN)


#define EM_NONE         ((Elf32_Half)0)     /* No machine.                                              */
#define EM_M32          ((Elf32_Half)1)     /* AT&T WE 32100.                                           */
#define EM_SPARC        ((Elf32_Half)2)     /* SPARC.                                                   */
#define EM_386          ((Elf32_Half)3)     /* Intel 80386.                                             */
#define EM_68K          ((Elf32_Half)4)     /* Motorola 68000.                                          */
#define EM_88K          ((Elf32_Half)5)     /* Motorola 88000.                                          */

#if 0
RESERVED 6 Reserved for future use 
#endif

#define EM_860          ((Elf32_Half)7)     /* Intel 80860.                                             */
#define EM_MIPS         ((Elf32_Half)8)     /* MIPS I Architecture.                                     */
#define EM_S370         ((Elf32_Half)9)     /* IBM System/370 Processor.                                */
#define EM_MIPS_RS3_LE  ((Elf32_Half)10)    /* MIPS RS3000 Little-endian.                               */

#if 0
#define RESERVED 11-14 Reserved for future use 
#endif

#define EM_PARISC       ((Elf32_Half)15)    /* Hewlett-Packard PA-RISC.                                 */
#define RESERVED        ((Elf32_Half)16)    /* Reserved for future use.                                 */
#define EM_VPP500       ((Elf32_Half)17)    /* Fujitsu VPP500.                                          */
#define EM_SPARC32PLUS  ((Elf32_Half)18)    /* Enhanced instruction set SPARC.                          */
#define EM_960          ((Elf32_Half)19)    /* Intel 80960.                                             */
#define EM_PPC          ((Elf32_Half)20)    /* PowerPC.                                                 */
#define EM_PPC64        ((Elf32_Half)21)    /* 64-bit PowerPC.                                          */

#if 0
RESERVED 22-35 Reserved for future use 
#endif

#define EM_V800         ((Elf32_Half)36)    /* NEC V800.                                                */
#define EM_FR20         ((Elf32_Half)37)    /* Fujitsu FR20.                                            */
#define EM_RH32         ((Elf32_Half)38)    /* TRW RH-32.                                               */
#define EM_RCE          ((Elf32_Half)39)    /* Motorola RCE.                                            */
#define EM_ARM          ((Elf32_Half)40)    /* Advanced RISC Machines ARM.                              */
#define EM_ALPHA        ((Elf32_Half)41)    /* Digital Alpha.                                           */
#define EM_SH           ((Elf32_Half)42)    /* Hitachi SH.                                              */
#define EM_SPARCV9      ((Elf32_Half)43)    /* SPARC Version 9.                                         */
#define EM_TRICORE      ((Elf32_Half)44)    /* Siemens Tricore embedded processor.                      */
#define EM_ARC          ((Elf32_Half)45)    /* Argonaut RISC Core, Argonaut Technologies Inc.           */
#define EM_H8_300       ((Elf32_Half)46)    /* Hitachi H8/300.                                          */
#define EM_H8_300H      ((Elf32_Half)47)    /* Hitachi H8/300H.                                         */
#define EM_H8S          ((Elf32_Half)48)    /* Hitachi H8S.                                             */
#define EM_H8_500       ((Elf32_Half)49)    /* Hitachi H8/500.                                          */
#define EM_IA_64        ((Elf32_Half)50)    /* Intel IA-64 processor architecture.                      */
#define EM_MIPS_X       ((Elf32_Half)51)    /* Stanford MIPS-X.                                         */
#define EM_COLDFIRE     ((Elf32_Half)52)    /* Motorola ColdFire.                                       */
#define EM_68HC12       ((Elf32_Half)53)    /* Motorola M68HC12.                                        */
#define EM_MMA          ((Elf32_Half)54)    /* Fujitsu MMA Multimedia Accelerator.                      */
#define EM_PCP          ((Elf32_Half)55)    /* Siemens PCP.                                             */
#define EM_NCPU         ((Elf32_Half)56)    /* Sony nCPU embedded RISC processor.                       */
#define EM_NDR1         ((Elf32_Half)57)    /* Denso NDR1 microprocessor.                               */
#define EM_STARCORE     ((Elf32_Half)58)    /* Motorola Star*Core processor.                            */
#define EM_ME16         ((Elf32_Half)59)    /* Toyota ME16 processor.                                   */
#define EM_ST100        ((Elf32_Half)60)    /* STMicroelectronics ST100 processor.                      */
#define EM_TINYJ        ((Elf32_Half)61)    /* Advanced Logic Corp. TinyJ embedded processor family.    */

#if 0
#define Reserved 62-65 Reserved for future use.
#endif

#define EM_FX66         ((Elf32_Half)66)    /* Siemens FX66 microcontroller.                            */
#define EM_ST9PLUS      ((Elf32_Half)67)    /* STMicroelectronics ST9+ 8/16 bit microcontroller.        */
#define EM_ST7          ((Elf32_Half)68)    /* STMicroelectronics ST7 8-bit microcontroller.            */
#define EM_68HC16       ((Elf32_Half)69)    /* Motorola MC68HC16 Microcontroller.                       */
#define EM_68HC11       ((Elf32_Half)70)    /* Motorola MC68HC11 Microcontroller.                       */
#define EM_68HC08       ((Elf32_Half)71)    /* Motorola MC68HC08 Microcontroller.                       */
#define EM_68HC05       ((Elf32_Half)72)    /* Motorola MC68HC05 Microcontroller.                       */
#define EM_SVX          ((Elf32_Half)73)    /* Silicon Graphics SVx.                                    */
#define EM_ST19         ((Elf32_Half)74)    /* STMicroelectronics ST19 8-bit microcontroller.           */
#define EM_VAX          ((Elf32_Half)75)    /* Digital VAX.                                             */
#define EM_CRIS         ((Elf32_Half)76)    /* Axis Communications 32-bit embedded processor.           */
#define EM_JAVELIN      ((Elf32_Half)77)    /* Infineon Technologies 32-bit embedded processor.         */
#define EM_FIREPATH     ((Elf32_Half)78)    /* Element 14 64-bit DSP Processor.                         */
#define EM_ZSP          ((Elf32_Half)79)    /* LSI Logic 16-bit DSP Processor.                          */
#define EM_MMIX         ((Elf32_Half)80)    /* Donald Knuth's educational 64-bit processor.             */
#define EM_HUANY        ((Elf32_Half)81)    /* Harvard University machine-independent object files .    */
#define EM_PRISM        ((Elf32_Half)82)    /* SiTera Prism.                                            */


#define EV_NONE         ((Elf32_Word)0)     /* Invalid version.         */
#define EV_CURRENT      ((Elf32_Word)1)     /* Current version.         */


#define EI_MAG0         ((uint8_t)0)        /* File identification.     */
#define EI_MAG1         ((uint8_t)1)        /* File identification.     */
#define EI_MAG2         ((uint8_t)2)        /* File identification.     */
#define EI_MAG3         ((uint8_t)3)        /* File identification.     */
#define EI_CLASS        ((uint8_t)4)        /* File class.              */
#define EI_DATA         ((uint8_t)5)        /* Data encoding.           */
#define EI_VERSION      ((uint8_t)6)        /* File version.            */
#define EI_PAD          ((uint8_t)7)        /* Start of padding bytes.  */
#define EI_OSABI        ((uint8_t)7)        /* Operating system/ABI identification.     */
#define EI_ABIVERSION   ((uint8_t)8)        /* ABI version.                             */


#define ELF_MAGIC_VALID(hptr)   (((ELF_MAG0(hptr)==0x7f) && \
    (ELF_MAG1(hptr)=='E') &&                                \
    (ELF_MAG2(hptr)=='L') &&                                \
    (ELF_MAG3(hptr)=='F')) ? true : false) 


#define ELFCLASSNONE    ((uint8_t)0)        /* Invalid class.           */
#define ELFCLASS32      ((uint8_t)1)        /* 32-bit objects.          */
#define ELFCLASS64      ((uint8_t)2)        /* 64-bit objects.          */

#define ELFDATANONE     ((uint8_t)0)        /* Invalid data encoding.   */
#define ELFDATA2LSB     ((uint8_t)1)        /* Little-Endian.           */
#define ELFDATA2MSB     ((uint8_t)2)        /* Big-Endian.              */

#if 0
typedef enum tagElf_EndianessType {
    ELF_INVALID_ENCODING,
    ELF_BIG_ENDIAN,
    ELF_LITTLE_ENDIAN
} Elf_EndianessType;
#endif

/*
** 
**  ELF Sections.
**
*/
#pragma pack(1)
typedef struct tagElf32_Shdr {
    Elf32_Word  sh_name;
    Elf32_Word  sh_type;
    Elf32_Word  sh_flags;
    Elf32_Addr  sh_addr;
    Elf32_Off   sh_offset;
    Elf32_Word  sh_size;
    Elf32_Word  sh_link;
    Elf32_Word  sh_info;
    Elf32_Word  sh_addralign;
    Elf32_Word  sh_entsize;
} Elf32_Shdr;
#pragma pack()


#define ELF_SECTION_SIZE    (sizeof(Elf32_Shdr))

#define ELF_SH_NAME(shr)         ((shr)->sh_name)
#define ELF_SH_TYPE(shr)         ((shr)->sh_type)
#define ELF_SH_FLAGS(shr)        ((shr)->sh_flags)
#define ELF_SH_ADDR(shr)         ((shr)->sh_addr)
#define ELF_SH_OFFSET(shr)       ((shr)->sh_offset)
#define ELF_SH_SIZE(shr)         ((shr)->sh_size)
#define ELF_SH_LINK(shr)         ((shr)->sh_link)
#define ELF_SH_INFO(shr)         ((shr)->sh_info)
#define ELF_SH_ADDRALIGN(shr)    ((shr)->sh_addralign)
#define ELF_SH_ENTSIZE(shr)      ((shr)->sh_entsize)

#define SHN_UNDEF       ((Elf32_Half)0)
#define SHN_LORESERVE   ((Elf32_Half)0xff00)
#define SHN_LOPROC      ((Elf32_Half)0xff00)
#define SHN_HIPROC      ((Elf32_Half)0xff1f)
#define SHN_ABS         ((Elf32_Half)0xfff1)
#define SHN_COMMON      ((Elf32_Half)0xfff2)
#define SHN_HIRESERVE   ((Elf32_Half)0xffff)


#define SHT_NULL        ((Elf32_Word)0)
#define SHT_PROGBITS    ((Elf32_Word)1)
#define SHT_SYMTAB      ((Elf32_Word)2)
#define SHT_STRTAB      ((Elf32_Word)3)
#define SHT_RELA        ((Elf32_Word)4)
#define SHT_HASH        ((Elf32_Word)5)
#define SHT_DYNAMIC     ((Elf32_Word)6)
#define SHT_NOTE        ((Elf32_Word)7)
#define SHT_NOBITS      ((Elf32_Word)8)
#define SHT_REL         ((Elf32_Word)9)
#define SHT_SHLIB       ((Elf32_Word)10)
#define SHT_DYNSYM      ((Elf32_Word)11)
#define SHT_LOPROC      ((Elf32_Word)0x70000000)
#define SHT_HIPROC      ((Elf32_Word)0x7fffffff)
#define SHT_LOUSER      ((Elf32_Word)0x80000000)
#define SHT_HIUSER      ((Elf32_Word)0xffffffff)


#define SHF_WRITE       ((Elf32_Word)0x1)
#define SHF_ALLOC       ((Elf32_Word)0x2)
#define SHF_EXECINSTR   ((Elf32_Word)0x4)
#define SHF_MASKPROC    ((Elf32_Word)0xf0000000)


/*
** 
**  ELF Symbol Table.
**
*/
#pragma pack(1)
typedef struct tagElf32_Sym {
    Elf32_Word  st_name;
    Elf32_Addr  st_value;
    Elf32_Word  st_size;
    uint8_t     st_info;
    uint8_t     st_other;
    Elf32_Half  st_shndx;
} Elf32_Sym;
#pragma pack()


#define ELF_SYM_TABLE_SIZE  (sizeof(Elf32_Sym))

#define STN_UNDEF           ((Elf32_Half)0)


#define ELF32_ST_BIND(i)    ((i) >> 4)
#define ELF32_ST_TYPE(i)    ((i) & 0xf)
#define ELF32_ST_INFO(b,t)  (((b) << 4) + ((t) & 0xf))


#define STB_LOCAL           ((Elf32_Half)0)
#define STB_GLOBAL          ((Elf32_Half)1)
#define STB_WEAK            ((Elf32_Half)2)
#define STB_LOPROC          ((Elf32_Half)13)
#define STB_HIPROC          ((Elf32_Half)15)


#define STT_NOTYPE          ((Elf32_Half)0)
#define STT_OBJECT          ((Elf32_Half)1)
#define STT_FUNC            ((Elf32_Half)2)
#define STT_SECTION         ((Elf32_Half)3)
#define STT_FILE            ((Elf32_Half)4)
#define STT_LOPROC          ((Elf32_Half)13)
#define STT_HIPROC          ((Elf32_Half)15)


/*
** 
**  Relocation.
**
*/
#pragma pack(1)
typedef struct tagElf32_Rel {
    Elf32_Addr  r_offset;
    Elf32_Word  r_info;
} Elf32_Rel;
#pragma pack()

#pragma pack(1)
typedef struct tagElf32_Rela {
    Elf32_Addr  r_offset;
    Elf32_Word  r_info;
    Elf32_Sword r_addend;
} Elf32_Rela;
#pragma pack()


#define ELF_RELOCATION_SIZE (sizeof(Elf32_Rela))


#define ELF32_R_SYM(i)      ((i) >> 8)
#define ELF32_R_TYPE(i)     ((unsigned char)(i))
#define ELF32_R_INFO(s,t)   (((s) << 8)+(unsigned char)(t))

/*
** 
**  Program Header.
**
*/
#pragma pack(1)
typedef struct tagElf32_Phdr {
    Elf32_Word  p_type;
    Elf32_Off   p_offset;
    Elf32_Addr  p_vaddr;
    Elf32_Addr  p_paddr;
    Elf32_Word  p_filesz;
    Elf32_Word  p_memsz;
    Elf32_Word  p_flags;
    Elf32_Word  p_align;
} Elf32_Phdr;
#pragma pack()


#define ELF_PHDR_SIZE       (sizeof(Elf32_Phdr))


#define ELF_PH_TYPE(phr)    ((phr)->p_type)
#define ELF_PH_OFFSET(phr)  ((phr)->p_offset)
#define ELF_PH_VADDR(phr)   ((phr)->p_vaddr)
#define ELF_PH_PADDR(phr)   ((phr)->p_paddr)
#define ELF_PH_FILESZ(phr)  ((phr)->p_filesz)
#define ELF_PH_MEMSZ(phr)   ((phr)->p_memsz)
#define ELF_PH_FLAGS(phr)   ((phr)->p_flags)
#define ELF_PH_ALIGN(phr)   ((phr)->p_align)


#define PT_NULL             ((Elf32_Word)0)
#define PT_LOAD             ((Elf32_Word)1)
#define PT_DYNAMIC          ((Elf32_Word)2)
#define PT_INTERP           ((Elf32_Word)3)
#define PT_NOTE             ((Elf32_Word)4)
#define PT_SHLIB            ((Elf32_Word)5)
#define PT_PHDR             ((Elf32_Word)6)
#define PT_LOPROC           ((Elf32_Word)0x70000000)
#define PT_HIPROC           ((Elf32_Word)0x7fffffff)

#define PF_X                ((Elf32_Word)0x1)           /* Execute      */
#define PF_W                ((Elf32_Word)0x2)           /* Write        */
#define PF_R                ((Elf32_Word)0x4)           /* Read         */
#define PF_MASKPROC         ((Elf32_Word)0xf0000000)    /* Unspecified  */

#endif  /* __ELF_H */
