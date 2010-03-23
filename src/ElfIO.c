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
#include "ElfIO.h"

#include <assert.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>


/* todo: OpenBSD-'l'-Fixes! */
#define STRNCPY strncpy
#define STRNCAT strncat

static uint16_t ElfIo_Convert16U(uint16_t w);
static uint32_t ElfIo_Convert32U(uint32_t dw);
static int32_t ElfIo_Convert32S(int32_t dw);

static const  char *Elf_MachineNames[]={
    "Unknown machine.",
    "No machine.",
    "AT&T WE 32100.",
    "SPARC.",
    "Intel 80386.",
    "Motorola 68000.",
    "Motorola 88000.",
    "Reserved for future use.",
    "Intel 80860.",
    "MIPS I Architecture.",
    "IBM System/370 Processor.",
    "MIPS RS3000 Little-endian.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Hewlett-Packard PA-RISC.",
    "Reserved for future use.",
    "Fujitsu VPP500.",
    "Enhanced instruction set SPARC.",
    "Intel 80960.",
    "PowerPC.",
    "64-bit PowerPC.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "NEC V800.",
    "Fujitsu FR20.",
    "TRW RH-32.",
    "Motorola RCE.",
    "Advanced RISC Machines ARM.",
    "Digital Alpha.",
    "Hitachi SH.",
    "SPARC Version 9.",
    "Siemens Tricore embedded processor.",
    "Argonaut RISC Core, Argonaut Technologies Inc.",
    "Hitachi H8/300.",
    "Hitachi H8/300H.",
    "Hitachi H8S.",
    "Hitachi H8/500.",
    "Intel IA-64 processor architecture.",
    "Stanford MIPS-X.",
    "Motorola ColdFire.",
    "Motorola M68HC12.",
    "Fujitsu MMA Multimedia Accelerator.",
    "Siemens PCP.",
    "Sony nCPU embedded RISC processor.",
    "Denso NDR1 microprocessor.",
    "Motorola Star*Core processor.",
    "Toyota ME16 processor. ",
    "STMicroelectronics ST100 processor.",
    "Advanced Logic Corp. TinyJ embedded processor family.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Reserved for future use.",
    "Siemens FX66 microcontroller.",
    "STMicroelectronics ST9+ 8/16 bit microcontroller.",
    "STMicroelectronics ST7 8-bit microcontroller.",
    "Motorola MC68HC16 Microcontroller.",
    "Motorola MC68HC11 Microcontroller.",
    "Motorola MC68HC08 Microcontroller.",
    "Motorola MC68HC05 Microcontroller.",
    "Silicon Graphics SVx.",
    "STMicroelectronics ST19 8-bit microcontroller.",
    "Digital VAX.",
    "Axis Communications 32-bit embedded processor.",
    "Infineon Technologies 32-bit embedded processor.",
    "Element 14 64-bit DSP Processor.",
    "LSI Logic 16-bit DSP Processor.",
    "Donald Knuth's educational 64-bit processor.",
    "Harvard University machine-independent object files .",
    "SiTera Prism."
};


#define ELF_NUM_OF_MACHINES (SIZEOF_ARRAY(Elf_MachineNames)-1)


Elf_EndianessType ElfIo_CheckHostEndianess(void)
{
    const uint16_t foo=0xaa55u;
    uint8_t const * const ptr=(uint8_t * const)&foo;
    
    if (0[ptr]==0xaa) {
        return ELF_BIG_ENDIAN;   
    } else {
        return ELF_LITTLE_ENDIAN;
    }
}


