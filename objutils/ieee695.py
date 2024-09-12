#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <github.com/Christoph2,
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


import os
from datetime import datetime
from functools import reduce

from objutils.logger import Logger


"""
$00-$7F     Simple number in the range 0 to 127, or 7-bit ASCII string with length 0 to 127.
$80-$84     Number larger than 127 or negative. 0 to 4 bytes follow. $80 is used as a place
            holder and means the value was not provided.
$85-$88     Unsigned numbers between 2ˆˆ32 and (2ˆˆ64)-1, or negative. Not supported in all installations.
$89-$8F     Unused.
$90-$9F     Reserved functions and operators.
$A0-$BF     Function values (arithmetic and logical).
$C0-$DA     Variable letters (null, A-Z).
$DB-$DD     Unused.
$DE-$DF     Extension length. If DE, the next byte is the length of an 8-bit string between 0 and 255
            bytes long. If DF, the next two bytes in high- order/low-order format are the length of
            an 8-bit string between 0 and 65535 bytes long.
$E0-$FA     Record headers.
$FB         Define Context.
$FC-$FF     Unused.

Table 2-1. Initial Bytes of IEEE Elements
"""

SMALL_NUMBER = 0x7F
SHORT_STRING = 0x7F
COMMAND_CODE = 0xE0

"""
ASP     = 0xD0    # Current Section PC.
ASS     = 0xD3    # Section Size.
ASR     = 0xD2    # Variable Values.
ASW     = 0xD7    # Variable Values.
ASA     = 0xC1    # Physical Region Size.
ASB     = 0xC2    # Physical Region Base Address.
ASP     = 0xC6    # Mau Size.
ASG     = 0xC7    # Execution Starting Address.
ASI     = 0xC9    # Variable Values.
ASL     = 0xCC    # Section Base Address.
ASM     = 0xCD    # M-Value.
ASN     = 0xCE
"""

F1 = 0xF1
E2 = 0xE2

##
## Header Part.
##
MB = 0xE0  # Module Beginning.
AD = 0xEC  # Address Descriptor.

ASW0 = 0x00  # Assign Pointer to AD Extension Part.
ASW1 = 0x01  # Assign Pointer to Environment Part.
ASW2 = 0x02  # Assign Pointer to Section Part.
ASW3 = 0x03  # Assign Pointer to External Part.
ASW4 = 0x04  # Assign Pointer to Debug Part.
ASW5 = 0x05  # Assign Pointer to Data Part.
ASW6 = 0x06  # Assign Pointer to Trailer Part.
ASW7 = 0x07  # Assign Pointer to Module End.


ASWAssignment = {
    ASW0: "AD Extension",
    ASW1: "Environment",
    ASW2: "Section",
    ASW3: "External",
    ASW4: "Debug",
    ASW5: "Data",
    ASW6: "Trailer",
    ASW7: "Module End",
}

##
## AD Extension Part (ASW0).
##
NN = 0xF0  # Variable Attributes
ATN = 0xCE  # Variable Attributes    - F1
ASN = 0xCE  # Variable Values    - E2


##
## Environment Part (ASW1).
##

## Same as ASW0
"""
NN      = 0xF0      # Variable Attributes
ATN     = 0xF1CE    # Variable Attributes
ASN     = 0xE2CE    # Variable Values
"""

##
## Section Definition Part (ASW2).
##
ST = 0xE6  # Section Type.
SA = 0xE7  # Section Alignment.
ASS = 0xD3  # Section Size.   - E2
ASL = 0xCC  # Section Base Address.   - E2
ASR = 0xD2  # Variable Values.  - E2
NC = 0xFB  # Define Context.
ASA = 0xC1  # Physical Region Size. - E2
ASB = 0xC2  # Physical Region Base Address. - E2
ASP = 0xC6  # Mau Size. - E2
ASF = 0xC6  # Mau Size. - E2
ASM = 0xCD  # M-Value.  - E2


##
## External Part (ASW3).
##
NI = 0xE8  # Public (External) Symbol.
ATI = 0xC9  # Variable Attribute. - F1
ASI = 0xC9  # Variable Values.  - E2
NX = 0xE9  # External Reference Name.
ATX = 0xD8  # External Reference Relocation Information.  - F1
WX = 0xF4  # Weak External Reference.


