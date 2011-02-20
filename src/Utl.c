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
#include "utl.h"
#include <string.h>

static const uint16_t PowerOfTwoTab16[16]={
    (uint16_t)0x0001,(uint16_t)0x0002,(uint16_t)0x0004,(uint16_t)0x0008,
    (uint16_t)0x0010,(uint16_t)0x0020,(uint16_t)0x0040,(uint16_t)0x0080,
    (uint16_t)0x0100,(uint16_t)0x0200,(uint16_t)0x0400,(uint16_t)0x0800,
    (uint16_t)0x1000,(uint16_t)0x2000,(uint16_t)0x4000,(uint16_t)0x8000
};


bool Utl_BitGet(uint16_t w,uint8_t num)
{
    return ((w & PowerOfTwoTab16[num])!=(uint16_t)0x0000);
}


uint16_t Utl_BitSet(uint16_t w,uint8_t num)
{
    return w|=PowerOfTwoTab16[num];
}


uint16_t Utl_BitReset(uint16_t w,uint8_t num)
{
    return w&=~(PowerOfTwoTab16[num]);
}


uint16_t Utl_BitToggle(uint16_t w,uint8_t num)
{
    return w^=PowerOfTwoTab16[num];
}


uint16_t Utl_BitGetHighest(uint16_t w)
{
    w|=w>>1;
    w|=w>>2;
    w|=w>>4;
    w|=w>>8;
    return w^(w>>1);
}


uint16_t Utl_BitGetLowest(uint16_t w)
{
    return (~w+1) & w;
}


uint16_t Utl_BitSetLowest(uint16_t w)
{
    return w | (w+1);
}


uint16_t Utl_BitResetLowest(uint16_t w)
{
    return w & (w-1);
}


uint8_t Utl_Log2(uint16_t num)
{
    uint8_t res=0;
    
    while (num>>=1) {
        res++;
    }

    return res;
}


Utl_EndianessType Utl_CheckHostEndianess(void)
{
    const uint16_t foo=0xaa55;
    uint8_t *ptr=(uint8_t*)&foo;
    
    if (0[ptr]==0xaa) {
        return UTL_BIG_ENDIAN;   
    } else {
        return UTL_LITTLE_ENDIAN;
    }
}

void sec_strcpy(char * dest,char const * src,size_t len)
{
    strncpy(dest,src,len);
//    strncpy_s(dest,len,src,len);
//    strcpy(file_name,argv[1]);
}