ElfIo_StatusType ElfIo_Init(ElfIo_Struct *str,char * const file_name,ElfIo_Mode mode)
{
    size_t len;
    int error;

    assert(file_name!=(char * const)NULL);

    if ((str->guard==sizeof(ElfIo_Struct)) && (str->file_opened==true)) {
        return ELFIO_E_STATE;
    }    

    if (!((mode==ELFIO_READ) || (mode==ELFIO_WRITE))) {
        return ELFIO_E_VALUE;
    }

    if ((len=strlen(file_name))>ELFIO_MAX_FILENAME_LEN) {
        return ELFIO_E_LIMIT;
    }    

    str->file_opened=false;
    str->guard=sizeof(ElfIo_Struct);
    str->mode=mode;    

#if defined(ELFIO_HAS_FOPEN_S)
    if ((error=fopen_s(&str->stream,file_name,(mode==ELFIO_READ) ? "rb" : "wb"  )) !=0 ) {
        return ELFIO_E_FILEIO;
    } else {
        str->file_opened=true;
    }
#else
    UNREFERENCED_PARAMETER(error);

    str->stream=fopen(file_name,(mode==ELFIO_READ) ? "rb" : "wb");

    if (str->stream==(FILE*)NULL) {
        return ELFIO_E_FILEIO;
    } else {
        str->file_opened=true;      
    }
#endif

    str->file_name=(char const *)malloc(len+1);
    assert(str->file_name!=(char const *)NULL);
    STRNCPY((char*)str->file_name,file_name,len);

    str->header=(Elf32_Ehdr *)malloc(ELF_HEADER_SIZE);
    assert(str->header!=(Elf32_Ehdr *)NULL);

    if (mode==ELFIO_READ) {
        /* Read Header. */
        if (fread((void*)str->header,ELF_HEADER_SIZE,1,str->stream)==0) {
            return ELFIO_E_FILEIO;
        } else {
            if (!ELF_MAGIC_VALID(str->header)) {
                return ELFIO_E_INVALID;

            }

            switch (ELF_DATA(str->header)) {
                case ELFDATA2LSB:
                    str->encoding=ELF_LITTLE_ENDIAN;
                        break;
                case ELFDATA2MSB:
                    str->encoding=ELF_BIG_ENDIAN;                    
                        break;
                default:
                    str->encoding=ELF_INVALID_ENCODING;
                    return ELFIO_E_INVALID;
            }

            if (ElfIo_CheckHostEndianess()!=str->encoding) {
                /* Convert Endianess. */
                ELF_TYPE(str->header)       = ElfIo_Convert16U(ELF_TYPE(str->header));
                ELF_MACHINE(str->header)    = ElfIo_Convert16U(ELF_MACHINE(str->header));
                ELF_VER(str->header)        = ElfIo_Convert32U(ELF_VER(str->header));
                ELF_ENTRY(str->header)      = ElfIo_Convert32U(ELF_ENTRY(str->header));
                ELF_PHOFF(str->header)      = ElfIo_Convert32U(ELF_PHOFF(str->header));
                ELF_SHOFF(str->header)      = ElfIo_Convert32U(ELF_SHOFF(str->header));
                ELF_FLAGS(str->header)      = ElfIo_Convert32U(ELF_FLAGS(str->header));
                ELF_EHSIZE(str->header)     = ElfIo_Convert16U(ELF_EHSIZE(str->header));
                ELF_PHENTSIZE(str->header)  = ElfIo_Convert16U(ELF_PHENTSIZE(str->header));
                ELF_PHNUM(str->header)      = ElfIo_Convert16U(ELF_PHNUM(str->header));
                ELF_SHENTSIZE(str->header)  = ElfIo_Convert16U(ELF_SHENTSIZE(str->header));
                ELF_SHSTRNDX(str->header)   = ElfIo_Convert16U(ELF_SHSTRNDX(str->header));
                ELF_SHNUM(str->header)      = ElfIo_Convert16U(ELF_SHNUM(str->header));
            }
        }
    }

    if (ELF_PHNUM(str->header)>0) {
        assert(ELF_PHDR_SIZE==ELF_PHENTSIZE(str->header));
        str->program_headers=(Elf32_Phdr*)malloc(ELF_PHDR_SIZE*ELF_PHNUM(str->header));
        assert(str->program_headers!=(Elf32_Phdr*)NULL);
    }

    if (ELF_SHNUM(str->header)>0) {
        assert(ELF_SECTION_SIZE==ELF_SHENTSIZE(str->header));
        str->section_headers=(Elf32_Shdr *)malloc(ELF_SECTION_SIZE*ELF_SHNUM(str->header));
        assert(str->section_headers!=(Elf32_Shdr*)NULL);
        
        str->sections=(MemorySection *)malloc(sizeof(MemorySection)*ELF_SHNUM(str->header));
        assert(str->sections!=(MemorySection *)NULL);
        memset(str->sections,'\0',sizeof(MemorySection)*ELF_SHNUM(str->header));
    }

    return ELFIO_E_OK;
}


