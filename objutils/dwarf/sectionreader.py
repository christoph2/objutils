#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <github.com/Christoph2,
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

from collections import namedtuple

from objutils.dwarf import constants
from objutils.dwarf.dwarfreader import DwarfReader
from objutils.dwarf.locinfo import Dissector

AbbreviationEntry = namedtuple('Abbreviation', 'tag, children, attrs')
InfoHeader = namedtuple('InfoHeader', 'length dwarfVersion abbrevOffs targetAddrSize')

DW_LNS_extended_op = 0

SET_OFFSET      = 1
IGNORE_OFFSET   = 2


FORM_READERS = {
    constants.DW_FORM_string:       'asciiz',
    constants.DW_FORM_udata:        'uleb',
    constants.DW_FORM_sdata:        'sleb',
    constants.DW_FORM_data1:        'u8',
    constants.DW_FORM_data2:        'u16',
    constants.DW_FORM_data4:        'u32',
    constants.DW_FORM_data8:        'u64',
    constants.DW_FORM_addr:         'addr',
    constants.DW_FORM_block:        'block',
    constants.DW_FORM_block1:       'block1',
    constants.DW_FORM_block2:       'block2',
    constants.DW_FORM_block4:       'block4',
    constants.DW_FORM_flag:         'u8',
    constants.DW_FORM_ref_addr:     'u32',
    constants.DW_FORM_ref1:         'u8',
    constants.DW_FORM_ref2:         'u16',
    constants.DW_FORM_ref4:         'u32',
    constants.DW_FORM_ref8:         'u64',
    constants.DW_FORM_ref_udata:    'uleb',
    ###
    constants.DW_FORM_strp:         'strp', # TODO: This is a offset into string table (.debug_str)!!!
    constants.DW_FORM_indirect:     '', # TODO: uleb value, that represents its form!
    constants.DW_FORM_sec_offset:   '', # This is an offset into the .debug_line/.debug_loc /.debug_macinfo section, p. 162ff
    constants.DW_FORM_exprloc:      '', # This is an unsigned LEB128 length followed by the number of information
                                        # bytes specified by the length (DW_FORM_exprloc).
    constants.DW_FORM_flag_present: '', #  the attribute is implicitly indicated as present, and no value is
                                        # encoded in the debugging information entry itself
    constants.DW_FORM_ref_sig8:     'u64',
}


class LNSregisters(object):
    """Registers of Line number information State-machine.
    """
    address  = 0
    op_index = 0
    fileNumber = 1
    line = 1
    column = 0
    is_stmt = False     # determined by default_is_stmt in the line number program header
    basic_block = False
    end_sequence = False
    prologue_end = False
    epilogue_begin = False
    isa = 0
    discriminator = 0
    #
    offset = 0

    def __init__(self, is_stmt, offset):
        self.is_stmt = is_stmt
        self.offset = offset


