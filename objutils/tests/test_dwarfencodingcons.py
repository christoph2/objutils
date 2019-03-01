##
##  Unittests.
##

import unittest
from objutils.dwarf import encoding

class TestEncodeULEB(unittest.TestCase):
    values = [2,     127,   128,      129,      130,      12857]
    results = [[2], [127], [128, 1], [129, 1], [130, 1], [185, 100]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEqual(encoding.ULEB.build(value), bytes(result))

    def testExceptionOnNegativeNumber(self):
        self.assertRaises(encoding.ULEBError, encoding.ULEB.build, -1)


class TestEncodeSLEB(unittest.TestCase):
    values = [-2, -127, -128, -129, -130, -12857]
    results = [[126], [129, 127], [128, 127], [255, 126], [254, 126], [199, 155, 127]]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEqual(encoding.SLEB.build(value), bytes(result))


class TestDecodeULEB(unittest.TestCase):
    values = [b'\x02', b'\x7f', b'\x80\x01', b'\x81\x01', b'\x82\x01', b'\xb9d']
    results = [2,      127,     128,         129,         130,         12857]

    def testDecoding(self):
        for value, result in zip(self.values, self.results):
            self.assertEqual(encoding.ULEB.parse(bytes(value)), result)


class TestDecodeSLEB(unittest.TestCase):
    values = [b'\x7e', b'\x81\x7f', b'\x80\x7f', b'\xff~', b'\xfe~', b'\xc7\x9b\x7f']
    results = [-2, -127, -128, -129, -130, -12857]

    def testEncoding(self):
        for value, result in zip(self.values, self.results):
            #self.assertEqual(encoding.SLEB.parse(bytes(value)), result)
            self.assertEqual(encoding.SLEB.parse(value), result)

def main():
    unittest.main()

if __name__ == '__main__':
    main()

