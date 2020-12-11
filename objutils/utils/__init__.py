#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    objutils - Object file library for Python.

   (C) 2010-2020 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import os
import sys
import threading

import six


def ffs(v: int) -> int:
    """Find first set bit."""
    if v == 0:
        return 0
    res = 0
    while (not (v & 1)):
        v >>= 1
        res += 1
    return res

def slicer(iterable, sliceLength, converter = None):
    if converter is None:
        converter = type(iterable)
    length = len(iterable)
    return [converter((iterable[item : item + sliceLength])) for item in range(0, length, sliceLength)]


def make_list(*args):
    result = []
    for arg in args:
        if hasattr(arg, '__iter__'):
            result.extend(list(arg))
        else:
            result.append(arg)
    return result


def int_to_array(value):
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

def get_python_version():
    return sys.version_info

PYTHON_VERSION = get_python_version()

if PYTHON_VERSION.major == 3:
    from io import BytesIO as StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
        #from io import TextIOWrapper as StringIO
        #io.TextIOWrapper(create_string_buffer())


def create_string_buffer(*args):
    """Create a string with file-like behaviour (StringIO on Python 2.x).
    """
    buf = StringIO(*args)
    return buf

def bin_extractor(fname, offset, length):
    """Extract a junk of data from a file.
    """
    fp = open(fname)
    fp.seek(offset)
    data = fp.read(length)
    return data

CYG_PREFIX = "/cygdrive/"

def cygpath_to_win(path):
    if path.startswith(CYG_PREFIX):
        path = path[len(CYG_PREFIX) : ]
        drive_letter = "{0}:\\".format(path[0])
        path = path[2 : ].replace("/", "\\")
        path = "{0}{1}".format(drive_letter, path)
    return path


import ctypes

class StructureWithEnums(ctypes.Structure):
    """Add missing enum feature to ctypes Structures.
    """
    _map = {}

    def __getattribute__(self, name):
        _map = ctypes.Structure.__getattribute__(self, '_map')
        value = ctypes.Structure.__getattribute__(self, name)
        if name in _map:
            EnumClass = _map[name]
            if isinstance(value, ctypes.Array):
                return [EnumClass(x) for x in value]
            else:
                return EnumClass(value)
        else:
            return value

    def __str__(self):
        result = []
        result.append("struct {0} {{".format(self.__class__.__name__))
        for field in self._fields_:
            attr, attrType = field
            if attr in self._map:
                attrType = self._map[attr]
            value = getattr(self, attr)
            result.append("    {0} [{1}] = {2!r};".format(attr, attrType.__name__, value))
        result.append("};")
        return '\n'.join(result)

    __repr__ = __str__


import subprocess

class CommandError(Exception):
    pass

def runCommand(cmd):
    proc = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    result = proc.communicate()
    proc.wait()
    if proc.returncode:
        raise CommandError("{0}".format(result[1]))
    return result[0]


class SingletonBase(object):
    _lock = threading.Lock()

    def __new__(cls, *args, **kws):
        # Double-Checked Locking
        if not hasattr(cls, '_instance'):
            try:
                cls._lock.acquire()
                if not hasattr(cls, '_instance'):
                    cls._instance = super(SingletonBase, cls).__new__(cls)
            finally:
                cls._lock.release()
        return cls._instance


"""
class RepresentationMixIn(object):

    def __repr__(self):
        keys = [k for k in self.__dict__ if not (k.startswith('__') and k.endswith('__'))]
        result = []
        result.append("{0!s} {{".format(self.__class__.__name__))
        for key in keys:
            value = getattr(self, key)
            if isinstance(value, int):
                line = "    {0!s} = 0x{1:X}".format(key, value)
            elif isinstance(value, (float, type(None))):
                line = "    {0!s} = {1!s}".format(key, value)
            elif isinstance(value, array):
                line = "    {0!s} = {1!s}".format(key, helper.hexDump(value))
            else:
                line = "    {0!s} = '{1!s}'".format(key, value)
            result.append(line)
        result.append("}")
        return '\n'.join(result)
"""

import mmap

def create_memorymapped_fileview(filename, writeable = False):
    size = os.path.getsize(filename)
    fd = os.open(filename, os.O_RDWR if writeable else os.O_RDONLY)
    if six.PY3:
        return memoryview(mmap.mmap(fd, size, access = mmap.ACCESS_WRITE if writeable else mmap.ACCESS_READ))
    else:
        return mmap.mmap(fd, size, access = mmap.ACCESS_WRITE if writeable else mmap.ACCESS_READ)

