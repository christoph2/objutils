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
#include <assert.h>
#include <stdio.h>

#include "ElfInfo.h"


static const char *ElfInfo_GetSectionType(Elf32_Word section_type);
const char *ElfInfo_GetSectionName(ElfIo_Struct const * str,Elf32_Word idx);

ElfIo_StatusType ElfInfo_PrintHeader(ElfIo_Struct const * str)
{
    const char *types[]={"Processor-specific.","No file type.","Relocatable file.",
        "Executable file.","Shared object file.","Core file."};
    const char *classes[]={"Invalid class.","32-bit objects.","64-bit objects."};
    const char *encodings[]={"Invalid data encoding","LITTLE","BIG"};

    uint16_t idx;
    Elf32_Half machine_id;
    Elf32_Half type_id;    
    Elf32_Half ehsize;
    uint8_t clss;
    uint8_t data;
    uint8_t abi;
    uint8_t abi_version;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    type_id=ELF_TYPE(str->header);
    machine_id=ELF_MACHINE(str->header);    
    ehsize=ELF_EHSIZE(str->header); /* should be used for validation ! */        
    clss=ELF_CLASS(str->header);
    data=ELF_DATA(str->header);
    abi=ELF_OSABI(str->header);
    abi_version=ELF_ABIVERSION(str->header);

    printf("===============================================================================\n");
    printf("ELF file header:\n");
    printf("===============================================================================\n");
    idx=type_id > 4u ? 0u : type_id+1;
    printf("File-Type:\t\t\t    0x%04x - %s\n",type_id,types[idx]);
    printf("Machine-ID:\t\t\t    0x%04x - %s\n",machine_id,ElfIo_GetMachineName(str));
    printf("Version:\t\t\t0x%08x - ",(unsigned int)ELF_VER(str->header));
    printf( ELF_VER(str->header)==0u ? "Invalid.\n" : "Current.\n");
    printf("Entry-Point:\t\t\t0x%08x\n",(unsigned int)ELF_ENTRY(str->header));
    printf("Start of program headers:\t0x%08x\n",(unsigned int)ELF_PHOFF(str->header));
    printf("Start of section headers:\t0x%08x\n",(unsigned int)ELF_SHOFF(str->header));
    printf("Flags:\t\t\t\t0x%08x\n",(unsigned int)ELF_FLAGS(str->header));
    printf("PHT entry size:\t\t\t0x%08x\n",(unsigned int)ELF_PHENTSIZE(str->header));
    printf("Number of PHT entries:\t\t0x%08x\n",(unsigned int)ELF_PHNUM(str->header));
    printf("SHT entry size:\t\t\t0x%08x\n",(unsigned int)ELF_SHENTSIZE(str->header));
    printf("Number of SHT entries:\t\t0x%08x\n",(unsigned int)ELF_SHNUM(str->header));
    printf("String table index:\t\t0x%08x\n",(unsigned int)ELF_SHSTRNDX(str->header));
    idx=clss > 2 ? 0 : clss;
    printf("Class:\t\t\t\t0x%08x - %s\n",(unsigned int)clss,classes[idx]);
    idx=data > 2 ? 0 : data;
    printf("Endianess:\t\t\t0x%08x - %s\n",(unsigned int)data,encodings[idx]);
    printf("ELF-ABI:\t\t\t0x%08x\n",(unsigned int)abi);
    printf("ELF-ABI-Version:\t\t0x%08x\n",(unsigned int)abi_version);

    return ELFIO_E_OK;
}


