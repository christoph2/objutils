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
#include "S19IO.h"

#define S19IO_MAX_FILENAME_LEN  ((uint8_t)0xff)

static uint8_t S19IO_CalculateChecksum(uint8_t const * const data,uint8_t len);

static uint8_t S19IO_CalculateChecksum(uint8_t const * const data,uint8_t len)
{
    uint8_t idx;
    uint8_t sum;

    for (idx=(uint8_t)0x00,sum=(uint8_t)0x00;idx<len;++idx) {
	sum+=data[idx];
    }

    return sum;
}


S19Io_StatusType S19Io_Init(S19Io_Struct *str,char * const file_name,S19Io_Mode mode)
{
    size_t len;
    int error=0;

    assert(file_name!=(char * const)NULL);

    if ((str->guard==sizeof(S19Io_Struct)) && (str->file_opened==true)) {
        return S19IO_E_STATE;
    }    

    if (!((mode==S19IO_READ) || (mode==S19IO_WRITE))) {
        return S19IO_E_VALUE;
    }

    if ((len=strlen(file_name))>S19IO_MAX_FILENAME_LEN) {
        return S19IO_E_LIMIT;
    }    

    str->file_opened=false;
    str->guard=sizeof(S19Io_Struct);
    str->mode=mode;    

    /* todo: als generelle File-I/O-Operationen kapseln!!! */
#if defined(S19IO_HAS_FOPEN_S)
    if ((error=fopen_s(&str->stream,file_name,(mode==S19IO_READ) ? "rt" : "wt"  )) !=0 ) {
        return S19IO_E_FILEIO;
    } else {
        str->file_opened=true;
    }
#else
    UNREFERENCED_PARAMETER(error);

    str->stream=fopen(file_name,(mode==S19IO_READ) ? "rt" : "wt");

    if (str->stream==(FILE*)NULL) {
        return S19IO_E_FILEIO;
    } else {
        str->file_opened=true;      
    }
#endif

    str->file_name=(char const *)malloc(len+1);
    assert(str->file_name!=(char const *)NULL);
    strncpy((char*)str->file_name,file_name,len);   /* STRNCPY((char*)str->file_name,file_name,len); */

    return S19IO_E_OK;
}


typedef enum tagS19Io_LineScanningStateType {
    START,
    READ_LINE,
    FINISHED
} S19Io_LineScanningStateType;

typedef enum tagS19Io_RecordType {
    S1,
    S2,
    S3,
    S5,
    S9,
    S8,
    S7
} S19Io_RecordType;


#define START_SYMBOL    ("S")

// Hinweis: S-REC ist generell BigEndian!!!

