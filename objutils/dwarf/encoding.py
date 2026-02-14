#!/usr/bin/env python

"""DWARF Binary Encoding and Construct Adapters.

This module provides custom Construct library adapters for parsing and building DWARF
binary debug information. It implements DWARF-specific variable-length and fixed-width
encoding schemes including LEB128, SLEB128, and various block formats.

Construct Library Integration:
    The module extends the construct library (https://github.com/construct/construct)
    with custom Construct subclasses that handle DWARF-specific binary encodings.
    Each adapter implements _parse() for reading and _build() for writing operations.

Custom Adapters:
    - ULEB: Unsigned LEB128 (Little-Endian Base-128) variable-length encoding.
    - SLEB: Signed LEB128 (Little-Endian Base-128) variable-length encoding with sign extension.
    - Block1/2/4: Fixed-size block data with 1/2/4-byte little-endian or big-endian length prefix.
    - BlockUleb: Variable-length block data with ULEB128 length prefix.
    - Address: Target architecture address encoding (1/2/4/8 bytes, endian-aware).
    - StrP: String pointer, resolves string offset to string value from debug_str section.
    - ArrayOfCStrings: Sequence of null-terminated C-strings.
    - FilenameSequence: DWARF line number program filename table entries.

Endianness Pattern:
    The Endianess enum (Little=0, Big=1) controls byte order interpretation. Adapters
    that support multiple architectures use this to select appropriate fixed-width
    encodings (e.g., Int32ul for little-endian, Int32ub for big-endian).

Error Handling:
    Custom exception types (ULEBError, SLEBError, ConstructError) provide DWARF-specific
    error messages for debugging binary data issues.

Copyright (C) 2010-2025 by Christoph Schueler
"""

import struct
import time
from dataclasses import dataclass
from enum import IntEnum

from construct import Int8ul, Int16ub, Int16ul, Int32ub, Int32ul, Int64ub, Int64ul
from construct.core import Bytes, Construct, ConstructError, CString, singleton


# from objutils.dwarf.lineprog import Line

NULL_CHAR: bytes = b"\x00"


class Endianess(IntEnum):
    """Byte Order (Endianness) Enumeration.
    
    Specifies the byte order used for multi-byte values in debug information.
    
    Attributes:
        Little (0): Little-endian byte order (least significant byte first).
        Big (1): Big-endian byte order (most significant byte first).
    """
    Little = 0
    Big = 1


class ULEBError(ConstructError):
    """Raised when ULEB128 parsing or building encounters an error."""
    pass


class SLEBError(ConstructError):
    """Raised when SLEB128 parsing or building encounters an error."""
    pass


@singleton
class ULEB(Construct):
    """Unsigned LEB128 (Little-Endian Base-128) Variable-Length Integer.
    
    Parses and builds unsigned variable-length integers using the LEB128 format.
    Each byte encodes 7 bits of data with the high bit as a continuation flag.
    
    Benefits:
        - Compact encoding: Small integers use 1 byte, larger integers use 2-4 bytes.
        - Widely used in DWARF for counts, offsets, and values.
        - Reduces debug information size compared to fixed-width formats.
    
    Examples:
        >>> from io import BytesIO
        >>> stream = BytesIO()
        >>> ULEB.build_stream(0x7F, stream)  # Single byte
        >>> stream.getvalue()
        b'\\x7f'
        >>> ULEB.build_stream(0x80, stream)  # Two bytes
        >>> stream.getvalue()
        b'\\x80\\x01'
    """
    
    def __init__(self, *args) -> None:
        super(__class__, self).__init__()

    def _parse(self, stream, context, path: str | None = None) -> int:
        """Parse a ULEB128-encoded value from stream.
        
        Args:
            stream: Input binary stream positioned at ULEB value.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Decoded unsigned integer value.
            
        Raises:
            ULEBError: If stream read fails or value is malformed.
        """
        result = 0
        shift = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise ULEBError(str(e)) from e
            result |= (bval & 0x7F) << shift
            if bval & 0x80 == 0:
                break
            shift += 7
        return result

    def _build(self, value: int, stream, context, path: str | None = None) -> None:
        """Build ULEB128-encoded bytes for unsigned value into stream.
        
        Args:
            value: Unsigned integer to encode.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
            
        Raises:
            ULEBError: If value is negative.
        """
        if value < 0:
            raise ULEBError("value must be non-negative.")
        result = []
        while True:
            bval = value & 0x7F
            value >>= 7
            if value != 0:
                bval |= 0x80
            result.append(bval)
            if value == 0:
                break
        stream.write(bytes(result))