##
## Debug Information Definition Part (ASW4).
##
BB = 0xF8  # Declare Block Beginning.
NN = 0xF0  # Declare Type Name, file name, line numbers, function name, variable names, etc.
TY = 0xF2  # Define Type Characteristics.
ASN = 0xCE  # Variable Values.  - E2
ASR = 0xD2  # Variable Values. - E2
BE = 0xF9  # Declare Block End.


##
## Data Part (ASW5).
##
SB = 0xE5  # Current Section.
ASP = 0xD0  # Current Section PC.   - E2
LD = 0xED  # Load Constant MAUs.
IR = 0xE3  # Initialize Relocation Base.
RE = 0xF7  # Repeat Data.
ASW = 0xD7  # Variable Values.  - E2
LR = 0xE4  # Load With Relocation.
LT = 0xFA  # Load With Translation.


##
## Trailer Part (ASW6).
##
ASG = 0xC7  # Execution Starting Address.   - E2


##
## Module End (ASW7).
##
ME = 0xE1  # Module End.
##  Checksum Records - 0xEE, 0xEF


##
##  Blocktypes.
##
BB1 = 1  # Type definitions local to a module.
BB2 = 2  # Type definitions global to all modules.
BB3 = 3  # A module. A non-separable unit of code, usually the result
# of a single compilation, i.e. a Modula-2 module or an Ada package.
BB4 = 4  # A global subprogram.
BB5 = 5  # A source file line number block.
BB6 = 6  # A local (static) subprogram.
BB10 = 10  # An assembler debugging information block.
BB11 = 11  # The module portion of a section.
BB20 = 20  # Library - contains a list of global symbols used in a module.


##
##  Object Format Types.
##
ObjectFormatTypes = {
    1: "Absolute (not relinkable)",
    2: "Relocatable",
    3: "Loadable",
    4: "Library",
}

CaseSensitivity = {1: "case insensitiv", 2: "case sensitiv"}

MemoryModel = {
    0: "tiny",  # Code and data are in the same single 64K segment/page.
    1: "small",  # Code and data each have a single 64K segment/page.
    2: "medium",  # Data has a single 64K segment/page, while code has multiple 64K segments/pages.
    3: "compact",  # Data has multiple 64K segments/pages, while code has a single 64K segment/page.
    4: "large",  # Both data and code have multiple 64K segments/pages.
    5: "big",  # Code has multiple 64K segments/pages, while there is a common "near" data area with
    # far data areas available; normaly data and stack are together
    6: "huge",  # All large arrays and structures are in their own section so that
    # addressing involves computations (you can have arrays and structures bigger than 64K)
}

FunctionsAndOperators = {
    0xA0: "@F",
    0xB0: "@AND",
    0xA1: "@T",
    0xB1: "@OR",
    0xA2: "@ABS",
    0xB2: "@XOR",
    0xA3: "@NEG",
    0xB3: "@EXT",
    0xA4: "@NOT",
    0xB4: "@INS",
    0xA5: "+",
    0xB5: "@ERR",
    0xA6: "-",
    0xB6: "@IF",
    0xA7: "/",
    0xB7: "@ELSE",
    0xA8: "*",
    0xB8: "@END",
    0xA9: "@MAX",
    0xB9: "@ESCAPE",
    0xAA: "@MIN",
    0xBA: "[",
    0xAB: "@MOD",
    0xBB: "]",
    0xAC: "<",
    0xBC: "{",
    0xAD: ">",
    0xBD: "}",
    0xAE: "=",
    0xBE: "(",
    0xAF: "!=",
    0xBF: ")",
}


ESCAPEFunctionEncodings = {
    0: "reserved",
    1: "@ISDEF",
    2: "@TRANS",
    3: "@SPLIT",
    4: "@INBLOCK",
    5: "@CALL_OPT",
}


class InvalidFormatError(Exception):
    pass


class Info:
    pass


class DebugInformation:
    def __init__(self):
        self.children = []

    def add(self, child):
        self.children.append(child)


