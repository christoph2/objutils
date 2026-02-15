#!/usr/bin/env python
# ruff: noqa: E402
# Imports come after module docstring

"""DWARF 4 debug information parser and processor.

This module provides a complete implementation for parsing and processing DWARF 4
debug information from ELF object files. DWARF is a standardized debugging data
format used by compilers to describe program structure, types, variables, and
source locations.

Key Components:
    - **DwarfProcessor**: Main entry point for parsing DWARF sections
    - **DebugInformationEntry (DIE)**: Represents program elements (functions, variables, types)
    - **Abbrevations**: Lookup table for DIE attribute schemas
    - **DwarfReaders**: Architecture-aware binary data parsers
    - **StackMachine**: Evaluates DWARF location expressions

DWARF Section Support:
    - **.debug_info**: Compilation unit structure and DIE tree
    - **.debug_abbrev**: Attribute schema definitions
    - **.debug_str**: String table for shared strings
    - **.debug_line**: Line number program data
    - **.debug_line_str**: Line table string data
    - **.debug_aranges**: Address range mapping (parsed but not processed)

Architecture:
    ```
    ELF File
      └── DwarfProcessor.from_elf()
            ├── Parse .debug_info sections
            ├── Load abbreviation tables (.debug_abbrev)
            ├── Decode compilation units
            └── Build DIE trees
                  ├── DIE attributes (names, types, locations)
                  ├── Location expressions (DW_AT_location)
                  └── Type information (DW_AT_type references)
    ```

Usage Example:
    ```python
    from objutils.elf import model
    from objutils.dwarf import DwarfProcessor
    
    # Load ELF file
    elf = model.Elf("firmware.elf", verbose=False)
    
    # Parse DWARF debug information
    dwarf = DwarfProcessor.from_elf(elf)
    
    # Access compilation units
    for cu in dwarf.compilation_units:
        print(f"CU: {cu.name} (offset: {cu.offset:#x})")
        
        # Traverse DIE tree
        for die in cu.dies:
            if die.tag == "DW_TAG_variable":
                name = die.get_attribute("DW_AT_name")
                location = die.get_attribute("DW_AT_location")
                print(f"Variable: {name} @ {location}")
    ```

Advanced Usage:
    ```python
    # Find specific DIEs by tag
    functions = dwarf.find_dies_by_tag("DW_TAG_subprogram")
    
    # Resolve type references
    for func in functions:
        return_type_ref = func.get_attribute("DW_AT_type")
        return_type_die = dwarf.resolve_die_reference(return_type_ref)
        print(f"{func.name} returns {return_type_die.name}")
    
    # Evaluate location expressions
    var_location_expr = var_die.attributes["DW_AT_location"]
    readers = dwarf.readers
    location_str = readers.dwarf_expression(var_location_expr.form, var_location_expr.value)
    ```

DIE Tree Structure:
    DWARF organizes debug information as a tree of Debug Information Entries:
    
    ```
    DW_TAG_compile_unit (root)
      ├── DW_TAG_subprogram (function)
      │     ├── DW_AT_name: "main"
      │     ├── DW_AT_type: <reference to int>
      │     └── DW_TAG_variable (local variable)
      │           ├── DW_AT_name: "x"
      │           ├── DW_AT_type: <reference>
      │           └── DW_AT_location: <expression>
      └── DW_TAG_base_type
            ├── DW_AT_name: "int"
            ├── DW_AT_byte_size: 4
            └── DW_AT_encoding: DW_ATE_signed
    ```

Abbreviation System:
    DIE structure is defined by abbreviation codes to save space:
    
    - **Abbrev Code**: Identifies the DIE's schema (tag + attributes)
    - **Abbreviation Table**: Maps codes to (tag, has_children, attribute_list)
    - Each compilation unit references its own abbreviation table
    
    This allows compact encoding: DIE stores abbrev code + attribute values only.

Location Expressions:
    DWARF uses expressions to describe variable locations dynamically:
    
    - Stack-based bytecode evaluated at runtime
    - Operations: DW_OP_addr, DW_OP_breg*, DW_OP_plus_uconst, etc.
    - Used for: Variables, struct members, array elements
    - Handles: Registers, frame-relative, optimized-out variables

Type System:
    DWARF represents C/C++ types as DIEs:
    
    - **Base types**: DW_TAG_base_type (int, float, char)
    - **Pointer types**: DW_TAG_pointer_type
    - **Array types**: DW_TAG_array_type + DW_TAG_subrange_type
    - **Struct/union**: DW_TAG_structure_type + DW_TAG_member
    - **Typedef**: DW_TAG_typedef
    - **Const/volatile**: DW_TAG_const_type, DW_TAG_volatile_type

Data Classes:
    The module uses dataclasses for clean data representation:
    
    - **@dataclass Attribute**: Single attribute definition
    - **@dataclass Abbrevation**: DIE schema (tag + attributes)
    - **@dataclass DIEAttribute**: Attribute with parsed value
    - **@dataclass DebugInformationEntry**: Complete DIE with children
    - **@dataclass DebugInformation**: Full compilation unit

Implementation Notes:
    - Lazy parsing: Only requested sections are processed
    - Reference resolution: DIE references use CU-relative offsets
    - Form handling: Each attribute form has specific parsing logic
    - String pooling: Shared strings use .debug_str section
    - Endianness: Architecture-aware via DwarfReaders

DWARF 4 Specification:
    This implementation follows DWARF 4 standard (2010):
    - Section 2: Attribute values and encodings
    - Section 3: Program scope entries (DIE structure)
    - Section 6: Line number information
    - Section 7: Data representation (LEB128, addresses)

Limitations:
    - DWARF 5 features not supported
    - Some vendor extensions not implemented
    - Split DWARF (.dwo files) not supported
    - CFI (Call Frame Information) not parsed

See Also:
    - objutils.dwarf.constants: DWARF tag/attribute/form enums
    - objutils.dwarf.readers: Binary data parsers
    - objutils.dwarf.sm: Stack machine for expressions
    - objutils.dwarf.traverser: High-level DIE tree navigation
    - objutils.dwarf.attrparser: Simplified DIE parsing
    - objutils.elf.model: ELF file parser
"""

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2024 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

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
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, List, Optional