@singleton
class SLEB(Construct):
    """Signed LEB128 (Little-Endian Base-128) Variable-Length Integer.
    
    Parses and builds signed variable-length integers using the LEB128 format with
    sign extension. The high bit of the last byte determines the sign.
    
    Benefits:
        - Compact encoding for signed values (negative or positive).
        - Negative numbers encoded efficiently with sign extension.
        - Standard DWARF format for signed values.
    
    Examples:
        >>> from io import BytesIO
        >>> stream = BytesIO()
        >>> SLEB.build_stream(-1, stream)  # Single byte: 0x7F
        >>> SLEB.build_stream(-64, stream)  # Two bytes
    """
    
    def __init__(self, *args) -> None:
        super(__class__, self).__init__()

    def _parse(self, stream, context, path: str | None = None) -> int:
        """Parse a SLEB128-encoded value from stream.
        
        Args:
            stream: Input binary stream positioned at SLEB value.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Decoded signed integer value.
            
        Raises:
            SLEBError: If stream read fails.
        """
        result = 0
        shift = 0
        idx = 0
        while True:
            try:
                bval = ord(stream.read(1))
            except Exception as e:
                raise SLEBError(str(e)) from e
            result |= (bval & 0x7F) << shift
            shift += 7
            idx += 1
            if bval & 0x80 == 0:
                break
        if (shift < 32) or (bval & 0x40) == 0x40:
            mask = -(1 << (idx * 7))
            result |= mask
        return result

    def _build(self, value: int, stream, context, path: str | None = None) -> None:
        """Build SLEB128-encoded bytes for signed value into stream.
        
        Args:
            value: Signed integer to encode (positive or negative).
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        result = []
        more = 1
        while more:
            bval = value & 0x7F
            value >>= 7
            if (value == 0 and (bval & 0x40) == 0x00) or (value == -1 and (bval & 0x40) == 0x40):
                more = 0
            else:
                bval |= 0x80
            result.append(bval)
        stream.write(bytes(result))


@singleton
class One(Construct):
    """Special Construct that always represents the value 1.
    
    Used in specific DWARF contexts where a single-byte constant value is needed.
    """
    
    def __init__(self, *args) -> None:
        super(__class__, self).__init__()

    def _parse(self, stream, context, path: str | None = None) -> int:
        """Parse returns constant 1."""
        return 1

    def _build(self, value: int, stream, context, path: str | None = None) -> None:
        """Build writes a single byte with value 1."""
        count = struct.pack("B", 1)
        value = 1
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


class Block(Construct):
    """Base class for DWARF block data with fixed-size length prefix.
    
    Block data consists of a length field (size specified in subclass) followed by
    that many bytes of binary data. Subclasses specify size and byte order.
    
    Attributes:
        BYTEORDER: Byte order indicator for struct.pack/unpack ('<' or '>').
        SIZE: Number of bytes in length prefix (1, 2, or 4).
        MASK: struct format character for length ('B', 'H', or 'L').
    """
    BYTEORDER: str = ""
    SIZE: int | None = None
    MASK: str | None = None

    def __init__(self, *args) -> None:
        super(__class__, self).__init__()

    def _parse(self, stream, context, path: str | None = None) -> bytes:
        """Parse block data with fixed-size length prefix.
        
        Args:
            stream: Input binary stream.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Binary data (bytes).
        """
        msk = f"{self.BYTEORDER}{self.MASK}"
        count = stream.read(self.SIZE)
        count = struct.unpack(msk, count)[0]
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value: bytes | bytearray, stream, context, path: str | None = None) -> None:
        """Build block data with fixed-size length prefix.
        
        Args:
            value: Binary data to encode.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        msk = f"{self.BYTEORDER}{self.MASK}"
        count = struct.pack(msk, len(value))
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


