
import unittest

from objutils.checksums import nibble_sum, lrc, rotatedXOR, xor
from objutils.checksums import COMPLEMENT_NONE, COMPLEMENT_ONES, COMPLEMENT_TWOS, ROTATE_LEFT, ROTATE_RIGHT


class TestNiblleSums(unittest.TestCase):

    def testNibbleSumCase1(self):
        self.assertEqual(nibble_sum(range(10)), 45)

    def testNibbleSumCase2(self):
        self.assertEqual(nibble_sum(range(100)), 222)

    # check that s.split fails when the separator is not a string
    #with self.assertRaises(TypeError):
    #    s.split(2)


class TestXor(unittest.TestCase):

    def testXorInverted(self):
        self.assertEqual(xor([0xbc, 0xaf, 0xfe, 0x11, 0x52, 0x60, 0x80], True), 0xb1)

    def testXorNotInverted(self):
        self.assertEqual(xor([0xbc, 0xaf, 0xfe, 0x11, 0x52, 0x60, 0x80], False), 0x4e)


class TestLRCs(unittest.TestCase):

    def testLRCCase1(self):
        self.assertEqual(lrc(range(10), 8, COMPLEMENT_NONE), 45)

    def testLRCCase2(self):
        self.assertEqual(lrc(range(100), 8, COMPLEMENT_NONE), 86)

    def testLRCCase3(self):
        self.assertEqual(lrc(range(10), 8, COMPLEMENT_ONES), 210)

    def testLRCCase4(self):
        self.assertEqual(lrc(range(100), 8, COMPLEMENT_ONES), 169)

    def testLRCCase5(self):
        self.assertEqual(lrc(range(10), 8, COMPLEMENT_TWOS), 211)

    def testLRCCase6(self):
        self.assertEqual(lrc(range(100), 8, COMPLEMENT_TWOS), 170)

    def testLRCCase7(self):
        self.assertEqual(lrc(range(10), 16, COMPLEMENT_NONE), 45)

    def testLRCCase8(self):
        self.assertEqual(lrc(range(100), 16, COMPLEMENT_NONE), 4950)

    def testLRCCase9(self):
        self.assertEqual(lrc(range(10), 16, COMPLEMENT_ONES), 65490)

    def testLRCCase10(self):
        self.assertEqual(lrc(range(100), 16, COMPLEMENT_ONES), 60585)

    def testLRCCase11(self):
        self.assertEqual(lrc(range(10), 16, COMPLEMENT_TWOS), 65491)

    def testLRCCase12(self):
        self.assertEqual(lrc(range(100), 16, COMPLEMENT_TWOS), 60586)

    def testLRCCase13(self):
        self.assertEqual(lrc(range(10), 32, COMPLEMENT_NONE), 45)

    def testLRCCase14(self):
        self.assertEqual(lrc(range(100), 32, COMPLEMENT_NONE), 4950)

    def testLRCCase15(self):
        self.assertEqual(lrc(range(10), 32, COMPLEMENT_ONES), 4294967250)

    def testLRCCase16(self):
        self.assertEqual(lrc(range(100), 32, COMPLEMENT_ONES), 4294962345)

    def testLRCCase17(self):
        self.assertEqual(lrc(range(10), 32, COMPLEMENT_TWOS), 4294967251)

    def testLRCCase18(self):
        self.assertEqual(lrc(range(100), 32, COMPLEMENT_TWOS), 4294962346)


class TestRXORs(unittest.TestCase):

    def testRXORCase1(self):
        self.assertEqual(rotatedXOR(range(10), 8, ROTATE_LEFT), 74)

    def testRXORCase2(self):
        self.assertEqual(rotatedXOR(range(100), 8, ROTATE_LEFT), 66)

    def testRXORCase3(self):
        self.assertEqual(rotatedXOR(range(10), 8, ROTATE_RIGHT), 186)

    def testRXORCase4(self):
        self.assertEqual(rotatedXOR(range(100), 8, ROTATE_RIGHT), 3)

    def testRXORCase5(self):
        self.assertEqual(rotatedXOR(range(10), 16, ROTATE_LEFT), 74)

    def testRXORCase6(self):
        self.assertEqual(rotatedXOR(range(100), 16, ROTATE_LEFT), 66)

    def testRXORCase7(self):
        self.assertEqual(rotatedXOR(range(10), 16, ROTATE_RIGHT), 186)

    def testRXORCase8(self):
        self.assertEqual(rotatedXOR(range(100), 16, ROTATE_RIGHT), 3)

    def testRXORCase9(self):
        self.assertEqual(rotatedXOR(range(10), 32, ROTATE_LEFT), 74)

    def testRXORCase10(self):
        self.assertEqual(rotatedXOR(range(100), 32, ROTATE_LEFT), 66)

    def testRXORCase11(self):
        self.assertEqual(rotatedXOR(range(10), 32, ROTATE_RIGHT), 186)

    def testRXORCase12(self):
        self.assertEqual(rotatedXOR(range(100), 32, ROTATE_RIGHT), 3)


if __name__ == '__main__':
    unittest.main()

