
import unittest

from objutils.checksums import nibbleSum, lrc, rotatedXOR
from objutils.checksums import COMPLEMENT_NONE, COMPLEMENT_ONES, COMPLEMENT_TWOS, ROTATE_LEFT, ROTATE_RIGHT

#print lrc(range(10), 8, COMPLEMENT_TWOS)
#print lrc(range(100), 8, COMPLEMENT_TWOS)

class TestNiblleSums(unittest.TestCase):

    def testNibbleSumCase1(self):
        self.assertEquals(nibbleSum(range(10)), 45)

    def testNibbleSumCase2(self):
        self.assertEquals(nibbleSum(range(100)), 222)

    # check that s.split fails when the separator is not a string
    #with self.assertRaises(TypeError):
    #    s.split(2)


class TestLRCs(unittest.TestCase):

    def testLRCCase1(self):
        self.assertEquals(lrc(range(10), 8, COMPLEMENT_NONE), 45)

    def testLRCCase2(self):
        self.assertEquals(lrc(range(100), 8, COMPLEMENT_NONE), 86)

    def testLRCCase3(self):
        self.assertEquals(lrc(range(10), 8, COMPLEMENT_ONES), 210)

    def testLRCCase4(self):
        self.assertEquals(lrc(range(100), 8, COMPLEMENT_ONES), 169)

    def testLRCCase5(self):
        self.assertEquals(lrc(range(10), 8, COMPLEMENT_TWOS), 211)

    def testLRCCase6(self):
        self.assertEquals(lrc(range(100), 8, COMPLEMENT_TWOS), 170)


class TestRXORs(unittest.TestCase):

    def testRXORCase1(self):
        self.assertEquals(rotatedXOR(range(10), 8, ROTATE_LEFT), 74)

    def testRXORCase2(self):
        self.assertEquals(rotatedXOR(range(100), 8, ROTATE_LEFT), 66)

    def testRXORCase3(self):
        self.assertEquals(rotatedXOR(range(10), 8, ROTATE_RIGHT), 186)

    def testRXORCase4(self):
        self.assertEquals(rotatedXOR(range(100), 8, ROTATE_RIGHT), 3)

if __name__ == '__main__':
    unittest.main()

