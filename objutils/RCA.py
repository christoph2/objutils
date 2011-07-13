#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cStringIO
import re
import HexFile

DATA=1
EOF=2


FORMATS=(
    (DATA,"AAAA DD;"),
    (EOF,":0000")
)

NULLS = re.compile(r'\0*\s*!M\s*(.*)', re.DOTALL | re.M)

class Reader(HexFile.Reader):
    def __init__(self, inFile, dataSep=None):

        data = re.sub('\0*$', ';\n:0000', NULLS.match(inFile.read()).group(1), 1)

        super(Reader, self).__init__(FORMATS, cStringIO.StringIO(data) , dataSep)

    def checkLine(self, line, formatType):
        if formatType == DATA:
            line.length = len(line.chunk)

    def isDataLine(self, line, formatType):
        return formatType == DATA
