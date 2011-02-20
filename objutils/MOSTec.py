#!/usr/bin/env python
# -*- coding: utf-8 -*-


import HexFile
import cStringIO

DATA=1
EOF=2

FORMATS=(
    (DATA,";LLAAAADDCCCC"),
    (EOF,";00")
)


class Reader(HexFile.Reader):
    def checkLine(self,line,formatType):
        if formatType==DATA:
            if line.length!=len(line.chunk):
                raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            # todo: factor out checksum calculation from line!!!
            checksum=((sum([line.length,(line.address & 0xff00)>>8,line.address & 0xff])+
                sum(line.chunk)) & 0xffff)
            if line.checksum!=checksum:
                raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self,line,formatType):
        return formatType==DATA


