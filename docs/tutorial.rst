Tutorial
========

This tutorial walks you through the basics of working with objutils: creating sections and images,
converting between HEX formats, controlling join behavior, and using typed access helpers.

If you prefer runnable examples, see the scripts and examples in the repository.

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

ASAM byte order and datatype helpers
------------------------------------

For ECU/ASAM style type names and byte orders (including word-swap variants), use the dedicated ASAM helpers:

When to use ASAM helpers instead of plain ``read_numeric*``/``write_numeric*``:

- Your metadata comes from A2L/ASAM naming (for example ``UWORD``/``ULONG``).
- You need ECU-specific byte order terms and MSW swapping.
- You want one consistent API for scalars, Python lists, and NumPy arrays.

Method overview:

- Scalars:

  - ``read_asam_numeric(addr, dtype, byte_order="MSB_LAST")``
  - ``write_asam_numeric(addr, value, dtype, byte_order="MSB_LAST")``

- Python arrays/tuples:

  - ``read_asam_numeric_array(addr, length, dtype, byte_order="MSB_LAST")``
  - ``write_asam_numeric_array(addr, data, dtype, byte_order="MSB_LAST")``

- NumPy arrays:

  - ``read_asam_ndarray(addr, length, dtype, shape=None, order=None, byte_order="MSB_LAST")``
  - ``write_asam_ndarray(addr, array, dtype, byte_order="MSB_LAST", order=None)``

- Strings:

  - ``read_asam_string(addr, dtype, length=-1)``
  - ``write_asam_string(addr, value, dtype)``

.. code-block:: python

   from objutils import Image, Section
   import numpy as np

   img = Image([Section(0x2000, bytes(64))])

   # ASAM numerics
   img.write_asam_numeric(0x2000, 0x11223344, "ULONG", "MSB_FIRST")
   img.write_asam_numeric(0x2004, 0x11223344, "ULONG", "MSB_FIRST_MSW_LAST")
   img.write_asam_numeric(0x2008, 0x11223344, "ULONG", "MSB_LAST_MSW_FIRST")

   # Roundtrip reads
   a = img.read_asam_numeric(0x2000, "ULONG", "MSB_FIRST")
   b = img.read_asam_numeric(0x2004, "ULONG", "MSB_FIRST_MSW_LAST")
   c = img.read_asam_numeric(0x2008, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM numeric arrays
   img.write_asam_numeric_array(0x2030, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")
   arr_values = img.read_asam_numeric_array(0x2030, 2, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM ndarrays
   arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x2040, arr, "UWORD", "MSB_FIRST", order="F")
   arr_roundtrip = img.read_asam_ndarray(0x2040, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")

   # ASAM strings
   img.write_asam_string(0x2010, "MOTOR", "ASCII")
   img.write_asam_string(0x2020, "Drehzahl", "UTF8")
   s0 = img.read_asam_string(0x2010, "ASCII")
   s1 = img.read_asam_string(0x2020, "UTF8")

Parameter semantics and common pitfalls:

- ``read_asam_numeric_array(..., length=N, ...)``: ``length`` means number of elements.
- ``read_asam_ndarray(..., length=N, ...)``: ``length`` means number of bytes.
- For ndarray reads with ``order="F"``, the project uses the existing historical
  shape convention in its Fortran helper path (see examples with ``shape=(3, 2)``
  for a logical ``2x3`` matrix).
- ``byte_order`` affects each element independently; it is not a whole-buffer reversal.
- ``MSW`` swapping only changes behavior for multi-word element sizes (typically
  32-bit and 64-bit data).

Practical verification pattern:

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x3000, bytes(32))])

   img.write_asam_numeric_array(0x3000, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")

   # 1) Verify expected raw memory bytes.
   assert img.read(0x3000, 8) == b"\x33\x44\x11\x22\x77\x88\x55\x66"

   # 2) Verify logical roundtrip.
   values = img.read_asam_numeric_array(0x3000, 2, "ULONG", "MSB_LAST_MSW_FIRST")
   assert values == (0x11223344, 0x55667788)

NumPy ASAM roundtrip with matrix data:

.. code-block:: python

   from objutils import Image, Section
   import numpy as np

   img = Image([Section(0x5000, bytes(64))])

   matrix = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x5000, matrix, "UWORD", "MSB_FIRST", order="F")

   matrix_rt = img.read_asam_ndarray(0x5000, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")
   assert np.array_equal(matrix_rt, matrix)

Supported ASAM byte orders:

- ``MSB_FIRST``
- ``MSB_LAST``
- ``MSB_FIRST_MSW_LAST``
- ``MSB_LAST_MSW_FIRST``
- ``LITTLE_ENDIAN`` (legacy alias for ``MSB_LAST``)
- ``BIG_ENDIAN`` (legacy alias for ``MSB_FIRST``)

Supported ASAM numeric datatypes:

- ``UBYTE``, ``SBYTE``
- ``UWORD``, ``SWORD``
- ``ULONG``, ``SLONG``
- ``A_UINT64``, ``A_INT64``
- ``FLOAT16_IEEE``, ``FLOAT32_IEEE``, ``FLOAT64_IEEE``

Supported ASAM string datatypes:

- ``ASCII``
- ``UTF8``
- ``UTF16``
- ``UTF32``

New ASAM helper methods for arrays:

- ``read_asam_numeric_array()`` / ``write_asam_numeric_array()``
- ``read_asam_ndarray()`` / ``write_asam_ndarray()``

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
