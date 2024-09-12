#!/usr/bin/env python
import unittest

from objutils import dumps, loads


MOSTEC = b""";10B000576F77212044696420796F75207265610624
;10B0106C6C7920676F207468726F756768206106B9
;10B0206C6C20746861742074726F75626C652006C6
;0DB030746F207265616420746869733F05A3
;00\n"""

S19 = b"""S113B000576F77212044696420796F7520726561D8
S113B0106C6C7920676F207468726F756768206143
S113B0206C6C20746861742074726F75626C652036
S110B030746F207265616420746869733F59
S5030004F8\n"""


class TestRoundtrip(unittest.TestCase):
    def testLoadsWorks(self):
        data = loads("mostec", MOSTEC)
        # data.hexdump()
        # print(dumps("srec", data))
        self.assertEqual(dumps("srec", data, s5record=True), S19)

    def testDumpsWorks(self):
        data = loads("srec", S19)
        self.assertEqual(dumps("mostec", data), MOSTEC)


if __name__ == "__main__":
    unittest.main()