@singleton
class BlockUleb(Block):
    """DWARF Block with ULEB128 Length Prefix.
    
    Variable-length block data where the length is encoded as ULEB128 rather than
    a fixed-width field. Allows compact encoding of arbitrarily large blocks.
    """
    
    def _parse(self, stream, context, path: str | None = None) -> bytes:
        """Parse block with ULEB128 length prefix."""
        count = ULEB.parse_stream(stream)
        result = Bytes(count).parse_stream(stream)
        return result

    def _build(self, value: bytes | bytearray, stream, context, path: str | None = None) -> None:
        """Build block with ULEB128 length prefix."""
        count = ULEB.build(len(value))
        stream.write(count)
        stream.write(bytes(value, encoding="ascii"))


@singleton
class Block1(Block):
    """DWARF Block with 1-Byte Little-Endian Length Prefix.
    
    Block data limited to 0-255 bytes with single-byte length field.
    Form: DW_FORM_block1.
    """
    SIZE = 1
    MASK = "B"
    BYTEORDER = "<"


@singleton
class Block2l(Block):
    """DWARF Block with 2-Byte Little-Endian Length Prefix.
    
    Block data limited to 0-65535 bytes with 2-byte little-endian length field.
    """
    SIZE = 2
    MASK = "H"
    BYTEORDER = "<"


@singleton
class Block2b(Block):
    """DWARF Block with 2-Byte Big-Endian Length Prefix.
    
    Block data limited to 0-65535 bytes with 2-byte big-endian length field.
    """
    SIZE = 2
    MASK = "H"
    BYTEORDER = ">"


@singleton
class Block4l(Block):
    """DWARF Block with 4-Byte Little-Endian Length Prefix.
    
    Block data limited to 0-4GB with 4-byte little-endian length field.
    Form: DW_FORM_block4.
    """
    SIZE = 4
    MASK = "L"
    BYTEORDER = "<"


@singleton
class Block4b(Block):
    """DWARF Block with 4-Byte Big-Endian Length Prefix.
    
    Block data limited to 0-4GB with 4-byte big-endian length field.
    """
    SIZE = 4
    MASK = "L"
    BYTEORDER = ">"


class Address(Construct):
    """DWARF Address Value Encoder/Decoder.
    
    Handles target architecture addresses with configurable size (1/2/4/8 bytes)
    and byte order (little-endian or big-endian).
    
    Attributes:
        TYPES: Mapping of address sizes to (little-endian, big-endian) type pairs.
    """
    TYPES: dict[int, tuple[Construct, Construct]] = {
        1: (Int8ul, Int8ul),
        2: (Int16ul, Int16ub),
        4: (Int32ul, Int32ub),
        8: (Int64ul, Int64ub),
    }

    def __init__(self, size: int, endianess: Endianess) -> None:
        """Initialize Address encoder/decoder.
        
        Args:
            size: Address size in bytes (1, 2, 4, or 8).
            endianess: Byte order (Endianess.Little or Endianess.Big).
            
        Raises:
            ValueError: If size not in (1, 2, 4, 8).
        """
        super(__class__, self).__init__()
        idx = 0 if endianess == Endianess.Little else 1
        if size not in (1, 2, 4, 8):
            raise ValueError(f"Address size '{size}' not supported.")
        if not isinstance(size, int):
            print("**SIZE is not int", size, endianess, idx, type(str))
        if not isinstance(idx, int):
            print("**IDX is not int", size, endianess, idx, type(idx))
        self.type = self.TYPES[size][idx]

    def _parse(self, stream, context, path: str | None = None) -> int:
        """Parse address from stream.
        
        Args:
            stream: Input binary stream.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Address value as integer.
        """
        return self.type.parse_stream(stream)

    def _build(self, value: int, stream, context, path: str | None = None) -> None:
        """Build address into stream.
        
        Args:
            value: Address value to encode.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        stream.write(self.type.build(value))


class StrP(Construct):
    """DWARF String Pointer (debug_str section offset).
    
    Resolves an offset in the debug_str section to the corresponding string value.
    The offset is encoded as a fixed-size field (typically 4 bytes in DWARF4).
    
    Attributes:
        image: Complete debug_str section binary data.
        endianess: Byte order for offset encoding.
        ntype: Construct type for offset field (Int32ul or Int32ub).
        stype: Construct for null-terminated string parsing.
    """
    BYTEORDER: str = ""
    SIZE: int | None = None
    MASK: str | None = None

    def __init__(self, image: bytes, endianess: Endianess) -> None:
        """Initialize string pointer decoder.
        
        Args:
            image: Complete debug_str section data.
            endianess: Byte order (Endianess.Little or Endianess.Big).
        """
        self.image = image
        self.endianess = endianess
        self.ntype = (Int32ul, Int32ub)[0 if endianess == Endianess.Little else 1]
        self.stype = CString(encoding="utf8")
        super(__class__, self).__init__()

    def _parse(self, stream, context, path: str | None = None) -> str:
        """Parse string pointer and resolve to actual string.
        
        Args:
            stream: Input binary stream positioned at offset field.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Resolved string value from debug_str section.
        """
        offset = self.ntype.parse_stream(stream)
        data = self.image[offset:]
        result = self.stype.parse(data)
        return result

    def _build(self, value: str, stream, context, path: str | None = None) -> None:
        """Build string pointer (not typically used for parsing).
        
        Args:
            value: String value.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        stream.write(self.type.build(value))