ElfIo_StatusType ElfInfo_PrintProgramTable(ElfIo_Struct const * str)
{
    const char *types[]={"NO TYPE","RELOC","EXEC","SHARED","CORE"};

    Elf32_Off hdr_offs;
    Elf32_Half num;
    Elf32_Half num_entries;
    Elf32_Phdr *buf;
	Elf32_Word flags;
	
    uint16_t idx;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    hdr_offs=ELF_PHOFF(str->header);

    num=0;
    num_entries=ELF_PHNUM(str->header);

    printf("\n\n");
    printf("===============================================================================\n");
    printf("Program header table:\n");
    printf("===============================================================================\n");
    printf("Type    Offset     VirtAddr   PhysAddr   FileSiz    MemSiz     Flags Align\n");
    printf("===============================================================================\n");

    while (num<num_entries) {
        buf=str->program_headers+num;
        flags=ELF_PH_FLAGS(buf);        
        idx=(uint16_t)(ELF_PH_TYPE(buf) > 4 ? 0 : ELF_PH_TYPE(buf));
        printf("%-7s ",types[idx]);
        printf("0x%08x ",(unsigned int)ELF_PH_OFFSET(buf));
        printf("0x%08x ",(unsigned int)ELF_PH_PADDR(buf));
        printf("0x%08x ",(unsigned int)ELF_PH_VADDR(buf));
        printf("0x%08x ",(unsigned int)ELF_PH_FILESZ(buf));
        printf("0x%08x ",(unsigned int)ELF_PH_MEMSZ(buf));
        (flags & PF_R) ? printf("R") : printf(" ");        
        (flags & PF_W) ? printf("W") : printf(" ");
        (flags & PF_X) ? printf("X") : printf(" ");
        printf("   0x%08x\n",(unsigned int)ELF_PH_ALIGN(buf));
        num++;
    }   
    return ELFIO_E_OK;
}


ElfIo_StatusType ElfIo_PrintSectionHeaderTable(ElfIo_Struct const * str)
{
    Elf32_Off hdr_offs;
    Elf32_Half num;
    Elf32_Half num_entries;    
    Elf32_Shdr *buf;    
    Elf32_Word flags;    

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    hdr_offs=ELF_SHOFF(str->header);

    num=0;
    num_entries=ELF_SHNUM(str->header);

    printf("\n\n");
    printf("===============================================================================\n");
    printf("Section header table:\n");
    printf("===============================================================================\n");
    printf("Nr.    Type      Addr.      Offset     Size       ES     Link   AL   Info\n");
	printf("       Name                            Flags\n");
    printf("===============================================================================\n");

    while (num<num_entries) {
        buf=str->section_headers+num;
        printf("[%04X] ",num);
        printf("%-10s",ElfInfo_GetSectionType(ELF_SH_TYPE(buf)));
        
        printf("0x%08x ",(unsigned int)ELF_SH_ADDR(buf));
        printf("0x%08x ",(unsigned int)ELF_SH_OFFSET(buf));
        printf("0x%08x ",(unsigned int)ELF_SH_SIZE(buf));
		printf("0x%04x ",(unsigned int)ELF_SH_ENTSIZE(buf));
		printf("0x%04x ",(unsigned int)ELF_SH_LINK(buf));
		printf("0x%02x ",(unsigned int)ELF_SH_ADDRALIGN(buf));
		printf("0x%08x\n",(unsigned int)ELF_SH_INFO(buf));
		
		printf("       ");
		printf("%-32s",ElfInfo_GetSectionName(str,ELF_SH_NAME(buf)));
		
		flags=ELF_SH_FLAGS(buf);
		(flags & SHF_ALLOC) ? printf("A") : printf(" ");		
		(flags & SHF_WRITE) ? printf("W") : printf(" ");                
        (flags & SHF_EXECINSTR) ? printf("X") : printf(" ");
		/*(flags & SHF_MASKPROC) ? printf("S") : printf(" "); */	/* todo: Handle this!!! */
		printf("\n");
        num++;
    }   
    return ELFIO_E_OK;
}

const char *ElfInfo_GetSectionType(Elf32_Word section_type)
{
    const char *res;

    const char *SectionTypes[]={
        "NULL","PROGBITS","SYMTAB","STRTAB","RELA","HASH",
        "DYNAMIC","NOTE","NOBITS","REL","SHLIB","DYNSYM",
    };

    const char *Others[]={
        "LOPROC","HIPROC","LOUSER","HIUSER","UNKNOWN"
    };

    if ((section_type>=0) && (section_type<=11)) {
        res=SectionTypes[section_type];
    } else {
        switch (section_type) {
            case SHT_LOPROC:
                res=Others[0];
                break;
            case SHT_HIPROC:
                res=Others[1];
                break;
            case SHT_LOUSER:
                res=Others[2];
                break;
            case SHT_HIUSER:
                res=Others[3];
                break;
            default:
                res=Others[4];
                break;
        }
    }
    return res;
}


const char *ElfInfo_GetSectionName(ElfIo_Struct const * str,Elf32_Word idx)
{
	/* todo: Range-Checking!!! */
    return &ElfIO_GetSection(str,str->header->e_shstrndx)->data[idx];
}
