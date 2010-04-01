/*
 * Copyright (c)2007- 2009 Christoph Schueler (chris@konnex-tools.de).
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