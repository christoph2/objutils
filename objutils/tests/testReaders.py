

import unittest
from objutils.utils import createStringBuffer
from objutils.readers import PlainBinaryReader


class TestReader(unittest.TestCase):

    def _createReader(self):
        return PlainBinaryReader(createStringBuffer(bytearray("hello world!", "ascii")), PlainBinaryReader.LITTLE_ENDIAN)

    def testSize(self):
        reader = self._createReader()
        self.assertEqual(reader.size, 12)

    def testInitialPosition(self):
        reader = self._createReader()
        self.assertEqual(reader.pos, 0)

    def testSetPosition(self):
        reader = self._createReader()
        reader.pos = 6
        self.assertEqual(reader.pos, 6)

    def testResetPosition(self):
        reader = self._createReader()
        reader.pos = 6
        reader.reset()
        self.assertEqual(reader.pos, 0)

    def testNextByte(self):
        reader = self._createReader()
        self.assertEqual(reader.nextByte(), 104)


class Decoder(unittest.TestCase):

    def _runTest(self, method, value, expected):
        dr = PlainBinaryReader(createStringBuffer(bytearray(value, "ascii")), PlainBinaryReader.LITTLE_ENDIAN)
        self.assertEqual(getattr(dr, method)(), expected)

    def sleb(self, value, expected):
        self._runTest("sleb", value, expected)

    def u8(self, value, expected):
        self._runTest("u8", value, expected)

    def s8(self, value, expected):
        self._runTest("s8", value, expected)

    def u16(self, value, expected):
        self._runTest("u16", value, expected)

    def s16(self, value, expected):
        self._runTest("s16", value, expected)

    def u32(self, value, expected):
        self._runTest("u32", value, expected)

    def s32(self, value, expected):
        self._runTest("s32", value, expected)

    def u64(self, value, expected):
        self._runTest("u64", value, expected)

    def s64(self, value, expected):
        self._runTest("s64", value, expected)

class TestDecoding(Decoder):

    def testSlb01(self):
        self.sleb("\x9b\xf1\x59", -624485)

    def testASCIIZValue(self):
        self._runTest("asciiz", "hello world!\x00", "hello world!")

    def testASCIIZEmpty(self):
        self._runTest("asciiz", "\x00", "")

    def testU8_1(self):
        self.u8("\x00", 0)

    def testU8_2(self):
        self.u8("\x80", 128)

    def testU8_3(self):
        self.u8("\xff", 255)

    def testS8_1(self):
        self.s8("\x00", 0)

    def testS8_2(self):
        self.s8("\x80", -128)

    def testS8_3(self):
        self.s8("\xff", -1)

    def testU16_1(self):
        self.u16("\x00\x00", 0)

    def testU16_2(self):
        self.u16("\x80\x00", 128)

    def testU16_3(self):
        self.u16("\x00\xff", 65280)

    def testS16_1(self):
        self.s16("\x00\x00", 0)

    def testS16_2(self):
        self.s16("\x00\x80", -32768)

    def testS16_3(self):
        self.s16("\xff\xff", -1)

    def testU32_1(self):
        self.u32("\x00\x00\x00\x00", 0)

    def testU32_2(self):
        self.u32("\x80\x00\x00\x00", 128)

    def testU32_3(self):
        self.u32("\x00\x00\x00\xff", 4278190080)

    def testS32_1(self):
        self.s32("\x00\x00\x00\x00", 0)

    def testS32_2(self):
        self.s32("\x00\x00\x00\x80", -2147483648)

    def testS32_3(self):
        self.s32("\xff\xff\xff\xff", -1)

    def testU64_1(self):
        self.u64("\x00\x00\x00\x00\x00\x00\x00\x00", 0)

    def testU64_2(self):
        self.u64("\x80\x00\x00\x00\x00\x00\x00\x00", 128)

    def testU64_3(self):
        self.u64("\x00\x00\x00\x00\x00\x00\x00\xff", 18374686479671623680)

    def testS64_1(self):
        self.s64("\x00\x00\x00\x00\x00\x00\x00\x00", 0)

    def testS64_2(self):
        self.s64("\x00\x00\x00\x00\x00\x00\x00\x80", -9223372036854775808)

    def testS64_3(self):
        self.s64("\xff\xff\xff\xff\xff\xff\xff\xff", -1)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

