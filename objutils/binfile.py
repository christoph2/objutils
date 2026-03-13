#!/usr/bin/env python
"""Reader/Writer for plain binfiles."""

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
from typing import Any, BinaryIO, Union

import objutils.hexfile as hexfile
from objutils.image import Image
from objutils.section import Section
from objutils.utils import create_string_buffer

##
## TODO: binzipped format: a separate file for each section + MANIFEST (csv: fname, address, length)
##


class NoContiniousError(Exception):
    pass


class Reader(hexfile.Reader):
    def load(self, fp: Union[str, BinaryIO], address: int = 0x0000, **kws: Any) -> Image:
        if isinstance(fp, str):
            fp = open(fp, "rb")
        data = fp.read()
        sec = Section(address, data)
        img = Image([sec], valid=True, join=False)
        if hasattr(fp, "close"):
            fp.close()
        return img

    def loads(self, image: Union[str, bytes, bytearray], address: int = 0x0000, **kws: Any) -> Image:
        if isinstance(image, str):
            return self.load(io.BytesIO(bytes(image, "ascii")), address)
        else:
            return self.load(io.BytesIO(image), address)

    def probe(self, fp: BinaryIO, **kws: Any) -> bool:
        """Binary files cannot be reliably probed by content alone."""
        return False


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


class BinZipReader(hexfile.Reader):
    def probe(self, fp: BinaryIO, **kws: Any) -> bool:
        """Probe for zip files."""
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, io.UnsupportedOperation):
            pass
        try:
            return zipfile.is_zipfile(fp)
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, io.UnsupportedOperation):
                pass

    def load(self, fp: Union[str, BinaryIO], **kws: Any) -> Image:
        """Load from zip file."""
        # TODO: Implementation
        return Image([], valid=True)

    def loads(self, data: Union[str, bytes, bytearray], **kws: Any) -> Image:
        """Load from zip bytes."""
        return self.load(io.BytesIO(data) if isinstance(data, (bytes, bytearray)) else io.BytesIO(data.encode()))


class BinZipWriter:
    SECTION_FILE_NAME = "image{0:d}.bin"
    MANIFEST_FILE_NAME = "IMAGES.mf"

    def dump(self, fp, image: Image, **kws):
        fp.write(self.dumps(image))
        if hasattr(fp, "close"):
            fp.close()

    def dumps(self, image: Image, **kws):
        """Serialize image to binary zip format.

        Note: This format is experimental and not fully implemented yet.
        """
        if hasattr(image, "sections") and not image.sections:
            return b""
        sections = sorted(image.sections, key=lambda x: x.start_address)
        manifest_buffer = io.StringIO()
        out_buffer = io.BytesIO()

        with closing(zipfile.ZipFile(out_buffer, mode="w")) as outFile:
            for idx, section in enumerate(sections):
                section_name = BinZipWriter.SECTION_FILE_NAME.format(idx)
                manifest_buffer.write(section_name)
                manifest_buffer.write("\t")
                manifest_buffer.write(str(section.start_address))
                manifest_buffer.write("\t")
                manifest_buffer.write(str(section.length))
                manifest_buffer.write("\n")

                # Write section data to zip
                outFile.writestr(section_name, bytes(section.data))

            # Write manifest
            manifest_buffer.seek(0)
            outFile.writestr("MANIFEST", manifest_buffer.read())

        out_buffer.seek(0)
        return out_buffer.read()
