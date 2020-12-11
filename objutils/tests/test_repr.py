#!/usr/bin/env python
# -*- coding: utf-8 -*-

from objutils.image import Image
from objutils.utils import PYTHON_VERSION
import unittest

if PYTHON_VERSION.major == 2:
    RESULT = "Section(address = 0X00000000, length = 10000, data = '\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\...\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f')"
else:
    RESULT = "Section(address = 0X00000000, length = 10000, data = b'\\x00\\x01\\x02\\x03\\x04\\x05\\x06...\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f')"


class TestRepr(unittest.TestCase):

    def testImageRepresentation(self):
        image = Image()
        image.insert_section([x % 256 for x in range(10000)])
        image.join_sections()
        self.assertEqual(repr(image), RESULT)

if __name__ == '__main__':
    unittest.main()

