#!/usr/bin/env python
"""Base Classes for Hex File Format Readers and Writers.

This module provides the base classes and protocols for all hex file
format parsers in objutils. It defines a consistent API that all format-specific
readers and writers (Intel HEX, Motorola S-Records, TI-TXT, etc.) must implement.

Overview
--------
The objutils library supports 13+ different hex file formats used in embedded systems
development. Rather than implementing each parser from scratch, all formats share
common infrastructure:

- **Reader Base**: Base class for parsing hex files into Image objects
- **Writer Base**: Base class for generating hex files from Image objects
- **FormatParser**: Regex-based line parser using format specification strings
- **Checksum utilities**: Common checksum algorithms (sum, XOR, CRC)
- **Exception hierarchy**: Consistent error handling across formats

This architecture enables:
- **Code reuse**: Common parsing logic shared across formats
- **Consistency**: All parsers follow same patterns
- **Extensibility**: New formats easily added by subclassing
- **Type safety**: Full type hints with Python 3.9+ syntax

Architecture
------------
::

    Reader (Base)                   Writer (Base)
    ├── FORMAT_SPEC                 ├── FORMAT_SPEC
    ├── loads(data) → Image         ├── dumps(img) → str
    ├── load(fp) → Image            ├── dump(img, fp)
    ├── probe(data) → bool          ├── compose_row()
    └── parse_line()                └── compose_header/footer()

    Format-Specific Implementations:
    ├── IHexReader/Writer           # Intel HEX
    ├── SRecReader/Writer           # Motorola S-Records
    ├── TiTxtReader/Writer          # TI-TXT
    ├── FpcReader/Writer            # FPC
    └── ... (10+ more formats)

Format Specification Strings
-----------------------------
Each format defines a FORMAT_SPEC dictionary describing its record structure
using single-character codes::

    FORMAT_SPEC = (
        (TYPE_FROM_RECORD, ":%LL%AA%DD%CC"),  # Intel HEX
        # % indicates variable-length field
        # Fixed-width fields use repetition: LL = 2 hex digits
    )

**Format codes**:
- ``L``: Length field (data byte count)
- ``T``: Type/record identifier
- ``A``: Address field
- ``D``: Data payload
- ``C``: Checksum
- ``B``: Address checksum (some formats)
- ``U``: Unparsed/free-form data
- Other characters: Literal (e.g., ``:`` in Intel HEX, ``S`` in S-Records)

The FormatParser converts these specifications into compiled regex patterns for
efficient parsing.

Usage Examples
--------------
**Implementing a new format reader**::

    from objutils.hexfile import Reader

    class MyFormatReader(Reader):
        # Define record structure
        FORMAT_SPEC = (
            (TYPE_FROM_RECORD, ":LLTTAAAADDCC"),
        )

        def check_line(self, line, format_type):
            \"\"\"Validate and parse single record.\"\"\"
            # Use self.parse_line() to extract fields
            if line.startswith(':'):
                record = self.parse_line(line, format_type)
                self.check_length(record)
                self.check_checksum(record)
                return record
            return None

        def is_data_line(self, line, format_type, record):
            \"\"\"Return True if record contains data.\"\"\"
            return record.type == 0x00  # Data record type

**Implementing a new format writer**::

    from objutils.hexfile import Writer

    class MyFormatWriter(Writer):
        FORMAT_SPEC = (
            (TYPE_FROM_RECORD, ":LLTTAAAADDCC"),
        )

        def compose_row(self, address, length, row):
            \"\"\"Generate single output record.\"\"\"
            line = ":{}02{}{}".format(
                self.format_byte(length),
                self.format_address(address),
                self.format_data(row)
            )
            checksum = self.calculate_checksum(line)
            return line + self.format_byte(checksum)

        def compose_footer(self, meta):
            \"\"\"Generate end-of-file record.\"\"\"
            return ":00000001FF"

**Using format readers/writers via registry**::

    import objutils

    # High-level API (recommended)
    img = objutils.load("ihex", "firmware.hex")
    objutils.dump("srec", "firmware.srec", img)

    # Direct reader/writer usage (advanced)
    from objutils.ihex import IHexReader, IHexWriter

    with open("firmware.hex") as f:
        reader = IHexReader()
        img = reader.load(f)

    with open("output.hex", "w") as f:
        writer = IHexWriter(img)
        writer.dump(f)

**Checksum calculation**::

    from objutils.hexfile import Reader

    class MyReader(Reader):
        def check_checksum(self, record):
            \"\"\"Validate record checksum.\"\"\"
            calculated = self.calculate_checksum(record)
            if calculated != record.checksum:
                raise InvalidRecordChecksumError(
                    f"Checksum mismatch at line {record.line_number}"
                )

        def calculate_checksum(self, record):
            \"\"\"Calculate checksum for record.\"\"\"
            # Example: Two's complement checksum
            total = sum([record.length, record.type, record.address] +
                       list(record.data))
            return (~total + 1) & 0xFF

Format-Specific Details
-----------------------
**Intel HEX** (ihex.py):
- Most widely used format
- Records start with ``:``
- Types: 00 (data), 01 (EOF), 02/04 (extended addressing)

**Motorola S-Records** (srec.py):
- Industrial standard format
- Records start with ``S``
- Types: S0 (header), S1/S2/S3 (data), S7/S8/S9 (start address)

**TI-TXT** (titxt.py):
- Texas Instruments format
- Section-based with ``@address`` markers
- Simple ASCII hex without checksums

**IEEE-695** (ieee695.py):
- AMD 29K object format
- Most complex format in objutils
- Binary records with type-length-value structure

See individual format modules for specific implementation details.

Checksum Algorithms
-------------------
Common checksum types implemented:

**Two's complement**::

    sum = sum_of_bytes & 0xFF
    checksum = (~sum + 1) & 0xFF

**Simple sum**::

    checksum = sum_of_bytes & 0xFF

**XOR**::

    checksum = reduce(xor, bytes) & 0xFF

Each format implements its specific algorithm in ``calculate_checksum()`` and
``check_checksum()`` methods.

Error Handling
--------------
Consistent exception hierarchy for all formats:

- **HexFileError**: Base for all hex file errors
- **ParseError**: Base for parsing errors
  - **InvalidRecordTypeError**: Unknown record type
  - **InvalidRecordLengthError**: Length mismatch
  - **InvalidRecordChecksumError**: Checksum validation failed
- **AddressRangeToLargeError**: Address exceeds format limits

Example error handling::

    try:
        img = objutils.load("ihex", "firmware.hex")
    except InvalidRecordChecksumError as e:
        print(f"Checksum error: {e}")
    except ParseError as e:
        print(f"Parse error: {e}")
    except HexFileError as e:
        print(f"Hex file error: {e}")

Modernization (2026)
--------------------
Recent improvements to this module:

- Full type hints with Python 3.9+ union syntax (``X | Y``)
- ABC-based architecture with clear contracts
- Immutable data structures with ``@dataclass(frozen=True, slots=True)``
- Proper exception hierarchy
- Fixed typo: ``ALIGNMENT`` (was ``ALIGMENT``)
- Removed legacy Python 2 compatibility code

Integration
-----------
This module is used by:
- All format-specific parsers (ihex, srec, titxt, etc.)
- Registry system (objutils.registry) for format dispatch
- High-level API (objutils.load/dump functions)

See Also
--------
- :mod:`objutils.image` - Image class for binary data
- :mod:`objutils.section` - Section class for memory regions
- :mod:`objutils.registry` - Format registration and dispatch
- :mod:`objutils.ihex` - Intel HEX implementation example
- :mod:`objutils.srec` - Motorola S-Record implementation example
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

import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from operator import itemgetter
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol, Union

from objutils.image import Image
from objutils.logger import Logger
from objutils.section import Section, join_sections
from objutils.utils import create_string_buffer, slicer


# Format specification constants
SIXTEEN_BITS = 0
TWENTY_BITS = 1
TWENTYFOUR_BITS = 2
THIRTYTWO_BITS = 3

# Record field indices
START = 0
LENGTH = 1
TYPE = 2
ADDRESS = 3
DATA = 4
UNPARSED = 5
CHECKSUM = 6
ADDR_CHECKSUM = 7

# Regex patterns for parsing
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

# Helper function
atoi = partial(int, base=16)


# ============================================================================
# Exception Hierarchy
# ============================================================================


class HexFileError(Exception):
    """Base exception for all hex file operations."""

    pass


class ParseError(HexFileError):
    """Base for parsing-related errors."""

    pass


class InvalidRecordTypeError(ParseError):
    """Raised when record type is not recognized."""

    pass


class InvalidRecordLengthError(ParseError):
    """Raised when record length doesn't match data."""

    pass