ElfIo_StatusType ElfIo_Deinit(ElfIo_Struct *str)
{
    uint32_t cnt;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->file_opened==false || str->mode==ELFIO_INVALID_MODE) {
        return ELFIO_E_STATE;
    }

    if (str->mode==ELFIO_READ && ELF_PHNUM(str->header)>0) {
        free((void*)str->program_headers);
    }

    if (str->mode==ELFIO_READ && ELF_SHNUM(str->header)>0) {
        free((void*)str->section_headers);

        for (cnt=0;cnt<ELF_SHNUM(str->header);++cnt) {
            if (str->sections[cnt].length>0) {
                free(str->sections[cnt].data);
            }
        }

        free((void*)str->sections);
    }

    str->guard=(uint8_t)0;
    str->file_opened=false;
    free((void*)str->header);
    free((void*)str->file_name);
    str->mode=ELFIO_INVALID_MODE;
    fclose(str->stream);

    return ELFIO_E_OK;    
}


uint16_t ElfIo_Convert16U(uint16_t w)
{
    return MAKEWORD(LOBYTE(w),HIBYTE(w));
}


uint32_t ElfIo_Convert32U(uint32_t dw)
{
    return MAKEDWORD(MAKEWORD(LOBYTE(LOWORD(dw)),HIBYTE(LOWORD(dw))),MAKEWORD(LOBYTE(HIWORD(dw)),HIBYTE(HIWORD(dw))));
}


int32_t ElfIo_Convert32S(int32_t dw)
{
    return MAKEDWORD(MAKEWORD(LOBYTE(LOWORD(dw)),HIBYTE(LOWORD(dw))),MAKEWORD(LOBYTE(HIWORD(dw)),HIBYTE(HIWORD(dw))));
}


char const * ElfIo_GetMachineName(ElfIo_Struct const * str)
{
    Elf32_Half table_index=0U;
    char const * ptr;

    ELFIO_WEAK_PARAM_CHECK(str);

    table_index=ELF_MACHINE(str->header);

    if (table_index >= ELF_NUM_OF_MACHINES) {
        table_index=0U;
    } else {
        table_index++;
    }

    ptr=Elf_MachineNames[table_index];
 
    return ptr;
}


ElfIo_StatusType ElfIo_ReadProgramTable(ElfIo_Struct const * str)
{
    Elf32_Off hdr_offs;
    Elf32_Half num;
    Elf32_Half num_entries;
    Elf32_Phdr *buf;
   int res;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    hdr_offs=ELF_PHOFF(str->header);
    
    res=fseek(str->stream,hdr_offs,SEEK_SET);
    if (res!=0) {
        return ELFIO_E_FILEIO;
    }
    
    num=0;
    num_entries=ELF_PHNUM(str->header);

    while (num<num_entries) {
        buf=str->program_headers+num;
        res=fread((void*)buf,sizeof(Elf32_Phdr),1,str->stream);
        if (res==0) {
            return ELFIO_E_FILEIO;
        }

        if (ElfIo_CheckHostEndianess()!=str->encoding) {
            ELF_PH_TYPE(buf)   = ElfIo_Convert32U(ELF_PH_TYPE(buf));
            ELF_PH_OFFSET(buf) = ElfIo_Convert32U(ELF_PH_OFFSET(buf));
            ELF_PH_VADDR(buf)  = ElfIo_Convert32U(ELF_PH_VADDR(buf));
            ELF_PH_PADDR(buf)  = ElfIo_Convert32U(ELF_PH_PADDR(buf));
            ELF_PH_FILESZ(buf) = ElfIo_Convert32U(ELF_PH_FILESZ(buf));
            ELF_PH_MEMSZ(buf)  = ElfIo_Convert32U(ELF_PH_MEMSZ(buf));
            ELF_PH_FLAGS(buf)  = ElfIo_Convert32U(ELF_PH_FLAGS(buf));
            ELF_PH_ALIGN(buf)  = ElfIo_Convert32U(ELF_PH_ALIGN(buf));
        }
        num++;
    }
   
    return ELFIO_E_OK;
}


