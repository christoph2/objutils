#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import cStringIO as StringIO
except NameError:
    import StringIO
import re

SAMPLE1="""
CC2VMC
64
160

1 0 0 0 20 0 20 0 32 0 0 0 255 255 0 0 0 0 31 0 59 0 90 0 120 0 151 0 181 0 212 0
243 0 17 1 48 1 78 1 0 0 2 0 1 0 128 0 128 0 192 0 148 0 212 0 20 0 255 255 255 255 255 255

132 65534 862 1118 1374 94 350 606 1630 204 0 50 195 65476 202 54596
131 4 144 65528 1860 80 836 86 152 65528 1604 202 54596 16452 144 65528
82 202 54596 68 132 18 144 65530 143 0 324 71 69 12 152 2
144 2 202 54438 143 0 324 69 159 0 1860 76 133 65512 32836 202
54596 130 8 202 54438 202 54540 144 65530 134 9999 76 133 9 144 65530
134 10000 72 202 54540 132 3 8260 202 54438 144 65530 134 999 76 133
9 144 65530 134 1000 72 202 54540 132 3 8260 202 54438 144 65530 25412
76 133 8 144 65530 25668 72 202 54540 132 3 8260 202 54438 144 65530
2372 76 133 8 144 65530 2628 72 202 54540 132 3 8260 202 54438 144
65530 202 54540 130 6 65535 65535 65535 65535 65535 65535 65535 65535 65535 65535 65535
"""

VMC_FILE = re.compile(r'''CC2VMC\s(?P<numberOfConstantBytes>\d+)\s(?P<numberOfCodeWords>\d+)[\n]{2}
    (?P<constBytes>(\d+\s)+.*?)[\n]{2}(?P<codeWords>(\d+\s)+.*)''', re.VERBOSE | re.M | re.DOTALL)

def bswap(value):
    hi = (value & 0xff00) >> 8
    lo = value & 0xff

    return lo << 8 | hi

class Reader(object):
    def __init__(self, infFile):
        data=infFile.read()

        match = VMC_FILE.match(data)
        if match:
            gd = match.groupdict()
            self.codeWords = map(bswap, map(int, gd['codeWords'].split()))
            self.constBytes = map(int, gd['constBytes'].split())
            self.numberOfConstantBytes = int(gd['numberOfConstantBytes'])
            self.numberOfCodeWords = int(gd['numberOfCodeWords'])

            assert self.numberOfConstantBytes == len(self.constBytes)
            assert self.numberOfCodeWords == len(self.codeWords)
        else:
            pass # todo: Error-Handling.

def main():
    r = Reader(StringIO.StringIO(SAMPLE1.strip()))

if __name__=='__main__':
    main()
