#!/usr/bin/env python
import unittest

from objutils import dumps, loads


TEST1 = b""" $A0000,
7F D2 43 A6 7F F3 43 A6 3F C0 00 3F 3B DE 70 0C
3B E0 00 01 93 FE 00 00 7F FA 02 A6 93 FE 00 04
7F FB 02 A6 93 FE 00 08 7F D2 42 A6 7F F3 42 A6
48 00 1F 04 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
$ACF00,
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
$$0FF0,\n"""

TEST2 = b"""
7F D2 43 A6 7F F3 43 A6 3F C0 00 3F 3B DE 70 0C
3B E0 00 01 93 FE 00 00 7F FA 02 A6 93 FE 00 04
7F FB 02 A6 93 FE 00 08 7F D2 42 A6 7F F3 42 A6
48 00 1F 04 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
$ACF00,
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
$$0FF0,\n"""

"""$A000000,
377 377 377 377 377 377 377 377 377 377 377 377 377 377 377 377
$S007760,
$A000000,
377%377%377%377%377%377%377%377%377%377%377%377%377%377%377%377%
$S007760,
$A000000,
377'377'377'377'377'377'377'377'377'377'377'377'377'377'377'377'
$S007760,
$A000000,
377'377'377'377'377'377'377'377'377'377'377'377'377'377'377'377'
$S007760,\n"""

TEST_HEX_PERCENT = b""" $A0000,
FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%FF%
$S0FF0,\n"""

TEST_HEX_SPACE = b""" $A0000,
FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
$S0FF0,\n"""

TEST_HEX_APOSTROPH = b""" $A0000,
FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'
$S0FF0,\n"""

TEST_HEX_COMMA = b""" $A0000,
FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,FF,
$S0FF0,\n"""

# TEST_HEX_ = """B $A0000,
# FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'FF'
# $S0FF0,"""

SREC = b"""S1130000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
S5030001FB\n"""


class TestAcceptance(unittest.TestCase):
    def _runTest(self, format):
        data = loads("ash", format)
        self.assertTrue(dumps("srec", data, s5record=True) == SREC)

    def testAcceptSpace(self):
        self._runTest(TEST_HEX_SPACE)

    def testAcceptPercent(self):
        self._runTest(TEST_HEX_PERCENT)

    def testAcceptComma(self):
        self._runTest(TEST_HEX_COMMA)

    def testAcceptApostroph(self):
        self._runTest(TEST_HEX_APOSTROPH)


class TestGenerateVariants(unittest.TestCase):
    def testWriteHexSpace(self):
        loads("srec", SREC)
        # print(dumps("ash", data, separator = "%"))
        # print()


def main():
    unittest.main()


if __name__ == "__main__":
    main()
