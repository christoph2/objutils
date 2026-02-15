#!/usr/bin/env python
"""Codec registry for hex file format readers and writers.

This module implements the central registry that manages all hex file format codecs
in objutils. It provides a singleton-based discovery and lookup mechanism that enables
format-agnostic file loading and conversion.

Architecture
------------
The registry system consists of:

1. **Registry singleton** - Central storage for all format codecs
2. **Codec tuple** - Pairs Reader/Writer classes with format metadata
3. **Automatic registration** - Formats self-register at import time
4. **Format detection** - Unified API for loading any supported format

When you import objutils, all format modules are imported in ``__init__.py``, and
each format registers itself via ``registry.register()``. This allows the high-level
API (``load()``, ``dump()``, etc.) to work with any format without hardcoded knowledge.

Format Registration
-------------------
Format modules register themselves at import time::

    # In objutils/ihex.py
    from objutils.registry import registry

    class Reader(hexfile.Reader):
        # ... implementation ...

    class Writer(hexfile.Writer):
        # ... implementation ...

    # Self-register when module is imported
    registry.register("ihex", Reader, Writer, "Intel HEX format")

After registration, the format is immediately available::

    import objutils
    img = objutils.load("ihex", "firmware.hex")  # Works!

High-Level API Integration
---------------------------
The registry enables the primary objutils API in ``__init__.py``::

    def load(format_name, filename, **kws):
        \"\"\"Load hex file in specified format.\"\"\"
        codec = registry.get(format_name)
        reader = codec.Reader()
        return reader.load(filename, **kws)

    def dump(format_name, filename, image, **kws):
        \"\"\"Write image in specified format.\"\"\"
        codec = registry.get(format_name)
        writer = codec.Writer()
        writer.dump(filename, image, **kws)

This abstraction allows format conversion with consistent API::

    img = objutils.load("srec", "input.srec")   # Load S-Records
    objutils.dump("ihex", "output.hex", img)    # Save as Intel HEX

Supported Formats
-----------------
The registry manages 13+ hex file formats (automatically registered at import):

**Modern formats** (widely used):
- ``ihex`` - Intel HEX (most common embedded format)
- ``srec`` - Motorola S-Records (automotive, embedded)
- ``titxt`` - Texas Instruments TXT format
- ``shf`` - Simple Hex Format (RFC 4194)

**Historical formats** (16-bit only):
- ``ash``, ``cosmac``, ``emon52``, ``etek``, ``fpc``
- ``mostec``, ``rca``, ``sig``, ``tek``

All formats follow the same Reader/Writer protocol defined in :mod:`objutils.hexfile`.

Usage Examples
--------------
**Format discovery**::

    from objutils.registry import registry

    # List all registered formats
    for name, codec in registry:
        print(f"{name}: {codec.description}")

    # Check available formats
    formats = registry.formats
    print(f"Supported: {', '.join(formats)}")

**Direct codec access**::

    # Get specific codec
    codec = registry.get("ihex")
    reader = codec.Reader()
    writer = codec.Writer()

    # Use Reader/Writer directly
    img = reader.load("firmware.hex")
    writer.dump("output.hex", img, row_length=32)

**Format conversion**::

    from objutils.registry import registry

    # Manual conversion
    srec_codec = registry.get("srec")
    ihex_codec = registry.get("ihex")

    img = srec_codec.Reader().load("input.srec")
    ihex_codec.Writer().dump("output.hex", img)

**Error handling**::

    from objutils.registry import registry, CodecDoesNotExistError

    try:
        codec = registry.get("invalid_format")
    except CodecDoesNotExistError as e:
        print(f"Format not found: {e}")
        print(f"Available: {registry.formats}")

**Checking format availability**::

    def supports_format(name):
        try:
            registry.get(name)
            return True
        except CodecDoesNotExistError:
            return False

    if supports_format("ihex"):
        print("Intel HEX is available")

**Iterating all codecs**::

    for format_name, codec in registry:
        reader = codec.Reader()
        writer = codec.Writer()
        print(f"{format_name}:")
        print(f"  Reader: {reader.__class__.__name__}")
        print(f"  Writer: {writer.__class__.__name__}")
        print(f"  Description: {codec.description}")

See Also
--------
- :mod:`objutils.hexfile` - Abstract base classes for readers/writers
- :mod:`objutils.ihex` - Intel HEX format implementation
- :mod:`objutils.srec` - Motorola S-Record format implementation
- :func:`objutils.load` - High-level format loading API
- :func:`objutils.dump` - High-level format writing API

Notes
-----
The Registry uses a singleton pattern, meaning only one registry instance exists
throughout the application lifetime. This ensures consistent format registration
across all objutils modules.

Format names are case-insensitive (``"IHEX"`` == ``"ihex"`` == ``"IHex"``), but
by convention we use lowercase names.

The registry preserves insertion order (uses OrderedDict), so formats are listed
in the order they were registered during ``objutils.__init__`` import.
"""

