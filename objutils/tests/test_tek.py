#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps
import unittest


TEK = b"""/B000100C576F77212044696420796F7520726561A5
/B010100D6C6C7920676F207468726F7567682061C1
/B020100E6C6C20746861742074726F75626C6520AF
/B0300D1B746F207265616420746869733F8D
/B03D001B"""

S19 = b"""S113B000576F77212044696420796F7520726561D8
S113B0106C6C7920676F207468726F756768206143
S113B0206C6C20746861742074726F75626C652036
S110B030746F207265616420746869733F59
S5030004F8"""


class TestRoundtrip(unittest.TestCase):

    def testLoadsWorks(self):
        data = loads("tek", TEK)
        #data.hexdump()
        #print(dumps("srec", data))
        self.assertEqual(dumps("srec", data, s5record = True), S19)

    def testDumpsWorks(self):
        data = loads("srec", S19)
        self.assertEqual(dumps("tek", data), TEK)


if __name__ == '__main__':
    unittest.main()

