/*
 * k_dk - Driver Kit for k_os (Konnex Operating-System based on the
 * OSEK/VDX-Standard).
 *
 * (C) 2007-2010 by Christoph Schueler <github.com/Christoph2,
 *                                      cpu12.gems@googlemail.com>
 *
 * All Rights Reserved
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */
#include "ElfIO.h"

#include <assert.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>


#define STRNCPY strncpy
#define STRNCAT strncat

/*
**	todo: Variant using Memory-Mapped-Files.
*/

static uint16_t ElfIo_Convert16U(uint16_t w);
static uint32_t ElfIo_Convert32U(uint32_t dw);
static int32_t ElfIo_Convert32S(int32_t dw);


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
                    str->encoding=UTL_LITTLE_ENDIAN;
					break;
                case ELFDATA2MSB:
                    str->encoding=UTL_BIG_ENDIAN;                    
					break;
                default:
                    str->encoding=UTL_INVALID_ENCODING;
                    return ELFIO_E_INVALID;
            }

            if (Utl_CheckHostEndianess()!=str->encoding) {
                /* Adjust Endianess. */
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


ElfIo_StatusType ElfIo_ReadProgramTable(ElfIo_Struct const * str)
{
    Elf32_Off hdr_offs;
    Elf32_Half num;
    Elf32_Half num_entries;
    Elf32_Phdr *header;
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
        header=str->program_headers+num;
        res=fread((void*)header,sizeof(Elf32_Phdr),1,str->stream);
        if (res==0) {
            return ELFIO_E_FILEIO;
        }

        if (Utl_CheckHostEndianess()!=str->encoding) {
            /* Adjust Endianess. */
            ELF_PH_TYPE(header)   = ElfIo_Convert32U(ELF_PH_TYPE(header));
            ELF_PH_OFFSET(header) = ElfIo_Convert32U(ELF_PH_OFFSET(header));
            ELF_PH_VADDR(header)  = ElfIo_Convert32U(ELF_PH_VADDR(header));
            ELF_PH_PADDR(header)  = ElfIo_Convert32U(ELF_PH_PADDR(header));
            ELF_PH_FILESZ(header) = ElfIo_Convert32U(ELF_PH_FILESZ(header));
            ELF_PH_MEMSZ(header)  = ElfIo_Convert32U(ELF_PH_MEMSZ(header));
            ELF_PH_FLAGS(header)  = ElfIo_Convert32U(ELF_PH_FLAGS(header));
            ELF_PH_ALIGN(header)  = ElfIo_Convert32U(ELF_PH_ALIGN(header));
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
    Elf32_Shdr *section_header;
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
        section_header=str->section_headers+num;
        res=fread((void*)section_header,sizeof(Elf32_Shdr),1,str->stream);
        if (res==0) {
            return ELFIO_E_FILEIO;
        }

        if (Utl_CheckHostEndianess()!=str->encoding) {
            /* Adjust Endianess. */
            ELF_SH_NAME(section_header)        = ElfIo_Convert32U(ELF_SH_NAME(section_header));
            ELF_SH_TYPE(section_header)        = ElfIo_Convert32U(ELF_SH_TYPE(section_header));
            ELF_SH_FLAGS(section_header)       = ElfIo_Convert32U(ELF_SH_FLAGS(section_header));
            ELF_SH_ADDR(section_header)        = ElfIo_Convert32U(ELF_SH_ADDR(section_header));
            ELF_SH_OFFSET(section_header)      = ElfIo_Convert32U(ELF_SH_OFFSET(section_header));
            ELF_SH_SIZE(section_header)        = ElfIo_Convert32U(ELF_SH_SIZE(section_header));
            ELF_SH_LINK(section_header)        = ElfIo_Convert32U(ELF_SH_LINK(section_header));
            ELF_SH_INFO(section_header)        = ElfIo_Convert32U(ELF_SH_INFO(section_header));
            ELF_SH_ADDRALIGN(section_header)   = ElfIo_Convert32U(ELF_SH_ADDRALIGN(section_header));
            ELF_SH_ENTSIZE(section_header)     = ElfIo_Convert32U(ELF_SH_ENTSIZE(section_header));
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


const Elf32_Sym ElfIO_GetSymbol(ElfIo_Struct const * str,Elf32_Word section,Elf32_Word idx)
{
    /* todo: Range check!!! */    
//    Elf32_Sym *symtab;
    Elf32_Sym sym;

    sym=((Elf32_Sym *)ElfIO_GetSection(str,section)->data)[idx];

    if (Utl_CheckHostEndianess()!=str->encoding) {    // todo: Endianess der Symbole konvertieren!!!
        sym.st_name=ElfIo_Convert32U(sym.st_name);
        sym.st_value=ElfIo_Convert32U(sym.st_value);
        sym.st_size=ElfIo_Convert32U(sym.st_size);
        sym.st_shndx=ElfIo_Convert32U(sym.st_shndx);
    }

    return sym;
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
