#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
import unittest

import pytest

from objutils import loads, dumps
from objutils.section import Section
from objutils.image import Builder, Image
from objutils.utils import create_string_buffer, PYTHON_VERSION


TEST1 = """
Section #0000
-------------
00000000  68 65 6c 6c 6f 20 77 6f 72 6c 64 21              |hello world!    |
---------------
       12 bytes
---------------
"""

LORUM_IPSUM = b"""Lorem ipsum dolor sit amet, corripit ars tolle mei ad nomine Stranguillio sit aliquip
ipsa Invitamus me. Accipiet duxit a lenoni nutrix ignoras misericordia mucrone possit caput vero diam
nostra praedicabilium subsannio oculos ut libertatem adhuc. Male nuptiarum condono hunc matrimonium
nisi se in modo invenit iuvenem quasi regnum diabolum limo. Athenagorae principio intus vero non dum,
litus Ephesum iube enim est in. Solum puella eius sed esse ait Cumque persequatur sic, credo puella
eius ad suis est Apollonius."""

def test_builder_hexdump(capsys):
    b0 = Builder()
    b0.add_section("hello world!")
    b0.join_sections()
    b0.hexdump(sys.stdout)
    captured = capsys.readouterr()
    assert captured.out == TEST1


def testFailIfSectionsAreNotIterateble():
    with pytest.raises(TypeError):
        bld = Builder(4711)

def testFailIfSectionIsNotValid():
    with pytest.raises(TypeError):
        bld = Builder(["abc"])

def testValidSections():
    builder = Builder([Section(0x1000, range(128))])


class TestBuilderParameters(unittest.TestCase):

    def createImage(self, auto_sort = False, auto_join = False):
        builder = Builder(auto_sort = auto_sort, auto_join = auto_join)
        builder.add_section(range(16), 0x90)
        builder.add_section(range(16), 0x80)
        builder.add_section(range(16), 0x70)
        builder.add_section(range(16), 0x60)
        builder.add_section(range(16), 0x50)
        return [s.start_address for s in builder.image]

    def testBuilderPreservesOrder(self):
        self.assertEqual(self.createImage(auto_sort = False), [144, 128, 112, 96, 80])

    def testBuilderSortsSegments(self):
        self.assertEqual(self.createImage(auto_sort = True), [80, 96, 112, 128, 144])

    def testBuilderAutoJoinsSegments(self):
        self.assertEqual(self.createImage(auto_sort = True, auto_join = True), [80])

    def testBuilderCantJoinSegments(self):
        self.assertEqual(self.createImage(auto_sort = False, auto_join = True), [144, 128, 112, 96, 80])

    def testBuilderConstructor1(self):
        builder = Builder()
        self.assertIsInstance(builder.image, Image)
        self.assertEqual(len(builder.image), 0)

    def testBuilderConstructor2(self):
        builder = Builder(None)
        self.assertIsInstance(builder.image, Image)
        self.assertEqual(len(builder.image), 0)

    def testBuilderConstructor3(self):
        sec0 = Section(data = "hello", start_address = 0x100)
        builder = Builder(sec0)
        self.assertIsInstance(builder.image, Image)
        self.assertEqual(len(builder.image), 1)

    def testBuilderConstructor4(self):
        sec0 = Section(data = "hello", start_address = 0x100)
        sec1 = Section(data = "world", start_address = 0x200)
        builder = Builder((sec0, sec1))
        self.assertIsInstance(builder.image, Image)
        self.assertEqual(len(builder.image), 2)


if __name__ == '__main__':
    unittest.main()

