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
#if !defined(__STD_TYPES_H)
#define __STD_TYPES_H


#if defined(__STDC__) && defined(__STDC_VERSION__)
#if __STDC_VERSION__>=199901L
        #define C99_COMPILER
#endif
#endif


#if defined(C99_COMPILER)

#include <stdint.h>
#include <stdbool.h>

#elif defined(__cplusplus)

#include <stdint>
#include <stdbool>

#else
/*
** todo: other Platforms then Intel-32 !!!
*/
typedef unsigned char       bool;
typedef signed char         int8_t;
typedef unsigned char       uint8_t;
typedef signed short        int16_t;
typedef unsigned short      uint16_t;
typedef signed long         int32_t;
typedef unsigned long       uint32_t;

typedef signed char         int_least8_t;
typedef unsigned char       uint_least8_t;
typedef signed short        int_least16_t;
typedef unsigned short      uint_least16_t;
typedef signed long         int_least32_t;
typedef unsigned long       uint_least32_t;

/*
typedef signed char         int_fast8_t;
typedef unsigned char       uint_fast8_t;
typedef signed short        int_fast16_t;
typedef unsigned short      uint_fast16_t;
typedef signed long         int_fast32_t;
typedef unsigned long       uint_fast32_t;
*/

#define true                ((bool)1)
#define false               ((bool)0)

#endif

#define LOBYTE(w)           ((uint8_t)((uint16_t)((uint16_t)(w) & 0x00ffU)))
#define HIBYTE(w)           ((uint8_t)((uint16_t)(((uint16_t)(w )>> 8) & 0x00ffU)))

#define LOWORD(dw)          ((uint16_t)((uint32_t)((uint32_t)(dw) & 0xffffU)))
#define HIWORD(dw)          ((uint16_t)((uint32_t)(((uint32_t)(dw) >> 16) & 0xffffU)))

#define MAKEWORD(h,l)       (((h) & ((uint8_t)0xff)) << 8 | ((l) & ((uint8_t)0xff)))
#define MAKEDWORD(h,l)      (((h) & ((uint16_t)0xffffu)) << 16 | ((l) & ((uint16_t)0xffffu)))

#define SWAP_VALUES(lhs,rhs)    \
    do {                        \
        (lhs)^=(rhs);           \
        (rhs)^=(lhs);           \
        (lhs)^=(rhs);           \
    } while(0)

#define SIZEOF_ARRAY(arr)   ((sizeof((arr))) / (sizeof((arr[0]))))
#define BEYOND_ARRAY(arr)   ((arr) + SIZE_OF_ARRAY((arr)))
#define FOREVER             while(TRUE)

#define UNREFERENCED_PARAMETER(p)   ((p)=(p))

#define NOT_ADDRESSABLE register

#define TO_STRING_2(s)  #s
#define TO_STRING(s)    TO_STRING_2(s)

#define GLUE2_2(a,b)    a ## b
#define GLUE2(a,b)      GLUE2_2(a,b)

#define GLUE3_2(a,b,c)  a ## b ## c
#define GLUE3(a,b,c)    GLUE3_2(a,b,c)


/* Static  (compile time) Assertion. */
#if defined(_C1x_COMPILER)
#define STATIC_ASSERT(cond,msg) _Static_assert((cond),(msg))
#else
#define STATIC_ASSERT(cond,msg)                 \
struct  GLUE2(__NEVER_USED_BY_ISO_C_,__LINE__){ \
    int x[(cond) ? 1 : -1];                     \
} 
#endif

#endif /*__STD_TYPES_H */

