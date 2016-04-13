#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils import loads, dumps
from objutils.Segment import Segment
from objutils.Image import Builder
from objutils.utils import createStringBuffer
import unittest


class TestBasicFunctionality(unittest.TestCase):

    def testBasic(self):
        b0 = Builder()
        b0.addSegment("hello world!")
        #b0.addSegment(unicode("€äöüßÄÖÜ", encoding = "latin-1"), 0x1000)
        b0.joinSegments()
        #b0.hexdump()


if __name__ == '__main__':
    unittest.main()

