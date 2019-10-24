#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps, probes
from objutils.hexfile import MetaRecord
from objutils.image import Image
import unittest

import pytest


SIG = b""":B00010A5576F77212044696420796F75207265617B
:B01010E56C6C7920676F207468726F756768206136
:B02010256C6C20746861742074726F75626C652068
:B0300D5F746F207265616420746869733FD1
:B03D00"""

IHEX = b"""
"""

SREC1 = b"""S113B000576F77212044696420796F7520726561D8
S113B0106C6C7920676F207468726F756768206143
S113B0206C20746861742074726F75626C6520742E
S10FB0306F207265616420746869733FCE
S9030000FC"""


SREC2 = b"""S21400B000576F77212044696420796F7520726561D7
S21400B0106C6C7920676F207468726F756768206142
S21400B0206C20746861742074726F75626C6520742D
S21000B0306F207265616420746869733FCD
S804000000FB"""

SREC3 = b"""S3150000B000576F77212044696420796F7520726561D6
S3150000B0106C6C7920676F207468726F756768206141
S3150000B0206C20746861742074726F75626C6520742C
S3110000B0306F207265616420746869733FCC
S70500000000FA"""

SREC4 = b"""S00D000073616D706C652E73313965
S315017FC0003B1879210016C07816C04B10EF87C76C95
S315017FC01080B74618586CEA2102186280EC808C0042
"""

def test_meta_data1():
    img = loads("srec", SREC1)
    assert img.meta == {8: [MetaRecord(format_type=8, address=0, chunk=None)]}

def test_meta_data2():
    img = loads("srec", SREC4)
    assert img.meta == {1: [MetaRecord(format_type=1, address=0, chunk=bytearray(b'sample.s19'))]}

class TestRoundtrip(unittest.TestCase):

    def testLoadsWorks(self):
        image = Image()
        image.insert_section("Wow! Did you really go through al that trouble to read this?", 0xb000)
        image.join_sections()
        self.assertEqual(dumps("srec", image, record_type = 1, s5record = False, start_address = 0x0000), SREC1)


class Test19Probe(unittest.TestCase):

    @pytest.mark.skip
    def testS19ProbeS1(self):
        self.assertEqual(probes(SREC1), "srec")

    @pytest.mark.skip
    def testS19ProbeS2(self):
        self.assertEqual(probes(SREC2), "srec")

    @pytest.mark.skip
    def testS19ProbeS3(self):
        self.assertEqual(probes(SREC3), "srec")


class TestS19Options(unittest.TestCase):

    def createImage(self, record_type, s5record, start_address = None):
        image = Image()
        image.insert_section(range(10), 0x1000)
        image.join_sections()
        return dumps("srec", image, record_type = record_type, s5record = s5record, start_address = start_address)

    def testS19includeS5RecordS1(self):
        self.assertEqual(self.createImage(1, True), b"S10D100000010203040506070809B5\nS5030001FB")

    def testS19includeS5RecordS2(self):
        self.assertEqual(self.createImage(2, True), b"S20E00100000010203040506070809B4\nS504000001FA")

    def testS19includeS5RecordS3(self):
        self.assertEqual(self.createImage(3, True), b"S30F0000100000010203040506070809B3\nS50500000001F9")

    def testS19excludeS5RecordS1(self):
        self.assertEqual(self.createImage(1, False), b"S10D100000010203040506070809B5")

    def testS19excludeS5RecordS2(self):
        self.assertEqual(self.createImage(2, False), b"S20E00100000010203040506070809B4")

    def testS19excludeS5RecordS3(self):
        self.assertEqual(self.createImage(3, False), b"S30F0000100000010203040506070809B3")

    def testS19includeStartAddressS1(self):
        self.assertEqual(self.createImage(1, False, 0x1000), b"S10D100000010203040506070809B5\nS9031000EC")

    def testS19includeStartAddressS2(self):
        self.assertEqual(self.createImage(2, False, 0x1000), b"S20E00100000010203040506070809B4\nS804001000EB")

    def testS19includeStartAddressS3(self):
        self.assertEqual(self.createImage(3, False, 0x1000), b"S30F0000100000010203040506070809B3\nS70500001000EA")


if __name__=='__main__':
    unittest.main()