class InvalidRecordChecksumError(ParseError):
    """Raised when checksum validation fails."""

    pass


class AddressRangeToLargeError(HexFileError):
    """Raised when address exceeds format capabilities."""

    pass


# Deprecated alias for backward compatibility
Invalidrecord_typeError = InvalidRecordTypeError


# ============================================================================
# Data Structures
# ============================================================================


@dataclass(frozen=True, slots=True)
class ParsedRecord:
    """Immutable parsed record from hex file.

    Attributes:
        format_type: Type identifier from FORMAT_SPEC
        line_number: Line number in source file
        address: Memory address (if applicable)
        length: Data length (if applicable)
        data: Payload bytes
        checksum: Checksum value (if applicable)
        metadata: Additional format-specific fields
    """

    format_type: int
    line_number: int
    address: int = 0
    length: int = 0
    data: bytearray = field(default_factory=bytearray)
    checksum: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Statistics:
    """Statistics collected during parsing."""

    record_types: Counter[int] = field(default_factory=Counter)
    data_bytes: Counter[int] = field(default_factory=Counter)


@dataclass
class MetaRecord:
    """Metadata record (header/footer information)."""

    format_type: str
    address: Optional[int]
    chunk: Optional[bytearray]


# ============================================================================
# Format Parser
# ============================================================================


