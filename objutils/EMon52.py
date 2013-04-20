#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2013 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

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

import objutils.HexFile as HexFile
import cStringIO

FORMATS=(
    (HexFile.TYPE_FROM_RECORD,"LL AAAA:DDCCCC"),
)

DATA=0
EOF=1
EXTENDED_SEGMENT_ADDRESS=2
START_SEGMENT_ADDRESS=3
EXTENDED_LINEAR_ADDRESS=4
START_LINEAR_ADDRESS=5


class Codec(object):
    def __init__(self,fileLike):
        self.fileLike=fileLike

    def readlines(self):
        for line in self.fileLike.readlines():
            yield line

    def writelines(self,lines):
        for line in lines:
            self.fileLike.write(line)


class Reader(HexFile.Reader):
    def __init__(self,formats,inFile,dataSep=None):

        super(Reader,self).__init__(formats,Codec(inFile),dataSep)

    def checkLine(self,line,formatType):
        if line.length!=len(line.chunk):
            raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        # todo: factor out checksum calculation from line!!!
        checksum=(sum(line.chunk) & 0xffff)
        if line.checksum!=checksum:
            raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self,line,formatType):
        return True

