##
##  Unittests.
##

import unittest
from objutils.dwarf import encoding

class testEncodeULEB(unittest.TestCase):
    values = [2, 127, 128, 129, 130, 12857]
    results = [[2], [127], [128, 1], [129, 1], [130, 1], [185, 100]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encoding.encodeULEB(value), result)

    def testExceptionOnNegativeNumber(self):
        self.assertRaises(ValueError, encoding.encodeULEB, -1)


class testEncodeSLEB(unittest.TestCase):
    values = [-2, -127, -128, -129, -130, -12857]
    results = [[126], [129, 127], [128, 127], [255, 126], [254, 126], [199, 155, 127]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encoding.encodeSLEB(value), result)


class testDecodeULEB(unittest.TestCase):
    values = [[2], [127], [128, 1], [129, 1], [130, 1], [185, 100]]
    results = [2, 127, 128, 129, 130, 12857]

    def testDecoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encoding.decodeULEB(value), result)


class testDecodeSLEB(unittest.TestCase):
    values = [[126], [129, 127], [128, 127], [255, 126], [254, 126], [199, 155, 127]]
    results = [-2, -127, -128, -129, -130, -12857]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEquals(encoding.decodeSLEB(value), result)


def sint(value, nbytes):
    mask = 2 ** ((nbytes * 8) - 1)
    if value >=mask:
        return (~value) + 1
    else:
        return value

def main():
    unittest.main()

if __name__ == '__main__':
    main()

