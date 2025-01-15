#!/usr/bin/env python
"""Reader/Writer for plain binfiles.
"""

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

import io
import zipfile
from contextlib import closing

from objutils.image import Image
from objutils.section import Section
from objutils.utils import create_string_buffer


##
## TODO: binzipped format: a separate file for each section + MANIFEST (csv: fname, address, length)
##


class NoContiniousError(Exception):
    pass


class Reader:
    def load(self, fp, address: int = 0x0000):
        if isinstance(fp, str):
            fp = open(fp, "rb")
        data = fp.read()
        sec = Section(address, data)
        img = Image([sec], valid=True)
        if hasattr(fp, "close"):
            fp.close()
        return img

    def loads(self, image: Image, address: int = 0x0000):
        if isinstance(image, str):
            return self.load(create_string_buffer(bytes(image, "ascii")), address)
        else:
            return self.load(create_string_buffer(image), address)


class Writer:
    def dump(self, fp, image: Image, filler: bytes = b"\xff", **kws):
        if isinstance(fp, str):
            fp = open(fp, "wb")
        fp.write(self.dumps(image, filler))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image: Image, filler: bytes = b"\xff", **kws):
        if not isinstance(filler, (bytes, int)):
            raise TypeError("filler must be of type 'bytes' or 'int'")
        if isinstance(filler, bytes) and len(filler) > 1:
            raise TypeError("filler must be a single byte")
        elif isinstance(filler, int) and filler > 255:
            raise ValueError("filler must be in range 0..255")
        result = bytearray()
        previous_address = None
        previous_length = None

        if hasattr(image, "sections") and not image.sections:
            return b""
        sections = sorted(image.sections, key=lambda x: x.start_address)
        for section in sections:
            if previous_address is not None:
                gap = section.start_address - (previous_address + previous_length)
                if gap > 0:
                    result.extend(filler * gap)
            result.extend(section.data)
            previous_address = section.start_address
            previous_length = section.length
        return result


class BinZipReader:
    pass


class BinZipWriter:
    SECTION_FILE_NAME = "image{0:d}.bin"
    MANIFEST_FILE_NAME = "IMAGES.mf"

    def dump(self, fp, image: Image, **kws):
        fp.write(self.dumps(image))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image: Image, **kws):
        if hasattr(image, "sections") and not image.sections:
            return b""
        sections = sorted(image.sections, key=lambda x: x.start_address)
        manifest_buffer = io.StringIO()
        out_buffer = io.BytesIO()
        # out_buffer = io.StringIO()
        print("BUF", out_buffer)
        with closing(zipfile.ZipFile(out_buffer, mode="w")) as outFile:
            print(outFile)
            for idx, section in enumerate(sections):
                print(section.start_address, section.length)
                # print("FN", BinZipWriter.SECTION_FILE_NAME.format(idx))
                manifest_buffer.write(BinZipWriter.SECTION_FILE_NAME.format(idx))
                manifest_buffer.write("\t")
                manifest_buffer.write(str(section.start_address))
                manifest_buffer.write("\t")
                manifest_buffer.write(str(section.length))
                manifest_buffer.write("\n")
        manifest_buffer.seek(0)
        print(manifest_buffer.read())
        return ""
