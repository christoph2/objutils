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
#if !defined(__TEXTFILE_H)
#define __TEXTFILE_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "MemSect.h"
#include "Utl.h"

typedef enum tagTxtIo_StatusType {
    TXTIO_E_OK,
    TXTIO_E_FILEIO,
    TXTIO_E_INVALID,
    TXTIO_E_STATE,
    TXTIO_E_VALUE,
    TXTIO_E_LIMIT
} TxtIo_StatusType;

typedef enum tagTxtIo_Mode {
    TXTIO_INVALID_MODE,
    TXTIO_READ,
    TXTIO_WRITE
} TxtIo_Mode;

typedef struct tagTxtIo_Struct {
    FILE * stream;
    char const * file_name;
    bool file_opened;
    uint8_t guard;
    TxtIo_Mode mode;
} TxtIo_Struct;

typedef struct tagTxtIo_LineInfoType {
    uint32_t startAddress;
    uint16_t length;
    // todo: void *specialData + kind.
} TxtIo_LineInfoType;

typedef bool (*LineScanningCallout)(char const * line,TxtIo_LineInfoType *info);

TxtIo_StatusType TxtIo_Init(TxtIo_Struct * str,char * const file_name,TxtIo_Mode mode);
TxtIo_StatusType TxtIo_ScanFile(TxtIo_Struct const * str,bool (*callout)(char const * line,TxtIo_LineInfoType *info));


#endif /* __TEXTFILE_H */
