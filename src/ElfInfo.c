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
#include <string.h>

#include "ElfInfo.h"


static const char *ElfInfo_GetSectionType(Elf32_Word section_type);
static const char *GetSymbolBinding(uint8_t value);
static const char *GetSymbolType(uint8_t value);
char const * GetSpecialSectionName(Elf32_Half section);

const char *ElfInfo_GetSectionName(ElfIo_Struct const * str,Elf32_Word idx);
const char *ElfInfo_GetSymbolName(ElfIo_Struct const * str,Elf32_Word section,Elf32_Word idx);

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

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    type_id=ELF_TYPE(str->header);
    machine_id=ELF_MACHINE(str->header);    
    ehsize=ELF_EHSIZE(str->header); /* should be used for validation ! */        
    clss=ELF_CLASS(str->header);
    data=ELF_DATA(str->header);    

    printf("===============================================================================\n");
    printf("ELF file header:\n");
    printf("===============================================================================\n");
    idx=type_id > 4u ? 0u : type_id+1;
    printf("File-Type:\t\t\t    0x%04x - %s\n",type_id,types[idx]);
    printf("Machine-ID:\t\t\t    0x%04x - %s\n",machine_id,ElfIo_GetMachineName(str));
    printf("Version:\t\t\t0x%08x - ",(uint32_t)ELF_VER(str->header));
    printf( ELF_VER(str->header)==0u ? "Invalid.\n" : "Current.\n");
    printf("Entry-Point:\t\t\t0x%08x\n",(uint32_t)ELF_ENTRY(str->header));
    printf("Start of program headers:\t0x%08x\n",(uint32_t)ELF_PHOFF(str->header));
    printf("Start of section headers:\t0x%08x\n",(uint32_t)ELF_SHOFF(str->header));
    printf("Flags:\t\t\t\t0x%08x\n",(uint32_t)ELF_FLAGS(str->header));
    printf("PHT entry size:\t\t\t0x%08x\n",(uint32_t)ELF_PHENTSIZE(str->header));
    printf("Number of PHT entries:\t\t0x%08x\n",(uint32_t)ELF_PHNUM(str->header));
    printf("SHT entry size:\t\t\t0x%08x\n",(uint32_t)ELF_SHENTSIZE(str->header));
    printf("Number of SHT entries:\t\t0x%08x\n",(uint32_t)ELF_SHNUM(str->header));
    printf("String table index:\t\t0x%08x\n",(uint32_t)ELF_SHSTRNDX(str->header));
    idx=clss > 2 ? 0 : clss;
    printf("Class:\t\t\t\t0x%08x - %s\n",(uint32_t)clss,classes[idx]);
    idx=data > 2 ? 0 : data;
    printf("Endianess:\t\t\t0x%08x - %s\n",(uint32_t)data,encodings[idx]);
    printf("ELF-ABI:\t\t\t0x%08x\n",(uint32_t)ELF_OSABI(str->header));
    printf("ELF-ABI-Version:\t\t0x%08x\n",(uint32_t)ELF_ABIVERSION(str->header));

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
        printf("0x%08x ",(uint32_t)ELF_PH_OFFSET(buf));
        printf("0x%08x ",(uint32_t)ELF_PH_PADDR(buf));
        printf("0x%08x ",(uint32_t)ELF_PH_VADDR(buf));
        printf("0x%08x ",(uint32_t)ELF_PH_FILESZ(buf));
        printf("0x%08x ",(uint32_t)ELF_PH_MEMSZ(buf));
        (flags & PF_R) ? printf("R") : printf(" ");        
        (flags & PF_W) ? printf("W") : printf(" ");
        (flags & PF_X) ? printf("X") : printf(" ");
        printf("   0x%08x\n",(uint32_t)ELF_PH_ALIGN(buf));
        num++;
    }   
    return ELFIO_E_OK;
}


