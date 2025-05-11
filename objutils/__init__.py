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

__version__ = "0.7.1"

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
from objutils.image import Image  # noqa: F401
from objutils.registry import registry
from objutils.section import Section  # noqa: F401


pretty.install()


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


console = Console()
tb_install(show_locals=True, max_frames=3)  # Install custom exception handler.


def load(codec_name, *args, **kws):
    """Load hex data from file.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    class:`Image`
    """
    return registry.get(codec_name).Reader().load(*args, **kws)


def loads(codec_name, *args, **kws):
    """Load hex data from bytes.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    class:`Image`
    """

    return registry.get(codec_name).Reader().loads(*args, **kws)


def probe(*args, **kws):
    """Try to guess codec from file.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    str
    """

    found = False
    for _, codec in registry._codecs.items():
        reader = codec.Reader()
        found = reader.probe(*args, **kws)
        if found:
            break
    return reader.codec_name if found else None


def probes(*args, **kws):
    """Try to guess codec from bytes.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    str
    """

    found = False
    for _, codec in registry:
        reader = codec.Reader()
        found = reader.probes(*args, **kws)
        if found:
            break
    return reader.codec_name if found else None


def dump(codec_name, *args, **kws):
    """Save hex data to file.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    bytes
    """

    registry.get(codec_name).Writer().dump(*args, **kws)


def dumps(codec_name, *args, **kws):
    """Save hex data to bytes.

    Parameters
    ----------
    codec_name: str
        Name of a registered codec.

    Returns
    -------
    bytes
    """

    return registry.get(codec_name).Writer().dumps(*args, **kws)
