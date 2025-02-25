#!/usr/bin/env python

__version__ = "0.1.1"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2025 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import partial
from operator import itemgetter

from objutils.image import Image
from objutils.logger import Logger
from objutils.section import Section, join_sections
from objutils.utils import create_string_buffer, slicer


"""
MemoryBlocks
------------
Segment-Types: generic,code,const,bss,... (s. ELF!?)
"""

"""
TODO:   Create a base class for Reader/Writer common functionality.
        FactoryMethods ???
        Parameter ['exceptionsOnErrors'].
"""

SIXTEEN_BITS = 0
TWENTY_BITS = 1
TWENTYFOUR_BITS = 2
THIRTYTWO_BITS = 3

START = 0
LENGTH = 1
TYPE = 2
ADDRESS = 3
DATA = 4
UNPARSED = 5
CHECKSUM = 6
ADDR_CHECKSUM = 7

MAP_GROUP_TO_REGEX = {
    LENGTH: r"(?P<length>[0-9a-zA-Z]{%d})",
    TYPE: r"(?P<type>\d{%d})",
    ADDRESS: r"(?P<address>[0-9a-zA-Z]{%d})",
    DATA: r"(?P<chunk>[0-9a-zA-Z]+)",
    UNPARSED: r"(?P<chunk>.*)",
    CHECKSUM: r"(?P<checksum>[0-9a-zA-Z]{%d})",
    ADDR_CHECKSUM: r"(?P<addrChecksum>[0-9a-zA-Z]{%d})",
}

MAP_CHAR_TO_GROUP = {
    "L": LENGTH,
    "T": TYPE,
    "A": ADDRESS,
    "D": DATA,
    "U": UNPARSED,
    "C": CHECKSUM,
    "B": ADDR_CHECKSUM,
}

TYPE_FROM_RECORD = 0

atoi = partial(int, base=16)


@dataclass
class Statistics:

    record_types: Counter = field(default_factory=Counter)
    data_bytes: Counter = field(default_factory=Counter)


class Invalidrecord_typeError(Exception):
    pass


class InvalidRecordLengthError(Exception):
    pass


class InvalidRecordChecksumError(Exception):
    pass


class AddressRangeToLargeError(Exception):
    pass


@dataclass
class MetaRecord:
    format_type: str
    address: int
    chunk: bytearray


class FormatParser:
    def __init__(self, fmt, data_separator=None):
        self.fmt = fmt
        self.translated_format = []
        self.data_separator = data_separator

    def parse(self):
        group = ""
        prevCh = ""
        for ch in self.fmt:
            if ch != prevCh:
                if group != "":
                    self.translateFormat(group)
                    group = ""
            group += ch
            prevCh = ch
        self.translateFormat(group)
        self.translated_format.append((0, 0, r"(?P<junk>(.*?))$"))  # ??
        ft = r"^{}".format("".join(map(itemgetter(2), self.translated_format)))
        return re.compile(ft, re.DOTALL | re.MULTILINE)

    def translateFormat(self, group):
        group_number = MAP_CHAR_TO_GROUP.get(group[0])
        length = len(group)
        if group_number is None:  # Handle invariants (i.e. fixed chars).
            if group[0] == " ":
                expr = rf"\s{{{length!s}}}"
            else:
                expr = group[0] * length
        else:
            expr = MAP_GROUP_TO_REGEX.get(group_number)
            if group_number == START:
                expr = expr % (self.startSign,)
            elif group_number == DATA:
                r"(?P<chunk>[0-9a-zA-Z]*)"
                if self.data_separator is not None:
                    expr = rf"(?P<chunk>[0-9a-zA-Z{self.data_separator!s}]*)"
                else:
                    pass
            elif group_number == UNPARSED:
                # print expr
                pass
            else:
                expr = expr % (length,)
        self.translated_format.append((group_number, length, expr))


class Container:
    def __init__(self):
        self.processing_instructions = []

    def add_processing_instruction(self, pi):
        self.processing_instructions.append(pi)


class BaseType:
    def error(self, msg):
        self.logger.error(msg)
        self.valid = False

    def warn(self, msg):
        self.logger.warn(msg)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)


