Tutorial
========

This tutorial walks you through the basics of working with objutils: creating sections and images,
converting between HEX formats, controlling join behavior, and using typed access helpers.

If you prefer runnable examples, see the scripts and examples in the repository.

Before you start
----------------

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

Use these helpers when your calibration metadata uses ASAM type names
(``ULONG``, ``UWORD``, ``FLOAT32_IEEE``) and ECU byte-order terms
(``MSB_FIRST``, ``MSB_LAST_MSW_FIRST``).

When to use ASAM helpers instead of plain ``read_numeric*``/``write_numeric*``:

- Your metadata comes from A2L/ASAM naming (for example ``UWORD``/``ULONG``).
- You need ECU-specific byte order terms and MSW swapping.
- You want one consistent API for scalars, Python lists, and NumPy arrays.

For signatures and parameter semantics of the array helpers, see the
``ASAM Array Cheat Sheet`` below.

The example below shows ASAM scalars, Python arrays, NumPy arrays, and strings
side by side in one small image.

.. code-block:: python

   from objutils import Image, Section
   import numpy as np

   img = Image([Section(0x3000, bytes(96))])

   # ASAM numerics
   img.write_asam_numeric(0x3000, 0x11223344, "ULONG", "MSB_FIRST")
   img.write_asam_numeric(0x3004, 0x11223344, "ULONG", "MSB_FIRST_MSW_LAST")
   img.write_asam_numeric(0x3008, 0x11223344, "ULONG", "MSB_LAST_MSW_FIRST")

   # Roundtrip reads
   a = img.read_asam_numeric(0x3000, "ULONG", "MSB_FIRST")
   b = img.read_asam_numeric(0x3004, "ULONG", "MSB_FIRST_MSW_LAST")
   c = img.read_asam_numeric(0x3008, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM numeric arrays
   img.write_asam_numeric_array(0x3020, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")
   arr_values = img.read_asam_numeric_array(0x3020, 2, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM ndarrays
   arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x3040, arr, "UWORD", "MSB_FIRST", order="F")
   arr_roundtrip = img.read_asam_ndarray(0x3040, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")

   # ASAM strings
   img.write_asam_string(0x3010, "MOTOR", "ASCII")
   img.write_asam_string(0x3030, "Drehzahl", "UTF8")
   s0 = img.read_asam_string(0x3010, "ASCII")
   s1 = img.read_asam_string(0x3030, "UTF8")

.. rubric:: NumPy ASAM roundtrip with matrix data

.. code-block:: python

   from objutils import Image, Section
   import numpy as np

   img = Image([Section(0x5000, bytes(64))])

   matrix = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x5000, matrix, "UWORD", "MSB_FIRST", order="F")

   matrix_rt = img.read_asam_ndarray(0x5000, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")
   assert np.array_equal(matrix_rt, matrix)

.. rubric:: Supported ASAM byte orders

- ``MSB_FIRST`` (big-endian)
- ``MSB_LAST`` (little-endian)
- ``MSB_FIRST_MSW_LAST`` (word-swapped)
- ``MSB_LAST_MSW_FIRST`` (word-swapped)
- ``LITTLE_ENDIAN`` (legacy alias for ``MSB_LAST``)
- ``BIG_ENDIAN`` (legacy alias for ``MSB_FIRST``)

.. rubric:: Supported ASAM numeric datatypes

- ``UBYTE``, ``SBYTE``
- ``UWORD``, ``SWORD``
- ``ULONG``, ``SLONG``
- ``A_UINT64``, ``A_INT64``
- ``FLOAT16_IEEE``, ``FLOAT32_IEEE``, ``FLOAT64_IEEE``

.. rubric:: Supported ASAM string datatypes

- ``ASCII``
- ``UTF8``
- ``UTF16``
- ``UTF32``

.. rubric:: ASAM Array Cheat Sheet

Quick reference for the ASAM array helpers on ``Image`` and ``Section``.

.. list-table::
   :header-rows: 1
   :widths: 30 18 22 20

   * - Method
     - ``length`` semantics
     - Returns
     - Typical usage
   * - ``read_asam_numeric_array(...)``
     - element count
     - ``tuple[int]`` / ``tuple[float]``
     - scalar lists/tuples
   * - ``write_asam_numeric_array(...)``
     - n/a (from ``len(data)``)
     - ``None``
     - scalar lists/tuples
   * - ``read_asam_ndarray(...)``
     - byte count
     - ``numpy.ndarray``
     - matrix/tensor data
   * - ``write_asam_ndarray(...)``
     - n/a (from ``array.nbytes``)
     - ``None``
     - matrix/tensor data

.. rubric:: Minimal signatures

- ``read_asam_numeric_array(addr, length, dtype, byte_order="MSB_LAST")``
- ``write_asam_numeric_array(addr, data, dtype, byte_order="MSB_LAST")``
- ``read_asam_ndarray(addr, length, dtype, shape=None, order=None, byte_order="MSB_LAST")``
- ``write_asam_ndarray(addr, array, dtype, byte_order="MSB_LAST", order=None)``

.. note::
   **Fortran-order**

   With ``order="F"``, keep the existing project convention used by
   ``fortran_array_from_buffer``. For a logical 2x3 matrix, reads use
   ``shape=(3, 2)`` in the current helper path.

.. warning::
   **Frequent pitfalls**

   - Confusing element count vs. byte count for ``length``.
   - Forgetting that byte order is applied per element, not per full buffer.
   - Passing unsupported ASAM dtype names (must be values like ``UWORD``/``ULONG``).
   - Assuming MSW swapping affects 8-bit types (it does not).

.. rubric:: Copy/paste example: ULONG array roundtrip

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x6000, bytes(32))])

   img.write_asam_numeric_array(0x6000, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")

   # Optional: verify raw in-memory bytes.
   assert img.read(0x6000, 8) == b"\x33\x44\x11\x22\x77\x88\x55\x66"

   # Main check: logical values roundtrip correctly.
   values = img.read_asam_numeric_array(0x6000, 2, "ULONG", "MSB_LAST_MSW_FIRST")
   assert values == (0x11223344, 0x55667788)

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
