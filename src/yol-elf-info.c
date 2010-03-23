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
#include <stdlib.h>
#include <string.h>

#include "ElfIO.h"
#include "ElfInfo.h"
#include "MemSect.h"

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
    ElfIo_StatusType res;
    ElfIo_Struct str;
    char file_name[256];

    if (argc!=2) {
	    return 0;
    }

    strcpy(file_name,argv[1]);

    res=ElfIo_Init(&str,file_name,ELFIO_READ);

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

    (void)ElfIo_Deinit(&str);

    return EXIT_SUCCESS;
}

void usage(void)
{
    exit(EXIT_SUCCESS);
}

