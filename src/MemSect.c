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
#include "MemSect.h"

#include <memory.h>
#include <stdlib.h>

MemorySection * MemorySection_Init(uint32_t length)
{
    MemorySection * ms;

    ms=malloc(sizeof(MemorySection));
    if (ms==NULL) {
        return (MemorySection * const )NULL;
    }

    memset(ms,'\0',sizeof(MemorySection));
    ms->data=malloc(length);

    if (ms->data==NULL) {
        return (MemorySection * const )NULL;
    }
    memset(ms->data,'\0',length);
    ms->length=length;

    return ms;
}

void MemorySection_Deinit(MemorySection * ms)
{
    if (ms->data) {
        free(ms->data);
        ms->data=(uint8_t*)NULL;
    }
    if (ms) {
        free(ms);
        ms=(MemorySection *)NULL;
    }
}