class Reader(BaseType):
    ALIGMENT = 0  # 2**n
    DATA_SEPARATOR = None
    VALID_CHARS = re.compile(r"^[a-fA-F0-9 :/;,%\n\r!?S]*$")  # General case, fits most formats.

    def __init__(self):
        self.logger = Logger("Reader")
        self.stats = Statistics()
        if isinstance(self.FORMAT_SPEC, str):
            self.formats = [FormatParser(self.FORMAT_SPEC, self.DATA_SEPARATOR).parse()]
        elif isinstance(self.FORMAT_SPEC, (list, tuple)):
            self.formats = []
            for format_type, format in self.FORMAT_SPEC:
                self.formats.append((format_type, FormatParser(format, self.DATA_SEPARATOR).parse()))

    def load(self, fp, **kws):
        if isinstance(fp, str):
            fp = open(fp, "rb")
        data = self.read(fp)  # .decode()
        if hasattr(fp, "close"):
            fp.close()
        return data

    def loads(self, image, **kws):
        if isinstance(image, str):
            return self.load(create_string_buffer(bytes(image, "ascii")))
        else:
            return self.load(create_string_buffer(image))

    def read(self, fp):
        sections = []
        matched = False
        self.valid = True
        meta_data = defaultdict(list)
        for line_number, line in enumerate(fp.readlines(), 1):
            for format_type, format in self.formats:
                if isinstance(line, bytes):
                    match = format.match(line.decode())
                else:
                    match = format.match(line)
                if match:
                    matched = True
                    container = Container()
                    container.line_number = line_number
                    dict_ = match.groupdict()
                    if dict_ != {}:
                        self.stats.record_types[format_type] += 1
                        # Handle scalar values.
                        for key, value in dict_.items():
                            if key not in ("chunk", "junk"):
                                setattr(container, key, atoi(value))
                            elif key == "junk":
                                setattr(container, key, value)
                        if "chunk" in dict_:
                            if self.parseData(container, format_type):
                                chunk = bytearray.fromhex(dict_["chunk"])
                            else:
                                # don't convert/parse stuff like symbols.
                                chunk = dict_["chunk"]
                            dict_.pop("chunk")
                            container.chunk = chunk  # setattr(container, "chunk", chunk)
                            self.stats.data_bytes[len(chunk)] += 1
                        self.check_line(container, format_type)
                        # this is to handle esoteric stuff like Intel seg:offs addressing and symbols.
                        self.special_processing(container, format_type)
                        if self.is_data_line(container, format_type):
                            sections.append(Section(container.address, container.chunk))
                        else:
                            chunk = container.chunk if hasattr(container, "chunk") else None
                            address = container.address if hasattr(container, "address") else None
                            meta_data[format_type].append(MetaRecord(format_type, address, chunk))
                    break
            if not matched:
                self.warn(f"Ignoring garbage line #{line_number:d}")
        if sections:
            return Image(sections=join_sections(sections), meta=meta_data)
        else:
            self.error("File seems to be invalid.")
            return Image([], valid=False)

    def _address_space(self, value):
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

    def maybe_binary_file(self, fp):
        fp.seek(0, os.SEEK_SET)
        header = fp.read(128)
        fp.seek(0, os.SEEK_SET)
        result = not bool(self.VALID_CHARS.match(header.decode()))
        return result

    def probe(self, fp):
        "Determine if object is valid."
        if self.maybe_binary_file(fp):
            return False
        matched = False
        for line_number, line in enumerate(fp.readlines(), 1):
            for _format_type, fmt in self.formats:  # NOTE: Same as in 'read()'!
                if isinstance(line, bytes):
                    match = fmt.match(line.decode())
                else:
                    match = fmt.match(line)
                if match:
                    matched = True
                    break
            if matched or line_number > 3:
                break
        return matched

    def probes(self, image):
        if isinstance(image, str):
            return self.probe(create_string_buffer(bytes(image, "ascii")))
        else:
            return self.probe(create_string_buffer(image))

    def check_line(self, line, format_type):
        raise NotImplementedError()

    def is_data_line(self, line, format_type):
        raise NotImplementedError()

    def classifyLine(self, line):
        raise NotImplementedError()

    def special_processing(self, line, format_type):
        pass

    def parseData(self, line, format_type):
        return True


