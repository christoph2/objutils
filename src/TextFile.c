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
#include "TextFile.h"

#define TXTIO_MAX_FILENAME_LEN  ((uint8_t)0xff)
#define TXTIO_MAX_LINE_LEN      (1024)

#if 0
"C:\\projekte\\csProjects\\yOBJl\\2CB_12.s19"
#endif



/*
** Scan file contents and construct contingues (if possible) memory blocks.
*/

TxtIo_StatusType TxtIo_Init(TxtIo_Struct *str,char * const file_name,TxtIo_Mode mode)
{
    size_t len;
    int error=0;

    assert(file_name!=(char * const)NULL);

    if ((str->guard==sizeof(TxtIo_Struct)) && (str->file_opened==true)) {
        return TXTIO_E_STATE;
    }    

    if (!((mode==TXTIO_READ) || (mode==TXTIO_WRITE))) {
        return TXTIO_E_VALUE;
    }

    if ((len=strlen(file_name))>TXTIO_MAX_FILENAME_LEN) {
        return TXTIO_E_LIMIT;
    }    

    str->file_opened=false;
    str->guard=sizeof(TxtIo_Struct);
    str->mode=mode;    

    /* todo: als generelle File-I/O-Operationen kapseln!!! */
#if defined(TXTIO_HAS_FOPEN_S)
    if ((error=fopen_s(&str->stream,file_name,(mode==TXTIO_READ) ? "rt" : "wt"  )) !=0 ) {
        return TXTIO_E_FILEIO;
    } else {
        str->file_opened=true;
    }
#else
    UNREFERENCED_PARAMETER(error);

    str->stream=fopen(file_name,(mode==TXTIO_READ) ? "rt" : "wt");

    if (str->stream==(FILE*)NULL) {
        return TXTIO_E_FILEIO;
    } else {
        str->file_opened=true;      
    }
#endif

    str->file_name=(char const *)malloc(len+1);
    assert(str->file_name!=(char const *)NULL);
    strncpy((char*)str->file_name,file_name,len);   /* STRNCPY((char*)str->file_name,file_name,len); */

    return TXTIO_E_OK;
}

#if 0
Textfile-Paramter
=================

char StartChar;
char Type[2];
char addressLen;


#endif

TxtIo_StatusType TxtIo_ScanFile(TxtIo_Struct const * str,bool (*callout)(char const * line,TxtIo_LineInfoType *info))
{
    static char buf[TXTIO_MAX_LINE_LEN+1];
    uint32_t lineCount=0UL;
    TxtIo_LineInfoType lineInfo;
    
    assert(str->file_opened==true);
    assert(str->mode==TXTIO_READ);
    assert(callout!=NULL);

    fseek(str->stream,0,SEEK_SET);
    while (!feof(str->stream)) {
        fgets(buf,TXTIO_MAX_LINE_LEN,str->stream);
        lineInfo.length=0U;
        lineInfo.startAddress=0UL;

        (callout)(buf,&lineInfo);
//        assert((lineInfo.length!=0U) && (lineInfo.startAddress!=0UL));
        lineCount++;
    }
    return TXTIO_E_OK;
}

static void TxtIo_ReadLine()
{

}
