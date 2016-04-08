#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps
from objutils.Segment  import Segment
from objutils.Image  import Image, Builder
import unittest

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.b0 = Builder()
        self.b1 = Builder()

    def tearDown(self):
        del self.b0
        del self.b1

class Equality(BaseTest):

    def testEqualImagesShallCompareEqualCase1(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("01234567890", 0x1000)
        self.assertTrue(self.b0.image == self.b1.image)

    def testEqualImagesShallCompareEqualCase2(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("01234567890", 0x1000)
        self.assertFalse(self.b0.image != self.b1.image)


class Inequality(BaseTest):

    def testInequalImagesShallCompareInequalCase1(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("abcdefghijk", 0x1000)
        self.assertTrue(self.b0.image != self.b1.image)

    def testInequalImagesShallCompareInequalCase2(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("abcdefghijk", 0x1000)
        self.assertFalse(self.b0.image == self.b1.image)

    def testInequalSizeImagesShallCompareInequalCase1(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("abcdef", 0x1000)
        self.assertTrue(self.b0.image != self.b1.image)

    def testInequalSizeImagesShallCompareInequalCase2(self):
        self.b0.addSegment("01234567890", 0x1000)
        self.b1.addSegment("abcdef", 0x1000)
        self.assertFalse(self.b0.image == self.b1.image)


if __name__ == '__main__':
    unittest.main()

