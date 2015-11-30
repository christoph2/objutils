
import unittest

from objutils.checksums import nibbleSum, lrc
from objutils.checksums import COMPLEMENT_NONE, COMPLEMENT_ONES, COMPLEMENT_TWOS

print lrc(range(10), 8, COMPLEMENT_NONE)
print lrc(range(100), 8, COMPLEMENT_NONE)

class TestChecksums(unittest.TestCase):

    def testNibbleSumCase1(self):
        self.assertEquals(nibbleSum(range(10)), 45)

    def testNibbleSumCase2(self):
        self.assertEquals(nibbleSum(range(100)), 222)


if __name__ == '__main__':
    unittest.main()