bool S19Io_LineScanning(char const * line,TxtIo_LineInfoType *info) /* todo: Einheitliche Fkt., die optional Daten zurückliefert.*/
{
    static S19Io_LineScanningStateType state=START;
    uint8_t type;
    uint32_t address;
    static uint32_t lineNumber=0x00000000UL;
    /* todo: statische Variable für den Typen: S9/8/7... */

    lineNumber++;

    if (strncmp(line,START_SYMBOL,strlen(START_SYMBOL))!=0) {
        return false;
    }

    type=line[1]-'0';

    switch (state) {
        case START:
            state=READ_LINE;
            break;
        case READ_LINE:
            switch (type) {
                case 0x01:
                    break;
                case 0x02:
                    break;
                case 0x03:
                    break;
                default:
                    fprintf("[%04X]: Unexpected Recordtype: '%u'.",lineNumber,type);
                    return false;
            }
            break;
        case FINISHED:
            break;
    }

    return true;
}
/*
                                        Motorola S-record description (p1 of 3)

                              Motorola S-records

   The following fairly complete description of Motorola S-records was
   found a number of years ago on the man pages of a UNIX system.
     _________________________________________________________________

   NAME

     srec - S-record file and record format

   DESCRIPTION

     An S-record file consists of a sequence of specially formatted
     ASCII character strings. An S-record will be less than or equal to
     78 bytes in length.

     The order of S-records within a file is of no significance and no
     particular order may be assumed.

     The general format of an S-record follows:

+-------------------//------------------//-----------------------+
| type | count | address  |            data           | checksum |
+-------------------//------------------//-----------------------+

     type -- A char[2] field. These characters describe the type of
     record (S0, S1, S2, S3, S5, S7, S8, or S9).

     count -- A char[2] field. These characters when paired and
     interpreted as a hexadecimal value, display the count of remaining
     character pairs in the record.

     address -- A char[4,6, or 8] field. These characters grouped and
     interpreted as a hexadecimal value, display the address at which
     the data field is to be loaded into memory. The length of the field
     depends on the number of bytes necessary to hold the address. A
     2-byte address uses 4 characters, a 3-byte address uses 6
     characters, and a 4-byte address uses 8 characters.

     data -- A char [0-64] field. These characters when paired and
     interpreted as hexadecimal values represent the memory loadable
     data or descriptive information.

     checksum -- A char[2] field. These characters when paired and
     interpreted as a hexadecimal value display the least significant
     byte of the ones complement of the sum of the byte values
     represented by the pairs of characters making up the count, the
     address, and the data fields.

     Each record is terminated with a line feed. If any additional or
     different record terminator(s) or delay characters are needed
     during transmission to the target system it is the responsibility
     of the transmitting program to provide them.

     S0 Record. The type of record is 'S0' (0x5330). The address field
     is unused and will be filled with zeros (0x0000). The header
     information within the data field is divided into the following
     subfields.

     mname is char[20] and is the module name.
     ver is char[2] and is the version number.
                                        Motorola S-record description (p2 of 3)
     rev is char[2] and is the revision number.
     description is char[0-36] and is a text comment.

     Each of the subfields is composed of ASCII bytes whose associated
     characters, when paired, represent one byte hexadecimal values in
     the case of the version and revision numbers, or represent the
     hexadecimal values of the ASCII characters comprising the module
     name and description.

     S1 Record. The type of record field is 'S1' (0x5331). The address
     field is intrepreted as a 2-byte address. The data field is
     composed of memory loadable data.

     S2 Record. The type of record field is 'S2' (0x5332). The address
     field is intrepreted as a 3-byte address. The data field is
     composed of memory loadable data.

     S3 Record. The type of record field is 'S3' (0x5333). The address
     field is intrepreted as a 4-byte address. The data field is
     composed of memory loadable data.

     S5 Record. The type of record field is 'S5' (0x5335). The address
     field is intrepreted as a 2-byte value and contains the count of
     S1, S2, and S3 records previously transmitted. There is no data
     field.

     S7 Record. The type of record field is 'S7' (0x5337). The address
     field contains the starting execution address and is intrepreted as
     4-byte address. There is no data field.

     S8 Record. The type of record field is 'S8' (0x5338). The address
     field contains the starting execution address and is intrepreted as
     3-byte address. There is no data field.

     S9 Record. The type of record field is 'S9' (0x5339). The address
     field contains the starting execution address and is intrepreted as
     2-byte address. There is no data field.

   EXAMPLE

     Shown below is a typical S-record format file.

     S00600004844521B
     S1130000285F245F2212226A000424290008237C2A
     S11300100002000800082629001853812341001813
     S113002041E900084E42234300182342000824A952
     S107003000144ED492
     S5030004F8
     S9030000FC

     The file consists of one S0 record, four S1 records, one S5 record
     and an S9 record.

     The S0 record is comprised as follows:
     * S0 S-record type S0, indicating it is a header record.
     * 06 Hexadecimal 06 (decimal 6), indicating that six character pairs
       (or ASCII bytes) follow.
     * 00 00 Four character 2-byte address field, zeroes in this example.
     * 48 44 52 ASCII H, D, and R - "HDR".
     * 1B The checksum.

     The first S1 record is comprised as follows:
                                        Motorola S-record description (p3 of 3)
     * S1 S-record type S1, indicating it is a data record to be loaded
       at a 2-byte address.
     * 13 Hexadecimal 13 (decimal 19), indicating that nineteen character
       pairs, representing a 2 byte address, 16 bytes of binary data, and
       a 1 byte checksum, follow.
     * 00 00 Four character 2-byte address field; hexidecimal address
       0x0000, where the data which follows is to be loaded.
     * 28 5F 24 5F 22 12 22 6A 00 04 24 29 00 08 23 7C Sixteen character
       pairs representing the actual binary data.
     * 2A The checksum.

     The second and third S1 records each contain 0x13 (19) character
     pairs and are ended with checksums of 13 and 52, respectively. The
     fourth S1 record contains 07 character pairs and has a checksum of
     92.

     The S5 record is comprised as follows:
     * S5 S-record type S5, indicating it is a count record indicating
       the number of S1 records
     * 03 Hexadecimal 03 (decimal 3), indicating that three character
       pairs follow.
     * 00 04 Hexadecimal 0004 (decimal 4), indicating that there are four
       data records previous to this record.
     * F8 The checksum.

     The S9 record is comprised as follows:
     * S9 S-record type S9, indicating it is a termination record.
     * 03 Hexadecimal 03 (decimal 3), indicating that three character
       pairs follow.
     * 00 00 The address field, hexadecimal 0 (decimal 0) indicating the
       starting execution address.
     * FC The checksum.
     _________________________________________________________________

Instructor Notes

     * There isn't any evidence that Motorola ever has made use of the
       header information within the data field of the S0 record, as
       described above. This must have been used by some third party
       vendors.
     * This is the only place that a 78-byte limit on total record length
       or 64-byte limit on data length is documented. These values
       shouldn't be trusted for the general case.
     * The count field can have values in the range of 0x3 (2 bytes of
       address + 1 byte checksum = 3, a not very useful record) to 0xff;
       this is the count of remaining character pairs, including
       checksum.
     * If you write code to convert S-Records, you should always assume
       that a record can be as long as 514 (decimal) characters in length
       (255 * 2 = 510, plus 4 characters for the type and count fields),
       plus any terminating character(s). That is, in establishing an
       input buffer in C, you would declare it to be an array of 515
       chars, thus leaving room for the terminating null character.
     _________________________________________________________________

*/