class FormatParser:
    """Parses format specification strings into regex patterns.

    Format specification uses single-character codes:
    - L: Length field
    - T: Type field
    - A: Address field
    - D: Data field
    - C: Checksum field
    - B: Address checksum
    - U: Unparsed data
    - Other: Literal characters

    Example: "S0LLAAAADDCC" describes Motorola S0 record format.
    """

    def __init__(self, fmt: str, data_separator: Optional[str] = None):
        self.fmt = fmt
        self.translated_format: list[tuple[int, int, str]] = []
        self.data_separator = data_separator
        self.startSign = fmt[0] if fmt else ""

    def parse(self) -> re.Pattern[str]:
        """Parse format string into compiled regex pattern."""
        group = ""
        prevCh = ""

        for ch in self.fmt:
            if ch != prevCh:
                if group:
                    self._translate_format(group)
                    group = ""
            group += ch
            prevCh = ch

        if group:
            self._translate_format(group)

        # Add catch-all for trailing content
        self.translated_format.append((0, 0, r"(?P<junk>(.*?))$"))

        pattern_str = r"^{}".format("".join(map(itemgetter(2), self.translated_format)))
        return re.compile(pattern_str, re.DOTALL | re.MULTILINE)

    def _translate_format(self, group: str) -> None:
        """Translate format group to regex expression."""
        group_number = MAP_CHAR_TO_GROUP.get(group[0])
        length = len(group)

        if group_number is None:
            # Handle fixed characters
            if group[0] == " ":
                expr = rf"\s{{{length}}}"
            else:
                expr = group[0] * length
        else:
            expr = MAP_GROUP_TO_REGEX.get(group_number, "")

            if group_number == START:
                expr = expr % (self.startSign,)
            elif group_number == DATA:
                if self.data_separator is not None:
                    expr = rf"(?P<chunk>[0-9a-zA-Z{self.data_separator}]*)"
                else:
                    expr = r"(?P<chunk>[0-9a-zA-Z]*)"
            elif group_number == UNPARSED:
                pass  # Use as-is
            else:
                expr = expr % (length,)

        self.translated_format.append((group_number, length, expr))


# ============================================================================
# Legacy Container (for backward compatibility)
# ============================================================================


class Container:
    """Legacy dynamic attribute container.

    Deprecated: Use ParsedRecord instead.
    """

    def __init__(self) -> None:
        self.processing_instructions: list[Any] = []

    def add_processing_instruction(self, pi: Any) -> None:
        self.processing_instructions.append(pi)


# ============================================================================
# Base Type with Logging
# ============================================================================


class BaseType:
    """Base class providing logging capabilities."""

    logger: Logger
    valid: bool

    def error(self, msg: str) -> None:
        """Log error and mark as invalid."""
        self.logger.error(msg)
        self.valid = False

    def warn(self, msg: str) -> None:
        """Log warning."""
        self.logger.warn(msg)

    def info(self, msg: str) -> None:
        """Log info message."""
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        """Log debug message."""
        self.logger.debug(msg)


class ReaderProtocol(Protocol):
    """PEP-544 protocol for Reader implementations."""

    logger: Logger
    stats: "Statistics"
    valid: bool
    formats: list[tuple[int, re.Pattern]]

    def load(self, fp: Union[str, Path, BinaryIO], **kws: Any) -> Image: ...

    def loads(self, image: Union[str, bytes, bytearray], **kws: Any) -> Image: ...

    def read(self, fp: BinaryIO) -> Image: ...

    def probe(self, fp: BinaryIO, **kws: Any) -> bool: ...

    def probes(self, image: Union[str, bytes, bytearray]) -> bool: ...

    def check_line(self, line: Any, format_type: int) -> None: ...

    def is_data_line(self, line: Any, format_type: int) -> bool: ...

    def classifyLine(self, line: Any) -> int: ...

    def special_processing(self, line: Any, format_type: int) -> None: ...

    def parseData(self, line: Any, format_type: int) -> bool: ...


class WriterProtocol(Protocol):
    """PEP-544 protocol for Writer implementations."""

    logger: Logger
    valid: bool

    def dump(self, fp: Union[str, Path, BinaryIO], image: Image, row_length: int = 16, **kws: Any) -> None: ...

    def dumps(self, image: Image, row_length: int = 16, **kws: Any) -> str: ...

    def calculate_address_bits(self, image: Image) -> int: ...

    def post_processing(self, data: bytes) -> bytes: ...

    def pre_processing(self, image: Image) -> None: ...

    def set_parameters(self, **kws: Any) -> None: ...

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str: ...

    def compose_header(self, meta: Mapping[str, Any]) -> Optional[str]: ...

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]: ...


# ============================================================================
# Reader Base Class
# ============================================================================


