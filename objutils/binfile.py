#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Reader/Writer for plain binfiles.
"""

__version__ = "0.1.1"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from contextlib import closing
import io
import zipfile

from objutils.section import Section
from objutils.image import Image, Builder
from objutils.utils import slicer, createStringBuffer, PYTHON_VERSION
from objutils.logger import Logger

##
## TODO: binzipped format: a separate file for each section + MANIFEST (csv: fname, address, length)
##

class NoContiniousError(Exception): pass


class Reader(object):

    def load(self, fp, address = 0x0000):
        data = fp.read()
        sec = Section(address, data)
        img = Image([sec], valid = True)
        if hasattr(fp, "close"):
            fp.close()
        return img

    def loads(self, image, address = 0x0000):
        if PYTHON_VERSION.major == 3:
            if isinstance(image, str):
                return self.load(createStringBuffer(bytes(image, "ascii")), address)
            else:
                return self.load(createStringBuffer(image), address)
        else:
            return self.load(createStringBuffer(image), address)


class Writer(object):
    def dump(self, fp, image, filler = b'\xff', **kws):
        fp.write(self.dumps(image, filler))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image, filler = b'\xff', **kws):
        if not isinstance(filler, (bytes, int)):
            raise TypeError("filler must be of type 'bytes' or 'int'")
        if isinstance(filler, bytes) and len(filler) > 1:
            raise TypeError("filler must be a single byte")
        elif isinstance(filler, int) and filler > 255:
            raise ValueError("filler must be in range 0..255")
        result = bytearray()
        previousAddress = None
        previousLength = None

        if isinstance(image, Builder):
            image = image.image     # Be tolerant.

        if hasattr(image, "sections") and  not image.sections:
            return b''
        sections = sorted(image.sections, key = lambda x: x.startAddress)
        for section in sections:
            if not previousAddress is None:
                gap = section.startAddress - (previousAddress + previousLength)
                if gap > 0:
                    result.extend(filler * gap)
            result.extend(section.data)
            previousAddress = section.startAddress
            previousLength = section.length
        return result

#

class BinZipReader(object):
    pass


class BinZipWriter(object):

    SECTION_FILE_NAME = "image{0:d}.bin"
    MANIFEST_FILE_NAME = "IMAGES.mf"

    def dump(self, fp, image, **kws):
        fp.write(self.dumps(image))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image, **kws):

        if hasattr(image, "sections") and  not image.sections:
            return b''
        sections = sorted(image.sections, key = lambda x: x.startAddress)
        manifestBuffer = io.StringIO()
        outBuffer = io.BytesIO()
        #outBuffer = io.StringIO()
        print("BUF", outBuffer)
        with closing(zipfile.ZipFile(outBuffer, mode = "w")) as outFile:
            print(outFile)
            for idx, section in enumerate(sections):
                print(section.startAddress, section.length)
                #print("FN", BinZipWriter.SECTION_FILE_NAME.format(idx))
                manifestBuffer.write(BinZipWriter.SECTION_FILE_NAME.format(idx))
                manifestBuffer.write("\t")
                manifestBuffer.write(str(section.startAddress))
                manifestBuffer.write("\t")
                manifestBuffer.write(str(section.length))
                manifestBuffer.write("\n")
        manifestBuffer.seek(0)
        print(manifestBuffer.read())
        return ''