class ArrayOfCStrings(Construct):
    """Array of Null-Terminated C-Strings.
    
    Parses a sequence of null-terminated strings (C-style) and returns them as a list.
    Terminates when a null string (zero-length) is encountered.
    
    Attributes:
        str_type: Construct for individual string (CString with encoding).
    """

    def __init__(self, encoding: str = "ascii") -> None:
        """Initialize string array decoder.
        
        Args:
            encoding: Character encoding for strings (default: "ascii").
        """
        self.str_type = CString(encoding=encoding)
        super().__init__()

    def _parse(self, stream, context, path: str | None = None) -> list[str]:
        """Parse array of null-terminated strings.
        
        Args:
            stream: Input binary stream.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            List of decoded strings (empty final string not included).
        """
        result = []

        while True:
            value = CString(encoding="utf8").parse_stream(stream)
            if not value:
                break
            result.append(value)
        # term = stream.read(1)
        return result

    def _build(self, values: list[str], stream, context, path: str | None = None) -> None:
        """Build array of null-terminated strings.
        
        Args:
            values: List of strings to encode.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        if values:
            for value in values:
                stream.write(self.str_type.build(value))
        else:
            stream.write(NULL_CHAR)
        # stream.write(NULL_CHAR)


@dataclass
class Filename:
    """DWARF Line Number Program Filename Table Entry.
    
    Represents a single file entry from the line number program's file table.
    
    Attributes:
        name: Source file name.
        dir_index: Index into directory table (0 for compilation directory).
        last_modified: Last modification time (Unix timestamp).
        length: File size in bytes.
    """
    name: str
    dir_index: int
    last_modified: int
    length: int


class FilenameSequence(Construct):
    """DWARF Line Number Program Filename Table.
    
    Parses the filename table from the line number program header. Each entry contains
    a filename, directory index, modification time, and file length. Table is terminated
    by a null filename.
    
    Used in .debug_line section for mapping code addresses to source files.
    """

    def __init__(self, encoding: str = "ascii") -> None:
        """Initialize filename table decoder.
        
        Args:
            encoding: Character encoding for filenames (default: "ascii").
        """
        self.str_type = CString(encoding=encoding)
        super().__init__()

    def _parse(self, stream, context, path: str | None = None) -> dict[int, Filename]:
        """Parse filename table from line number program.
        
        Args:
            stream: Input binary stream positioned at filename table.
            context: Construct parsing context.
            path: Path for error messages.
            
        Returns:
            Dictionary mapping 1-based indices to Filename entries.
        """
        result = {}
        idx = 1
        while True:
            current = stream.tell()
            ch = stream.read(1)
            if ch == NULL_CHAR:
                break
            stream.seek(current)
            name = self.str_type.parse_stream(stream)
            if not name:
                break
            dir_index = ULEB.parse_stream(stream)
            last_mod = ULEB.parse_stream(stream)
            file_length = ULEB.parse_stream(stream)
            result[idx] = Filename(name, dir_index, time.ctime(last_mod), file_length)
            idx += 1
        return result

    def _build(self, values: dict[int, Filename], stream, context, path: str | None = None) -> None:
        """Build filename table.
        
        Args:
            values: Dictionary of Filename entries.
            stream: Output binary stream.
            context: Construct building context.
            path: Path for error messages.
        """
        if values:
            for value in values:
                stream.write(self.str_type.build(value))
        else:
            stream.write(NULL_CHAR)
        stream.write(NULL_CHAR)
