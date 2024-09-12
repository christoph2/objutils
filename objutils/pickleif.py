#!/usr/bin/env python

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2019 by Christoph Schueler <github.com/Christoph2,
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


import abc


DUMMY_PROTOCOL = None


class PickleIF:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def dump(self, obj, file_, protocol=DUMMY_PROTOCOL):
        pass

    @abc.abstractmethod
    def dumps(self, obj, protocol=DUMMY_PROTOCOL):
        pass

    @abc.abstractmethod
    def load(self, file_):
        pass

    @abc.abstractmethod
    def loads(self, string_):
        pass
