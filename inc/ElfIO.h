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
#if !defined(__ELFIO_H)
#define __ELFIO_H

#include <stdio.h>
#include "config.h"
#include "Elf.h"
#include "MemSect.h"
#include "Utl.h"

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
    Utl_EndianessType encoding;
} ElfIo_Struct;


#define ELFIO_WEAK_PARAM_CHECK(pstr)	(assert((pstr)->guard==sizeof(ElfIo_Struct)))

ElfIo_StatusType ElfIo_Init(ElfIo_Struct *str,char * const file_name,ElfIo_Mode mode);
ElfIo_StatusType ElfIo_Deinit(ElfIo_Struct *str);

ElfIo_StatusType ElfIo_ReadProgramTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_ReadSectionHeaderTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_ReadSections(ElfIo_Struct const * str);

Elf32_Shdr * ElfIO_GetSectionHeader(ElfIo_Struct const * str,Elf32_Word idx);
MemorySection * ElfIO_GetSection(ElfIo_Struct const * str,Elf32_Word idx);
const Elf32_Sym ElfIO_GetSymbol(ElfIo_Struct const * str,Elf32_Word section,Elf32_Word idx);

void ElfIo_ExitUnimplemented(char * const feature);
void ElfIo_ExitError(char *s, ...);

#endif /* __ELFIO_H */

