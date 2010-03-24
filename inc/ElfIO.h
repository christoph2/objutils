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
#if !defined(__ELFIO_H)
#define __ELFIO_H

#include <stdio.h>
#include "config.h"
#include "Elf.h"
#include "MemSect.h"

#define ELFIO_MAX_FILENAME_LEN	((uint8_t)0xff)

typedef enum tagElfIo_StatusType {
    ELFIO_E_OK,
    ELFIO_E_FILEIO,
    ELFIO_E_INVALID,
    ELFIO_E_STATE,
    ELFIO_E_VALUE,
    ELFIO_E_LIMIT
} ElfIo_StatusType;

typedef enum tagElfIo_Mode {
    ELFIO_INVALID_MODE,
    ELFIO_READ,
    ELFIO_WRITE
} ElfIo_Mode;

typedef struct tagElfIo_Struct {
    FILE * stream;
    char const * file_name;
    bool file_opened;
    ElfIo_Mode mode;
    Elf32_Ehdr * header;
    Elf32_Phdr * program_headers;
    Elf32_Shdr * section_headers;
    MemorySection *sections;
    uint8_t guard;
    Elf_EndianessType encoding;
} ElfIo_Struct;


#define ELFIO_WEAK_PARAM_CHECK(pstr)	(assert((pstr)->guard==sizeof(ElfIo_Struct)))

Elf_EndianessType ElfIo_CheckHostEndianess(void);

ElfIo_StatusType ElfIo_Init(ElfIo_Struct *str,char * const file_name,ElfIo_Mode mode);
ElfIo_StatusType ElfIo_Deinit(ElfIo_Struct *str);

ElfIo_StatusType ElfIo_ReadProgramTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_ReadSectionHeaderTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_ReadSections(ElfIo_Struct const * str);

Elf32_Shdr * ElfIO_GetSectionHeader(ElfIo_Struct const * str,Elf32_Word idx);
MemorySection * ElfIO_GetSection(ElfIo_Struct const * str,Elf32_Word idx);
const Elf32_Sym ElfIO_GetSymbol(ElfIo_Struct const * str,Elf32_Word section,Elf32_Word idx);

char const * ElfIo_GetMachineName(ElfIo_Struct const * str);

void ElfIo_ExitUnimplemented(char * const feature);
void ElfIo_ExitError(char *s, ...);

#endif /* __ELFIO_H */