class Section:
    def __init__(self, sectionType, sectionName, parentSectionIndex):
        self.sectionType = sectionType
        self.sectionName = sectionName
        self.parentSectionIndex = parentSectionIndex
        self.regionSize = []
        self.physicalAddress = []
        self.sectionOffset = []
        self.mauSize = 0
        self.mValue = None
        self.segments = {}


class Reader:
    def __init__(self, inFile):
        if not hasattr(inFile, "read"):
            raise TypeError("Need a file-like object.")
        self.logger = Logger("IEEE695")
        self.inFile = inFile
        self.info = Info()
        self.info.ASWs = {}
        self.fpos = 0
        self.blockType = []
        self.finished = False
        self.symbols = {}
        self.externalSymbols = {}
        self.sections = {}
        self.nnRecords = {}
        self.contexts = {}
        diRoot = DebugInformation()
        diRoot.parent = None
        diRoot.name = "ROOT"
        self.debugInformation = [diRoot]
        self.diParents = [diRoot]
        self.currentSection = None
        self.currentSectionIndex = None
        ####
        self._nb = 0
        self.dbCollection = bytearray()

        while not self.finished:
            cc = self.readByte(self.fpos)
            if cc == MB:
                self.onModuleBegin()
            elif cc == AD:
                self.onAD()
            elif cc == E2:
                self.onE2()
            elif cc == NX:
                self.onNX()
            elif cc == WX:
                self.onWX()
            elif cc == NN:
                self.onNN()
            elif cc == F1:
                self.onF1()
            elif cc == ST:
                self.onST()
            elif cc == NC:
                self.onNC()
            elif cc == SA:
                self.onSA()
            elif cc == NI:
                self.onNI()
            elif cc == BB:
                self.onBB()
            elif cc == BE:
                self.onBE()
            elif cc == TY:
                self.onTY()
            elif cc == SB:
                self.onSB()
            elif cc == LD:
                self.onLD()
            elif cc == ME:
                self.onME()
            else:
                raise NotImplementedError(f"0x{cc:02X}")

    def setCurrentSectionIndex(self, index):
        self.currentSectionIndex = index

    def checkSectionIndex(self, index):
        if self.currentSectionIndex is None:
            print("No current Section Index.")
        elif self.currentSectionIndex != index:
            print
            print("Invalid Section Index.")

    def readByte(self, offset):
        "Read 8bit quantity"
        self.inFile.seek(offset, os.SEEK_SET)
        result = ord(self.inFile.read(1))
        self.fpos = self.inFile.tell()
        return result

    def readWord(self, offset):
        "Read 16bit quantity"
        self.inFile.seek(offset, os.SEEK_SET)
        hi = ord(self.inFile.read(1))
        lo = ord(self.inFile.read(1))
        self.fpos = self.inFile.tell()
        return hi << 8 | lo

    def readNumber(self, offset):
        "Read number of abitrary length"
        self.inFile.seek(offset, os.SEEK_SET)
        typecode = self.readByte(offset)
        if typecode <= SMALL_NUMBER:
            # length: [0..127]
            result = typecode
        elif 0x80 <= typecode <= 0x88:
            # length (in bytes) [0..8]
            length = typecode & ~0x80
            data = self.inFile.read(length)
            self.fpos = self.inFile.tell()
            result = reduce(lambda x, y: (x * 256) + ord(y), data, 0)
        return result

    def readString(self, offset):
        typecode = self.readByte(offset)

        if typecode <= SHORT_STRING:
            # length: [0..127]
            length = typecode
        elif typecode == 0xDE:
            # length: [0..255]
            length = self.readByte(offset + 1)
        elif typecode == 0xDF:
            # length: [0..65535]
            length = self.readWord(offset + 1)
        else:
            raise TypeError(f"Invalid typecode [{typecode:02x}].")
        result = self.inFile.read(length)
        self.fpos = self.inFile.tell()
        return result

    def readCharacter(self, offset):
        result = chr(self.readByte(offset) - 0x80)
        if ord(result) > ord("Z"):
            result = None
        return result

    def checkOptional(self, offset, isString=False):
        "Read and maybe putback"
        cc = self.readByte(offset)
        if cc >= COMMAND_CODE:
            self.inFile.seek(offset, os.SEEK_SET)  # Put back.
            self.fpos = offset
            return None
        if isString:
            self.inFile.seek(offset, os.SEEK_SET)  # Put back.
            self.fpos = offset
            return self.readString(offset)
        else:
            if 0xC0 <= cc <= 0xDA:
                result = chr(cc - 0x80)
                if ord(result) > ord("Z"):
                    result = None
            else:
                return self.readNumber(offset)

    def symbolByName(self, name):
        pass

    def symbolByIndex(self, index):
        pass

    ################################
    ################################
    ################################
    def onModuleBegin(self):
        "{$E0}{Id1}{Id2}"
        self.info.processor = self.readString(self.fpos)
        self.info.module = self.readString(self.fpos)

        self.logger.debug(f"PROCESSOR: '{self.info.processor!s}' MODULE: '{self.info.module!s}'.")

    def onAD(self):
        "$EC}{n1}{n2}[a]"
        self.info.numberOfBits = self.readNumber(self.fpos)
        self.info.numberOfMAUs = self.readNumber(self.fpos)
        self.info.adressWidth = self.info.numberOfBits * self.info.numberOfMAUs
        self.info.byteOrder = self.checkOptional(self.fpos)

    def onE2(self):
        "{$E2}{$D7}{0x}{n}"
        """
        ASR     = 0xD2    # Variable Values.
        """
        discr = self.readByte(self.fpos)
        if discr == ASW:
            addr = self.readByte(self.fpos)
            byteOffset = self.readNumber(self.fpos)
            self.info.ASWs[addr] = (ASWAssignment[addr], byteOffset)
        elif discr == ASS:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].sectionSize = self.readNumber(self.fpos)
            self.logger.debug(f"Section-Size: 0x{self.sections[sectionIndex].sectionSize:04x}")
        elif discr == ASA:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].regionSize.append(self.readNumber(self.fpos))
        elif discr == ASB:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].physicalAddress.append(self.readNumber(self.fpos))
        elif discr == ASR:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].sectionOffset.append(self.readNumber(self.fpos))
        elif discr == ASF:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].mauSize = self.readNumber(self.fpos)
            self.logger.debug(f"MAU-Size: 0x{self.sections[sectionIndex].mauSize:04x}")
        elif discr == ASL:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].sectionBaseAddr = self.readNumber(self.fpos)
            self.logger.debug(f"Section-BaseAddr: 0x{self.sections[sectionIndex].sectionBaseAddr:04x}")
        elif discr == ASM:
            sectionIndex = self.readNumber(self.fpos)
            self.checkSectionIndex(sectionIndex)
            self.sections[sectionIndex].mValue = self.readNumber(self.fpos)
        elif discr == ASI:
            # There may be more than one ASI/ATI record pair for a single
            # name since constants defined in SETs and #defines my be redefined repeatedly.
            symbolIndex = self.readNumber(self.fpos)
            expr = self.readNumber(self.fpos)
            self.symbols[symbolIndex].expr = expr
        elif discr == ASN:
            symbolNameIndex = self.readNumber(self.fpos)  # noqa: F841
            symbolTypeIndex = self.readNumber(self.fpos)  # noqa: F841
        elif discr == ASP:
            sectionIndex = self.readNumber(self.fpos)  # ? check sec-Index!!?
            newValue = self.readNumber(self.fpos)  # noqa: F841
        elif discr == ASG:
            delim = self.readByte(self.fpos)
            if delim != 0xBE:
                pass  # todo: FormatError!!!
            executionStartingAddr = self.readNumber(self.fpos)
            self.logger.debug(f"STARTING-ADDRESS: 0x{executionStartingAddr:04X}")
            delim = self.readByte(self.fpos)
            if delim != 0xBF:
                pass  # todo: FormatError!!!
            self.info.executionStartingAddr = executionStartingAddr
        else:
            raise NotImplementedError(hex(discr))

    def onNN(self):
        "{$F0}{n1}{Id}"
        symbolType = self.readNumber(self.fpos)
        symbolName = self.readString(self.fpos)

        self.nnRecords[symbolType] = Info()
        self.nnRecords[symbolType].name = symbolName
        self.nnRecords[symbolType].atn = {}

        # self.logger.debug("Symbol-Type: 0x%02x Name: '%s'" % (symbolType, symbolName))

    def onNX(self):
        "{$E9}{n1}{Id}"
        externalReferenceIndex = self.readNumber(self.fpos)
        symbolName = self.readString(self.fpos)
        self.externalSymbols[externalReferenceIndex] = Info()
        self.externalSymbols[externalReferenceIndex].symbolName = symbolName

    def onWX(self):
        "{$F4}{n1}{n2}{n3}"
        externalReferenceIndex = self.readNumber(self.fpos)
        defaultSize = self.readNumber(self.fpos)
        defaultValue = self.readNumber(self.fpos)
        self.externalSymbols[externalReferenceIndex].defaultSize = defaultSize
        self.externalSymbols[externalReferenceIndex].defaultValue = defaultValue

    def onF1(self):
        """
        ATI     = 0xF1C9    # Variable Attribute.
        ATX     = 0xF1D8    # External Reference Relocation Information.
        ATN     = 0xF1CE    # Variable Attributes.
        """
        discr = self.readByte(self.fpos)
        if discr == ATI:
            numberOfElements = 0
            symbolNameIndex = self.readNumber(self.fpos)
            symbolTypeIndex = self.readNumber(self.fpos)
            attrDef = self.readNumber(self.fpos)
            if attrDef == 8:
                pass
            elif attrDef == 16:
                symbolClass = self.readNumber(self.fpos)
                publicLocalIndicator = self.checkOptional(self.fpos)
                numericValue = self.checkOptional(self.fpos)
                stringValue = self.checkOptional(self.fpos)

                self.symbols[symbolNameIndex].symbolClass = symbolClass
                self.symbols[symbolNameIndex].publicLocalIndicator = publicLocalIndicator
                self.symbols[symbolNameIndex].numericValue = numericValue
                self.symbols[symbolNameIndex].stringValue = stringValue
            elif attrDef == 19:
                pass
            else:
                pass  # todo: FormatError!!!
            ##            n4 =self.readNumber(self.fpos) # If n2 is non-zero, number of elements in the symbol type specified in n2
            if symbolTypeIndex != 0:
                numberOfElements = self.readNumber(self.fpos)
            self.symbols[symbolNameIndex].symbolTypeIndex = symbolTypeIndex
            self.symbols[symbolNameIndex].numberOfElements = numberOfElements
            self.symbols[symbolNameIndex].attrDef = attrDef
        elif discr == ATX:
            externalReferenceIndex = self.readNumber(self.fpos)
            typeIndex = self.readNumber(self.fpos)
            sectionIndex = self.readNumber(self.fpos)
            shortExternalFlag = self.readNumber(self.fpos)
            self.externalSymbols[externalReferenceIndex].typeIndex = typeIndex
            self.externalSymbols[externalReferenceIndex].sectionIndex = sectionIndex
            self.externalSymbols[externalReferenceIndex].shortExternalFlag = shortExternalFlag
        elif discr == ATN:  # todo: onATN
            symbolNameIndex = self.readNumber(self.fpos)
            symbolTypeIndex = self.readNumber(self.fpos)
            attrDef = self.readNumber(self.fpos)
            if attrDef == 1:
                stackOffset = self.readNumber(self.fpos)  # noqa: F841
            elif attrDef == 2:
                registerIndex = self.readNumber(self.fpos)
            elif attrDef == 3:
                pass
            #            elif attrDef == 4:
            #                pass
            elif attrDef == 7:
                lineNumber = self.readNumber(self.fpos)  # noqa: F841
                columnNumber = self.readNumber(self.fpos)  # noqa: F841
                res1 = self.checkOptional(self.fpos)  # noqa: F841
                res2 = self.checkOptional(self.fpos)  # noqa: F841
            elif attrDef == 8:
                pass
            elif attrDef == 9:
                absoluteProgramCounterOffset = self.readNumber(self.fpos)  # noqa: F841
                # if symbolNameIndex == 0:
                #     registerResourceIndex = self.readByte(self.fpos)
            elif attrDef == 10:
                registerIndex = self.readNumber(self.fpos)  # noqa: F841
                frameOffset = self.readNumber(self.fpos)  # noqa: F841
            #            elif attrDef == 11:
            #                pass
            elif attrDef == 19:
                numberOfElements = self.readNumber(self.fpos)
                localGlobal = self.checkOptional(self.fpos)  # noqa: F841
            elif attrDef == 37:
                self.info.objectFormatVersionNumber = self.readNumber(self.fpos)
                self.info.objectFormatRevisionLevel = self.readNumber(self.fpos)  # noqa: F841
            elif attrDef == 38:  # noqa: F841
                self.info.objectFormatType = ObjectFormatTypes[self.readNumber(self.fpos)]  # noqa: F841
            elif attrDef == 39:  # noqa: F841
                self.info.symbolCaseSensitivity = CaseSensitivity[self.readNumber(self.fpos)]
            elif attrDef == 40:
                self.info.memoryModel = MemoryModel[self.readNumber(self.fpos)]
            elif attrDef == 50:  # noqa: F841
                year = self.readNumber(self.fpos)
                month = self.readNumber(self.fpos)
                day = self.readNumber(self.fpos)
                hour = self.readNumber(self.fpos)  # noqa: F841
                minute = self.readNumber(self.fpos)  # noqa: F841
                second = self.readNumber(self.fpos)
                self.info.creationDate = datetime(year, month, day, hour, minute, second)
            elif attrDef == 51:
                self.info.commandLine = self.readString(self.fpos)
            elif attrDef == 52:  # noqa: F841
                self.info.executionStatus = self.readNumber(self.fpos)
            elif attrDef == 53:
                self.info.hostEnvironment = self.readNumber(self.fpos)
            elif attrDef == 54:
                tool = self.readNumber(self.fpos)  # noqa: F841    # noqa: F841
                version = self.readNumber(self.fpos)  # noqa: F841
                revision = self.readNumber(self.fpos)  # noqa: F841
                revisionLevel = self.checkOptional(self.fpos)  # noqa: F841
            elif attrDef == 55:
                self.info.comments = self.readString(self.fpos)
            elif attrDef == 64:
                typeIdent = self.readNumber(self.fpos)  # noqa: F841
                addATN = self.readNumber(self.fpos)  # noqa: F841
            elif attrDef == 65:
                miscString = self.readString(self.fpos)  # noqa: F841
            else:
                raise NotImplementedError(f"Invalid ATN-Attr: 0x{attrDef:02x}")
                # todo: FormatError
        else:
            raise NotImplementedError(hex(discr))
            # todo: FormatError

    def onST(self):
        "${E6}{n1}{l}[Id][n2][n3][n4]"
        sectionIndex = self.readByte(self.fpos)
        self.setCurrentSectionIndex(sectionIndex)
        f = self.readCharacter(self.fpos)
        if f == "A":
            s, t = self.readCharacter(self.fpos), self.readCharacter(self.fpos)
            sectionType = f + s + t
        elif f == "B":
            pass
        elif f == "C":
            pass
        elif f == "E":
            pass  # todo: 'EA' / 'EZ' !!!
        elif f == "M":
            pass
        elif f == "T":
            pass
        # todo: 'ZC' / 'ZM'.
        else:
            raise NotImplementedError(f"SEG-TYPE: {f!s}")

        sectionName = self.readString(self.fpos)
        parentSectionIndex = self.checkOptional(self.fpos)

        if f == "T":
            brotherSectionIndex = self.readNumber(self.fpos)  # noqa: F841

        if f in ("B", "T"):
            contextIndex = self.readNumber(self.fpos)  # noqa: F841

        self.sections[sectionIndex] = Section(sectionType, sectionName, parentSectionIndex)
        self.logger.debug(f"SECTION [{sectionType!s}:{sectionName!s}]")
        # SA, ASA, ASB, ASF, ASL, ASM, ASR, and ASS records must appear after the ST record they refer to.
        """
        ASP absolute code
        ASR absolute ROM data
        ASD absolute data

        CP code
        CR ROM data
        CD data

        EAP common absolute code
        EAR common absolute ROM data
        EAD common absolute data

        ZCP  short code
        ZCR  short ROM data
        ZCD  short data
        """

    def onNC(self):
        "{$FB}{n1}{Id}"
        contextIndex = self.readNumber(self.fpos)
        contextName = self.readString(self.fpos)
        self.contexts[contextIndex] = contextName

    def onSA(self):
        "{$E7}{n1}[n2][n3]"
        sectionIndex = self.readByte(self.fpos)
        self.checkSectionIndex(sectionIndex)
        boundaryAlignmentDivisor = self.checkOptional(self.fpos)
        self.sections[sectionIndex].boundaryAlignment = 2**boundaryAlignmentDivisor
        self.sections[sectionIndex].pageSize = self.checkOptional(self.fpos)

    def onNI(self):
        "{$E8}{n}{Id}"
        nameIndex = self.readNumber(self.fpos)  # must be > 31, 0 - 31 reserved.
        symbolName = self.readString(self.fpos)
        info = Info()
        info.nameIndex = nameIndex
        info.symbolName = symbolName
        self.symbols[nameIndex] = info
        self.logger.debug(f"SYMBOL: {symbolName!s}")  # followed by ASI.

    def onBB(self):
        blockType = self.readByte(self.fpos)
        blockSize = self.readNumber(self.fpos)
        info = DebugInformation()
        info.parent = self.diParents[-1]
        info.blockType = blockType
        info.blockSize = blockSize
        if blockSize == 0:
            pass
        if blockType == BB1:
            self.blockType.append(1)
            module_name = self.readString(self.fpos)
            info.module_name = module_name
            info.name = "BB1"
            self.logger.debug(f"MODULE-NAME: {module_name!s}")
        elif blockType == BB2:
            self.blockType.append(2)
            zeroLengthName = self.readString(self.fpos)
            info.zeroLengthName = zeroLengthName
            info.name = "BB2"
        elif blockType == BB3:
            self.blockType.append(3)
            module_name = self.readString(self.fpos)
            info.module_name = module_name
            info.name = "BB3"
        elif blockType == BB4:
            self.blockType.append(4)
            functionName = self.readString(self.fpos)
            stackSpaceRequired = self.readNumber(self.fpos)
            typeIndexOfReturnValue = self.readNumber(self.fpos)
            offsetExpr = self.readNumber(self.fpos)
            info.functionName = functionName
            info.stackSpaceRequired = stackSpaceRequired
            info.typeIndexOfReturnValue = typeIndexOfReturnValue
            info.offsetExpr = offsetExpr
            info.name = "BB4"
        elif blockType == BB5:
            self.blockType.append(5)
            sourceFilename = self.readString(self.fpos)
            year = self.checkOptional(self.fpos)  # todo: factor-out (namedtuple)!!!
            month = self.checkOptional(self.fpos)
            day = self.checkOptional(self.fpos)
            hour = self.checkOptional(self.fpos)
            minute = self.checkOptional(self.fpos)
            second = self.checkOptional(self.fpos)
            info.sourceFilename = sourceFilename
            info.year = year
            info.month = month
            info.day = day
            info.hour = hour
            info.minute = minute
            info.second = second
            info.name = "BB5"
        elif blockType == BB6:
            self.blockType.append(6)
            functionName = self.readString(self.fpos)
            stackRequired = self.readNumber(self.fpos)
            typeIndexForReturnValue = self.readNumber(self.fpos)
            offsetExpr = self.readNumber(self.fpos)
            info.functionName = functionName
            info.stackRequired = stackRequired
            info.typeIndexForReturnValue = typeIndexForReturnValue
            info.offsetExpr = offsetExpr
            info.name = "BB6"
        elif blockType == BB10:
            self.blockType.append(10)
            module_name = self.readString(self.fpos)
            objFileName = self.readString(self.fpos)
            toolType = self.readNumber(self.fpos)
            versionRevision = self.checkOptional(self.fpos, isString=True)
            year = self.checkOptional(self.fpos)
            month = self.checkOptional(self.fpos)
            day = self.checkOptional(self.fpos)
            hour = self.checkOptional(self.fpos)
            minute = self.checkOptional(self.fpos)
            second = self.checkOptional(self.fpos)
            info.module_name = module_name
            info.objFileName = objFileName
            info.toolType = toolType
            info.versionRevision = versionRevision
            info.year = year
            info.month = month
            info.day = day
            info.hour = hour
            info.minute = minute
            info.second = second
            info.name = "BB10"
        elif blockType == BB11:
            self.blockType.append(11)
            zeroLengthName = self.readString(self.fpos)
            sectionType = self.readNumber(self.fpos)
            sectionIndex = self.readNumber(self.fpos)
            offsetExpr = self.readNumber(self.fpos)
            dummy = self.readByte(self.fpos)  # $90 - Comma operator!!!
            sectionMapping = self.readNumber(self.fpos)
            info.zeroLengthName = zeroLengthName
            info.sectionType = sectionType
            info.sectionIndex = sectionIndex
            info.offsetExpr = offsetExpr
            info.dummy = dummy
            info.sectionMapping = sectionMapping
            info.name = "BB11"
        elif blockType == BB20:
            self.blockType.append(20)
            raise NotImplementedError("BB20")
        parent = self.diParents[-1]
        parent.add(info)
        self.diParents.append(info)
        # self.logger.debug(" " * len(self.diParents), "BB{0:d}".format(blockType))

    def onBE(self):
        blockType = self.blockType.pop()
        self.diParents.pop()
        if blockType in (4, 6):
            functionEndAddr = self.readNumber(self.fpos)  # noqa: F841
        elif blockType == 11:
            moduleSectionSize = self.checkOptional(self.fpos)  # noqa: F841

    def onTY(self):
        """"""
        typeIndex = self.readNumber(self.fpos)  # noqa: F841
        if self.readByte(self.fpos) != 0xCE:
            pass  # todo: raise FormatError!!
        localNameIndex = self.readNumber(self.fpos)  # noqa: F841
        values = []
        while True:
            value = self.checkOptional(self.fpos)
            if value is None:
                break
            else:
                values.append(value)

    def onSB(self):
        "{$E5}{n1}"
        sectionIndex = self.readNumber(self.fpos)
        sec = self.sections[sectionIndex]
        self.logger.debug(f"Data for section: '{sec.sectionName!s}'. {sec.sectionSize:d} bytes of data to follow.")

    def onLD(self):
        "{$ED}{n1}{...}"
        numberOfMAUs = self.readNumber(self.fpos)
        data = self.inFile.read((numberOfMAUs * self.info.numberOfBits) / 8)
        self.logger.debug(f"reading {len(data):d} bytes")

        # SB ASP LD
        self._nb += len(data)
        self.dbCollection.extend(data)

        self.fpos = self.inFile.tell()

    def onME(self):
        "Module End Record Type"
        self.finished = True
        self.logger.debug(f"{self._nb:d} Data-Bytes.")


