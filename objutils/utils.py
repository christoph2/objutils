#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2014 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import itertools
import sys

def slicer(iterable, sliceLength, converter = None):
    if converter is None:
        converter = type(iterable)
    length = len(iterable)
    return [converter((iterable[item : item + sliceLength])) for item in range(0, length, sliceLength)]


def makeList(*args):
    result = []
    for arg in args:
        if hasattr(arg, '__iter__'):
            result.extend(list(arg))
        else:
            result.append(arg)
    return result


def intToArray(value):
    result = []
    while value:
        result.append(value & 0xff)
        value >>= 8
    if result:
        return list(reversed(result))
    else:
        return [0]


class Curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs
        return self.fun(*(self.pending + args), **kw)


identity = lambda self,x: x

def getPythonVersion():
    return sys.version_info

PYTHON_VERSION = getPythonVersion()

if PYTHON_VERSION.major == 3:
    from io import BytesIO as StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO


def createStringBuffer(*args):
    """Create a string with file-like behaviour (StringIO on Python 2.x).
    """
    return StringIO(*args)

def binExtractor(fname, offset, length):
    """Extract a junk of data from a file.
    """
    fp = open(fname)
    fp.seek(offset)
    data = fp.read(length)
    return data


