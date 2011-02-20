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
#if !defined(__S19IO_H)
#define __S19IO_H

#include "TextFile.h"

typedef enum tagS19Io_StatusType {
    S19IO_E_OK,
    S19IO_E_FILEIO,
    S19IO_E_INVALID,
    S19IO_E_STATE,
    S19IO_E_VALUE,
    S19IO_E_LIMIT
} S19Io_StatusType;

typedef enum tagS19Io_Mode {
    S19IO_INVALID_MODE,
    S19IO_READ,
    S19IO_WRITE
} S19Io_Mode;

typedef struct tagS19Io_Struct {
    FILE * stream;
    char const * file_name;
    bool file_opened;
    uint8_t guard;
    S19Io_Mode mode;
} S19Io_Struct;

S19Io_StatusType S19Io_Init(S19Io_Struct * str,char * const file_name,S19Io_Mode mode);
bool S19Io_LineScanning(char const * line,TxtIo_LineInfoType *info);

#if 0
ElfIo_StatusType ElfIo_Deinit(S19Io_Struct *str);
#endif

#endif /* __S19IO_H */

