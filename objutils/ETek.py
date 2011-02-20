#!/usr/bin/env python
# -*- coding: utf-8 -*-

import HexFile
import cStringIO

DATA=1
SYMBOL=2
EOF=3

FORMATS=(
    (DATA,"%LL6CCAAAADD"),
    (SYMBOL,"%LL3CCU"),
    (EOF,"/AAAA00BB"),
)

class Reader(HexFile.Reader):
    def __init__(self,inFile):
        super(Reader,self).__init__(FORMATS,inFile)

    def nibbleSum(self,accu,b):
        hn=(b & 0xf0) >> 4
        ln=b & 0x0f
        s=hn+ln
        return accu+s

    def checkLine(self,line,formatType):
        if formatType==DATA:
            line.length=(line.length-10)/2
            if line.length!=len(line.chunk):
                raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
            ns=0
            for b in [(line.address & 0xff00)>>8,line.address & 0xff,line.length]:
                ns=self.nibbleSum(ns,b)
            for b in line.chunk:
                ns=self.nibbleSum(ns,b)
            checksum=( ~ (sum(line.chunk))+line.length+(line.address>>8)+(line.address & 0xff) ) & 0xff
        elif formatType==SYMBOL:
            chunk=line.chunk
            print chunk
            '''
            if line.checksum!=checksum:
                raise HexFile.InvalidRecordChecksumError()
            '''

    def isDataLine(self,line,formatType):
        return formatType==DATA

    def parseData(self,line,formatType):
        return formatType!=SYMBOL

