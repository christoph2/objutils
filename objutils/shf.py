#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Reader/Writer S Hexdump Format (rfc4149).
"""

__version__ = "0.1.1"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from hashlib import sha1
import re
import xml.etree.ElementTree as ET

from objutils.logger import Logger
from objutils.utils import create_string_buffer, PYTHON_VERSION
from objutils.image import Image
from objutils.section import Section

SHF_DTD = """<!--
    DTD for the S Hexdump Format, as of 2003-10-10
    Linus Walleij, Joachim Strombergson, Patrik Faltstrom 2003

    Refer to this DTD as:

    <!ENTITY % SHF PUBLIC "-//IETF//DTD SHF//EN" "http://ietf.org/dtd/shf.dtd">
        %SHF;
-->

<?xml version="1.0" encoding="UTF-8"?>

<!ELEMENT dump (block)+>
<!ATTLIST dump
    name CDATA #REQUIRED
    blocks CDATA #IMPLIED>

<!ELEMENT block (#PCDATA)>
    <!ATTLIST block
    name CDATA #REQUIRED
    address CDATA #REQUIRED
    word_size CDATA #REQUIRED
    length CDATA #REQUIRED
    checksum CDATA #REQUIRED>
"""

SHA1_DIGEST = lambda text: sha1(text).hexdigest()

WHITESPACE = re.compile("\s*")

remove_ws = lambda text: WHITESPACE.sub("", text)

class Reader(object):
    """
    """

    logger = Logger(__name__)

    def load(self, fp):
        if isinstance(fp, str):
            fp = open(fp, "rb")
        data = fp.read()
        root = ET.fromstring(data)
        sections = []
        for idx, child in enumerate(root):
            tag = child.tag
            attrib = child.attrib
            text = remove_ws(child.text)
            section_data = bytearray.fromhex(text)
            name = attrib.get('name')
            if name is None:
                self.logger.error("Block #{}: Missing required attribute `name`.".format(idx))
                continue
            address = attrib.get('address')
            if address:
                address = remove_ws(address)
                address = int(address, 16)
            else:
                self.logger.error("Block #{}: Missing required attribute `address`.".format(idx))
                continue
            length = attrib.get('length')
            if length:
                length = remove_ws(length)
                length = int(length, 16)
            else:
                self.logger.error("Block #{}: Missing required attribute `length`.".format(idx))
                continue
            word_size = attrib.get('word_size')
            if word_size:
                word_size = remove_ws(word_size)
                word_size = int(word_size, 16)
            else:
                self.logger.error("Block #{}: Missing required attribute `wordsize`.".format(idx))
                continue
            if len(section_data) != (length * word_size):
                self.logger.error("Block #{}: Mismatch between (`length` * `word_size`) and actual block length.".format(idx))
                continue
            checksum = attrib.get('checksum')
            if checksum:
                checksum = remove_ws(checksum)
                if SHA1_DIGEST(section_data) != checksum:
                    self.logger.error("Block #{}: Wrong `checksum`.".format(idx))
                    continue
            else:
                self.logger.error("Block #{}: Missing required attribute `checksum`.".format(idx))
                continue
            #print(tag, attrib)
            #print(section_data, SHA1_DIGEST(section_data))
            sections.append(Section(address, section_data))
        img = Image(sections)
        if hasattr(fp, "close"):
            fp.close()
        return img

    def loads(self, image):
        if PYTHON_VERSION.major == 3:
            if isinstance(image, str):
                return self.load(create_string_buffer(bytes(image, "ascii")))
            else:
                return self.load(create_string_buffer(image))
        else:
            return self.load(create_string_buffer(image))


class Writer(object):
    """
    """

    logger = Logger(__name__)

    def dump(self, fp, image, **kws):
        if isinstance(fp, str):
            fp = open(fp, "wb")
        fp.write(self.dumps(image))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image, **kws):
        BLOCK_SIZE = 16
        result = []
        result.append('<?xml version="1.0" encoding="UTF-8"?>')
        result.append('<dump name="SHF dump by objutils" blocks="{:04x}">'.format(len(image._sections)))
        if hasattr(image, "sections") and  not image.sections:
            return b''
        sections = sorted(image.sections, key = lambda x: x.start_address)
        for idx, section in enumerate(sections):
            result.append('    <block name="Section #{:04x}" address="{:08x}" word_size="01" length="{:08x}" checksum="{}">'.\
                format(idx, section.start_address, section.length, SHA1_DIGEST(section.data)))
            nblocks = len(section.data) // BLOCK_SIZE
            remaining = len(section.data) % BLOCK_SIZE
            offset = 0
            for _ in range(nblocks):
                result.append("        {}".format(" ".join(
                    ["{:02x}".format(x) for x in section.data[offset : offset + BLOCK_SIZE]]))
                )
                offset += BLOCK_SIZE
            if remaining:
                result.append("        {}".format(" ".join(
                    ["{:02x}".format(x) for x in section.data[offset : offset + remaining]]))
                )
            result.append('    </block>')
        result.append("</dump>")
        return bytes("\n".join(result), encoding = "ascii")
