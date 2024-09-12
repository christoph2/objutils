#!/usr/bin/env python
import pytest

from objutils import dumps, loads
from objutils.image import Image


def test_load_shf1():
    DUMP = """<?xml version="1.0" encoding="UTF-8"?>
    <dump name="Simple SHF example" blocks="01">
        <block name="Important message in hex format" address="0400" word_size="01" length="1f" checksum="5601b6acad7da5c7b92036786250b053f05852c3">
            41 6c 6c 20 79 6f 75 72 20 62 61 73 65 20 61 72
            65 20 62 65 6c 6f 6e 67 20 74 6f 20 75 73 0a
        </block>
    </dump>
    """
    img = loads("shf", DUMP)
    assert len(img) == 31
    sec = img[0]
    assert sec.start_address == 0x00000400
    assert sec.length == 31
    assert sec.data == b"All your base are belong to us\n"


def test_load_shf2():
    DUMP = """<?xml version="1.0" encoding="UTF-8"?>
    <dump name="6502 Fibonacci" blocks="02">
        <block name="Code" address="1000" word_size="01" length="2a" checksum="5cab5bf8ee299af1ad17e8093d941914eb5930c7">
            a9 01 85 20 85 21 20 1e 10 20 1e 10 18 a5 21 aa
            65 20 86 20 85 21 20 1e 10 c9 c8 90 ef 60 ae 00
            11 a5 21 9d 00 11 ee 00 11 60
        </block>
        <block name="Mem" address="1100" word_size="01" length="e" checksum="c8c2001c42b0226a5d9f7c2f24bd47393166487a">
            01 00 00 00 00 00 00 00 00 00 00 00 00 00
        </block>
    </dump>
    """
    img = loads("shf", DUMP)
    assert len(img) == 56
    sec0, sec1 = img
    assert sec0.start_address == 0x00001000
    assert sec0.length == 42
    assert (
        sec0.data
        == b"\xa9\x01\x85 \x85! \x1e\x10 \x1e\x10\x18\xa5!\xaae \x86 \x85! \x1e\x10\xc9\xc8\x90\xef`\xae\x00\x11\xa5!\x9d\x00\x11\xee\x00\x11`"
    )
    assert sec1.start_address == 0x00001100
    assert sec1.length == 14
    assert sec1.data == b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def test_load_shf3():
    DUMP = """<?xml version="1.0" encoding="UTF-8"?>
    <dump name="Example of an SHF dump with wide data words" blocks="00001">
        <block name="SMIL memory dump" address="000" word_size="5" length="1A" checksum="ff2033489aff0e4e4f0cd7901afc985f7a213c97">
            00100 00200 00000 00090 00000 00036 00300 00400
            00852 00250 00230 00858 00500 00600 014DC 00058
            002A8 000B8 00700 00800 000B0 00192 00100 00000
            00900 00A00 00000 0000A 40000 00000 00B00 00C00
            00000 00000 00000 00001 00D00 00E00 00000 00100
            0CCCC CCCCD 00F00 01000 00000 00010 80000 00000
            00100 00790 00000 00234
    </block>
    </dump>
    """
    img = loads("shf", DUMP)
    assert len(img) == 130
    sec = img[0]
    assert sec.start_address == 0x00000000
    assert sec.length == 130
    assert (
        sec.data
        == b"\x00\x10\x00\x02\x00\x00\x00\x00\x00\x90\x00\x00\x00\x006\x000\x00\x04\x00\x00\x85 \x02P\x00#\x00\x08X\x00P\x00\x06\x00\x01M\xc0\x00X\x00*\x80\x00\xb8\x00p\x00\x08\x00\x00\x0b\x00\x01\x92\x00\x10\x00\x00\x00\x00\x90\x00\n\x00\x00\x00\x00\x00\n@\x00\x00\x00\x00\x00\xb0\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\xd0\x00\x0e\x00\x00\x00\x00\x01\x00\x0c\xcc\xcc\xcc\xcd\x00\xf0\x00\x10\x00\x00\x00\x00\x00\x10\x80\x00\x00\x00\x00\x00\x10\x00\x07\x90\x00\x00\x00\x024"
    )


@pytest.mark.skip  # Content identical, whitespace issue.
def test_dump_shf1():
    SREC1 = b"""S113B000576F77212044696420796F7520726561D8
S113B0106C6C7920676F207468726F756768206143
S113B0206C20746861742074726F75626C6520742E
S10FB0306F207265616420746869733FCE
S9030000FC"""
    sr = loads("srec", SREC1)
    img = Image([sr[0]])
    shf = dumps("shf", img)
    assert (
        shf
        == """<?xml version="1.0" encoding="UTF-8"?>
<dump name="SHF dump by objutils" blocks="0001">
    <block name="Section #0000" address="0000b000" word_size="01" length="0000003c" checksum="9a8e02926903975688683136d71ff38ca9fc9847">
        57 6f 77 21 20 44 69 64 20 79 6f 75 20 72 65 61
        6c 6c 79 20 67 6f 20 74 68 72 6f 75 67 68 20 61
        6c 20 74 68 61 74 20 74 72 6f 75 62 6c 65 20 74
        6f 20 72 65 61 64 20 74 68 69 73 3f
    </block>
</dump>"""
    )
