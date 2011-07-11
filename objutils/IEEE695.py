#!/usr/bin/env python
# -*- coding: utf-8 -*-


##
## Header Part.
##
MB      = 0xE0       # Module Beginning.
AD      = 0xEC       # Address Descriptor.
ASW0    = 0xE2D700   # Assign Pointer to AD Extension Part.
ASW1    = 0xE2D701   # Assign Pointer to Environment Part.
ASW2    = 0xE2D702   # Assign Pointer to Section Part.
ASW3    = 0xE2D703   # Assign Pointer to External Part.
ASW4    = 0xE2D704   # Assign Pointer to Debug Part.
ASW5    = 0xE2D705   # Assign Pointer to Data Part.
ASW6    = 0xE2D706   # Assign Pointer to Trailer Part.
ASW7    = 0xE2D707   # Assign Pointer to Module End.


##
## AD Extension Part (ASW0).
##
NN      = 0xF0       # Variable Attributes
ATN     = 0xF1CE     # Variable Attributes
ASN     = 0xE2CE     # Variable Values


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
ST      = 0xE6      # Section Type.
SA      = 0xE7      # Section Alignment.
ASS     = 0xE2D3    # Section Size.
ASL     = 0xE2CC    # Section Base Address.
ASR     = 0xE2D2    # Variable Values.
NC      = 0xFB      # Define Context.
ASA     = 0xE2C1    # Physical Region Size.
ASB     = 0xE2C2    # Physical Region Base Address.
ASP     = 0xE2C6    # Mau Size.
ASM     = 0xE2CD    # M-Value.


##
## External Part (ASW3).
##
NI      = 0xE8      # Public (External) Symbol.
ATI     = 0xF1C9    # Variable Attribute.
ASI     = 0xE2C9    # Variable Values.
ASR     = 0xE2D2    # Variable Values.
NX      = 0xE9      # External Reference Name.
ATX     = 0xF1D8    # External Reference Relocation Information.
WX      = 0xF4      # Weak External Reference.


##
## Debug Information Definition Part (ASW4).
##
BB      = 0xF8      # Declare Block Beginning.
NN      = 0xF0      # Declare Type Name, file name, line numbers, function name, variable names, etc.
TY      = 0xF2      # Define Type Characteristics.
ATN     = 0xF1CE    # Variable Attributes.
ASN     = 0xE2CE    # Variable Values.
ASR     = 0xE2D2    # Variable Values.
BE      = 0xF9      # Declare Block End.


##
## Data Part (ASW5).
##
SB      = 0xE5      # Current Section.
ASP     = 0xE2D0    # Current Section PC.
LD      = 0xED      # Load Constant MAUs.
IR      = 0xE3      # Initialize Relocation Base.
RE      = 0xF7      # Repeat Data.
ASR     = 0xE2D2    # Variable Values.
ASW     = 0xE2D7    # Variable Values.
LR      = 0xE4      # Load With Relocation.
LT      = 0xFA      # Load With Translation.


##
## Trailer Part (ASW6).
##
ASG     = 0xE2C7    # Execution Starting Address.


##
## Module End (ASW7).
##
ME      = 0xE1      # Module End.
##Checksum Records - 0xEE, 0xEF


def main():
    inf = file(r'c:\projekte\csProjects\yObjl\tests\2cb_12.695', 'rb')
    pass

if __name__ == '__main__':
    main()
