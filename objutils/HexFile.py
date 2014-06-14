#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.1"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2014 by Christoph Schueler <github.com/Christoph2,
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

from collections import defaultdict, namedtuple
import logging
from functools import partial
import re
import sys
import types
from objutils.Segment import Segment, joinSegments
from objutils.Image import Image
from operator import itemgetter
from objutils.pickleif import PickleIF
from objutils.slicer import slicer



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

BYTES = re.compile('([0-9a-zA-Z]{2})')

class InvalidRecordTypeError(Exception): pass
class InvalidRecordLengthError(Exception): pass
class InvalidRecordChecksumError(Exception): pass

MetaRecord = namedtuple('MetaRecord', 'formatType address chunk')

class FormatParser(object):
    def __init__(self, fmt, dataSep = None):
        self.fmt = fmt
        self.translatedFmt = []
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
                    expr = "(?P<chunk>[0-9a-zA-Z%s]*)" % (self.dataSep, )
                else:
                    pass
            elif groupNumber == UNPARSED:
                print expr
            else:
                expr = expr % (length, )
        self.translatedFmt.append((groupNumber, length, expr))


class Container(object):
    def __init__(self):
        self.processingInstructions = []

    def addPI(self, pi):
        self.processingInstructions.append(pi)


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
        metaData = defaultdict(list)
        for line in self.inFile.readlines():
            for formatType, format in self.formats:
                match = format.match(line)
                if match:
                    container = Container()
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
                            segments.append(Segment(container.address, container.length, container.chunk))
                        else:
                            chunk = container.chunk if hasattr(container, 'chunk') else None
                            metaData[formatType].append(MetaRecord(formatType, container.address, chunk))
        return Image(joinSegments(segments), metaData)

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


class Writer(object):


    def dump(self, fp, image, rowLength = 16):
        fp.write(dumps(image, rowLength))

    def dumps(self, image, rowLength = 16):
        result = []
        header = self.composeHeader(image.meta)
        if header:
            result.append(header)
        for segment in image:
            address = segment.address
            rows = slicer(segment.data, rowLength, lambda x:  [int(y) for y in x])
            for row in rows:
                length = len(row)
                result.append(self.composeRow(address, length, row))
                address += rowLength
        footer = self.composeFooter(image.meta)
        if footer:
            result.append(footer)
        return '\n'.join(result)

    def composeRow(self, address, length, row):
        raise NotImplementedError()

    def composeHeader(self, meta):
        return None

    def composeFooter(self, meta):
        return None

    @staticmethod
    def hexBytes(row, spaced = False):
        spacer = ' ' if spaced else ''
        return spacer.join(["%02X" % x for x in row])

