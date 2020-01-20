#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import enum
import operator
import functools
import struct
import zlib

COMPLEMENT_NONE = 0
COMPLEMENT_ONES = 1
COMPLEMENT_TWOS = 2

def lrc(data, width, comp = COMPLEMENT_NONE):
    """Longitudinal redundancy check.
    """

    mask = (2 ** width)

    cs = sum(data) % mask

    if comp == COMPLEMENT_NONE:
        pass
    elif comp == COMPLEMENT_ONES:
        cs ^= (mask - 1)
    elif comp == COMPLEMENT_TWOS:
        cs = ((cs ^ (mask - 1)) + 1) % mask

    return cs


def rolb(value):
    """Rotate byte left.
    """
    value &= 0xff
    carry = (value & 0x80) == 0x80
    value = (value << 1) & 0xff
    value |= 1 if carry else 0
    return value

def rorb(value):
    """Rotate byte right.
    """
    value &= 0xff
    carry = (value & 0x01) == 0x01
    value = value >> 1
    value |= 0x80 if carry else 0
    return value

def xor(frame, invert = True):
    return functools.reduce(operator.xor, frame, 0xff if invert else 0x00)

ROTATE_LEFT = rolb
ROTATE_RIGHT = rorb

def rotatedXOR(values, width, rotator):
    """Rotated XOR cipher.
    """
    cs = 0
    for value in values:
        cs ^= value
        cs = rotator(cs)
    return cs  % (2 ** width)

def nibble_sum(data):
    result = 0
    for d in data:
        hn = (d & 0xf0) >> 4
        ln = d & 0x0f
        result +=  hn + ln
    return result % 256

##
##
##
class Algorithm(enum.IntEnum):
    """Enumerates available checksum algorithms
    """
    CHK_ADD_11 = 1
    CHK_ADD_12 = 2
    CHK_ADD_14 = 3
    CHK_ADD_22 = 4
    CHK_ADD_24 = 5
    CHK_ADD_44 = 6
    CHK_CRC_16 = 7
    CHK_CRC_16_CCITT = 8
    CHK_CRC_32 = 9
    CHK_USER_DEFINED = 10


CRC16 = (
    0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
    0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
    0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
    0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
    0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
    0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
    0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
    0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
    0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
    0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
    0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
    0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
    0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
    0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
    0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
    0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
    0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
    0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
    0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
    0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
    0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
    0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
    0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
    0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
    0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
    0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
    0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
    0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
    0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
    0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
    0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
    0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202,
)

CRC16_CCITT = (
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0,
)


def reflect(data, nBits):
    """Reflect data, i.e. reverse bit order.

    Parameters
    ----------
    data : int
    nBits : int
        width in bits of `data`
    """
    reflection = 0x00000000
    for bit in range(nBits):
        if data & 0x01:
            reflection |= (1 << ((nBits - 1) - bit))
        data = (data >> 1)
    return reflection


class Crc16:
    """Calculate CRC (16-bit)


    Parameters
    ----------
    table: list-like
        lookup table for CRC calculation
    initalRemainder : int
        value to start with
    finalXorValue : int
        final XOR value
    reflectData : bool
        reflect input data
    reflectRemainder : bool
        reflect output data

    .. [1] A PAINLESS GUIDE TO CRC ERROR DETECTION ALGORITHMS
           http://www.ross.net/crc/download/crc_v3.txt
    .. [2] Understanding and implementing CRC (Cyclic Redundancy Check)
           calculation
           http://www.sunshine2k.de/articles/coding/crc/understanding_crc.html
    .. [3] Online CRC calculator
           http://zorc.breitbandkatze.de/crc.html
    """
    WIDTH = 16

    def __init__(self, table, initalRemainder, finalXorValue, reflectData,
                 reflectRemainder):
        self.table = table
        self.initalRemainder = initalRemainder
        self.finalXorValue = finalXorValue
        self.reflectData = reflectData
        self.reflectRemainder = reflectRemainder

    def __call__(self, frame):
        remainder = self.initalRemainder
        for ch in frame:
            data = self.reflectIn(ch, remainder)
            remainder = (self.table[data] ^ (remainder << 8)) & 0xffff
        return self.reflectOut(remainder)

    def reflectIn(self, ch, remainder):
        if self.reflectData:
            return (reflect(ch, 8) ^ (remainder >> (self.WIDTH - 8))) & 0xff
        else:
            return (ch ^ (remainder >> (self.WIDTH - 8))) & 0xff

    def reflectOut(self, remainder):
        if self.reflectRemainder:
            return reflect(remainder, 16) ^ self.finalXorValue
        else:
            return remainder ^ self.finalXorValue


def adder(modulus):
    """Factory function for modulus adders

    Parameters
    ----------
    modulus : int
        modulus to use

    Returns
    -------
    function
        adder function

    Examples
    --------
    >>> a256=adder(256)
    >>> a256([11, 22, 33, 44, 55, 66, 77, 88, 99])
    239

    """
    def add(frame):
        return sum(frame) % modulus
    return add


def wordSum(modulus, step):
    """Factory function for (double-)word modulus sums

    Parameters
    ----------
    modulus : int
    step : [2, 4]
        2 - word wise
        4 - double-word wise

    Returns
    -------
    function
        summation function
    """
    def add(frame):
        if step == 2:
            mask = "<H"
        elif step == 4:
            mask = "<I"
        else:
            raise NotImplementedError("Only WORDs or DWORDs are supported.")
        x = [struct.unpack(mask, frame[x:x + step])[0]
             for x in range(0, len(frame), step)]
        return sum(x) % modulus
    return add


ADD11 = adder(2 ** 8)
ADD12 = adder(2 ** 16)
ADD14 = adder(2 ** 32)
ADD22 = wordSum(2 ** 16, 2)
ADD24 = wordSum(2 ** 32, 2)
ADD44 = wordSum(2 ** 32, 4)
CRC16 = Crc16(CRC16, 0x0000, 0x0000, True, True)
CRC16_CCITT = Crc16(CRC16_CCITT, 0xffff, 0x0000, False, False)


def CRC32(x):
    return zlib.crc32(bytes(x)) & 0xffffffff


def userDefined(x):
    """User defined algorithms are not supported yet.
    """
    raise NotImplementedError(
        "Checksum method 'CHK_USER_DEFINED' not supported yet.")


ALGO = {
    "CHK_ADD_11":       ADD11,
    "CHK_ADD_12":       ADD12,
    "CHK_ADD_14":       ADD14,
    "CHK_ADD_22":       ADD22,
    "CHK_ADD_24":       ADD24,
    "CHK_ADD_44":       ADD44,
    "CHK_CRC_16":       CRC16,
    "CHK_CRC_16_CCITT":  CRC16_CCITT,
    "CHK_CRC_32":       CRC32,
    "CHK_USER_DEFINED": userDefined
}


def check(frame, algo):
    """Calculate checksum using given algorithm

    Parameters
    ----------
    frame : list of integers
    algo : `ALGO`

    Returns
    -------
    int
    """
    fun = ALGO.get(algo)
    if fun:
        return fun(frame)
    else:
        raise NotImplementedError("Invalid algorithm '{}'.".format(algo))