ElfIo_StatusType ElfIo_PrintSectionHeaderTable(ElfIo_Struct const * str)
{
    Elf32_Half num;
    Elf32_Half num_entries;    
    Elf32_Shdr *buf;    
    Elf32_Word flags;    

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

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
        printf("0x%08x ",(uint32_t)ELF_SH_ADDR(buf));
        printf("0x%08x ",(uint32_t)ELF_SH_OFFSET(buf)); /* Offset only needed internally. */
        printf("0x%08x ",(uint32_t)ELF_SH_SIZE(buf));
		printf("0x%04x ",(uint32_t)ELF_SH_ENTSIZE(buf));
		printf("0x%04x ",(uint32_t)ELF_SH_LINK(buf));
		printf("0x%02x ",(uint32_t)ELF_SH_ADDRALIGN(buf));
		printf("0x%08x\n",(uint32_t)ELF_SH_INFO(buf));
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


ElfIo_StatusType ElfIo_PrintSymbols(ElfIo_Struct const * str)
{
    Elf32_Half i;
    Elf32_Half num_entries;
    Elf32_Shdr * section_header;
    Elf32_Sym sym;
    size_t num_symbols;
    size_t j;
    char const * section_name;
    uint32_t section_idx;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    i=0;
    num_entries=ELF_SHNUM(str->header);

    printf("\n\n");
    printf("===============================================================================\n");
    printf("Symbols:\n");
    printf("===============================================================================\n");
    printf("Value      Size   Type    Bind   Ndx\n");
    printf("Name\n");
    printf("===============================================================================\n");

    while (i<num_entries) {
        section_header=&str->section_headers[i];
        if ((section_header->sh_type==SHT_SYMTAB) || (section_header->sh_type==SHT_DYNSYM)) {
            assert(section_header->sh_entsize==sizeof(Elf32_Sym));            
            num_symbols=section_header->sh_size/section_header->sh_entsize;
            section_idx=section_header->sh_link;            

            for (j=0;j<num_symbols;++j) {
                sym=ElfIO_GetSymbol(str,i,j);
                printf("0x%08x ",(uint32_t)sym.st_value);
                printf("0x%08x ",(uint32_t)sym.st_size);                                
                printf("%-7s ",GetSymbolType(ELF32_ST_TYPE(sym.st_info)));
                printf("%-6s ",GetSymbolBinding(ELF32_ST_BIND(sym.st_info)));
                
                section_name=GetSpecialSectionName(sym.st_shndx);
                if (section_name) {
                    printf("%-8s",section_name);
                } else {
                    printf("0x%08x ",(uint32_t)sym.st_shndx);
                }                
                printf("\n%s\n",ElfInfo_GetSymbolName(str,section_idx,sym.st_name));
            }
        }
        ++i;
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


const char *GetSymbolBinding(uint8_t value)
{
    const char * bindings[]={
        "LOCAL","GLOBAL","WEAK","PROC","UNK"
    };

    if ((value>=STB_LOCAL) && (value<=STB_WEAK)) {
        return bindings[value];
    } else if ((value>=STB_LOPROC) && (value<=STB_HIPROC)) {
        return bindings[3];
    } else {
        return bindings[4];
    }

}


const char *GetSymbolType(uint8_t value)
{
    const char * types[]={
        "NOTYPE","OBJECT","FUNC","SECTION","FILE","PROC","UNKNOWN"
    };

    if ((value>=STT_NOTYPE) && (value<=STT_FILE)) {
        return types[value];
    } else if ((value>=STT_LOPROC) && (value<=STT_HIPROC)) {
        return types[5];
    } else {
        return types[6];
    }
}

char const * GetSpecialSectionName(Elf32_Half section)
{
    const char * SpecialSections[]={
        "UNDEF","PROC","ABS","COMMON",(char const*)NULL
    };
    if (section==SHN_UNDEF) {
        return SpecialSections[0];
    } else if ((section>=SHN_LOPROC) && (section<=SHN_HIPROC)) {
        return SpecialSections[1];
    } else if (section==SHN_ABS) {
        return SpecialSections[2];
    } else if (section==SHN_COMMON) {
        return SpecialSections[3];
    } else {
        return SpecialSections[4];
    }
}


const char *ElfInfo_GetSectionName(ElfIo_Struct const * str,Elf32_Word idx)
{
	/* todo: Range-Checking!!! */
    return &ElfIO_GetSection(str,str->header->e_shstrndx)->data[idx];
}


const char *ElfInfo_GetSymbolName(ElfIo_Struct const * str,Elf32_Word section,Elf32_Word idx)
{
	/* todo: Range-Checking!!! */
    return &ElfIO_GetSection(str,section)->data[idx];
}