from construct import (
    Array,
    BitStruct,
    Computed,
    CString,
    Enum,
    Flag,
    If,
    IfThenElse,
    Int8sl,
    Int8ul,
    Int16sb,
    Int16sl,
    Int16ub,
    Int16ul,
    Int32sb,
    Int32sl,
    Int32ub,
    Int32ul,
    Int64sb,
    Int64sl,
    Int64ub,
    Int64ul,
    Padding,
    Pass,
    Struct,
    Switch,
    Tell,
    this,
)

from objutils.dwarf import constants
from objutils.dwarf.encoding import (
    SLEB,
    ULEB,
    Address,
    ArrayOfCStrings,
    Block1,
    Block2b,
    Block2l,
    Block4b,
    Block4l,
    BlockUleb,
    Endianess,
    FilenameSequence,
    One,
    StrP,
)
from objutils.dwarf.lineprog import LineNumberProgram
from objutils.dwarf.readers import DwarfReaders
from objutils.dwarf.sm import StackMachine
from objutils.elf import model


# Mapping of attribute encodings to their enum types
ENCODED_ATTRIBUTES = {
    constants.AttributeEncoding.encoding: constants.BaseTypeEncoding,
    constants.AttributeEncoding.decimal_sign: constants.DecimalSign,
    constants.AttributeEncoding.endianity: constants.Endianity,
    constants.AttributeEncoding.accessibility: constants.Accessibility,
    constants.AttributeEncoding.visibility: constants.Visibility,
    constants.AttributeEncoding.virtuality: constants.Virtuality,
    constants.AttributeEncoding.language: constants.Languages,
    constants.AttributeEncoding.identifier_case: constants.IdentifierCase,
    constants.AttributeEncoding.calling_convention: constants.CallingConvention,
    constants.AttributeEncoding.inline: constants.Inline,
    constants.AttributeEncoding.ordering: constants.Ordering,
    constants.AttributeEncoding.discr_list: constants.DiscriminantDescriptor,
    constants.AttributeEncoding.defaulted: constants.Defaulted,
}


def encoding_repr(encoding, value):
    """Convert encoded attribute value to human-readable string.

    Args:
        encoding: Attribute encoding type from constants
        value: Raw integer value to decode

    Returns:
        Enum member name or "Unknown encoding value" string
    """
    encoder = ENCODED_ATTRIBUTES[encoding]
    if value in encoder.__members__.values():
        dv = encoder(value).name
        return dv
    else:
        return f"Unknown encoding value ({value})"


@dataclass(frozen=True)
class Attribute:
    """Attribute definition in abbreviation table.

    Defines structure of a single DIE attribute: what it represents (encoding),
    how it's stored (form), and optional special handling.

    Attributes:
        encoding: Semantic meaning (DW_AT_name, DW_AT_type, etc.)
        form: Binary representation (DW_FORM_string, DW_FORM_data4, etc.)
        special_value: Optional metadata (e.g., implicit const value)
    """

    encoding: constants.AttributeEncoding
    form: constants.AttributeForm
    special_value: Optional[Any] = None

    def __iter__(self):
        yield self.encoding
        yield self.form
        yield self.special_value


@dataclass(frozen=True)
class Abbrevation:
    """DIE schema definition from abbreviation table.

    Abbreviations define the structure of DIEs to reduce file size.
    Each compilation unit has its own abbreviation table.

    Attributes:
        tag: DIE type (DW_TAG_subprogram, DW_TAG_variable, etc.)
        children: Whether DIE has child DIEs (hierarchical structure)
        attrs: List of Attribute definitions for this DIE schema
    """

    tag: str
    children: bool = False
    attrs: list[Any] = field(default_factory=list)


