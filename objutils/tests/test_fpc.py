#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps, probes
import unittest

import pytest

#for key, value in sorted(registry.registry().items()):
#    print("{0:10} {1}".format(key, value.description))


SREC = b"""S123B000576F77212044696420796F75207265616C6C7920676F207468726F7567682061DF
S120B0206C6C20746861742074726F75626C6520746F207265616420746869733F73
S5030002FA"""

FPC = b"""$kL&@h%%,:,B.\?00EPuX0K3rO0JI))
$;UPR'%%,:<Hn&FCG:at<GVF(;G9wIw
$7FD1p%%,:LHmy:>GTV%/KJ7@GE[kYz
$B[6\;%%,:\KIn?GFWY/qKI1G5:;-_e
$%%%%%"""


fromSrec =  loads('srec', SREC)
dataFromSRec = dumps('fpc', fromSrec)   # Fixme: Does _NOT_ return 'bytes'!

fromFPC =  loads('fpc', FPC)
dataFromFPC = dumps('srec', fromFPC, row_length = 32, s5record = True)


class TestRoundTrip(unittest.TestCase):

    def testFromSrec(self):
        self.assertEqual(dataFromSRec, FPC)
        #pass

    def testFromFPC(self):
        self.assertEqual(dataFromFPC, SREC)


class TestProbe(unittest.TestCase):

    @pytest.mark.skip
    def testProbeSrec(self):
        self.assertEqual(probes(SREC), "srec")

    @pytest.mark.skip
    def testProbeFpc(self):
        self.assertEqual(probes(FPC), "fpc")


if __name__ == '__main__':
    unittest.main()

