#!/usr/bin/env python
"""Package entry-point.

Registers CODECS and implements an interface to them.

- :func:`load`
- :func:`loads`
- :func:`probe`
- :func:`probes`
- :func:`dump`
- :func:`dumps`

The first parameter is always the codec name.
"""

__version__ = "0.9.0"

__all__ = [
    "Image",
    "Section",
    "LazySection",
    "InvalidAddressError",
    "registry",
    "load",
    "loads",
    "dump",
    "dumps",
    "probe",
    "probes",
]

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <cpu12.gems@googlemail.com>

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
import os
import sys
from pathlib import Path
from typing import Any, BinaryIO, Optional

from rich import pretty
from rich.console import Console
from rich.traceback import install as tb_install

import objutils.ash
import objutils.binfile
import objutils.cosmac
import objutils.emon52
import objutils.etek
import objutils.fpc
import objutils.ihex
import objutils.mostec
import objutils.rca
import objutils.shf
import objutils.sig
import objutils.srec
import objutils.tek
import objutils.titxt
from objutils.image import Image, InvalidAddressError  # noqa: F401
from objutils.registry import registry
from objutils.section import Section, LazySection  # noqa: F401

# Optional developer-friendly console and tracebacks; disabled by default for library consumers.
_ENABLE_RICH = os.getenv("OBJUTILS_RICH", "0").lower() in {"1", "true", "yes"}
if _ENABLE_RICH and sys.stderr.isatty():
    pretty.install()
    tb_install(show_locals=True, max_frames=3)
    console = Console()
else:
    console = None  # type: ignore[assignment]

registry.register("bin", objutils.binfile.Reader, objutils.binfile.Writer, "Plain binary format.")
registry.register(
    "binzip",
    objutils.binfile.BinZipReader,
    objutils.binfile.BinZipWriter,
    "Zipped binary format.",
)
registry.register("sig", objutils.sig.Reader, objutils.sig.Writer, "Signetics format.")
registry.register(
    "srec",
    objutils.srec.Reader,
    objutils.srec.Writer,
    "Motorola S-Records (a.k.a. S19).",
)
registry.register(
    "titxt",
    objutils.titxt.Reader,
    objutils.titxt.Writer,
    "Texas Instruments MSP430 text format.",
)
registry.register(
    "emon52",
    objutils.emon52.Reader,
    objutils.emon52.Writer,
    "Elektor Monitor (EMON52) file format.",
)
registry.register("etek", objutils.etek.Reader, objutils.etek.Writer, "Extended Tektonix format.")
registry.register("fpc", objutils.fpc.Reader, objutils.fpc.Writer, "Four packed code file format.")
registry.register("ihex", objutils.ihex.Reader, objutils.ihex.Writer, "Intel IHex format.")
registry.register("mostec", objutils.mostec.Reader, objutils.mostec.Writer, "MOSTech format.")
registry.register("rca", objutils.rca.Reader, objutils.rca.Writer, "RCA format.")
registry.register("tek", objutils.tek.Reader, objutils.tek.Writer, "Tektonix format.")
registry.register("cosmac", objutils.cosmac.Reader, objutils.cosmac.Writer, "RCA COSMAC format.")
registry.register("ash", objutils.ash.Reader, objutils.ash.Writer, "ASCII hex space formats.")
registry.register("shf", objutils.shf.Reader, objutils.shf.Writer, "S Hexdump Format (rfc4149).")


def load(codec_name: str, fp: str | Path | BinaryIO, join: bool = False, **kws: Any) -> Image:
    """Load hex data from file.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    class:`Image`
    """
    return registry.get(codec_name).Reader().load(fp, join=join, **kws)


def loads(codec_name: str, data: str | bytes | bytearray, join: bool = False, **kws: Any) -> Image:
    """Load hex data from bytes.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    class:`Image`
    """

    return registry.get(codec_name).Reader().loads(data, join=join, **kws)


def probe(fp: BinaryIO, **kws: Any) -> Optional[str]:
    """Try to guess codec from file.

    Returns
    -------
    str | None
        The detected codec name or None if undetected.
    """
    # Priority order for probing.
    # We prioritize formats with more unique/strict probing logic (like 'sig' vs 'ihex')
    # to avoid false positives.
    priority = ["sig", "srec", "titxt", "shf", "fpc", "ihex"]
    codecs_to_test = []

    # First, the high-priority ones
    for name in priority:
        try:
            codec = registry.get(name)
            codecs_to_test.append((name, codec))
        except Exception:
            pass

    # Then all others
    for name, codec in registry:
        if name not in priority:
            codecs_to_test.append((name, codec))

    for name, codec in codecs_to_test:
        try:
            reader = codec.Reader()
            if hasattr(reader, "probe") and reader.probe(fp, **kws):
                return name
        except Exception:
            pass
    return None


def probes(data: str | bytes | bytearray, **kws: Any) -> Optional[str]:
    """Try to guess codec from bytes.

    Returns
    -------
    str | None
        The detected codec name or None if undetected.
    """
    if isinstance(data, str):
        buffer = io.BytesIO(data.encode("ascii", errors="ignore"))
    else:
        buffer = io.BytesIO(data)

    return probe(buffer, **kws)


def dump(codec_name: str, fp: str | Path | BinaryIO, image: Image, **kws: Any) -> None:
    """Save hex data to file.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    bytes
    """

    registry.get(codec_name).Writer().dump(fp, image, **kws)


def dumps(codec_name: str, image: Image, **kws: Any) -> bytearray:
    """Save hex data to bytearray.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    bytes
    """

    return registry.get(codec_name).Writer().dumps(image, **kws)
