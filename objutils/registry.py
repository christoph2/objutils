#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <cpu12.gems@googlemail.com>

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

from collections import namedtuple, OrderedDict

from objutils.utils import SingletonBase

class CodecDoesNotExistError(Exception): pass
class CodecAlreadyExistError(Exception): pass

Codec = namedtuple("Codec", "Reader Writer description")

class Registry(SingletonBase):

    def __init__(self):
        self._codecs = OrderedDict()

    def __iter__(self):
        return iter(self._codecs.items())

    def _get_codecs(self):
        return self._codecs

    def _get_formats(self):
        return sorted(self.codecs.keys())

    def get(self, name):
        codec = self.codecs.get(name.lower())
        if not codec:
            raise CodecDoesNotExistError(name)
        return codec

    def register(self, name, readerClass, writerClass, description = ''):
        if name in self.codecs:
            raise CodecAlreadyExistError(name)
        self._codecs[name] = Codec(readerClass, writerClass, description)
        readerClass.codecName = name
        writerClass.codecName = name

    codecs = property(_get_codecs)
    formats = property(_get_formats)

registry = Registry()
