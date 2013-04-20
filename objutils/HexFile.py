#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.1"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2012 by Christoph Schueler <github.com/Christoph2,
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

import logging
import heapq
from functools import partial
from operator import itemgetter
import re
import sys
import types


'''
MemoryBlocks
------------
Segment-Types: generic,code,const,bss,... (s. ELF!?)
'''

"""
TODO:   Create a base class for Reader/Writer common functionality.
        FactoryMethods ???
        Logger!!!
        Parameter ['exceptionsOnErrors'].

"""

SIXTEEN_BITS    = 0
TWENTY_BITS     = 1
TWENTYFOUR_BITS = 2
THIRTYTWO_BITS  = 3

START           = 0
LENGTH          = 1
TYPE            = 2
ADDRESS         = 3
DATA            = 4
UNPARSED        = 5
CHECKSUM        = 6
ADDR_CHECKSUM   = 7

MAP_GROUP_TO_REGEX = {
    LENGTH          : "(?P<length>[0-9a-zA-Z]{%d})",
    TYPE            : "(?P<type>\d{%d})",
    ADDRESS         : "(?P<address>[0-9a-zA-Z]{%d})",
    DATA            : "(?P<chunk>[0-9a-zA-Z]*)",
    UNPARSED        : "(?P<chunk>.*)",
    CHECKSUM        : "(?P<checksum>[0-9a-zA-Z]{%d})",
    ADDR_CHECKSUM   : "(?P<addrChecksum>[0-9a-zA-Z]{%d})",
}

MAP_CHAR_TO_GROUP={
    'L': LENGTH,
    'T': TYPE,
    'A': ADDRESS,
    'D': DATA,
    'U': UNPARSED,
    'C': CHECKSUM,
    'B': ADDR_CHECKSUM,
}

TYPE_FROM_RECORD=0

atoi = partial(int, base = 16)

BYTES=re.compile('([0-9a-zA-Z]{2})')


class SegmentType(object):
    def __init__(self, address = 0, length = 0, data = bytearray()):
        self.address = address
        self.length = length
        self.data = data

    def __getitem__(self, key):
        if key == 0:
            return self.address
        elif key == 1:
            return self.length
        elif key == 2:
            return self.data
        else:
            raise IndexError()

    def __repr__(self):
        return "Segment (address: '0X%X' len: '%d')" % (self.address, self.length)


class InvalidRecordTypeError(Exception): pass
class InvalidRecordLengthError(Exception): pass
class InvalidRecordChecksumError(Exception): pass


class FormatParser(object):
    def __init__(self, fmt, dataSep = None):
        self.fmt = fmt
        self.translatedFmt = []
        if dataSep == ' ':
            dataSep = '\s'
        self.dataSep = dataSep

    def parse(self):
        if not isinstance(self.fmt, types.StringType):
            raise TypeError
        group = ''
        prevCh = ''
        for ch in self.fmt:
            if ch != prevCh:
                if group != '':
                    self.translateFormat(group)
                    group = ''
            group += ch
            prevCh = ch
        self.translateFormat(group)
        ft = ''.join(map(itemgetter(2), self.translatedFmt))
        return re.compile(ft, re.DOTALL | re.MULTILINE)

    def translateFormat(self, group):
        groupNumber = MAP_CHAR_TO_GROUP.get(group[0])
        length = len(group)
        if groupNumber is None:    # Handle invariants (i.e. fixed chars).
            if group[0] == ' ':
                expr = '\s{%s}' % (length, )
            else:
                expr = group[0] * length
        else:
            expr = MAP_GROUP_TO_REGEX.get(groupNumber, None)
            if groupNumber == START:
                expr = expr % (self.startSign, )
            elif groupNumber == DATA:
                "(?P<chunk>[0-9a-zA-Z]*)"
                if self.dataSep is not None:
                    expr = "(?P<chunk>([0-9a-zA-Z]{2}%s)*)" % (self.dataSep, )
                else:
                    #expr="(%s*)" % expr
                    pass
            elif groupNumber == UNPARSED:
                print expr
            else:
                expr = expr % (length, )
        self.translatedFmt.append((groupNumber, length, expr))


class Cont(object): pass

class Reader(object):
    aligment = 0  # 2**n

    def __init__(self, formats, inFile, dataSep = None):
        if not hasattr(inFile, 'readlines'):
            raise TypeError("Need a file-like object.")
        self.inFile = inFile
        if isinstance(formats, types.StringType):
            self.formats = [FormatParser(formats, dataSep).parse()]
        elif isinstance(formats,(types.ListType, types.TupleType)):
            self.formats = []
            for formatType, format in formats:
                self.formats.append((formatType, FormatParser(format, dataSep).parse()))
        self.logger = logging.getLogger("object.utils")

    def read(self):
        segments = []
        resultSegments = []
        for line in self.inFile.readlines():
            for formatType, format in self.formats:
                match = format.match(line)
                if match:
                    container = Cont()
                    dict_ = match.groupdict()
                    if dict_ != {}:
                        # Handle scalar values.
                        for key, value in dict_.items():
                            if key != 'chunk':
                                setattr(container, key, atoi(value))
                        if dict_.has_key('chunk'):
                            if self.parseData(container, formatType):
                                chunk = bytearray(map(atoi, BYTES.findall(dict_['chunk'])))
                            else:
                                # don't convert/parse stuff like symbols.
                                chunk = dict_['chunk']
                            dict_.pop('chunk')
                            setattr(container, 'chunk', chunk)
                        self.checkLine(container, formatType)
                        # this is to handle esoteric stuff like Intel seg:offs addressing and symbols.
                        self.specialProcessing(container, formatType)
                        if self.isDataLine(container, formatType):
                            # print chunk
                            segments.append(SegmentType(container.address, container.length, container.chunk))
                        else:
			    pass
                            #print container # Sonderfälle als 'processingInstructions' speichern!!!
        segments.sort(key = itemgetter(0))
        prevSegment = SegmentType()
        while segments:
            segment = segments.pop(0)
            if segment.address == prevSegment.address + prevSegment.length and resultSegments:
                resultSegments[-1].data.extend(segment.data)
                resultSegments[-1].length += segment.length
            else:
                # Create a new Segment.
                resultSegments.append(SegmentType(segment.address, segment.length, segment.data))
            prevSegment = segment
        lastSeg = resultSegments[-1]
        # deduce Adressspace from last segment.
        self.addressSpace = self._addressSpace(lastSeg.address + lastSeg.length)
	## TODO: Add start-address, if available.
        return resultSegments

    def _addressSpace(self, value):
        if value < 2**16:
            return SIXTEEN_BITS
        elif value < 2**20:
            return TWENTY_BITS
        elif value < 2**24:
            return TWENTYFOUR_BITS
        elif value < 2**32:
            return THIRTYTWO_BITS
        else:
            raise ValueError("Unsupported Addressspace size.")

    def probe(self):
        "Determine if valid object from first line." # if object is valid.
        raise NotImplementedError()

    def checkLine(self, line, formatType):
        raise NotImplementedError()

    def isDataLine(self, line, formatType):
        raise NotImplementedError()

    def classifyLine(self, line):
        raise NotImplementedError()

    def specialProcessing(self, line, formatType):
        pass

    def parseData(self, line, formatType):
        return True

