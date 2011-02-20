#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator
import HexFile

FORMATS=(
    (HexFile.TYPE_FROM_RECORD,":LLAAAATTDDCC"),
)

DATA=0
EOF=1
EXTENDED_SEGMENT_ADDRESS=2
START_SEGMENT_ADDRESS=3
EXTENDED_LINEAR_ADDRESS=4
START_LINEAR_ADDRESS=5


class curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs
        return self.fun(*(self.pending + args), **kw)


identity=lambda self,x: x

class Reader(HexFile.Reader):
    def __init__(self,formats,inFile):
        super(Reader,self).__init__(formats,inFile)
        self.segmentAddress=0

    def checkLine(self,line,formatType):
        if line.length!=len(line.chunk):
            raise HexFile.InvalidRecordLengthError("Byte count doesn't match length of actual data.")
        # todo: factor out checksum calculation from line!!!
        checksum=(~(sum([line.type,line.length,(line.address & 0xff00)>>8,line.address & 0xff])+
            sum(line.chunk)) & 0xff)+1
        if line.checksum!=checksum:
            print "CHECKSUM ERROR"
#            raise HexFile.InvalidRecordChecksumError()

    def isDataLine(self,line,formatType):
        if line.type==DATA:
            return True
        else:
            return False

    def specialProcessing(self,line,formatType):
        if line.type==DATA:
            line.address=self._addressCalculator(line.address)
        elif line.type==EXTENDED_SEGMENT_ADDRESS:
            seg=((line.chunk[0])<<8) | (line.chunk[1])
            self._addressCalculator=curry(operator.add,seg<<4)
            print "EXTENDED_SEGMENT_ADDRESS: ",hex(seg)
        elif line.type==START_SEGMENT_ADDRESS:
            cs=((line.chunk[0])<<8) |(line.chunk[1])
            ip=((line.chunk[2])<<8) |(line.chunk[3])
            print "START_SEGMENT_ADDRESS: %s:%s" % (hex(cs),hex(ip))
        elif line.type==EXTENDED_LINEAR_ADDRESS:
            seg=((line.chunk[0])<<8) | (line.chunk[1])
            self._addressCalculator=curry(operator.add,seg<<16)
            print "EXTENDED_LINEAR_ADDRESS: ",hex(seg)
        elif line.type==START_LINEAR_ADDRESS:
            eip=((line.chunk[0])<<24) | ((line.chunk[1])<<16) | ((line.chunk[2])<<8) |(line.chunk[3])
            print "START_LINEAR_ADDRESS: ",hex(eip)

    _addressCalculator=identity

