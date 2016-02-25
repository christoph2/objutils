#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.1"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2015 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import math
import re
import sys

from objutils.Segment import Segment, joinSegments
from objutils.Image import Image
from operator import itemgetter
from objutils.pickleif import PickleIF
from objutils.utils import slicer, PYTHON_VERSION
from objutils.logger import Logger


if PYTHON_VERSION.major == 3:
    from io import BytesIO as StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO


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
class AddressRangeToLargeError(Exception): pass

MetaRecord = namedtuple('MetaRecord', 'formatType address chunk')

class FormatParser(object):
    def __init__(self, fmt, dataSep = None):
        self.fmt = fmt
        self.translatedFmt = []
        self.dataSep = dataSep

    def parse(self):
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
                #print expr
                pass
            else:
                expr = expr % (length, )
        self.translatedFmt.append((groupNumber, length, expr))


class Container(object):
    def __init__(self):
        self.processingInstructions = []

    def addPI(self, pi):
        self.processingInstructions.append(pi)


class Reader(object):
    ALIGMENT = 0  # 2**n
    DATA_SEPARATOR = None

    def __init__(self):
        self.logger = Logger("Reader")
        if isinstance(self.FORMAT_SPEC, str):
            self.formats = [FormatParser(self.FORMAT_SPEC, self.DATA_SEPARATOR).parse()]
        elif isinstance(self.FORMAT_SPEC, (list, tuple)):
            self.formats = []
            for formatType, format in self.FORMAT_SPEC:
                self.formats.append((formatType, FormatParser(format, self.DATA_SEPARATOR).parse()))

    def load(self, fp, **kws):
        if PYTHON_VERSION.major == 3:
            return self.read(fp)# .decode()
        else:
            return self.read(fp)

    def loads(self, image, **kws):
        if PYTHON_VERSION.major == 3:
            return self.load(StringIO(bytes(image, "ascii")))
        else:
            return self.load(StringIO(image))

    def read(self, fp):
        segments = []
        matched = False
        self.valid = True
        metaData = defaultdict(list)
        for (lineNumber, line) in enumerate(fp.readlines(), 1):
            for formatType, format in self.formats:
                if isinstance(line, bytes):
                    match = format.match(line.decode())
                else:
                    match = format.match(line)
                if match:
                    matched = True
                    container = Container()
                    container.lineNumber = lineNumber
                    dict_ = match.groupdict()
                    if dict_ != {}:
                        # Handle scalar values.
                        for key, value in dict_.items():
                            if key != 'chunk':
                                setattr(container, key, atoi(value))
                        if 'chunk' in dict_:
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
                            segments.append(Segment(container.address, container.chunk))
                        else:
                            chunk = container.chunk if hasattr(container, 'chunk') else None
                            metaData[formatType].append(MetaRecord(formatType, container.address, chunk))
                    break
            if not matched:
                self.warn("Ignoring garbage line #%u" % lineNumber)
        if segments:
            return Image(joinSegments(segments), metaData, self.valid)
        else:
            self.error("File seems to be invalid.")
            return Image([], valid = False)

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

    def error(self, msg):
        self.logger.error(msg)
        self.valid = False

    def warn(self, msg):
        self.logger.warn(msg)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

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

    def dump(self, fp, image, rowLength = 16, **kws):   # TODO: rename to bytesPerRow!
        fp.write(dumps(image, rowLength))

    def dumps(self, image, rowLength = 16, **kws):
        result = []

        if self.calculateAddressBits(image) > self.MAX_ADDRESS_BITS:
            raise AddressRangeToLargeError('could not encode image.')

        if kws:
            params = self.saveParameters(**kws)

        self.preProcessing(image)

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
        if kws:
            self.restoreParameters(params)
        if footer:
            result.append(footer)
        return '\n'.join(result)

    def calculateAddressBits(self, image):
        lastSegment = sorted(image.segments, key = lambda s: s.address)[-1]
        highestAddress = lastSegment.address + lastSegment.length
        return int(math.ceil(math.log(highestAddress + 1) / math.log(2)))

    def preProcessing(self, image):
        pass

    def saveParameters(self, **kws):
        params = {}
        for k, v in kws.items():
            try:
                params[k] = getattr(self, k)
            except AttributeError:
                raise AttributeError("Invalid keyword argument '%s'." % k)
            else:
                setattr(self, k, v)
        return params

    def restoreParameters(self, params):
        for k, v in params.items():
            setattr(self, k, v)


    def composeRow(self, address, length, row):
        raise NotImplementedError()

    def composeHeader(self, meta):
        return None

    def composeFooter(self, meta):
        return None

    def wordToBytes(self, word):
        h = (word & 0xff00) >> 8
        l = word & 0x00ff
        return h, l

    @staticmethod
    def hexBytes(row, spaced = False):
        spacer = ' ' if spaced else ''
        return spacer.join(["%02X" % x for x in row])


class ASCIIHexReader(Reader):
    HEADER_PATTERN = None
    FOOTER_PATTERN = None
    DATA_PATTERN = "(?:[0-9a-zA-Z]{2}[{0}]?)*"

    def __init__(self, separators = ' '):
        self.separators = separators
        self.dataPattern = Reader.DATA_PATTERN.format(separators)

    def read(self, fp):
        if PYTHON_VERSION.major == 3:
            lines = fp.read().decode()
        else:
            lines = fp.read()
        segments = []
        address = 0
        previousAddress = 0
        resultLines = []
        for line in lines.splitlines():
            match = ADDRESS.match(line)
            if match:
                address = int(match.groupdict()['value'], 16)
                if resultLines:
                        segments.append((previousAddress, resultLines))
                previousAddress = address
                resultLines = []
            else:
                if not line.startswith('q'):
                    resultLines.append(line)

            if resultLines:
                segments.append((address, resultLines))

            chunks = []
            for address, segment in segments:
                for line in segment:
                    #print(line)
                    #chunk = bytearray(self._getByte(line))
                    chunk = [int(ch, 16) for ch in line.split()]
                    #chunk = bytes(self._getByte(line))
                    chunks.append(Segment(address, chunk))
                    address += len(chunk)

            return Image(joinSegments(chunks))

        def _getByte(self, chunk):
            print(chunk)
            for line in chunk.splitlines():
                print("xxx",line)
                for ch in line.split():
                    yield chr(int(ch, 16))


class ASCIIHexWriter(Writer):

    MAX_ADDRESS_BITS = 16
    previousAddress = None

    def composeRow(self, address, length, row):
        prependAddress =  True if address != self.previousAddress else False
        self.previousAddress = (address + length)
        if prependAddress:
            line = "{0}\n{1}".format("@{0:04X}".format(address), " ".join(["{0:02X}".format(x) for x in row]))
        else:
            line = " ".join(["{0:02X}".format(x) for x in row])
        return line

    def composeFooter(self, meta):
        line = "q\n"
        return line

