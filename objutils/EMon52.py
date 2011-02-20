#!/usr/bin/env python
# -*- coding: utf-8 -*-

import HexFile
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

