#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

__copyright__ = """
    pyObjUtils - Object file library for Python.

   (C) 2010-2016 by Christoph Schueler <cpu12.gems@googlemail.com>

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

import io
import os

from mako.template import Template
from mako.runtime import Context
from mako import exceptions

import objutils.utils as utils

indentText = lambda text, leftmargin = 0: '\n'.join(["{0}{1}".format((" " * leftmargin), line, ) for line in text.splitlines()])

def render(tmpl, namespace = {}, leftMargin = 0, rightMargin = 80, formatExceptions = True, encoding = 'utf-8'):
    buf = io.StringIO()
    ctx = Context(buf, **namespace)
    try:
        tobj = Template(text = tmpl, output_encoding = encoding, format_exceptions = formatExceptions)
        tobj.render_context(ctx)
    except:
        print(exceptions.text_error_template().render())
        return None
    return indentText(buf.getvalue(), leftMargin)