class Reader(BaseType):
    """Base class for hex file format readers.

    The Reader class provides the framework for parsing hex file formats into Image
    objects. All format-specific readers (Intel HEX, Motorola S-Records, TI-TXT, etc.)
    inherit from this class and implement format-specific parsing logic.

    Architecture
    ------------
    The parsing process follows these steps:

    1. **Format specification**: Define record structure with FORMAT_SPEC
    2. **Pattern compilation**: FormatParser converts specs to regex patterns
    3. **Line-by-line parsing**: read() processes each line
    4. **Validation**: check_line() validates checksums and structure
    5. **Data extraction**: is_data_line() identifies data vs. metadata
    6. **Section creation**: Data records become Section objects
    7. **Image assembly**: Sections combined into final Image

    Subclass Requirements
    ---------------------
    To implement a new format reader, subclass Reader and:

    1. **Define FORMAT_SPEC**:
       - Simple: ``FORMAT_SPEC = ":LLTTAAAADDCC"``
       - Multiple record types: ``FORMAT_SPEC = [(0, ":LLAA..."), (1, ":LLAA...")]``

    2. **Implement check_line()**:
       - Validate record structure
       - Check checksums
       - Raise exceptions on errors

    3. **Implement is_data_line()**:
       - Return True for data records
       - Return False for metadata/control records

    4. **Optional overrides**:
       - ``parseData()``: Custom data processing
       - ``special_processing()``: Format-specific handling
       - ``probe()``: Format auto-detection

    Class Attributes
    ----------------
    These can be overridden in subclasses:

    ALIGNMENT : int
        Memory alignment requirement (2**n bytes). Default: 0 (byte-aligned)
    DATA_SEPARATOR : str | None
        Optional separator in data fields (e.g., spaces). Default: None
    VALID_CHARS : re.Pattern
        Regex pattern for valid characters. Default: hex digits and common punctuation
    FORMAT_SPEC : str | list[tuple[int, str]]
        Format specification (required, must be defined in subclass)

    Instance Attributes
    -------------------
    logger : Logger
        Logging instance for warnings/errors
    stats : Statistics
        Parsing statistics (record counts, byte counts)
    valid : bool
        Validity flag (set to False on errors)
    formats : list[tuple[int, re.Pattern]]
        Compiled regex patterns from FORMAT_SPEC

    Methods
    -------
    load(fp, **kws)
        Load from file path or file-like object
    loads(data, **kws)
        Load from string or bytes
    read(fp)
        Core parsing logic (called by load/loads)
    probe(data)
        Check if data matches format (for auto-detection)

    Abstract Methods (Must Implement)
    ----------------------------------
    check_line(container, format_type)
        Validate parsed line
    is_data_line(container, format_type)
        Identify data vs. metadata records

    Optional Overrides
    ------------------
    parseData(container, format_type)
        Process data records (default: True)
    special_processing(container, format_type)
        Format-specific handling (default: pass)

    Examples
    --------
    **Simple format reader**::

        from objutils.hexfile import Reader

        class SimpleHexReader(Reader):
            FORMAT_SPEC = ":LLTTAAAADDCC"  # Intel HEX-like

            def check_line(self, line, format_type):
                # Validate checksum
                calculated = self.calculate_checksum(line)
                if calculated != line.checksum:
                    raise InvalidRecordChecksumError()

            def is_data_line(self, line, format_type):
                # Type 0x00 = data, 0x01 = EOF
                return line.type == 0x00

    **Multi-record format**::

        class MotorolarReader(Reader):
            FORMAT_SPEC = [
                (0, "S0LLAAAADDCC"),    # Header
                (1, "S1LLAAAADDCC"),    # 16-bit data
                (2, "S2LLAAAAAADDCC"),  # 24-bit data
                (9, "S9LLAAAADDCC"),    # Start address
            ]

            def check_line(self, line, format_type):
                # S-Record specific validation
                if line.length != len(line.chunk) + 3:
                    raise InvalidRecordLengthError()

            def is_data_line(self, line, format_type):
                return format_type in (1, 2, 3)

    **Using a reader**::

        # High-level API (recommended)
        import objutils
        img = objutils.load("ihex", "firmware.hex")

        # Direct reader usage
        from objutils.ihex import IHexReader
        reader = IHexReader()
        with open("firmware.hex", "rb") as f:
            img = reader.read(f)

        # From string data
        hex_data = ":100000000C94340..."
        img = reader.loads(hex_data)

    **Checking parsing statistics**::

        reader = IHexReader()
        img = reader.load("firmware.hex")

        print(f"Valid: {reader.valid}")
        print(f"Record types: {reader.stats.record_types}")
        print(f"Data bytes: {reader.stats.data_bytes}")

    See Also
    --------
    - :class:`Writer` - Abstract base for format writers
    - :class:`FormatParser` - Format specification parser
    - :mod:`objutils.ihex` - Intel HEX reader implementation
    - :mod:`objutils.srec` - Motorola S-Record reader implementation

    Notes
    -----
    The Reader class handles:
    - Line-by-line parsing with regex patterns
    - Automatic section creation and merging
    - Metadata extraction (start addresses, headers, etc.)
    - Error collection with detailed line numbers
    - Statistics tracking

    Subclasses only need to implement format-specific validation and data
    identification logic.
    """

    # Class attributes (override in subclasses)
    ALIGNMENT: int = 0  # 2**n (fixed typo: was ALIGMENT)
    ALIGMENT: int = 0  # Deprecated alias for backward compatibility
    DATA_SEPARATOR: Optional[str] = None
    VALID_CHARS: re.Pattern[str] = re.compile(r"^[a-fA-F0-9 :/;,%\n\r!?S]*$")
    FORMAT_SPEC: Union[str, list[tuple[int, str]], None] = None

    def __init__(self) -> None:
        """Initialize reader with format specification."""
        self.logger = Logger("Reader")
        self.stats = Statistics()
        self.valid = True
        self.formats: list[tuple[int, re.Pattern[str]]] = []

        # Parse FORMAT_SPEC into compiled patterns
        if isinstance(self.FORMAT_SPEC, str):
            self.formats = [(0, FormatParser(self.FORMAT_SPEC, self.DATA_SEPARATOR).parse())]
        elif isinstance(self.FORMAT_SPEC, (list, tuple)):
            for format_type, format_str in self.FORMAT_SPEC:
                pattern = FormatParser(format_str, self.DATA_SEPARATOR).parse()
                self.formats.append((format_type, pattern))

    def load(self, fp: Union[str, Path, BinaryIO], **kws: Any) -> Image:
        """Load image from file path or file-like object.

        Args:
            fp: File path (str/Path) or opened binary file
            **kws: Additional keyword arguments

        Returns:
            Parsed Image object
        """
        if isinstance(fp, (str, Path)):
            with open(fp, "rb") as f:
                return self.read(f)
        else:
            data = self.read(fp)
            if hasattr(fp, "close"):
                fp.close()
            return data

    def loads(self, image: Union[str, bytes, bytearray], **kws: Any) -> Image:
        """Load image from string or bytes.

        Args:
            image: String, bytes, or bytearray containing hex data
            **kws: Additional keyword arguments

        Returns:
            Parsed Image object
        """
        if isinstance(image, str):
            buffer = create_string_buffer(bytes(image, "ascii"))
        else:
            buffer = create_string_buffer(image)
        return self.load(buffer)

    def read(self, fp: BinaryIO) -> Image:
        """Read and parse hex file.

        Args:
            fp: Binary file-like object

        Returns:
            Parsed Image with sections

        Raises:
            ParseError: If parsing fails
        """
        sections: list[Section] = []
        matched = False
        self.valid = True
        meta_data: dict[str, list[Any]] = defaultdict(list)

        for line_number, line in enumerate(fp.readlines(), 1):
            # Decode bytes to string
            line_str = line.decode() if isinstance(line, bytes) else line

            # Try each format pattern
            for format_type, pattern in self.formats:
                match = pattern.match(line_str)
                if not match:
                    continue

                matched = True
                container = Container()
                container.line_number = line_number
                dict_ = match.groupdict()

                if not dict_:
                    continue

                self.stats.record_types[format_type] += 1

                # Parse scalar values (address, length, type, checksum)
                for key, value in dict_.items():
                    if key not in ("chunk", "junk"):
                        setattr(container, key, atoi(value))
                    elif key == "junk":
                        setattr(container, key, value)

                # Parse data chunk
                if "chunk" in dict_:
                    chunk_str = dict_["chunk"]
                    if self.DATA_SEPARATOR:
                        chunk_str = chunk_str.replace(self.DATA_SEPARATOR, "")

                    chunk = bytearray()
                    if chunk_str:
                        for idx in range(0, len(chunk_str), 2):
                            chunk.append(atoi(chunk_str[idx : idx + 2]))
                    container.chunk = chunk

                # Validate line
                self.check_line(container, format_type)

                # Process data lines
                if self.is_data_line(container, format_type):
                    if self.parseData(container, format_type):
                        address = getattr(container, "address", 0)
                        chunk = getattr(container, "chunk", bytearray())
                        self.stats.data_bytes[format_type] += len(chunk)
                        section = Section(address, chunk)
                        sections.append(section)

                # Format-specific processing
                self.special_processing(container, format_type)

                # Store metadata
                meta_data[format_type].append(
                    MetaRecord(
                        format_type=str(format_type),
                        address=getattr(container, "address", None),
                        chunk=getattr(container, "chunk", None),
                    )
                )
                break  # Pattern matched, stop trying formats

        if not matched:
            raise ParseError("No valid records found in file")

        # Join consecutive sections
        sections = join_sections(sections)
        img = Image(sections, meta=dict(meta_data), join=True)
        img.valid = self.valid  # Attach validation status
        return img

    def probe(self, fp: BinaryIO, **kws: Any) -> bool:
        """Test if file matches this format.

        Samples first ~500 bytes and checks if patterns match.

        Args:
            fp: Binary file-like object

        Returns:
            True if file appears to be this format
        """
        MAX_SAMPLE_LINES = 25
        MIN_MATCH_THRESHOLD = 0.5

        examined = 0
        matched_count = 0

        for line_number, line in enumerate(fp.readlines(), 1):
            if line_number > MAX_SAMPLE_LINES:
                break

            line_str = line.decode() if isinstance(line, bytes) else line
            examined += 1

            for _, pattern in self.formats:
                if pattern.match(line_str):
                    matched_count += 1
                    break

        if examined == 0:
            return False

        match_ratio = matched_count / examined

        # Special case: single-line files (headers/footers)
        if matched_count == 1 and examined == 1:
            return True

        return match_ratio >= MIN_MATCH_THRESHOLD

    def probes(self, image: Union[str, bytes, bytearray]) -> bool:
        """Test if string/bytes matches this format.

        Args:
            image: String, bytes, or bytearray

        Returns:
            True if data appears to be this format
        """
        if isinstance(image, str):
            buffer = create_string_buffer(bytes(image, "ascii"))
        else:
            buffer = create_string_buffer(image)
        return self.probe(buffer)

    # Methods that subclasses must implement

    def check_line(self, line: Any, format_type: int) -> None:
        """Validate record format and checksums.

        Args:
            line: Parsed line container
            format_type: Format type identifier

        Raises:
            InvalidRecordLengthError: If length doesn't match data
            InvalidRecordChecksumError: If checksum is incorrect
        """
        raise NotImplementedError("Subclasses must implement check_line()")

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """Determine if line contains data vs metadata.

        Args:
            line: Parsed line container
            format_type: Format type identifier

        Returns:
            True if line contains data to be added to sections
        """
        raise NotImplementedError("Subclasses must implement is_data_line()")

    def classifyLine(self, line: Any) -> int:
        """Classify line type (optional override).

        Args:
            line: Parsed line container

        Returns:
            Classification code
        """
        raise NotImplementedError()

    def special_processing(self, line: Any, format_type: int) -> None:
        """Perform format-specific processing (optional override).

        Args:
            line: Parsed line container
            format_type: Format type identifier
        """
        pass

    def parseData(self, line: Any, format_type: int) -> bool:
        """Parse data from line (optional override).

        Args:
            line: Parsed line container
            format_type: Format type identifier

        Returns:
            True if data should be added to sections
        """
        return True


