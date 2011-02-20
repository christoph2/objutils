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
#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "ElfIO.h"
#include "ElfInfo.h"
#include "MemSect.h"
#include "S19Io.h"

/*
**
**  pxc-read-elf
**  ============
**  - Shows infos about ELF-Files.
**  - Study this file for usage of 'pxc-elfio'-Lib.
**
*/

bool verbose=true;

void usage(void);

int main(int argc,char **argv)
{
    /*
    ElfIo_StatusType res;
    ElfIo_Struct str;
    */
    TxtIo_StatusType res;
    TxtIo_Struct str;
    char file_name[256];

    if (argc!=2) {
	    return 0;
    }

    strcpy(file_name,argv[1]);

    res=TxtIo_Init(&str,file_name,TXTIO_READ);
    res=TxtIo_ScanFile(&str,S19Io_LineScanning);

/*    res=ElfIo_Init(&str,file_name,ELFIO_READ);    */

    switch (res) {
    	case ELFIO_E_OK:
	    	break;
	    case ELFIO_E_FILEIO:
	        /* you can check 'errno', or so. */
	        ElfIo_ExitError("\aERROR: I/O-Problems, like file not found.\n");
	    case ELFIO_E_INVALID:
	        ElfIo_ExitError("\aERROR: Invalid ELF-Magic.\n");
	    case ELFIO_E_STATE:
	        ElfIo_ExitError("\aERROR: ELF-Structure already initialized.\n");
	    case ELFIO_E_VALUE:
	        ElfIo_ExitError("\aERROR: Mode must be 'ELFIO_READ' or 'ELFIO_WRITE'.\n");
	    case ELFIO_E_LIMIT:
	        ElfIo_ExitError("\aERROR: Sorry, the length of your filename exceeds the limit of %u.\n",ELFIO_MAX_FILENAME_LEN);
	    default:
	        assert(false);
    }

    /* Reached only if OK. */

    (void)ElfInfo_PrintHeader(&str);

    (void)ElfIo_ReadProgramTable(&str);
    (void)ElfIo_ReadSectionHeaderTable(&str);
    (void)ElfIo_ReadSections(&str);
    (void)ElfInfo_PrintProgramTable(&str);
    (void)ElfIo_PrintSectionHeaderTable(&str);
    (void)ElfIo_PrintSymbols(&str);
	(void)ElfIo_PrintNotes(&str);

    (void)ElfIo_Deinit(&str);

    return EXIT_SUCCESS;
}

void usage(void)
{
    exit(EXIT_SUCCESS);
}

