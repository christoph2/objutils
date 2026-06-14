#!/usr/bin/env python
"""OpenOCD ``flash mdb`` text format reader/writer.

This module handles the ASCII hex output produced by the OpenOCD ``flash mdb``
(memory display bytes) command.

Format specification:
- One line per memory region chunk
- Address: ``0x<8 hex digits>`` followed by ``: ``
- Data: space-separated lowercase hex bytes
- Lines are independent – each carries its own start address

Example::

    0x00008000: aa 50 01 02 00 90 00 00 00 50 00 00 6e 76 73 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0x00008020: aa 50 01 00 00 e0 00 00 00 20 00 00 6f 74 61 64 61 74 61 00 00 00 00 00 00 00 00 00 00 00 00 00

Usage::

    import objutils

    img = objutils.load("oocdtxt", "openocd_bytes.txt")
    objutils.dump("ihex", "output.hex", img)
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2026 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any, BinaryIO, Union

import objutils.hexfile as hexfile
from objutils.image import Image
from objutils.section import Section, join_sections

# Matches a full OpenOCD mdb output line:  0x00008000: aa bb cc ...
LINE_PATTERN = re.compile(r"^0x(?P<address>[0-9a-fA-F]{1,8}):\s+(?P<data>(?:[0-9a-fA-F]{2}\s*)+)\s*$")

# Used by the probe() heuristic – just needs to see the characteristic prefix
PROBE_PATTERN = re.compile(r"^0x[0-9a-fA-F]{1,8}:\s+[0-9a-fA-F]{2}")

#: Default bytes per output row (matches the typical ``flash mdb 0xADDR 32`` output)
DEFAULT_ROW_LENGTH = 32


class Reader(hexfile.Reader):
    """OpenOCD ``flash mdb`` text format reader.

    Parses the ASCII hex output of the OpenOCD ``flash mdb`` command into an
    :class:`~objutils.image.Image` object.  Each line must follow the pattern::

        0x<address>: <bb> <bb> ...

    Lines that do not match the pattern are silently skipped so that files
    containing extra context (prompt lines, echo of the command, …) are still
    readable.
    """

    # FORMAT_SPEC is required by the base __init__; we override read() completely
    # (same approach as ASCIIHexReader).
    FORMAT_SPEC = [(0, "0xAAAAAAAA: D")]
    DATA_SEPARATOR = " "

    def read(self, fp: BinaryIO, join: bool = False) -> Image:
        """Parse an OpenOCD mdb text file.

        Args:
            fp: Binary file-like object.
            join: Merge consecutive sections when ``True``.

        Returns:
            :class:`~objutils.image.Image` built from all parsed lines.

        Raises:
            hexfile.ParseError: If no valid records were found.
        """
        sections: list[Section] = []
        content = fp.read()
        text = content.decode(errors="replace") if isinstance(content, (bytes, bytearray)) else content

        for line in text.splitlines():
            match = LINE_PATTERN.match(line.strip())
            if not match:
                continue
            address = int(match.group("address"), 16)
            raw = match.group("data").split()
            data = bytearray(int(b, 16) for b in raw if b)
            if data:
                sections.append(Section(address, data))

        if not sections:
            raise hexfile.ParseError("No valid OpenOCD mdb records found in file.")

        if join:
            sections = join_sections(sections)
        return Image(sections, join=False)

    def probe(self, fp: BinaryIO, **kws: Any) -> bool:
        """Return ``True`` when the file looks like OpenOCD mdb output.

        Reads up to 25 lines and counts how many match the expected pattern.

        Args:
            fp: Binary file-like object.

        Returns:
            ``True`` if at least half of the non-empty lines match.
        """
        start_pos = 0
        try:
            start_pos = fp.tell()
        except (AttributeError, OSError):
            pass

        examined = 0
        matched = 0

        try:
            for _ in range(25):
                line = fp.readline()
                if not line:
                    break
                line_str = line.decode(errors="replace") if isinstance(line, (bytes, bytearray)) else line
                line_str = line_str.strip()
                if not line_str:
                    continue
                examined += 1
                if PROBE_PATTERN.match(line_str):
                    matched += 1
        finally:
            try:
                fp.seek(start_pos)
            except (AttributeError, OSError):
                pass

        if examined == 0:
            return False
        return (matched / examined) >= 0.5

    # Required by the base class but unused when read() is overridden.
    def check_line(self, line: Any, format_type: int) -> None:
        """No-op – validation is performed inline inside :meth:`read`."""

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Always returns ``True`` – every successfully parsed line is a data line."""
        return True


class Writer(hexfile.Writer):
    """OpenOCD ``flash mdb`` text format writer.

    Serialises an :class:`~objutils.image.Image` into the ASCII hex format
    produced by OpenOCD's ``flash mdb`` command.  Each row is written as::

        0x<address>: <bb> <bb> ...

    The default row length is :data:`DEFAULT_ROW_LENGTH` (32 bytes) to match
    typical OpenOCD output, but any value accepted by
    :meth:`~objutils.hexfile.Writer.dump` / :meth:`~objutils.hexfile.Writer.dumps`
    is valid.
    """

    MAX_ADDRESS_BITS = 32

    def dump(self, fp: Union[str, Path, BinaryIO], image: Image, row_length: int = DEFAULT_ROW_LENGTH, **kws: Any) -> None:
        """Write *image* to *fp*.

        Args:
            fp: File path or writable binary file-like object.
            image: Image to serialise.
            row_length: Bytes per output row (default: :data:`DEFAULT_ROW_LENGTH`).
        """
        super().dump(fp, image, row_length=row_length, **kws)

    def dumps(self, image: Image, row_length: int = DEFAULT_ROW_LENGTH, **kws: Any) -> bytearray:
        """Serialise *image* to a :class:`bytearray`.

        Args:
            image: Image to serialise.
            row_length: Bytes per output row (default: :data:`DEFAULT_ROW_LENGTH`).

        Returns:
            Serialised hex file as :class:`bytearray`.
        """
        return super().dumps(image, row_length=row_length, **kws)

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Format a single data row.

        Args:
            address: Start address of the row.
            length: Number of data bytes in the row.
            row: Byte values to encode.

        Returns:
            Formatted string, e.g. ``0x00008000: aa bb cc ...``
        """
        return "0x{:08x}: {}".format(address, " ".join(f"{b:02x}" for b in row))