## $C0-$DA Variable letters (null, A-Z).

## Information-Variables: s. 3

"""
Number Format:
--------------
•   If the value is between 0-127 decimal, the number is $0-$7F.
•   If the value is greater than 127 decimal, then the number must be defined by 1 byte of count with the high
    order bit set ($80) followed by the indicated number of bytes of numeric data with the most significant byte
    first. The range for the count is usually 0-4 (i.e. $80-$84) and can be 0-8 on some installations. This form is
    also valid for numbers in the range 0-127.
    Example: $7FFF is encoded as {$82}{$7F}{$FF} (3 bytes). 0 can be encoded as {$00} or {$81}{$00}, 2ˆˆ32
    can be encoded as {$85}{01}{00}{00}{00}{00}, etc.
•   Omitted optional fields in records may be represented by a byte count of zero.
    Example: {$80}

Negative numbers have these characteristics:
    • Numbers use $80-$88.
    • All readers must handle $80-$84.
    • Some processors can use $85 through $88 (see the appendix for your processor).
    • Numbers are construed as unsigned except where indicated as signed.
    • Signed numbers use signed complement notation; negative numbers must set highest bit of largest
      representable number (e.g., {$84}{$FF}{$FF}{$FF}{$FF} is -1 for 32-bit and smaller processors).

"""
