#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <github.com/Christoph2,
                                        cpu12.gems@googlemail.com>

   All Rights Reserved

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import objutils.dwarf.constants
import unittest


class Attribute(object):
  __slots__ = ['_name', '_value']

  def __init__(self, name, value):
    self._name = name
    self._value = value

  def _getName(self):
    return self._name

  def _getValue(self):
    return self._value

  def __repr__(self):
    return "Attribute(%s = %s)" % (self.name, self.value)

  name = property(_getName)
  value = property(_getValue)


class DebuggingInformationEntry(object):
    __slots__ = ['_tag', '_attributes', '_parent', '_siblings', '_children']

    def __init__(self, tag, attributes, parent = None, siblings = None, children = None):
      if siblings is None:
        siblings = []
      if children is None:
        children = []
      self._tag = tag
      self._attributes = attributes
      self._parent = parent
      self._siblings = siblings
      self._children = children


    def _getTag(self):
      return self._tag

    def _getAttributes(self):
      return self._attributes

    def _getParent(self):
      return self._parent

    def _getSiblings(self):
      return self._siblings

    def _getChildren(self):
      return self._children

    tag = property(_getTag)
    attributes = property(_getAttributes)
    parent = property(_getParent)
    siblings = property(_getSiblings)
    children = property(_getChildren)


def createAttributes(*attributes):
  result = []

  for name, value in attributes:
    result.append(Attribute(name, value))
  return result


##
##def test():
##
##  attrs = createAttributes( ("Name", 'int'), ("ByteSize", 4),  ("Encoding", "signed integer"))
##  baseType = DebuggingInformationEntry('baseType', attrs)
##
##  attrs = createAttributes( ('Name', ' main'), ('File', 'hello.c'), ('Line', 2), ('Type', 'int'), ('LowPC', 0x0), ('HighPC', 0x2b),
##    ('External', 'yes'),
##  )
##  subprogram = DebuggingInformationEntry('subprograms', attrs, children = [baseType])
##
##  attrs = createAttributes( ('Dir', '/home/dwarf/examples'), ('Name', 'hello.c'), ('LowPC', 0x2000), ('HighPC', 0x2b00), ('Producer', 'GCC'))
##  compilationUnit = DebuggingInformationEntry('compilationUnit', attrs, children = [subprogram])
##
##
##def main():
##    print constants.DW_TAG_base_type
##    test()
##    die = DebuggingInformationEntry('flonz', [])
##
##if __name__ == '__main__':
##    main()
##
##
