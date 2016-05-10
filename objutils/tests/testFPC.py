#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps, probes
from objutils.Segment import Segment
from objutils.Image import Image
from objutils.registry import Registry
import unittest

#for key, value in sorted(registry.registry().items()):
#    print("{0:10} {1}".format(key, value.description))


SREC = """S123B000576F77212044696420796F75207265616C6C7920676F207468726F7567682061DF
S120B0206C6C20746861742074726F75626C6520746F207265616420746869733F73
S5030002FA"""

FPC = """$kL&@h%%,:,B.\?00EPuX0K3rO0JI))
$;UPR'%%,:<Hn&FCG:at<GVF(;G9wIw
$7FD1p%%,:LHmy:>GTV%/KJ7@GE[kYz
$B[6\;%%,:\KIn?GFWY/qKI1G5:;-_e
$%%%%%"""


fromSrec =  loads('srec', SREC)
dataFromSRec = dumps('fpc', fromSrec)

fromFPC =  loads('fpc', FPC)
dataFromFPC = dumps('srec', fromFPC, rowLength = 32)


class TestRoundTrip(unittest.TestCase):

    def testFromSrec(self):
        self.assertEqual(dataFromSRec, FPC)

    def testFromFPC(self):
        self.assertEqual(dataFromFPC, SREC)


class TestProbe(unittest.TestCase):

    def testProbeSrec(self):
        self.assertEqual(probes(SREC), "srec")
        
    def testProbeFpc(self):
        self.assertEqual(probes(FPC), "fpc")        


if __name__ == '__main__':
    unittest.main()