class DebugSectionReader(object):

    def __init__(self, sections, byteorderPrefix):
        self.byteorderPrefix = byteorderPrefix
        print(sections.keys())
        self.sections = sections
        self.instantiateReaders()
        self.abbrevs = {}
        self.infoHeaders = []
        if '.debug_info' in self.sections:
            self.scanDebugInfoHeaders()

    def instantiateReaders(self):
        self.readers = {}
        for name, section in self.sections.items():
            if section.image is not None:
                self.readers[name] = DwarfReader(section.image, self, self.byteorderPrefix)

    def getReader(self, name):
        return self.readers[name]

    def process(self):
        for name, image in self.sections.items():
            print(name)
        #if '.debug_ranges' in self.sections:
        #    self.processRanges()
        if '.debug_line' in self.sections:
            self.processLineSection()
        if '.debug_abbrev' in self.sections:
            self.processAbbreviations()
        if '.debug_info' in self.sections:
            self.processInfoSection()
        if '.debug_pubnames' in self.sections :
            self.processPubNames()
        """
            .debug_aranges
            .debug_frame
            .debug_info
            .debug_line
            .debug_pubnames
.           .debug_pubtypes
            .debug_types
            ## debug_loc
        """


    def processAbbreviations(self):
        dr = self.getReader('.debug_abbrev')
        abbrevs = {}
        abbrevEntries = {}
        offsetState = SET_OFFSET
        while dr.pos < dr.size:
            startPos = dr.pos
            if offsetState == SET_OFFSET:
                offset = dr.pos
                offsetState = IGNORE_OFFSET
            code = dr.uleb()
            if code == 0:
                abbrevs[offset] = abbrevEntries
                abbrevEntries = {}
                offsetState = SET_OFFSET
                continue
            tagValue = dr.uleb()
            tag = constants.TAG_MAP.get(tagValue, tagValue)
            children = dr.u8()
            attrSpecs = []
            if dr.pos == 0x69:
                pass
            print("   {0:d}      {1!s}    [{2!s}]".format(code, tag, "has children" if children == constants.DW_CHILDREN_yes else "no children"))
            while True:
                attrValue = dr.uleb()
                attr = constants.AttributeEncoding(attrValue)
                formValue = dr.uleb()
                form = constants.AttributeForm(formValue)
                if attrValue == 0 and formValue == 0:
                    print("    DW_AT value: 0     DW_FORM value: 0")
                    break
                if attr.value in attr.MAP:
                    print("    {0!s} {1!s}".format(attr.MAP[attr.value], form.MAP[form.value]))
                else:
                    print("    Unknown AT value: {0:x} {1!s}".format(attr.value, form.MAP[form.value]))
                attrSpecs.append((attr, form))
            abbrevEntries[code] = AbbreviationEntry(tag, "DW_CHILDREN_yes" if children == constants.DW_CHILDREN_yes else "DW_CHILDREN_no", attrSpecs)
            #print startPos, abbrevEntries[code]
        #if abbrevs == {}:   # NOTBEHELF!!!
        #    abbrevs[offset] = abbrevEntries
        self.abbrevs = abbrevs
        dr.reset()

    def processRanges(self):
        name = ".debug_ranges"
        dr = self.getReader('.debug_ranges')
        if not dr.size:
            print("\nThe {0} section is empty.".format(name))
            return
        else:
            print("Contents of the %s section:\n".format(name))
            print("    Offset   Begin    End")
        while dr.pos < dr.size:
            offset = dr.u32()
            begin = dr.u32()
            end = dr.u32()
            b  = dr.u32()
            c  = dr.u32()

    def processInfoSection(self):
        dr = self.getReader('.debug_info')
        while dr.pos < dr.size:
            sectionHeaderStart = dr.pos
            length = dr.u32()
            stopPosition = dr.pos + length
            dwarfVersion = dr.u16()
            abbrevOffs = dr.u32()
            abbrevs = self.abbrevs.get(abbrevOffs, None)
            if abbrevs is None:
                print("*** Error: Invalid Abbreviations ***")
                return
            targetAddrSize = dr.u8()
            dr.wordSize = targetAddrSize

            while dr.pos < stopPosition:
                entryOffset = dr.pos
                number = dr.uleb()
                if number == 0:
                    print("<*** EMPTY ***>")
                    continue
                try:
                    entry = abbrevs[number]
                except KeyError as e:   # TODO: genau analysieren!!!
                    print("ENTRY NOT FOUND: {0:d} [{1!s}]".format(number, e))
                    continue
                print("<{0:x}><{1:x}>: Abbrev Number: {2:d} ({3!s})".format(sectionHeaderStart, entryOffset, number, entry.tag))
                for attr in entry.attrs:
                    offset = dr.pos
                    attribute, form = attr
                    reader = FORM_READERS[form.value]
                    attrValue = getattr(dr, reader)()
                    if attribute.value in (constants.DW_AT_return_addr, constants.DW_AT_location, # constants.DW_AT_frame_base,
                        constants.DW_AT_data_member_location):
                        dis = Dissector(attrValue, targetAddrSize)
                        attrValue = dis.run()
                    print("   <{0:x}>   {1:18!s}    : {2!s}".format(offset, attribute, attrValue))
        dr.reset()

    def processPubNames(self):  # TODO: NameLookupTable
        dr = self.getReader('.debug_pubnames')  # '.debug_pubtypes'
        print("Contents of the .debug_pubnames section:")
        while dr.pos < dr.size:
            length = dr.u32()
            stopPosition = dr.pos + length
            dwarfVersion = dr.u16()
            debugInfoOffs = dr.u32()
            debugInfoLen = dr.u32()
            print("  Length:                              {0:d}".format(length  ))
            print("  Version:                             {0:d}".format(dwarfVersion ))
            print("  Offset into .debug_info section:     0x{0:x}".format(debugInfoOffs ))
            print("  Size of area in .debug_info section: {0:d}".format(debugInfoLen ))
            print()
            print("    Offset      Name")
            while dr.pos < stopPosition:
                #tb = dr.u8()
                entryOffset = dr.u32()
                if not entryOffset:
                    break
                entryName = dr.asciiz()
                print("    {0:12!s} {1!s}".format(hex(entryOffset), entryName))

    def scanDebugInfoHeaders(self):
        dr = self.getReader('.debug_info')
        result = []
        while dr.pos < dr.size:
            length = dr.u32()

            nextPosition = dr.pos + length
            dwarfVersion = dr.u16()
            abbrevOffs = dr.u32()
            targetAddrSize = dr.u8()
            dr.pos = nextPosition
            result.append(InfoHeader(length, dwarfVersion, abbrevOffs, targetAddrSize))
        dr.reset()
        self.infoHeaders = result

    def processLineSection(self):
        print("Raw dump of debug contents of section .debug_line:\n")
        dr = self.getReader('.debug_line')
        while dr.pos < dr.size:
            sectionOffset = dr.pos
            length = dr.u32()
            stopPosition = dr.pos + length
            dwarfVersion = dr.u16()
            headerLength = dr.u32() # in the 64-bit DWARF format, this field is an 8-byte unsigned length!!!
            minimumInstructionLength = dr.u8()
            #maximumOperationsPerInstruction = dr.u8()  # DWARF4
            defaultIsStmt = True if dr.u8() == 0x01 else False
            lineBase = dr.s8()
            lineRange = dr.u8()
            # maximumLineIncrement = (lineBase + lineRange -1)
            #
            # If the desired line increment is greater than the maximum line
            # increment, a standard opcode must be used instead of a special opcode.

            opcodeBase = dr.u8()    # The number assigned to the first special opcode.

            if not dwarfVersion in [2, 3, 5]:
                #raise Excpetion("Invalid DWARF-Version: '%u'." % dwarfVersion)
                return # We can't continue for now.

            standardOpcodeLengths = []
            for i in range(1, opcodeBase):
                olen = dr.u8()
                standardOpcodeLengths.append(olen)
                #print "Opcode %u has %u args" % (i, olen)
            includeDirectories = []
            while True:
                directory = dr.asciiz()
                if directory:
                    includeDirectories.append(directory)
                else:
                    # The last entry is followed by a single null byte.
                    break

            print("  Offset:                      {0:x}".format(sectionOffset ))           # BYTE-ORDER??!!
            print("  Length:                      {0:d}".format(length ))
            print("  DWARF Version:               {0:d}".format((dwarfVersion)))
            print("  Prologue Length:             {0:d}".format(headerLength ))            # BYTE-ORDER??!!
            print("  Minimum Instruction Length:  {0:d}".format(minimumInstructionLength ))
            #print("  Maximum Operations per Instruction: %u" % (maximumOperationsPerInstruction, ))
            print("  Initial value of 'is_stmt':  {0:d}".format(defaultIsStmt ))
            print("  Line Base:                   {0:d}".format(lineBase ))
            print("  Line Range:                  {0:d}".format((lineRange)))
            print("  Opcode Base:                 {0:d}".format((opcodeBase)))

            print("\n  Opcodes:")
            for idx, args in enumerate(standardOpcodeLengths, 1):
                print("   Opcode {0:d} has {1:d} args".format(idx, args))

            if includeDirectories:
                #print "What now?"
                 print(" The Directory Table (offset 0x18):") # Cheeck: Offset!??
                 for idx, directory in enumerate(includeDirectories, 1):
                     print("  {0:d}     {1!s}".format(idx, directory))
            else:
                print(" The Directory Table is empty.")

            #" The File Name Table (offset 0x3c):"

            fileNames = []
            idx = 0
            while True:
                filename = dr.asciiz()
                if filename:
                    idx += 1
                    directoryIndex = dr.uleb()
                    timeOfLastModification = dr.uleb()
                    fileLength = dr.uleb()
                    fileNames.append(filename)  # TODO: namedtuple.
                    print("{0:d} {1:d} {2:d} {3:d} {4!s}".format(idx, directoryIndex, timeOfLastModification, fileLength, filename))
                else:
                    break

            if dr.pos >= stopPosition:
                continue

            #statements = []
            lineNumberProgram = []
            address = 0
            line = 1
            while True:
                regs = LNSregisters(defaultIsStmt, dr.pos)
                print("[0x{0:08x}]  ".format(dr.pos), )
                opcode = dr.u8()
                if opcode >= opcodeBase:
                    # Special opcodes.
                    """
                    1. Add a signed integer to the line register.
                    2. Modify the operation pointer by incrementing the address and op_index registers as described below.

                    """
                    adjustedOpcode = opcode - opcodeBase
                    addrIncr = (adjustedOpcode / lineRange)  * minimumInstructionLength
                    lineIncr = lineBase + (adjustedOpcode % lineRange)
                    address += addrIncr
                    line += lineIncr
                    regs.op_index = adjustedOpcode  # ???
                    regs.basic_block = False
                    regs.prologue_end = False
                    regs.epilogue_begin = False
                    regs.discriminator = 0
                    print("Special opcode {0:d}: advance Address by {1:d} to 0x{2:x} and Line by {3:d} to {4:d}".format(adjustedOpcode, addrIncr, address, lineIncr, line))

                else:
                    if opcode == DW_LNS_extended_op:
                        # Extended opcodes.
                        extOpLen = dr.uleb()
                        extOp = dr.u8()

                        if extOp == constants.DW_LNE_end_sequence:
                            regs.end_sequence = True
                            line = 1
                            print("Extended opcode 1: End of Sequence")
                        elif extOp == constants.DW_LNE_set_address:
                            address = dr.addr()
                            print("Extended opcode 2: set Address to 0x{0:x}".format(address))
                        elif extOp == constants.DW_LNE_define_file:
                            print("Extended opcode 3: define new File Table entry")
                            fileName = dr.asciiz()
                            directoryIndex = dr.uleb()
                            timeOfLastModification = dr.uleb()
                            fileLength = dr.uleb()
                            # TODO: Append to filename-Table!!!
                            print("Entry Dir     Time    Size    Name")
                            print(" 1    {0:d}       {1:d}       {2:d}       {3!s}".format(directoryIndex, timeOfLastModification, fileLength, fileName))
                        elif extOp == constants.DW_LNE_set_discriminator:
                            raise Exception("FIX ME!!!")
                        else:
                            raise AttributeError("Unexpected extended opcode: '{0:d}'".format(opcode))
                    else:
                        # Standard opcodes.
                        if opcode == constants.DW_LNS_copy:
                            regs.basic_block = False
                            print("Copy")
                        elif opcode == constants.DW_LNS_advance_pc:
                            addressIncr = dr.uleb() * minimumInstructionLength
                            address += addressIncr
                            print("Advance PC by {0:d} to 0x{1:x}".format(addressIncr, address))
                        elif opcode == constants.DW_LNS_advance_line:
                            lineIncr = dr.uleb()
                            line += lineIncr
                            print("Advance Line by {0:d} to {1:d}".format(lineIncr, line ))
                        elif opcode == constants.DW_LNS_set_file:
                            regs.fileNumber = dr.uleb()
                            print("Set File Name to entry {0:d} in the File Name Table".format((regs.fileNumber)))
                        elif opcode == constants.DW_LNS_set_column:
                            regs.column = dr.uleb()
                            print("Set column to {0:d}".format(regs.column))
                        elif opcode == constants.DW_LNS_negate_stmt:
                            regs.is_stmt = not regs.is_stmt # Check!!!
                        elif opcode == constants.DW_LNS_set_basic_block:
                            regs.basic_block = True
                            print("Set basic block")
                        elif opcode == constants.DW_LNS_const_add_pc:
                            offset = ((255 - opcodeBase) / lineRange) * minimumInstructionLength
                            address += offset
                            print("Advance PC by constant {0:d} to 0x{1:x}".format(offset, address))
                        elif opcode == constants.DW_LNS_fixed_advance_pc:
                            addrInc = dr.u16()
                            address += addrInc
                            print("Advance PC by fixed size amount {0:d} to 0x{1:x}".format(addrInc, address))
                        elif opcode == constants.DW_LNS_set_prologue_end:
                            print("Set prologue_end to true")
                            regs.prologue_end = True
                        elif opcode == constants.DW_LNS_set_epilogue_begin:
                            print("Set epilogue_begin to true")
                        elif opcode == constants.DW_LNS_set_isa:
                            pass
                        else:
                            raise AttributeError("Unexpected standard opcode: '{0:d}'".format(opcode))
                regs.line = line
                regs.address = address
                lineNumberProgram.append(regs)
                if dr.pos >= stopPosition:
                    #if regs.end_sequence == True:
                    break