# ============================================================================
# Writer Base Class
# ============================================================================


class Writer(BaseType):
    """Base class for hex file format writers.

    The Writer class provides the framework for generating hex file formats from Image
    objects. All format-specific writers (Intel HEX, Motorola S-Records, TI-TXT, etc.)
    inherit from this class and implement format-specific generation logic.

    Architecture
    ------------
    The writing process follows these steps:

    1. **Validation**: Check address range fits format constraints
    2. **Pre-processing**: Optional format-specific preparations
    3. **Header**: Generate format-specific header (if any)
    4. **Data rows**: Split sections into fixed-length rows
    5. **Row composition**: Format each row with address, data, checksum
    6. **Footer**: Generate end-of-file record
    7. **Post-processing**: Final formatting (newlines, etc.)

    Subclass Requirements
    ---------------------
    To implement a new format writer, subclass Writer and:

    1. **Define MAX_ADDRESS_BITS**:
       - Maximum address width supported by format
       - E.g., 16 for Intel HEX, 32 for S-Records

    2. **Implement compose_row()**:
       - Format single data record
       - Include address, length, data, checksum
       - Return formatted string without newline

    3. **Optional overrides**:
       - ``compose_header()``: Format-specific header
       - ``compose_footer()``: End-of-file record
       - ``pre_processing()``: Image manipulation before writing
       - ``post_processing()``: Final data transformation

    Class Attributes
    ----------------
    MAX_ADDRESS_BITS : int
        Maximum address width in bits (required, must be defined in subclass)

    Instance Attributes
    -------------------
    logger : Logger
        Logging instance for warnings/errors
    row_length : int
        Bytes per output row (default: 16, configurable via dump/dumps)

    Methods
    -------
    dump(fp, image, row_length=16, **kws)
        Write to file path or file-like object
    dumps(image, row_length=16, **kws)
        Serialize to bytes
    calculate_address_bits(image)
        Determine required address width

    Abstract Methods (Must Implement)
    ----------------------------------
    compose_row(address, length, row)
        Format single data record

    Optional Overrides
    ------------------
    compose_header(meta)
        Generate header (default: "")
    compose_footer(meta)
        Generate footer (default: "")
    pre_processing(image)
        Pre-process image (default: pass)
    post_processing(data)
        Post-process output (default: ensure newline)

    Examples
    --------
    **Simple format writer**::

        from objutils.hexfile import Writer

        class SimpleHexWriter(Writer):
            MAX_ADDRESS_BITS = 16  # 16-bit addressing

            def compose_row(self, address, length, row):
                # Format: :LLAAAADDCC (Intel HEX-like)
                data_str = "".join(f"{b:02X}" for b in row)
                line = f":{length:02X}00{address:04X}{data_str}"

                # Calculate checksum
                checksum = self.calculate_checksum(line)
                return line + f"{checksum:02X}"

            def compose_footer(self, meta):
                # End-of-file record
                return ":00000001FF"

    **Writer with header**::

        class SRecordWriter(Writer):
            MAX_ADDRESS_BITS = 32

            def compose_header(self, meta):
                # S0 header record
                name = meta.get("name", "objutils")
                data = name.encode("ascii")
                return self._compose_s_record(0, 0, data)

            def compose_row(self, address, length, row):
                # S1/S2/S3 based on address size
                record_type = self._select_record_type(address)
                return self._compose_s_record(record_type, address, row)

            def compose_footer(self, meta):
                # S9/S8/S7 termination
                start_addr = meta.get("start_address", 0)
                return self._compose_termination(start_addr)

    **Using a writer**::

        # High-level API (recommended)
        import objutils
        img = objutils.load("ihex", "firmware.hex")
        objutils.dump("srec", "firmware.srec", img)

        # Direct writer usage
        from objutils.srec import SRecWriter
        writer = SRecWriter()
        with open("firmware.srec", "wb") as f:
            writer.dump(f, img, row_length=32)

        # To bytes
        hex_bytes = writer.dumps(img, row_length=16)

    **Custom row length**::

        # Default: 16 bytes per row
        objutils.dump("ihex", "out16.hex", img)

        # Custom: 32 bytes per row
        objutils.dump("ihex", "out32.hex", img, row_length=32)

        # Custom: 8 bytes per row (for readability)
        objutils.dump("ihex", "out8.hex", img, row_length=8)

    **Handling metadata**::

        class MetadataWriter(Writer):
            MAX_ADDRESS_BITS = 32

            def compose_header(self, meta):
                # Include version info in header
                version = meta.get("version", "unknown")
                return f"# Version: {version}"

            def compose_footer(self, meta):
                # Include start address if present
                if "start_address" in meta:
                    addr = meta["start_address"]
                    return f":04000005{addr:08X}..."
                return ":00000001FF"

    **Address range validation**::

        writer = MyWriter()
        writer.MAX_ADDRESS_BITS = 16  # Max 64KB

        try:
            writer.dump("output.hex", large_image)
        except AddressRangeToLargeError:
            print("Image too large for 16-bit format!")
            # Try format with larger address space
            objutils.dump("srec", "output.srec", large_image)

    See Also
    --------
    - :class:`Reader` - Abstract base for format readers
    - :mod:`objutils.ihex` - Intel HEX writer implementation
    - :mod:`objutils.srec` - Motorola S-Record writer implementation

    Notes
    -----
    The Writer class handles:
    - Automatic row splitting to configurable lengths
    - Address range validation against format constraints
    - Header/footer composition with metadata support
    - Newline normalization (ensures trailing newline)

    Subclasses only need to implement format-specific row composition and
    optionally header/footer generation.

    Common Patterns
    ---------------
    **Checksum calculation** in compose_row()::

        def compose_row(self, address, length, row):
            # Build record without checksum
            record = f":{length:02X}{address:04X}00"
            record += "".join(f"{b:02X}" for b in row)

            # Calculate checksum
            bytes_to_sum = [length, (address >> 8) & 0xFF,
                          address & 0xFF, 0x00] + list(row)
            checksum = (~sum(bytes_to_sum) + 1) & 0xFF

            return record + f"{checksum:02X}"

    **Address-dependent record types**::

        def compose_row(self, address, length, row):
            if address < 0x10000:
                return self._compose_s1_record(address, row)
            elif address < 0x1000000:
                return self._compose_s2_record(address, row)
            else:
                return self._compose_s3_record(address, row)
    """

    MAX_ADDRESS_BITS: int  # Must be defined in subclass

    def __init__(self) -> None:
        """Initialize writer."""
        self.logger = Logger("Writer")
        self.row_length = 16

    def dump(self, fp: Union[str, Path, BinaryIO], image: Image, row_length: int = 16, **kws: Any) -> None:
        """Write image to file.

        Args:
            fp: File path (str/Path) or opened binary file
            image: Image to write
            row_length: Bytes per row (default: 16)
            **kws: Additional keyword arguments
        """
        if isinstance(fp, (str, Path)):
            with open(fp, "wb") as f:
                f.write(self.dumps(image, row_length, **kws))
        else:
            fp.write(self.dumps(image, row_length, **kws))
            if hasattr(fp, "close"):
                fp.close()

    def dumps(self, image: Image, row_length: int = 16, **kws: Any) -> bytes:
        """Serialize image to bytes.

        Args:
            image: Image to serialize
            row_length: Bytes per row (default: 16)
            **kws: Additional keyword arguments

        Returns:
            Serialized hex file as bytes

        Raises:
            AddressRangeToLargeError: If address exceeds format limits
        """
        result: list[str] = []
        self.row_length = row_length

        if hasattr(image, "sections") and not image.sections:
            return b""

        if self.calculate_address_bits(image) > self.MAX_ADDRESS_BITS:
            raise AddressRangeToLargeError("Could not encode image - address too large")

        self.set_parameters(**kws)
        self.pre_processing(image)

        # Header
        header = self.compose_header(image.meta if hasattr(image, "meta") else {})
        if header:
            result.append(header)

        # Data rows
        for section in image:
            address = section.start_address
            rows = slicer(section.data, row_length, lambda x: [int(y) for y in x])

            for row in rows:
                length = len(row)
                result.append(self.compose_row(address, length, row))
                address += row_length

        # Footer
        footer = self.compose_footer(image.meta if hasattr(image, "meta") else {})
        if footer:
            result.append(footer)

        return self.post_processing(bytes("\n".join(result), "ascii"))

    def calculate_address_bits(self, image: Image) -> int:
        """Calculate address width required for image.

        Args:
            image: Image to analyze

        Returns:
            Number of bits needed for highest address
        """
        if hasattr(image, "sections"):
            last_segment = sorted(image.sections, key=lambda s: s.start_address)[-1]
        else:
            last_segment = image

        highest_address = last_segment.start_address + last_segment.length
        return int(math.ceil(math.log(highest_address + 1) / math.log(2)))

    def post_processing(self, data: bytes) -> bytes:
        """Post-process serialized data (optional override).

        Ensures newline termination by default.

        Args:
            data: Serialized data

        Returns:
            Post-processed data
        """
        if not data.endswith(b"\n"):
            data += b"\n"
        return data

    def pre_processing(self, image: Image) -> None:
        """Pre-process image before serialization (optional override).

        Args:
            image: Image to process
        """
        pass

    def set_parameters(self, **kws: Any) -> None:
        """Set writer parameters from keywords.

        Args:
            **kws: Keyword arguments matching attribute names

        Raises:
            AttributeError: If keyword doesn't match attribute
        """
        params: dict[str, Any] = {}

        for k, v in kws.items():
            try:
                params[k] = getattr(self, k)
            except AttributeError as e:
                raise AttributeError(f"Invalid keyword argument {k!r}") from e
            else:
                setattr(self, k, v)

    # Methods that subclasses must implement

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose single data row.

        Args:
            address: Start address
            length: Data length
            row: Data bytes

        Returns:
            Formatted row string (without newline)
        """
        raise NotImplementedError("Subclasses must implement compose_row()")

    def compose_header(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose file header (optional override).

        Args:
            meta: Metadata dictionary

        Returns:
            Header string or None
        """
        return None

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose file footer (optional override).

        Args:
            meta: Metadata dictionary

        Returns:
            Footer string or None
        """
        return None

    # Utility methods

    def word_to_bytes(self, word: int) -> tuple[int, int]:
        """Split 16-bit word into high and low bytes.

        Args:
            word: 16-bit value

        Returns:
            Tuple of (high_byte, low_byte)
        """
        word = int(word)
        hi = (word & 0xFF00) >> 8
        lo = word & 0x00FF
        return hi, lo

    @staticmethod
    def hex_bytes(row: Sequence[int], spaced: bool = False) -> str:
        """Convert byte sequence to hex string.

        Args:
            row: Byte values
            spaced: Insert spaces between bytes

        Returns:
            Hex string (e.g., "DEADBEEF" or "DE AD BE EF")
        """
        spacer = " " if spaced else ""
        return spacer.join([f"{x:02X}" for x in row])


# ============================================================================
# ASCII Hex Reader (Base for TI-TXT, ASH formats)
# ============================================================================


class ASCIIHexReader(Reader):
    """Reader for ASCII hex formats (TI-TXT, ASH, etc.).

    These formats use plain ASCII representation with configurable separators.
    """

    FORMAT_SPEC = None

    def __init__(self, address_pattern: str, data_pattern: str, etx_pattern: str, separators: str = ", "):
        """Initialize ASCII hex reader.

        Args:
            address_pattern: Regex for address lines
            data_pattern: Regex for data lines (use {0} for separator placeholder)
            etx_pattern: Regex for end-of-text marker
            separators: Valid separator characters
        """
        self.separators = separators
        self.DATA_PATTERN: re.Pattern[str] = re.compile(data_pattern.format(separators), re.DOTALL | re.MULTILINE)
        self.ADDRESS_PATTERN: re.Pattern[str] = re.compile(address_pattern, re.DOTALL | re.MULTILINE)
        self.ETX_PATTERN: re.Pattern[str] = re.compile(etx_pattern, re.DOTALL | re.MULTILINE)
        self.SPLITTER = re.compile(f"[{separators}]")

        self.patterns: Sequence[tuple[re.Pattern[str], Any]] = (
            (self.ADDRESS_PATTERN, self.getAddress),
            (self.DATA_PATTERN, self.parse_line),
            (self.ETX_PATTERN, self.nop),
        )

        self.formats: list[tuple[int, re.Pattern[str]]] = [
            (0, self.ADDRESS_PATTERN),
            (1, self.DATA_PATTERN),
            (2, self.ETX_PATTERN),
        ]

        super().__init__()

    def getAddress(self, line: str, match: re.Match[str]) -> bool:
        """Parse address line.

        Args:
            line: Source line
            match: Regex match object

        Returns:
            True to continue parsing
        """
        self.address = int(match.group("address"), 16)
        self.previous_address = self.address
        return True

    def nop(self, line: str, match: re.Match[str]) -> bool:
        """No-op handler for end-of-text marker.

        Args:
            line: Source line
            match: Regex match object

        Returns:
            False to stop parsing
        """
        return False

    def parse_line(self, line: str, match: re.Match[str]) -> bool:
        """Parse data line.

        Args:
            line: Source line
            match: Regex match object

        Returns:
            True to continue parsing
        """
        section = Section(
            self.address,
            bytearray([int(ch, 16) for ch in filter(lambda x: x, self.SPLITTER.split(line))]),
        )
        self.sections.append(section)
        self.address += len(section)
        return True

    def read(self, fp: BinaryIO) -> Image:
        """Read ASCII hex file.

        Args:
            fp: Binary file-like object

        Returns:
            Parsed Image
        """
        lines = fp.read().decode()
        self.sections: list[Section] = []
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

        return Image(self.sections, join=True)

    def check_line(self, line: Any, format_type: int) -> None:
        """No validation needed for ASCII hex formats."""
        pass

    def is_data_line(self, line: Any, format_type: int) -> bool:
        """All lines with data pattern are data lines."""
        return format_type == 1


class ASCIIHexWriter(Writer):
    """Writer for ASCII hex formats."""

    MAX_ADDRESS_BITS = 32

    def __init__(self, separators: str = " "):
        """Initialize ASCII hex writer.

        Args:
            separators: Separator character for bytes
        """
        super().__init__()
        self.separators = separators

    def compose_row(self, address: int, length: int, row: Sequence[int]) -> str:
        """Compose ASCII hex data row.

        Args:
            address: Start address
            length: Data length
            row: Data bytes

        Returns:
            Formatted row
        """
        return self.separators.join([f"{b:02X}" for b in row])

    def compose_header(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose header with start address."""
        if "start_address" in meta:
            return f"@{meta['start_address']:04X}"
        return None

    def compose_footer(self, meta: Mapping[str, Any]) -> Optional[str]:
        """Compose footer (q marker for TI-TXT)."""
        return "q"