ElfIo_StatusType ElfIo_ReadSectionHeaderTable(ElfIo_Struct const * str)
{
    Elf32_Off hdr_offs;
    Elf32_Half num;
    Elf32_Half num_entries;
    Elf32_Shdr *buf;
    int res;

    ELFIO_WEAK_PARAM_CHECK(str);

    if (str->mode!=ELFIO_READ) {
        return ELFIO_E_STATE;
    }

    hdr_offs=ELF_SHOFF(str->header);
    
    res=fseek(str->stream,hdr_offs,SEEK_SET);
    if (res!=0) {
        return ELFIO_E_FILEIO;
    }
    
    num=0;
    num_entries=ELF_SHNUM(str->header);

    while (num<num_entries) {
        buf=str->section_headers+num;
        res=fread((void*)buf,sizeof(Elf32_Shdr),1,str->stream);
        if (res==0) {
            return ELFIO_E_FILEIO;
        }

        if (ElfIo_CheckHostEndianess()!=str->encoding) {
            ELF_SH_NAME(buf)        = ElfIo_Convert32U(ELF_SH_NAME(buf));
            ELF_SH_TYPE(buf)        = ElfIo_Convert32U(ELF_SH_TYPE(buf));
            ELF_SH_FLAGS(buf)       = ElfIo_Convert32U(ELF_SH_FLAGS(buf));
            ELF_SH_ADDR(buf)        = ElfIo_Convert32U(ELF_SH_ADDR(buf));
            ELF_SH_OFFSET(buf)      = ElfIo_Convert32U(ELF_SH_OFFSET(buf));
            ELF_SH_SIZE(buf)        = ElfIo_Convert32U(ELF_SH_SIZE(buf));
            ELF_SH_LINK(buf)        = ElfIo_Convert32U(ELF_SH_LINK(buf));
            ELF_SH_INFO(buf)        = ElfIo_Convert32U(ELF_SH_INFO(buf));
            ELF_SH_ADDRALIGN(buf)   = ElfIo_Convert32U(ELF_SH_ADDRALIGN(buf));
            ELF_SH_ENTSIZE(buf)     = ElfIo_Convert32U(ELF_SH_ENTSIZE(buf));
        }
        num++;
    }
   
    return ELFIO_E_OK;
}


ElfIo_StatusType ElfIo_ReadSections(ElfIo_Struct const * str)
{
    Elf32_Half num;
    Elf32_Half num_entries;    
    Elf32_Shdr *section;
    int res;

    num=0;
    num_entries=ELF_SHNUM(str->header);

    while (num<num_entries) {
        section=ElfIO_GetSectionHeader(str,num);
        if ((section->sh_type!=SHT_NOBITS) && (section->sh_size>0)) {
            str->sections[num].data=(uint8_t *)malloc(section->sh_size);
            assert(str->sections[num].data!=(uint8_t *)NULL);
            str->sections[num].length=section->sh_size;
            memset(str->sections[num].data,'\0',section->sh_size);            
            res=fseek(str->stream,section->sh_offset,SEEK_SET);
            if (res!=0) {
                    return ELFIO_E_FILEIO;
            }
            res=fread((void*)str->sections[num].data,section->sh_size,1,str->stream);                        
            if (res==0) {
                return ELFIO_E_FILEIO;
            }
            
        }
        num++;
    }

    return ELFIO_E_OK;
}


Elf32_Shdr * ElfIO_GetSectionHeader(ElfIo_Struct const * str,Elf32_Word idx)
{		
    return (Elf32_Shdr*)&str->section_headers[idx];
}


MemorySection * ElfIO_GetSection(ElfIo_Struct const * str,Elf32_Word idx)
{
    return (MemorySection * )&str->sections[idx];
}


void ElfIo_ExitUnimplemented(char * const feature)
{
    fprintf(stderr,"I'm sorry, but '%s' is not implemented.\n",feature);

    exit(2);
}


void ElfIo_ExitError(char *msg,...)
{
    va_list ap;

    va_start(ap,msg);
    vfprintf(stderr,msg,ap);
    va_end(ap);
    exit(1);
}
