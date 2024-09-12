#!/usr/bin/env python
import unittest

from objutils import dumps, loads


EMON52 = b"""10 0000:57 6F 77 21 20 44 69 64 20 79 6F 75 20 72 65 61 0564
10 0010:6C 6C 79 20 67 6F 20 74 68 72 6F 75 67 68 20 61 05E9
10 0020:6C 6C 20 74 68 69 73 20 74 72 6F 75 62 6C 65 20 05ED
10 0030:74 6F 20 72 65 61 64 20 74 68 69 73 20 73 74 72 05F0
04 0040:69 6E 67 21 015F\n"""

S19 = b"""S1130000576F77212044696420796F752072656188
S11300106C6C7920676F207468726F7567682061F3
S11300206C6C20746869732074726F75626C6520DF
S1130030746F2072656164207468697320737472CC
S1070040696E672159
S5030005F7\n"""


class TestRoundtrip(unittest.TestCase):
    def testLoadsWorks(self):
        data = loads("emon52", EMON52)
        self.assertEqual(dumps("srec", data, s5record=True), S19)

    def testDumpsWorks(self):
        data = loads("srec", S19)
        self.assertEqual(dumps("emon52", data), EMON52)


if __name__ == "__main__":
    unittest.main()
