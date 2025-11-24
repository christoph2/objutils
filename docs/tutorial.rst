Tutorial
========

This tutorial walks you through the basics of working with objutils: creating sections and images,
converting between HEX formats, controlling join behavior, and using typed access helpers.

If you prefer a notebook, also see tutorial1.ipynb in the repository root (can be viewed on GitHub).

Prerequisites
-------------

- Install the package: ``pip install objutils``
- Basic familiarity with Python byte sequences

Hello, HEX world
----------------

Start by importing the primary entry points:

.. code-block:: python

   from objutils import Image, Section, dump, load, dumps, loads

Create two sections and inspect them:

.. code-block:: python

   sec0 = Section(start_address=0x1000, data=b"Hello HEX world!")
   sec1 = Section(0x2000, range(1, 17))

   img = Image([sec0, sec1])
   img.hexdump()

Persist as S‑Records and read back as Intel HEX:

.. code-block:: python

   dump("srec", "example.srec", img)
   img2 = load("srec", "example.srec")
   dump("ihex", "example.hex", img2)

Join vs. no-join
----------------

By default, consecutive sections are joined into a single section when possible. You can disable this:

.. code-block:: python

   s0 = Section(0x100, range(1, 9))
   s1 = Section(0x108, range(9, 17))

   img_joined = Image([s0, s1])           # default join=True
   img_nojoin = Image([s0, s1], join=False)

   img_joined.hexdump()
   img_nojoin.hexdump()

Typed access (strings, numbers, arrays)
---------------------------------------

Use the typed helpers to read/write structured binary data with explicit endianness.

.. code-block:: python

   img = Image([Section(0x1000, bytes(64))])

   # Strings (C-style NUL-terminated)
   img.write_string(0x1000, "Hello HEX world!")

   # Scalars with endianness
   img.write_numeric(0x1010, 0x10203040, "uint32_be")
   img.write_numeric(0x1014, 0x50607080, "uint32_le")

   # Arrays
   img.write_numeric_array(0x1018, [0x1000, 0x2000, 0x3000], "uint16_le")

   img.hexdump()

Supported scalar types:

- uint8, int8
- uint16, int16
- uint32, int32
- uint64, int64
- float32, float64

An endianness suffix (``_be`` or ``_le``) is required.

CLI companions
--------------

The library ships with handy command-line tools. A few favorites:

- ``oj-hex-info``: inspect HEX files, optionally with a hexdump (``-d``)
- ``oj-elf-extract``: extract loadable sections from an ELF to HEX (ihex/shf/srec)
- ``oj-elf-arm-attrs``: dump ``.ARM.attributes`` from an ELF

Examples:

.. code-block:: shell

   oj-hex-info srec example.srec -d
   oj-elf-extract build/app.elf app.srec -t srec

What next?
----------

- See HOW-TOs for short, task-oriented recipes.
- Explore the full API reference in the modules section.
