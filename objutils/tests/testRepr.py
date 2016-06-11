#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import io
#import os
from objutils import loads, dumps
from objutils.section import Section
from objutils.image import Builder
#from objutils.utils import createStringBuffer, PYTHON_VERSION
import unittest

TEST1 = "Section(address = 0X00000000, length = 10000, data = '\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\...\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f')"

class TestRepr(unittest.TestCase):

    def testImageRepresentation(self):
        builder = Builder()
        builder.addSegment([x % 256 for x in range(10000)])
        builder.joinSections()
        self.assertEqual(repr(builder.image), TEST1)

if __name__ == '__main__':
    unittest.main()

