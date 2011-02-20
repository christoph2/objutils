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
#if !defined(__ELF_INFO_H)
#define __ELF_INFO_H

#include "ElfIO.h"

ElfIo_StatusType ElfInfo_PrintHeader(ElfIo_Struct const * str);
char const * ElfInfo_GetMachineName(ElfIo_Struct const * str);
ElfIo_StatusType ElfInfo_PrintProgramTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_PrintSectionHeaderTable(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_PrintSymbols(ElfIo_Struct const * str);
ElfIo_StatusType ElfIo_PrintNotes(ElfIo_Struct const * str);

#endif /* __ELF_INFO_H */