class Writer(BaseType):
    def __init__(self):
        self.logger = Logger("Writer")

    def dump(self, fp, image, row_length=16, **kws):  # TODO: rename to bytesPerRow!
        if isinstance(fp, str):
            fp = open(fp, "wb")
        fp.write(self.dumps(image, row_length))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image, row_length=16, **kws):
        result = []
        self.row_length = row_length
        if hasattr(image, "sections") and not image.sections:
            return b""
        if self.calculate_address_bits(image) > self.MAX_ADDRESS_BITS:
            raise AddressRangeToLargeError("could not encode image.")
        self.set_parameters(**kws)
        self.pre_processing(image)
        header = self.compose_header(image.meta if hasattr(image, "meta") else {})
        if header:
            result.append(header)
        for section in image:
            address = section.start_address
            rows = slicer(section.data, row_length, lambda x: [int(y) for y in x])
            for row in rows:
                length = len(row)
                result.append(self.compose_row(address, length, row))
                address += row_length
        footer = self.compose_footer(image.meta if hasattr(image, "meta") else {})
        if footer:
            result.append(footer)
        return self.post_processing(bytes("\n".join(result), "ascii"))

    def calculate_address_bits(self, image):
        if hasattr(image, "sections"):
            last_segment = sorted(image.sections, key=lambda s: s.start_address)[-1]
        else:
            last_segment = image
        highest_address = last_segment.start_address + last_segment.length
        return int(math.ceil(math.log(highest_address + 1) / math.log(2)))

    def post_processing(self, data):
        if not data.endswith(b"\n"):
            data += b"\n"
        return data

    def pre_processing(self, image):
        pass

    def set_parameters(self, **kws) -> None:
        params = {}
        for k, v in kws.items():
            try:
                params[k] = getattr(self, k)
            except AttributeError as e:
                raise AttributeError(f"Invalid keyword argument {k!r}.") from e
            else:
                setattr(self, k, v)

    def compose_row(self, address, length, row):
        raise NotImplementedError()

    def compose_header(self, meta):
        return None

    def compose_footer(self, meta):
        return None

    def word_to_bytes(self, word):
        word = int(word)
        hi = (word & 0xFF00) >> 8
        lo = word & 0x00FF
        return hi, lo

    @staticmethod
    def hex_bytes(row, spaced=False):
        spacer = " " if spaced else ""
        return spacer.join([f"{x:02X}" for x in row])


class ASCIIHexReader(Reader):
    FORMAT_SPEC = None

    def __init__(self, address_pattern, data_pattern, etx_pattern, separators=", "):
        self.separators = separators
        self.DATA_PATTERN = re.compile(data_pattern.format(separators), re.DOTALL | re.MULTILINE)
        self.ADDRESS_PATTERN = re.compile(address_pattern, re.DOTALL | re.MULTILINE)
        self.ETX_PATTERN = re.compile(etx_pattern, re.DOTALL | re.MULTILINE)
        self.SPLITTER = re.compile(f"[{separators}]")
        self.patterns = (
            (self.ADDRESS_PATTERN, self.getAddress),
            (self.DATA_PATTERN, self.parse_line),
            (self.ETX_PATTERN, self.nop),
        )
        self.formats = [
            (0, self.ADDRESS_PATTERN),
            (1, self.DATA_PATTERN),
            (2, self.ETX_PATTERN),
        ]
        super().__init__()

    def getAddress(self, line, match):
        self.address = int(match.group("address"), 16)
        self.previous_address = self.address
        return True

    def nop(self, line, match):
        return False

    def parse_line(self, line, match):
        section = Section(
            self.address,
            bytearray([int(ch, 16) for ch in filter(lambda x: x, self.SPLITTER.split(line))]),
        )
        self.sections.append(section)
        self.address += len(section)
        return True

    def read(self, fp):
        lines = fp.read().decode()
        self.sections = []
        self.address = 0
        breakRequest = False
        for line in lines.splitlines():
            for pattern, action in self.patterns:
                match = pattern.match(line)
                if match:
                    if not action(line, match):
                        breakRequest = True
                    break
            if breakRequest:
                break
        return Image(join_sections(self.sections))


class ASCIIHexWriter(Writer):
    MAX_ADDRESS_BITS = 16
    previous_address = None

    def __init__(self, address_designator):
        self.separator = " "
        self.address_designator = address_designator
        super().__init__()

    def compose_row(self, address, length, row):
        prepend_address = True if address != self.previous_address else False
        self.previous_address = address + length
        if prepend_address:
            line = "{}\n{}".format(
                f"{self.address_designator}{address:04X}",
                f"{self.separator}".join([f"{x:02X}" for x in row]),
            )
        else:
            line = " ".join([f"{x:02X}" for x in row])
        self.row_callout(address, length, row)
        return line

    def row_callout(self, address, length, row):
        pass
