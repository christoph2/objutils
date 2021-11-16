#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""DWARF4 Parser.
"""

__version__ = "0.1.0"
__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2021 by Christoph Schueler <github.com/Christoph2,
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

from collections import namedtuple, OrderedDict
import io

from construct import CString, Enum, If, Struct
from construct import this
from construct import Computed, Pass, Switch, Tell
from construct import Int16ul, Int32ul, Int64ul, Int8ul
from construct import Int16ub, Int32ub, Int64ub

from objutils.dwarf import constants
from objutils.dwarf.encoding import ULEB, SLEB, Address, StrP, Block1, BlockUleb, One

Abbreviation = namedtuple('Abbreviation', 'tag children attrs')

ident = lambda x: x

class DwarfProcessor:
    """
    """
    DATATYPES32 = {
        "Addr":   (Int32ul, Int32ub),   # 4 - Unsigned program address
    }

    UTF8String = CString(encoding = "utf8")

    def __init__(self, sections, b64, endianess):
        self.b64 = b64
        self.endianess = 1 if endianess == "<" else 0
        debug_sections = sections.fetch(name_pattern = ".debug*")
        self.debug_sections = {section.section_name: section for section in debug_sections}
        if ".debug_str" in self.debug_sections:
            self.strings = self.debug_sections[".debug_str"].section_image
        else:
            self.strings = b""

        #print(self.strings.read())
        self.installReaders()

    def installReaders(self):
        BASIC_READERS = {
            "u8":   (Int8ul, Int8ul),
            "u16":  (Int16ul, Int16ub),
            "u32":  (Int32ul, Int32ub),
            "u64":  (Int64ul, Int64ub)
        }
        idx = 0 if self.endianess == 1 else 1
        for name, reader in BASIC_READERS.items():
            setattr(self, name, reader[idx])

    def get_string(self, offset):
        #self.strings.seek(offset)
        #result = self.UTF8String.parse_stream(self.strings)
        result = str(self.debug_sections[".debug_str"])[offset : offset + 25]
        return bytes(result, encoding = "ascii")


    def do_abbrevs(self):
        section = self.debug_sections['.debug_abbrev']
        image = section.section_image
        length = len(section.section_image)
        Abbrevation = Struct(
            "start" / Tell,
            "code" / ULEB,
            "details" / If(lambda ctx: ctx.code != 0,
            Struct(
                    "tag" / ULEB,
                    "children" / self.u8,
                )
            ),
            "stop" / Tell,
        )
        Attribute = Struct(
            "start" / Tell,
            "attrValue" / ULEB,
            "formValue" / ULEB,
            "stop" / Tell,
            "next"/ Computed((this.attrValue != 0) and (this.formValue != 0)),
        )
        offset = 0
        result = OrderedDict()
        kOffs = offset
        while True:
            print("Offset: {}".format(offset))
            abbrev = Abbrevation.parse(image[offset : ])
            if abbrev.code != 0:
                print("{} {} {}".format(abbrev.code, constants.Tag(abbrev.details.tag), abbrev.details.children == 1))
            key = (kOffs, abbrev.code, )
            offset += abbrev.stop - abbrev.start
            if offset >= length:
                break
            if abbrev.code == 0:
                kOffs = offset
                result[key] = Abbreviation(0, False, [])
                continue
            result[key] = Abbreviation(constants.Tag(abbrev.details.tag), (abbrev.details.children == 1), [])
            while True:
                attr = Attribute.parse(image[offset : ])

                if attr.attrValue != 0 and attr.formValue != 0:
                    result[key].attrs.append((constants.AttributeEncoding(attr.attrValue), constants.AttributeForm(attr.formValue)))
                    print("   {} {}".format(constants.AttributeEncoding(attr.attrValue), constants.AttributeForm(attr.formValue)))
                offset += (attr.stop - attr.start)
                if not attr.next:
                    break
        self.abbreviations = result

    def do_mac_info(self):
        if not '.debug_macinfo' in self.debug_sections:
            return
        section = self.debug_sections['.debug_macinfo']
        image = io.BytesIO(section.section_image)
        length = len(section.section_image)

        MacInfo = Struct(
            "start" / Tell,
            "macType" / Enum(ULEB, default = ident,
                DW_MACINFO_define  = 0x01,
                DW_MACINFO_undef  = 0x02,
                DW_MACINFO_start_file  = 0x03,
                DW_MACINFO_end_file  = 0x04,
                DW_MACINFO_vendor_ext  = 0xff,
            ),
            "parameters" / Switch(this.macType, {
                "DW_MACINFO_define": Struct("lineNumber" / ULEB, "value" / CString(encoding = "ascii")),
                "DW_MACINFO_undef": Struct("lineNumber" / ULEB, "value" / CString(encoding = "ascii")),
                "DW_MACINFO_start_file": Struct("lineNumber" / ULEB, "fileNumber" / ULEB),
                "DW_MACINFO_end_file": Pass,
                "DW_MACINFO_vendor_ext": Struct("constant" / ULEB, "value" / CString(encoding = "ascii")),
            },
                default = Pass,
            ),
            "stop" / Tell,
        )
        offset = 0
        while True:
            macInfo = MacInfo.parse_stream(image)
            offset += macInfo.stop - macInfo.start
            print(offset, macInfo)
            if offset >= length - 1:
                break

    def get_form_readers(self, addressSize):
        return {
            constants.AttributeForm.DW_FORM_string:       CString(encoding = "utf8"),
            constants.AttributeForm.DW_FORM_udata:        ULEB,
            constants.AttributeForm.DW_FORM_sdata:        SLEB,
            constants.AttributeForm.DW_FORM_data1:        self.u8,
            constants.AttributeForm.DW_FORM_data2:        self.u16,
            constants.AttributeForm.DW_FORM_data4:        self.u32,
            constants.AttributeForm.DW_FORM_data8:        self.u64,
            constants.AttributeForm.DW_FORM_addr:         Address(addressSize, self.endianess),
            constants.AttributeForm.DW_FORM_block:        BlockUleb,
            constants.AttributeForm.DW_FORM_block1:       Block1,
            constants.AttributeForm.DW_FORM_block2:       'block2',
            constants.AttributeForm.DW_FORM_block4:       'block4',
            constants.AttributeForm.DW_FORM_flag:         self.u8,
            constants.AttributeForm.DW_FORM_ref_addr:     self.u32,
            constants.AttributeForm.DW_FORM_ref1:         self.u8,
            constants.AttributeForm.DW_FORM_ref2:         self.u16,
            constants.AttributeForm.DW_FORM_ref4:         self.u32,
            constants.AttributeForm.DW_FORM_ref8:         self.u64,
            constants.AttributeForm.DW_FORM_ref_udata:    ULEB,
            constants.AttributeForm.DW_FORM_strp:         StrP(self.strings, self.endianess),
            constants.AttributeForm.DW_FORM_indirect:     None, # TODO: uleb value, that represents its form!
            constants.AttributeForm.DW_FORM_sec_offset:   self.u32,
            constants.AttributeForm.DW_FORM_exprloc:      BlockUleb,
            constants.AttributeForm.DW_FORM_flag_present: One,
            constants.AttributeForm.DW_FORM_ref_sig8:     self.u64,
        }

    def process_attributes(self, image, readers, size, abbrevOffset):
        Attribute = Struct(
            "start" / Tell,
            "attr" / ULEB,
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
            abbr = self.abbreviations.get((abbrevOffset, attr.attr))
            if attr.attr == 0 or not abbr.tag:
                print("<{}><{:02x}>: {}".format(level, start, "Abbrev Number: 0"))
                level -= 1
                if lastAttr:
                    break
            else:
                #print(dir(abbr))
                print(abbr.tag.MAP)
                #print("<{}><{:02x}>: Abbrev Number: {} ({})".format(level, start, attr.attr, abbr.tag.name))
                print("<{}><{:02x}>: Abbrev Number: {} ()".format(level, start, attr.attr, ))
                for enc, form in abbr.attrs:
                    reader = readers.get(form)
                    start = image.tell()
                    if form != constants.DW_FORM_flag_present:
                        value = reader.parse_stream(image)
                    else:
                        value = 1
                    startValue = "<{:x}>".format(start)
                    print("   {:7} {:20}: {}".format(startValue, enc.name, value))
                    stop = image.tell()
                    offset += (stop - start)
                    if offset >= size - 1:
                        lastAttr = True
                pos = image.tell()
            if hasattr(abbr, "children") and abbr.children:
                level += 1

    def process_compile_unit(self, image):
        CompileUnit = Struct(
            "start" / Tell,
            "unit_length" / self.u32,
            "version" / self.u16,
            "debug_abbrev_offset" / self.u32,
            "address_size" / self.u8,
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )
        startPos = image.tell()
        cu = CompileUnit.parse_stream(image)
        print("   Compilation Unit @ offset 0x{:x}:".format(cu.start))
        print("   Length:        0x{:x} (32-bit)".format(cu.unit_length))
        print("   Version:       2".format(cu.version))
        print("   Abbrev Offset: 0x{:x}".format(cu.debug_abbrev_offset))
        print("   Pointer Size:  {}".format(cu.address_size))
        stopPos = image.tell()
        return cu

    def do_dbg_info(self):
        if not '.debug_info' in self.debug_sections:
            return
        section = self.debug_sections['.debug_info']
        image = io.BytesIO(section.section_image)
        length = len(section.section_image)
        DbgInfo = Struct(
            "start" / Tell,
            "unit_length" / self.u32,
            "version" / self.u16,
            "debug_abbrev_offset" / self.u32,
            "address_size" / self.u8,
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )
        Attribute = Struct(
            "start" / Tell,
            "attr" / ULEB,
            "stop" / Tell,
            "size" / Computed(this.stop - this.start),
        )
        offset = 0
        finished = False
        while True:
            pos = image.tell()
            if pos >= length - 1:
                break
            dbgInfo = DbgInfo.parse_stream(image) # CU
            print("   Compilation Unit @ offset 0x{:x}:".format(dbgInfo.start))
            print("   Start:         {:08x}".format(dbgInfo.start))
            print("   Stop:          {:08x}".format(dbgInfo.stop))
            print("   Size:          {:08x}".format(dbgInfo.size))
            print("   Length:        0x{:x} (32-bit)".format(dbgInfo.unit_length))
            print("   Version:       2".format(dbgInfo.version))
            print("   Abbrev Offset: 0x{:x}".format(dbgInfo.debug_abbrev_offset))
            print("   Pointer Size:  {}".format(dbgInfo.address_size))
            pos = 0
            offset += dbgInfo.stop - dbgInfo.start
            formReaders = self.get_form_readers(dbgInfo.address_size)
            print("Pos, Length", pos, dbgInfo.unit_length)
            if pos >= dbgInfo.unit_length:
                break
            while True:
                start = image.tell()
                attr = Attribute.parse_stream(image)
                abbr = self.abbreviations.get((dbgInfo.debug_abbrev_offset, attr.attr))
                if not abbr:
                    print("<{:02x}>: {}".format(start, "Abbrev Number: 0"))
                else:
                    #print("<{:02x}>: Abbrev Number: {} ({})".format(start, enc.name, value))
                    for enc, form in abbr.attrs:
                        reader = formReaders.get(form)
                        if reader is None:
                            print("*EF", enc, form, start, attr, abbr)
                        start = image.tell()
                        value = reader.parse_stream(image)
                        print("    <{:02x}> {}: {}".format(start, enc, value))
                        stop = image.tell()
                    offset += (attr.stop - attr.start)
                    pos = image.tell()
                    #if pos >= 0x8727:
                    #    print("chk")
                    if pos >= dbgInfo.unit_length:
                        image.seek(image.tell() + 1)
                        break

    def pubnames(self):
        if not '.debug_pubnames' in self.debug_sections:
            return
        section = self.debug_sections['.debug_pubnames']
        image = io.BytesIO(section.section_image)
        length = len(section.section_image)

        Header = Struct(
            "start" / Tell,
            "unit_length" / self.u32,
            "version" / self.u16,
            "debug_info_offset" / self.u32,
            "debug_info_length" / self.u32,
            "stop" / Tell,
        )
        Entry = Struct (
            "start" / Tell,
            "offset" / self.u32,
            "name" / CString(encoding = "ascii"),
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
        if not '.debug_aranges' in self.debug_sections:
            return
        section = self.debug_sections['.debug_aranges']
        image = io.BytesIO(section.section_image)
        length = len(section.section_image)
        print("ARANGES")
        Header = Struct(
            "start" / Tell,
            "unit_length" / self.u32,
            "version" / self.u16,
            "debug_info_offset" / self.u32,
            "address_size" / self.u8,
            "segment_size" / self.u8,
            "stop" / Tell,
        )
        Entry = Struct (
            "start" / Tell,
            "length" / self.u32,
            "address" / self.u32,
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
                if entry.address == 0 and entry.length == 0:
                    break
                if entry.stop >= header.unit_length:
                    finished = True
                    break

"""
    dbSecs = ep.debugSections()

    dp = DwarfProcessor(dbSecs, ep.b64, ep.endianess)
    dp.pubnames()
    dp.aranges()
    dp.doAbbrevs()
    dp.processDebugInfo()
    #dp.doMacInfo()
    values = (0x5b6e, 0xcd6, 0x5b6e)
"""