__copyright__ = """
    objutils - Object file library for Python.

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

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any, NamedTuple

from objutils.utils import SingletonBase


class CodecDoesNotExistError(Exception):
    """Raised when requesting a format codec that is not registered.

    Examples
    --------
    ::

        from objutils.registry import registry, CodecDoesNotExistError

        try:
            codec = registry.get("unknown_format")
        except CodecDoesNotExistError:
            print("Format not registered")
    """

    pass


class CodecAlreadyExistError(Exception):
    """Raised when attempting to register a format that already exists.

    This prevents accidental overwriting of existing format handlers.

    Examples
    --------
    ::

        from objutils.registry import registry, CodecAlreadyExistError

        try:
            registry.register("ihex", MyReader, MyWriter)
        except CodecAlreadyExistError:
            print("Intel HEX already registered")
    """

    pass


class Codec(NamedTuple):
    """Container for format reader, writer, and metadata.

    Attributes
    ----------
    Reader : type
        Reader class for this format (subclass of :class:`objutils.hexfile.Reader`)
    Writer : type
        Writer class for this format (subclass of :class:`objutils.hexfile.Writer`)
    description : str
        Human-readable format description

    Examples
    --------
    ::

        from objutils.registry import registry

        # Access codec components
        codec = registry.get("ihex")
        reader_cls = codec.Reader
        writer_cls = codec.Writer
        desc = codec.description

        # Instantiate reader/writer
        reader = codec.Reader()
        writer = codec.Writer()
    """

    Reader: type[Any]
    Writer: type[Any]
    description: str


class Registry(SingletonBase):
    """Singleton registry for hex file format codecs.

    The Registry maintains a central mapping of format names to their Reader/Writer
    classes. It enables format-agnostic file operations through the high-level
    objutils API.

    This class uses the singleton pattern - only one instance exists throughout the
    application. Access the global instance via the module-level ``registry`` variable.

    Attributes
    ----------
    codecs : OrderedDict[str, Codec]
        Mapping of format names to Codec tuples (read-only property)
    formats : list[str]
        Sorted list of registered format names (read-only property)

    Methods
    -------
    register(name, readerClass, writerClass, description="")
        Register a new format codec
    get(name)
        Retrieve codec for a format name

    Examples
    --------
    **Accessing the registry**::

        from objutils.registry import registry

        # List all formats
        print(registry.formats)
        # ['ash', 'cosmac', 'emon52', 'etek', 'fpc', 'ihex', ...]

        # Iterate codecs
        for name, codec in registry:
            print(f"{name}: {codec.description}")

    **Getting a codec**::

        codec = registry.get("ihex")
        reader = codec.Reader()
        writer = codec.Writer()

    **Registering a new format** (typically done in format modules)::

        from objutils.registry import registry
        from objutils.hexfile import Reader, Writer

        class MyFormatReader(Reader):
            # ... implementation ...

        class MyFormatWriter(Writer):
            # ... implementation ...

        registry.register("myformat", MyFormatReader, MyFormatWriter,
                         "My Custom Format")

    See Also
    --------
    - :class:`Codec` - Tuple containing Reader/Writer classes
    - :mod:`objutils.hexfile` - Abstract base classes
    - :func:`objutils.load` - High-level loading API
    - :func:`objutils.dump` - High-level writing API

    Notes
    -----
    The registry is populated automatically when objutils is imported. Each
    format module registers itself in the module-level code via::

        registry.register("format_name", ReaderClass, WriterClass, "description")

    Format names are case-insensitive but stored and displayed in lowercase.

    The singleton pattern ensures all parts of the application share the same
    registry state, preventing duplicate registrations or inconsistent format
    availability.
    """

    def __init__(self):
        """Initialize empty codec registry.

        This is called only once due to singleton pattern.
        """
        self._codecs: "OrderedDict[str, Codec]" = OrderedDict()

    def __iter__(self) -> Iterator[tuple[str, Codec]]:
        """Iterate over (format_name, codec) pairs.

        Yields
        ------
        tuple[str, Codec]
            Format name and corresponding Codec tuple

        Examples
        --------
        ::

            for name, codec in registry:
                print(f"{name}: {codec.Reader.__name__}")
        """
        return iter(self._codecs.items())

    def _get_codecs(self) -> "OrderedDict[str, Codec]":
        """Get codec mapping (internal property getter)."""
        return self._codecs

    def _get_formats(self) -> list[str]:
        """Get sorted format names (internal property getter)."""
        return sorted(self.codecs.keys())

    def get(self, name: str) -> Codec:
        """Retrieve codec for a format name.

        Parameters
        ----------
        name : str
            Format name (case-insensitive), e.g., "ihex", "srec"

        Returns
        -------
        Codec
            Codec tuple containing Reader, Writer, and description

        Raises
        ------
        CodecDoesNotExistError
            If format name is not registered

        Examples
        --------
        ::

            from objutils.registry import registry

            # Get Intel HEX codec
            codec = registry.get("ihex")
            reader = codec.Reader()
            writer = codec.Writer()

            # Case-insensitive
            codec = registry.get("IHEX")  # Same result

        ::

            # Error handling
            try:
                codec = registry.get("invalid")
            except CodecDoesNotExistError:
                print(f"Available formats: {registry.formats}")
        """
        codec = self.codecs.get(name.lower())
        if not codec:
            raise CodecDoesNotExistError(name)
        return codec

    def register(self, name: str, readerClass: type[Any], writerClass: type[Any], description: str = "") -> None:
        """Register a new format codec.

        Adds a format to the registry, making it available through the high-level
        objutils API. This is typically called at module import time by format
        implementations.

        Parameters
        ----------
        name : str
            Format identifier (lowercase recommended), e.g., "ihex"
        readerClass : type
            Reader class (must subclass :class:`objutils.hexfile.Reader`)
        writerClass : type
            Writer class (must subclass :class:`objutils.hexfile.Writer`)
        description : str, optional
            Human-readable format description (default: "")

        Raises
        ------
        CodecAlreadyExistError
            If format name is already registered

        Examples
        --------
        **Typical usage in a format module**::

            from objutils.registry import registry
            from objutils import hexfile

            class Reader(hexfile.Reader):
                # ... implementation ...

            class Writer(hexfile.Writer):
                # ... implementation ...

            # Self-register at import
            registry.register("myformat", Reader, Writer,
                            "My Custom Hex Format")

        **After registration**::

            import objutils

            # Format is immediately available
            img = objutils.load("myformat", "data.mhf")
            objutils.dump("myformat", "output.mhf", img)

        Notes
        -----
        This method also sets a ``codecName`` attribute on both the Reader and
        Writer classes, allowing them to identify their registered format name::

            reader = codec.Reader()
            print(reader.codecName)  # "myformat"
        """
        if name in self.codecs:
            raise CodecAlreadyExistError(name)
        self._codecs[name] = Codec(readerClass, writerClass, description)
        readerClass.codecName = name
        writerClass.codecName = name

    codecs = property(_get_codecs)
    formats = property(_get_formats)


#: Global registry instance (singleton).
#:
#: This is the primary interface for accessing the format registry.
#: All format modules register themselves with this instance during import.
#:
#: Examples
#: --------
#: ::
#:
#:     from objutils.registry import registry
#:
#:     # List formats
#:     print(registry.formats)
#:
#:     # Get codec
#:     codec = registry.get("ihex")
#:
#:     # Iterate
#:     for name, codec in registry:
#:         print(f"{name}: {codec.description}")
registry = Registry()