@dataclass
class Readers:
    """Container for binary data readers.

    Dynamically populated with reader instances based on target architecture.
    Used internally by DwarfReaders to organize parsers.
    """

    pass


@dataclass
class DIEAttribute:
    """Parsed DIE attribute with value.

    Represents a single attribute within a DIE, containing both raw binary
    value and human-readable display representation.

    Attributes:
        raw_value: Unparsed binary value (bytes, int, or parsed structure)
        display_value: Human-readable string representation
    """

    raw_value: Any
    display_value: str

    def toJSON(self):
        print("Hello!?")


@dataclass
class DebugInformationEntry:
    """Debug Information Entry (DIE) from DWARF info.

    Represents a single program element (function, variable, type, etc.)
    with attributes and optional children forming a hierarchical tree.

    Attributes:
        name: DIE tag name (e.g., "DW_TAG_subprogram")
        attributes: Dictionary mapping attribute names to DIEAttribute instances
        children: List of child DIEs (for hierarchical structures)

    Example:
        ```python
        # Function DIE with local variable child
        func_die = DebugInformationEntry(
            name="DW_TAG_subprogram",
            attributes={
                "DW_AT_name": DIEAttribute("main", "main"),
                "DW_AT_type": DIEAttribute(0x1234, "<0x1234>")
            },
            children=[var_die]  # Local variable
        )
        ```
    """

    name: str
    attributes: list = field(default_factory=list)
    children: list = field(default_factory=list)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


@dataclass
class DebugInformation:
    """Complete debug information for a compilation unit.

    Contains all DIEs from a single .debug_info compilation unit,
    with both flat (offset-indexed) and hierarchical representations.

    Attributes:
        die_map: Flat mapping of DIE offset -> DIE instance
        die_entries: Hierarchical list of top-level DIEs with children
    """

    die_map: dict[int, DebugInformationEntry]
    die_entries: list[DebugInformationEntry]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Abbrevations:
    """Abbreviation table parser and cache.

    Parses and caches abbreviation definitions from .debug_abbrev section.
    Abbreviations define the schema (tag + attributes) for DIEs, allowing
    compact encoding in .debug_info.

    Structure:
        Each abbreviation entry contains:
        - Code: Unique identifier within the table
        - Tag: DIE type (DW_TAG_*)
        - Children flag: Whether DIE has children
        - Attribute list: (encoding, form) pairs

    Example Abbreviation:
        ```
        Code: 1
        Tag: DW_TAG_subprogram
        Children: yes
        Attributes:
          - DW_AT_name, DW_FORM_string
          - DW_AT_type, DW_FORM_ref4
          - DW_AT_low_pc, DW_FORM_addr
        ```

    Usage:
        ```python
        abbrevs = Abbrevations(debug_abbrev_section)
        schema = abbrevs.get(offset=0, item=1)  # Get abbreviation code 1
        print(schema.tag)  # "DW_TAG_subprogram"
        print(schema.children)  # True
        ```
    """

    AbbrevationHeader = Struct(
        "start" / Tell,
        "code" / ULEB,
        "stop" / Tell,
    )

    AbbrevationBody = Struct(
        "start" / Tell,
        "tag" / ULEB,
        "children" / Int8ul,
        "stop" / Tell,
    )

    AttributeStruct = Struct(
        "start" / Tell,
        "attrValue" / ULEB,
        "formValue" / ULEB,
        "stop" / Tell,
        "next" / Computed((this.attrValue != 0) and (this.formValue != 0)),
    )

    SpecialValueStruct = Struct(
        "start" / Tell,
        "value" / ULEB,
        "stop" / Tell,
    )

    def __init__(self, section):
        """Initialize abbreviation parser.

        Args:
            section: .debug_abbrev section from ELF file
        """
        self.image = section.image
        self.length = len(section.image)
        self.abbrevations = {}

    def get(self, abbr_offset, item):
        """Retrieve abbreviation schema by code.

        Args:
            abbr_offset: Offset into .debug_abbrev section (CU-specific)
            item: Abbreviation code number

        Returns:
            Abbrevation instance or None if code is 0
        """
        if item == 0:
            return None
        if (abbr_offset, item) in self.abbrevations:
            return self.abbrevations.get(
                (
                    abbr_offset,
                    item,
                )
            )
        else:
            return self._fetch(abbr_offset, item)

    def _fetch(self, abbr_offset, item):
        """Parse abbreviation from raw bytes and cache it.

        Parses abbreviation table starting at abbr_offset, caching all
        entries encountered until the requested item is found.

        Args:
            abbr_offset: Start offset in abbreviation section
            item: Target abbreviation code

        Returns:
            Abbrevation instance for the requested code
        """
        offset = abbr_offset
        while True:
            abbrv_header = self.AbbrevationHeader.parse(self.image[offset:])
            # print("ABBREV-CODE", hex(offset), abbrv_header)
            code = abbrv_header.code
            offset += abbrv_header.stop - abbrv_header.start
            if code == 0:
                continue
            key = (
                abbr_offset,
                code,
            )
            if offset >= self.length:
                break
            abbrv_body = self.AbbrevationBody.parse(self.image[offset:])
            tag = abbrv_body.tag
            children = abbrv_body.children
            offset += abbrv_body.stop - abbrv_body.start

            try:
                self.abbrevations[key] = Abbrevation(
                    constants.Tag(tag).name,
                    (children == 1),
                    [],
                )
            except TypeError:
                self.abbrevations[key] = Abbrevation(
                    f"User TAG value: 0x{tag:04x}",
                    (children == 1),
                    [],
                )

            while True:
                attr = self.AttributeStruct.parse(self.image[offset:])
                if not attr.next:
                    # key_offset = offset
                    break
                if attr.formValue == constants.AttributeForm.DW_FORM_implicit_const:
                    offset += attr.stop - attr.start
                    special_value = self.SpecialValueStruct.parse(self.image[offset:])
                    offset += special_value.stop - special_value.start
                    self.abbrevations[key].attrs.append(
                        Attribute(
                            constants.AttributeEncoding(attr.attrValue),
                            constants.AttributeForm(attr.formValue),
                            special_value.value,
                        )
                    )
                    continue
                if attr.attrValue != 0 and attr.formValue != 0:
                    #
                    try:
                        self.abbrevations[key].attrs.append(
                            Attribute(
                                constants.AttributeEncoding(attr.attrValue),
                                constants.AttributeForm(attr.formValue),
                            )
                        )
                    except TypeError:
                        self.abbrevations[key].attrs.append(
                            Attribute(
                                constants.FakeEncoding(attr.attrValue),
                                constants.AttributeForm(attr.formValue),
                            )
                        )
                offset += attr.stop - attr.start
            if code == item:
                return self.abbrevations[key]


