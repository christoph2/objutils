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
#if !defined(__UTL_H)
#define __UTL_H

#include "StdTypes.h"

#ifdef __cplusplus
extern "C"
{
#endif  /* __cplusplus */

typedef enum tagUtl_EndianessType {
	UTL_INVALID_ENCODING,
    UTL_BIG_ENDIAN,
    UTL_LITTLE_ENDIAN
} Utl_EndianessType;

Utl_EndianessType Utl_CheckHostEndianess(void);

bool Utl_BitGet(uint16_t w,uint8_t num);
uint16_t Utl_BitSet(uint16_t w,uint8_t num);
uint16_t Utl_BitReset(uint16_t w,uint8_t num);
uint16_t Utl_BitToggle(uint16_t w,uint8_t num);
uint16_t Utl_BitGetHighest(uint16_t w);
uint16_t Utl_BitGetLowest(uint16_t w);
uint16_t Utl_BitSetLowest(uint16_t w);
uint16_t Utl_BitResetLowest(uint16_t w);
uint8_t Utl_Log2(uint16_t num);

#ifdef __cplusplus
}
#endif  /* __cplusplus */

#endif  /* __UTL_H */
