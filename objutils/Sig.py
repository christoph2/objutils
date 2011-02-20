#!/usr/bin/env python
# -*- coding: utf-8 -*-

import HexFile

DATA=1
EOF=2

FORMATS=(
    (DATA,":AAAALLBBDDCC"),
    (EOF,":00")
)

class Reader(HexFile.Reader):

    def checkByte(self,checksum,b):
        checksum^=b
        checksum<<=1
        if checksum & 0x100==0x100:
            checksum|=0x01
        checksum &= 0xff
        return checksum

    def checkLine(self,line,formatType):
        if formatType==DATA:
            if line.length!=len(line.chunk):
                raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            addrChecksum=0
            for b in [(line.address & 0xff00)>>8,line.address & 0xff,line.length]:
                addrChecksum=self.checkByte(addrChecksum,b)
            if line.addrChecksum!=addrChecksum:
                raise HexFile.InvalidRecordChecksumError()
            checksum=0
            for b in line.chunk:
                checksum=self.checkByte(checksum,b)
            if line.checksum!=checksum:
                raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self,line,formatType):
        return formatType==DATA