class DwarfProcessor:
    """Main DWARF debug information processor.

    Parses and processes DWARF 4 debug sections from ELF files. Provides access
    to compilation units, DIE trees, line number programs, and other debug data.

    Architecture:
        1. Loads DWARF sections from ELF file
        2. Initializes architecture-specific readers (endianness, address size)
        3. Parses abbreviation tables (.debug_abbrev)
        4. Decodes compilation units from .debug_info
        5. Builds hierarchical DIE trees
        6. Resolves string/type references

    Attributes:
        b64: True if 64-bit architecture
        endianess: Target byte order (Endianess.Little or Endianess.Big)
        debug_sections: Dictionary of DWARF sections from ELF
        strings: .debug_str section content (shared string pool)
        line_strings: .debug_line_str section content
        readers: Binary data readers (DwarfReaders.readers)
        stack_machine: Expression evaluator (StackMachine instance)
        compilation_units: List of parsed compilation units

    Usage:
        ```python
        from objutils.elf import model
        from objutils.dwarf import DwarfProcessor

        # Load ELF file
        elf = model.Elf("firmware.elf", verbose=False)

        # Parse DWARF information
        dwarf = DwarfProcessor.from_elf(elf)

        # Access compilation units
        for cu in dwarf.compilation_units:
            print(f"Compilation Unit: {cu.name}")

            # Traverse DIE tree
            for die in cu.dies:
                print(f"  {die.tag}: {die.get('DW_AT_name')}")
        ```

    Advanced Usage:
        ```python
        # Find specific DIEs
        variables = [die for cu in dwarf.compilation_units
                     for die in cu.dies
                     if die.tag == "DW_TAG_variable"]

        # Access line number information
        line_program = dwarf.get_line_program(cu_offset)

        # Evaluate location expressions
        location_expr = var_die.attributes["DW_AT_location"]
        result = dwarf.stack_machine.evaluate(location_expr.value)
        ```

    Supported DWARF Sections:
        - **.debug_info**: Core debug data (required)
        - **.debug_abbrev**: Abbreviation tables (required)
        - **.debug_str**: String table (optional but common)
        - **.debug_line**: Line number programs (optional)
        - **.debug_line_str**: Line table strings (optional)
        - **.debug_aranges**: Address ranges (parsed but not processed)

    Note:
        The processor expects an ELF file with DWARF 4 format debug sections.
        Earlier or later DWARF versions may not parse correctly.
    """

    DATATYPES32 = {
        "Addr": (Int32ul, Int32ub),  # 4 - Unsigned program address
    }

    UTF8String = CString(encoding="utf8")

    def __init__(self, elf_parser):
        """Initialize DWARF processor from ELF parser.

        Args:
            elf_parser: objutils.elf.model.Elf instance with debug sections

        Raises:
            TypeError: If ELF file contains no DWARF sections
        """

        self.b64 = elf_parser.b64
        self.endianess = Endianess.Little if elf_parser.endianess == "<" else Endianess.Big
        self.debug_sections = elf_parser.debug_sections()
        # print(self.debug_sections.keys())
        if not self.debug_sections:
            raise TypeError("File has no DWARF sections.")
        # self.debug_sections = {
        #    section.section_name: section for section in debug_sections
        # }
        if ".debug_str" in self.debug_sections:
            self.strings = self.debug_sections[".debug_str"].image
        else:
            self.strings = b""
        if ".debug_line_str" in self.debug_sections:
            self.line_strings = self.debug_sections[".debug_line_str"].image
        else:
            self.line_strings = b""

        self.db_session = elf_parser.session
        self.install_dwarf_readers()

    def install_dwarf_readers(self):
        """Initialize architecture-specific binary data readers.

        Creates DwarfReaders instance configured for target architecture
        (32/64-bit, little/big-endian) and associates it with this processor.
        """
        # Verwende die neue, wiederverwendbare Readers-Klasse
        address_size = 8 if self.b64 else 4
        factory = DwarfReaders(
            endianess=self.endianess,
            address_size=address_size,
            strings=self.strings,
            line_strings=self.line_strings,
        )
        self.readers = factory.readers
        self.stack_machine = factory.stack_machine

    def get_string(self, offset: int):
        """Retrieve string from .debug_str section.

        Args:
            offset: Byte offset into string table

        Returns:
            Null-terminated string at specified offset
        """
        # self.strings.seek(offset)
        # result = self.UTF8String.parse_stream(self.strings)
        result = str(self.debug_sections[".debug_str"])[offset : offset + 25]
        return bytes(result, encoding="ascii")
        if ".debug_abbrev" in self.debug_sections:
            key = ".debug_abbrev"
        elif ".debug_global_abbrev" in self.debug_sections:
            key = ".debug_global_abbrev"
        else:
            raise TypeError("Neither .debug_abbrev nor .debug_global_abbrev section found")
        section = self.debug_sections[key]
        image = section.image
        length = len(section.image)

        AbbrevationHeader = Struct(
            "start" / Tell,
            "code" / self.readers.uleb,
            "stop" / Tell,
        )

        AbbrevationBody = Struct(
            "start" / Tell,
            "tag" / self.readers.uleb,
            "children" / self.readers.u8,
            "stop" / Tell,
        )

        AttributeStruct = Struct(
            "start" / Tell,
            "attrValue" / self.readers.uleb,
            "formValue" / self.readers.uleb,
            "stop" / Tell,
            "next" / Computed((this.attrValue != 0) and (this.formValue != 0)),
        )

        SpecialValueStruct = Struct(
            "start" / Tell,
            "value" / self.readers.uleb,
            "stop" / Tell,
        )

        offset: int = 0
        result = OrderedDict()
        key_offset: int = offset
        while True:
            abbrv_header = AbbrevationHeader.parse(image[offset:])
            print("ABBREV-CODE", hex(offset), abbrv_header)
            code = abbrv_header.code
            key = (
                key_offset,
                code,
            )
            offset += abbrv_header.stop - abbrv_header.start
            if offset >= length:
                break
            if code == 0:
                continue

            abbrv_body = AbbrevationBody.parse(image[offset:])
            tag = abbrv_body.tag
            children = abbrv_body.children
            offset += abbrv_body.stop - abbrv_body.start

            try:
                result[key] = Abbrevation(
                    constants.Tag(tag).name,
                    (children == 1),
                    [],
                )
            except TypeError:
                result[key] = Abbrevation(
                    f"User TAG value: 0x{tag:04x}",
                    (children == 1),
                    [],
                )

            while True:
                attr = AttributeStruct.parse(image[offset:])
                print("ATTR", attr)
                if not attr.next:
                    # key_offset = offset
                    break
                if attr.formValue == constants.AttributeForm.DW_FORM_implicit_const:
                    offset += attr.stop - attr.start
                    special_value = SpecialValueStruct.parse(image[offset:])
                    offset += special_value.stop - special_value.start
                    result[key].attrs.append(
                        Attribute(
                            constants.AttributeEncoding(attr.attrValue),
                            special_value.value,
                        )
                    )
                    continue
                if attr.attrValue != 0 and attr.formValue != 0:
                    try:
                        result[key].attrs.append(
                            Attribute(
                                constants.AttributeEncoding(attr.attrValue),
                                constants.AttributeForm(attr.formValue),
                            )
                        )
                    except TypeError:
                        result[key].attrs.append(
                            Attribute(
                                constants.FakeEncoding(attr.attrValue),
                                constants.AttributeForm(attr.formValue),
                            )
                        )
                offset += attr.stop - attr.start
            print("Finished Attrs.")
        self.abbrevations = result

    def do_lines(self):
        if ".debug_line" in self.debug_sections:
            key = ".debug_line"
        elif ".debug_global_line" in self.debug_sections:
            key = ".debug_global_line"
        else:
            return
        section = self.debug_sections[key]
        image = io.BytesIO(section.image)
        length = len(section.image)  # noqa: F841

        VersionInformation = Struct("unit_length" / self.readers.u32, "version" / self.readers.u16)
        version_information = VersionInformation.parse_stream(image)
        # print(version_information)

        if version_information.version == 2:
            LineNumberProgramHeader = Struct(
                "prologue_length" / self.readers.u32,
                "minimum_instruction_length" / self.readers.u8,
                "default_is_stmt" / self.readers.u8,
                "line_base" / self.readers.s8,
                "line_range" / self.readers.u8,
                "opcode_base" / self.readers.s8,
                "standard_opcode_lengths" / Array(this.opcode_base - 1, self.readers.u8),
                "include_directories" / ArrayOfCStrings(),
                "file_names" / FilenameSequence(),
            )
        else:
            LineNumberProgramHeader = Struct(
                "header_length" / self.readers.u16,
                "minimum_instruction_length" / self.readers.u8,
                "maximum_operations_per_instruction" / self.readers.u8,
                "default_is_stmt" / self.readers.u8,
                "line_base" / self.readers.s8,
                "line_range" / self.readers.u8,
                "opcode_base" / self.readers.u8,
                "stop" / Tell,
            )

        hdr = LineNumberProgramHeader.parse_stream(image)
        prg = LineNumberProgram(image)  # noqa: F841

    def do_mac_info(self):
        if ".debug_macinfo" in self.debug_sections:
            section = self.debug_sections[".debug_macinfo"]
            image = io.BytesIO(section.image)
            length = len(section.image)

            MacInfo = Struct(
                "start" / Tell,
                "macType"
                / Enum(
                    self.readers.uleb,
                    default=lambda v: v,
                    DW_MACINFO_define=0x01,
                    DW_MACINFO_undef=0x02,
                    DW_MACINFO_start_file=0x03,
                    DW_MACINFO_end_file=0x04,
                    DW_MACINFO_vendor_ext=0xFF,
                ),
                "parameters"
                / Switch(
                    this.macType,
                    {
                        "DW_MACINFO_define": Struct("lineNumber" / self.readers.uleb, "value" / self.readers.cstring_ascii),
                        "DW_MACINFO_undef": Struct("lineNumber" / self.readers.uleb, "value" / self.readers.cstring_ascii),
                        "DW_MACINFO_start_file": Struct("lineNumber" / self.readers.uleb, "fileNumber" / self.readers.uleb),
                        "DW_MACINFO_end_file": Pass,
                        "DW_MACINFO_vendor_ext": Struct("constant" / self.readers.uleb, "value" / self.readers.cstring_ascii),
                    },
                    default=Pass,
                ),
                "stop" / Tell,
            )
            offset = 0
            while True:
                macInfo = MacInfo.parse_stream(image)
                offset += macInfo.stop - macInfo.start
                # print(offset, macInfo)
                if offset >= length - 1:
                    break
        elif ".debug_macro" in self.debug_sections:
            section = self.debug_sections[".debug_macro"]
            image = io.BytesIO(section.image)
            length = len(section.image)

            MacroInformationHeader = Struct(
                "start" / Tell,
                "version" / self.readers.u16,
                "flags"
                / BitStruct(
                    Padding(5),
                    "opcode_operands_table" / Flag,
                    "debug_line_offset" / Flag,
                    "offset_size" / Flag,
                ),
                "debug_line_offset"
                / If(
                    lambda ctx: ctx.flags.debug_line_offset,
                    self.readers.u32,
                ),
                "stop" / Tell,
            )

            MacroInformationHeader.parse_stream(image)

    def get_form_readers(self, addressSize):
        return {
            constants.AttributeForm.DW_FORM_string: self.readers.cstring_utf8,
            constants.AttributeForm.DW_FORM_udata: self.readers.uleb,
            constants.AttributeForm.DW_FORM_sdata: self.readers.sleb,
            constants.AttributeForm.DW_FORM_data1: self.readers.u8,
            constants.AttributeForm.DW_FORM_data2: self.readers.u16,
            constants.AttributeForm.DW_FORM_data4: self.readers.u32,
            constants.AttributeForm.DW_FORM_data8: self.readers.u64,
            constants.AttributeForm.DW_FORM_addr: Address(addressSize, self.endianess),
            constants.AttributeForm.DW_FORM_block: self.readers.block_uleb,
            constants.AttributeForm.DW_FORM_block1: self.readers.block1,
            constants.AttributeForm.DW_FORM_block2: self.readers.block2,
            constants.AttributeForm.DW_FORM_block4: self.readers.block4,
            constants.AttributeForm.DW_FORM_flag: self.readers.u8,
            constants.AttributeForm.DW_FORM_ref_addr: self.readers.u32,
            constants.AttributeForm.DW_FORM_ref1: self.readers.u8,
            constants.AttributeForm.DW_FORM_ref2: self.readers.u16,
            constants.AttributeForm.DW_FORM_ref4: self.readers.u32,
            constants.AttributeForm.DW_FORM_ref8: self.readers.u64,
            constants.AttributeForm.DW_FORM_ref_udata: self.readers.uleb,
            constants.AttributeForm.DW_FORM_strp: self.readers.strp,
            constants.AttributeForm.DW_FORM_indirect: None,  # TODO: uleb value, that represents its form!
            constants.AttributeForm.DW_FORM_sec_offset: self.readers.u32,
            constants.AttributeForm.DW_FORM_exprloc: self.readers.block_uleb,
            constants.AttributeForm.DW_FORM_flag_present: One,
            constants.AttributeForm.DW_FORM_ref_sig8: self.readers.u64,
            constants.AttributeForm.DW_FORM_line_strp: self.readers.line_strp,
            constants.AttributeForm.DW_FORM_implicit_const: None,
        }

    def process_attributes(self, image, readers, size, abbrevOffset):
        Attribute = Struct(
            "start" / Tell,
            "attr" / self.readers.uleb,
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )
        level = 0
        offset = 0
        lastAttr = False
        while True:
            start = image.tell()
            attr = Attribute.parse_stream(image)
            offset += attr.size
            abbr = self.abbrevations.get((abbrevOffset, attr.attr))
            if attr.attr == 0 or not abbr.tag:
                print(f"<{level}><{start:02x}>: Abbrev Number: 0")
                level -= 1
                if lastAttr:
                    break
            else:
                print(abbr.tag.MAP)
                print(f"<{level}><{start:02x}>: Abbrev Number: {attr.attr} ()")
                for enc, form in abbr.attrs:
                    reader = readers.get(form)
                    start = image.tell()
                    if form != constants.DW_FORM_flag_present:
                        value = reader.parse_stream(image)
                    else:
                        value = 1
                    startValue = f"<{start:x}>"
                    print(f"   {startValue:7} {enc.name:20}: {value}")
                    stop = image.tell()
                    offset += stop - start
                    if offset >= size - 1:
                        lastAttr = True
            if hasattr(abbr, "children") and abbr.children:
                level += 1

    def do_dbg_info(self):
        if ".debug_info" in self.debug_sections:
            key = ".debug_info"
        elif ".debug_global_info" in self.debug_sections:
            key = ".debug_global_info"
        else:
            raise TypeError("Neither .debug_info nor .debug_global_info section found")

        if ".debug_abbrev" in self.debug_sections:
            dbg_key = ".debug_abbrev"
        elif ".debug_global_abbrev" in self.debug_sections:
            dbg_key = ".debug_global_abbrev"
        else:
            raise TypeError("Neither .debug_abbrev nor .debug_global_abbrev section found")

        dbg_section = self.debug_sections[dbg_key]
        self.abbrevations = Abbrevations(dbg_section)

        section = self.debug_sections[key]
        image = io.BytesIO(section.image)
        section_length = len(section.image)

        CommonHeader = Struct(
            "start" / Tell,
            "unit_length" / self.readers.u32,
            "version" / self.readers.u16,
            "stop" / Tell,
        )

        UnitHeader5 = Struct(
            "start" / Tell,
            "unit_type" / self.readers.u8,
            "address_size" / self.readers.u8,
            "debug_abbrev_offset" / self.readers.u32,
            "stop" / Tell,
        )

        UnitHeaderClassic = Struct(
            "start" / Tell,
            "debug_abbrev_offset" / self.readers.u32,
            "address_size" / self.readers.u8,
            "stop" / Tell,
        )

        DbgInfo = Struct(
            "start" / Tell,
            "header" / CommonHeader,
            "body" / IfThenElse(this.header.version < 5, UnitHeaderClassic, UnitHeader5),
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )

        Attribute = Struct(
            "start" / Tell,
            "attr" / self.readers.uleb,
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )
        offset = 0
        result = []
        die_map = {}
        idx = 0
        while True:
            section_pos = image.tell()
            if section_pos >= section_length - 1:
                break
            root_element = DebugInformationEntry("root")
            die_stack = [root_element]
            db_die_stack = []

            dbgInfo = DbgInfo.parse_stream(image)  # CU
            # print(dbgInfo)
            cu_length = dbgInfo.header.unit_length
            version = dbgInfo.header.version
            if version < 5:
                debug_abbrev_offset = dbgInfo.body.debug_abbrev_offset
                address_size = dbgInfo.body.address_size
            else:
                debug_abbrev_offset = dbgInfo.body.debug_abbrev_offset
                address_size = dbgInfo.body.address_size
            idx += 1
            print(
                f"   Compilation Unit #{idx:05d}  offset: 0x{dbgInfo.start:08x}  length: 0x{cu_length:08x}  abbrev-offset: 0x{debug_abbrev_offset:08x}  pointer-size:  {address_size}  version: {version}"
            )
            level = 0
            pos = 0
            offset += dbgInfo.stop - dbgInfo.start
            form_readers = self.get_form_readers(address_size)
            if pos >= cu_length:
                break
            while True:
                start = image.tell()
                if start >= dbgInfo.start + cu_length + 4:
                    break
                if start >= section_length - 1:
                    break
                attr = Attribute.parse_stream(image)
                abbr = self.abbrevations.get(debug_abbrev_offset, attr.attr)
                if not abbr:
                    # End of a sibling list: pop one level on both in-memory and DB stacks
                    if level > 0:
                        level -= 1
                    # Pop in-memory DIE stack if we have a nested context (keep root at index 0)
                    if len(die_stack) > 1:
                        die_stack.pop()
                    # Pop DB parent stack so subsequent siblings attach to the correct parent
                    if db_die_stack:
                        db_die_stack.pop()
                else:
                    die = DebugInformationEntry(abbr.tag)
                    db_die = model.DebugInformationEntry(tag=abbr.tag)
                    # Cache-friendly: store DIE offset for quick lookups by external tools
                    db_die.offset = start
                    # Store CU start for reference resolution later
                    db_die.cu_start = dbgInfo.start
                    # Set parent on DB DIE if we have one on stack
                    if db_die_stack:
                        db_die.parent = db_die_stack[-1]
                    self.db_session.add(db_die)
                    if attr.attr != 0:
                        die_stack[-1].children.append(die)
                    die_start = start
                    if abbr.children:
                        die_stack.append(die)
                        # Push this db_die as the current parent for subsequent entries until a null DIE is encountered
                        db_die_stack.append(db_die)
                        level += 1
                    else:
                        pass
                    for enc, form, special_value in abbr.attrs:
                        reader = form_readers.get(form)
                        start = image.tell()
                        if reader is None:
                            if form == constants.AttributeForm.DW_FORM_implicit_const:
                                value = special_value
                                # In-memory representation (keep minimal to preserve structure)
                                die.attributes.append((enc.name, DIEAttribute(value, value)))
                                # DB attribute: store name, form, raw value; display computed lazily
                                db_die.attributes.append(model.DIEAttribute(name=int(enc), form=int(form), raw_value=value))
                                offset += attr.stop - attr.start
                                pos = image.tell()
                                if pos >= dbgInfo.start + cu_length + 4:
                                    break
                                continue
                            else:
                                # Unknown reader; skip gracefully
                                continue
                        try:
                            value = reader.parse_stream(image)
                        except Exception:
                            # Reraise without printing for performance
                            raise
                        # In-memory representation: do not compute heavy display, keep simple
                        die.attributes.append((enc.name, DIEAttribute(value, value)))
                        # DB attribute: store for lazy display
                        try:
                            db_die.attributes.append(model.DIEAttribute(name=int(enc), form=int(form), raw_value=value))
                        except Exception:
                            db_die.attributes.append(model.DIEAttribute(name=int(enc), raw_value=value))
                    offset += attr.stop - attr.start
                    pos = image.tell()
                    if pos >= dbgInfo.start + cu_length + 4:
                        break
                die_map[die_start] = die
            result.append(root_element)
            self.db_session.commit()
        return DebugInformation(die_map, [d.children[0] for d in result])

    def pubnames(self):
        if ".debug_pubnames" not in self.debug_sections:
            return
        section = self.debug_sections[".debug_pubnames"]
        image = io.BytesIO(section.image)
        length = len(section.image)

        Header = Struct(
            "start" / Tell,
            "unit_length" / self.readers.u32,
            "version" / self.readers.u16,
            "debug_info_offset" / self.readers.u32,
            "debug_info_length" / self.readers.u32,
            "stop" / Tell,
        )
        Entry = Struct(
            "start" / Tell,
            "offset" / self.readers.u32,
            "name" / self.readers.cstring_ascii,
            "stop" / Tell,
        )
        offset = 0
        finished = False
        while True:
            if finished:
                break
            header = Header.parse_stream(image)
            offset += header.stop - header.start
            print(offset, header)
            if offset >= length - 1:
                break
            while True:
                entry = Entry.parse_stream(image)
                offset += entry.stop - entry.start
                if entry.offset == 0:
                    break
                if entry.stop >= header.unit_length:
                    finished = True
                    break

    def aranges(self):
        if ".debug_aranges" not in self.debug_sections:
            return
        section = self.debug_sections[".debug_aranges"]
        image = io.BytesIO(section.image)
        length = len(section.image)
        Header = Struct(
            "start" / Tell,
            "unit_length" / self.readers.u32,
            "version" / self.readers.u16,
            "debug_info_offset" / self.readers.u32,
            "address_size" / self.readers.u8,
            "segment_size" / self.readers.u8,
            "stop" / Tell,
        )
        Entry = Struct(
            "start" / Tell,
            "length" / self.readers.u32,
            "address" / self.readers.u32,
            "stop" / Tell,
        )
        offset = 0
        finished = False
        while True:
            if finished:
                break
            header = Header.parse_stream(image)
            offset += header.stop - header.start
            if offset >= length - 1:
                break
            while True:
                entry = Entry.parse_stream(image)
                offset += entry.stop - entry.start
                if entry.address == 0 and entry.length == 0:
                    break
                if entry.stop >= header.unit_length:
                    finished = True
                    break
