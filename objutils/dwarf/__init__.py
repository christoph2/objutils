#!/usr/bin/env python
"""DWARF4 Parser.
"""

__version__ = "0.1.0"
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
from objutils.dwarf.sm import StackMachine
from objutils.elf import model


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
    encoder = ENCODED_ATTRIBUTES[encoding]
    if value in encoder.__members__.values():
        dv = encoder(value).name
        return dv
    else:
        return f"Unknown encoding value ({value})"


@dataclass(frozen=True)
class Attribute:
    encoding: constants.AttributeEncoding
    form: constants.AttributeForm
    special_value: Optional[Any] = None

    def __iter__(self):
        yield self.encoding
        yield self.form
        yield self.special_value


@dataclass(frozen=True)
class Abbrevation:
    tag: str
    children: bool = False
    attrs: List[Any] = field(default_factory=List)


@dataclass
class Readers:
    pass


@dataclass
class DIEAttribute:
    raw_value: Any
    display_value: str

    def toJSON(self):
        print("Hello!?")


@dataclass
class DebugInformationEntry:
    name: str
    attributes: List = field(default_factory=list)
    children: List = field(default_factory=list)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


@dataclass
class DebugInformation:
    die_map: dict[int, DebugInformationEntry]
    die_entries: List[DebugInformationEntry]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Abbrevations:

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
        self.image = section.image
        self.length = len(section.image)
        self.abbrevations = {}

    def get(self, abbr_offset, item):
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
    """ """

    DATATYPES32 = {
        "Addr": (Int32ul, Int32ub),  # 4 - Unsigned program address
    }

    UTF8String = CString(encoding="utf8")

    def __init__(self, elf_parser):

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
        self.installReaders()

    def installReaders(self):
        BASIC_READERS = {
            #      Little    Big
            "u8": (Int8ul, Int8ul),
            "s8": (Int8sl, Int8sl),
            "u16": (Int16ul, Int16ub),
            "s16": (Int16sl, Int16sb),
            "u32": (Int32ul, Int32ub),
            "s32": (Int32sl, Int32sb),
            "u64": (Int64ul, Int64ub),
            "s64": (Int64sl, Int64sb),
            "block2": (Block2l, Block2b),
            "block4": (Block4l, Block4b),
        }
        self.readers = Readers()
        print("SIZE-INFO", 8 if self.b64 else 4, self.endianess)
        self.readers.native_address = Address(8 if self.b64 else 4, self.endianess)
        self.readers.uleb = ULEB
        self.readers.sleb = SLEB
        self.readers.block1 = Block1
        self.readers.block_uleb = BlockUleb
        self.readers.cstring_ascii = CString(encoding="ascii")
        self.readers.cstring_utf8 = CString(encoding="utf8")
        self.readers.strp = StrP(self.strings, self.endianess)
        self.readers.line_strp = StrP(self.line_strings, self.endianess)
        idx = 0 if self.endianess == Endianess.Little else 1
        for name, reader in BASIC_READERS.items():
            setattr(self.readers, name, reader[idx])
        self.stack_machine = StackMachine(self.readers)

    def get_string(self, offset: int):
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
                # key_offset = offset
                # result[key] = Abbrevation(0, False, [])
                print("CONT!!!")
                continue

            abbrv_body = AbbrevationBody.parse(image[offset:])
            tag = abbrv_body.tag
            children = abbrv_body.children
            print("BODY", abbrv_body, constants.Tag(tag).name)
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
                    #
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
        from pprint import pprint

        pprint(result)
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
        print("LineNumber", hdr)
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
        while True:
            section_pos = image.tell()
            if section_pos >= section_length - 1:
                break
            root_element = DebugInformationEntry("root")
            die_stack = [root_element]

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

            print("*" * 80)
            print(f"   Compilation Unit @ offset 0x{dbgInfo.start:x}:")  # TODO: offset is needed for _refx types!!!
            print(f"   Length:        0x{cu_length:x} (32-bit)")
            print(f"   Version:       {version}")
            print(f"   Abbrev Offset: 0x{debug_abbrev_offset:x}")
            print(f"   Pointer Size:  {address_size}")
            level = 0
            pos = 0
            offset += dbgInfo.stop - dbgInfo.start
            form_readers = self.get_form_readers(address_size)
            print("Pos, Length", pos, cu_length)
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
                    print(f"<{start:2x}>: Abbrev Number: 0 ---")
                    level -= 1
                else:
                    die = DebugInformationEntry(abbr.tag)
                    db_die = model.DebugInformationEntry(tag=abbr.tag)
                    self.db_session.add(db_die)
                    if attr.attr != 0:
                        die_stack[-1].children.append(die)
                    print(f"{'   ' * (level + 1)}<{level}><{start:02x}>: Abbrev Number: {attr.attr} ({abbr.tag})")
                    die_start = start
                    if abbr.children:
                        die_stack.append(die)
                        level += 1
                    else:
                        pass
                    if attr.attr == 0:
                        level -= 1
                        if len(die_stack):
                            die_stack.pop()
                        else:
                            print("DIE_STACK empty!!!")
                    for enc, form, special_value in abbr.attrs:
                        reader = form_readers.get(form)
                        start = image.tell()
                        if reader is None:
                            if form == constants.AttributeForm.DW_FORM_implicit_const:
                                print("DW_FORM_implicit_const")
                                value = special_value
                                display_value = value
                                print(f"{'   ' * (level + 1)}<{start:02x}> {enc.name}: {display_value}")
                                die.attributes.append(
                                    (
                                        enc.name,
                                        DIEAttribute(value, display_value),
                                    )
                                )
                                db_die.attributes.append(
                                    model.DIEAttribute(name=enc.name, raw_value=value, display_value=display_value)
                                )
                                offset += attr.stop - attr.start
                                pos = image.tell()
                                if pos >= dbgInfo.start + cu_length + 4:
                                    break
                                continue
                            else:
                                print("*EF", enc, form, start, attr, abbr)
                        try:
                            value = reader.parse_stream(image)
                        except Exception as e:
                            print("EXC", e, reader, form)
                            raise
                        if enc in (
                            constants.AttributeEncoding.location,
                            constants.AttributeEncoding.GNU_call_site_value,
                            constants.AttributeEncoding.frame_base,
                            constants.AttributeEncoding.GNU_call_site_target,
                            constants.AttributeEncoding.vtable_elem_location,
                            constants.AttributeEncoding.data_member_location,
                            constants.AttributeEncoding.return_addr,
                        ):
                            if form in (
                                constants.AttributeForm.DW_FORM_exprloc,
                                constants.AttributeForm.DW_FORM_block,
                                constants.AttributeForm.DW_FORM_block1,
                                constants.AttributeForm.DW_FORM_block2,
                                constants.AttributeForm.DW_FORM_block4,
                            ):
                                display_value = self.dwarf_expression(value)
                            else:
                                try:
                                    display_value = f"0x{value:08x}"
                                except Exception:
                                    print("VALUE", value, enc, form)
                                    raise
                        elif enc in ENCODED_ATTRIBUTES:
                            res = encoding_repr(enc, value)
                            display_value = f"{res} (0x{value:08x})"
                        else:
                            if form in (
                                constants.AttributeForm.DW_FORM_ref1,
                                constants.AttributeForm.DW_FORM_ref2,
                                constants.AttributeForm.DW_FORM_ref4,
                                constants.AttributeForm.DW_FORM_ref8,
                                constants.AttributeForm.DW_FORM_ref_udata,
                            ):
                                value += dbgInfo.start
                                display_value = f"0x{value:08x}"
                            elif form == constants.AttributeForm.DW_FORM_ref_addr:
                                display_value = f"0x{value:08x}"
                            else:
                                display_value = value
                        print(f"{'   ' * (level + 1)}<{start:02x}> {enc.name}: {display_value}")
                        die.attributes.append(
                            (
                                enc.name,
                                DIEAttribute(value, display_value),
                            )
                        )
                        db_die.attributes.append(model.DIEAttribute(name=enc.name, raw_value=value, display_value=display_value))
                    offset += attr.stop - attr.start
                    pos = image.tell()
                    if pos >= dbgInfo.start + cu_length + 4:
                        break
                # print(db_die, db_die.attributes)
                # self.db_session.bulk_save_objects([db_die])
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
                print("ENTRY", entry)
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

    def dwarf_expression(self, expr: bytes) -> str:
        return self.stack_machine.evaluate(expr)

        OPs = constants.Operation
        OPERATIONS_WITH_OPERANDS = {
            OPs.addr: (self.readers.native_address,),
            OPs.const1u: (self.readers.u8,),
            OPs.const1s: (self.readers.s8,),
            OPs.const2u: (self.readers.u16,),
            OPs.const2s: (self.readers.s16,),
            OPs.const4u: (self.readers.u32,),
            OPs.const4s: (self.readers.s32,),
            OPs.const8u: (self.readers.u64,),
            OPs.const8s: (self.readers.s64,),
            OPs.constu: (self.readers.uleb,),
            OPs.consts: (self.readers.sleb,),
            OPs.pick: (self.readers.u8,),
            OPs.plus_uconst: (self.readers.uleb,),
            OPs.bra: (self.readers.s16,),
            OPs.skip: (self.readers.s16,),
            OPs.breg0: (self.readers.sleb,),
            OPs.breg1: (self.readers.sleb,),
            OPs.breg2: (self.readers.sleb,),
            OPs.breg3: (self.readers.sleb,),
            OPs.breg4: (self.readers.sleb,),
            OPs.breg5: (self.readers.sleb,),
            OPs.breg6: (self.readers.sleb,),
            OPs.breg7: (self.readers.sleb,),
            OPs.breg8: (self.readers.sleb,),
            OPs.breg9: (self.readers.sleb,),
            OPs.breg10: (self.readers.sleb,),
            OPs.breg11: (self.readers.sleb,),
            OPs.breg12: (self.readers.sleb,),
            OPs.breg13: (self.readers.sleb,),
            OPs.breg14: (self.readers.sleb,),
            OPs.breg15: (self.readers.sleb,),
            OPs.breg16: (self.readers.sleb,),
            OPs.breg17: (self.readers.sleb,),
            OPs.breg18: (self.readers.sleb,),
            OPs.breg19: (self.readers.sleb,),
            OPs.breg20: (self.readers.sleb,),
            OPs.breg21: (self.readers.sleb,),
            OPs.breg22: (self.readers.sleb,),
            OPs.breg23: (self.readers.sleb,),
            OPs.breg24: (self.readers.sleb,),
            OPs.breg25: (self.readers.sleb,),
            OPs.breg26: (self.readers.sleb,),
            OPs.breg27: (self.readers.sleb,),
            OPs.breg29: (self.readers.sleb,),
            OPs.breg30: (self.readers.sleb,),
            OPs.breg31: (self.readers.sleb,),
            OPs.regx: (self.readers.uleb,),
            OPs.fbreg: (self.readers.sleb,),
            OPs.bregx: (self.readers.uleb, self.readers.sleb),
            OPs.piece: (self.readers.uleb,),
            OPs.deref_size: (self.readers.u8,),
            OPs.xderef_size: (self.readers.u8,),
            OPs.call2: (self.readers.u16,),
            OPs.call4: (self.readers.u32,),
            OPs.call_ref: (self.readers.native_address,),
            OPs.bit_piece: (self.readers.uleb, self.readers.uleb),
            OPs.implicit_value: (self.readers.uleb,),  # todo: array (size os param #0)
            OPs.implicit_pointer: (self.readers.native_address, self.readers.sleb),
            OPs.addrx: (self.readers.uleb,),  # offset into .debug_addr
            OPs.constx: (self.readers.uleb,),  # offset into .debug_addr
            OPs.entry_value: (self.readers.uleb,),  # todo: array (size os param #0)
            OPs.const_type: (self.readers.uleb, self.readers.u8, self.readers.block1),  # todo: array (size os param #1)
            OPs.regval_type: (self.readers.uleb, self.readers.uleb),
            OPs.deref_type: (self.readers.u8, self.readers.uleb),
            OPs.xderef_type: (self.readers.u8, self.readers.uleb),
            OPs.convert: (self.readers.uleb,),
            OPs.reinterpret: (self.readers.uleb,),
            OPs.GNU_entry_value: (self.readers.uleb,),  # todo: array (size os param #0)
            OPs.GNU_const_type: (self.readers.uleb, self.readers.u8, self.readers.block1),  # todo: array (size os param #1)
            OPs.GNU_regval_type: (self.readers.uleb, self.readers.uleb),
            OPs.GNU_deref_type: (self.readers.u8, self.readers.uleb),
            OPs.GNU_convert: (self.readers.uleb,),
            OPs.GNU_reinterpret: (self.readers.uleb,),
            OPs.GNU_parameter_ref: (self.readers.native_address,),
        }
        opcode_num = 0
        image = io.BytesIO(expr)
        result: list[str] = []
        while True:
            data = image.read(1)
            if data == b"":
                break
            opcode_num = data[0]
            try:
                opcode = OPs(opcode_num)
            except ValueError:
                print(f"Opcode not found {opcode_num!r}")
                opcode_name = "<unk>"
            else:
                opcode_name = opcode.name
            print("\tEXPR: ", opcode_num, opcode_name)
            if opcode in OPERATIONS_WITH_OPERANDS:
                for operand in OPERATIONS_WITH_OPERANDS.get(opcode, []):
                    value = operand.parse_stream(image)
                    print(value, end=" ")
                if opcode in (OPs.entry_value, OPs.implicit_value, OPs.GNU_entry_value):
                    data = Array(value, self.readers.u8).parse_stream(image)
                    print("KRASS!!!", opcode, value, list(data))
            else:
                result.append(opcode_name)
        return result
