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
   img.write_asam_ndarray(0x3040, arr, "UWORD", "MSB_FIRST", index_mode="COLUMN_DIR")
   arr_roundtrip = img.read_asam_ndarray(0x3040, 6, "UWORD", shape=(3, 2), index_mode="COLUMN_DIR", byte_order="MSB_FIRST")

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
   img.write_asam_ndarray(0x5000, matrix, "UWORD", "MSB_FIRST", index_mode="COLUMN_DIR")

   matrix_rt = img.read_asam_ndarray(0x5000, 6, "UWORD", shape=(3, 2), index_mode="COLUMN_DIR", byte_order="MSB_FIRST")
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

.. rubric:: Encoding override for ASAM strings

When an ECU stores text that cannot be decoded with the default ASAM mapping
(for example Latin-1 characters in a nominally ASCII field), pass an explicit
``encoding`` keyword argument to override:

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x4000, bytes(64))])

   # Write a string that contains a non-ASCII character (Ü = 0xDC in Latin-1)
   img.write_asam_string(0x4000, "MOTOR_ÜBERDREHZAHL", "ASCII", encoding="latin-1")

   # Read it back with the same override
   text = img.read_asam_string(0x4000, "ASCII", encoding="latin-1")
   # text == 'MOTOR_ÜBERDREHZAHL'

Without ``encoding=...`` the codec is derived from *dtype* as usual
(``ASCII`` → ``"ascii"``, ``UTF8`` → ``"utf-8"``, …).

.. rubric:: ASAM Array Cheat Sheet

Quick reference for the ASAM array helpers on ``Image`` and ``Section``.

.. list-table::
   :header-rows: 1
   :widths: 30 18 28 20

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
   * - ``read_asam_ndarray(...)`` ROW_DIR / COLUMN_DIR
     - element count
     - ``numpy.ndarray``
     - matrix/tensor data
   * - ``read_asam_ndarray(...)`` ALTERNATE_WITH_X/Y
     - ignored (derived from shape)
     - ``AlternateArrayResult(values, axis)``
     - interleaved axis+value maps
   * - ``write_asam_ndarray(...)``
     - n/a (from ``array.nbytes``)
     - ``None``
     - matrix/tensor data

.. rubric:: Minimal signatures

- ``read_asam_numeric_array(addr, length, dtype, byte_order="MSB_LAST")``
- ``write_asam_numeric_array(addr, data, dtype, byte_order="MSB_LAST")``
- ``read_asam_ndarray(addr, length, dtype, shape=None, byte_order="MSB_LAST", index_mode="ROW_DIR")``
- ``write_asam_ndarray(addr, array, dtype, byte_order="MSB_LAST", index_mode="ROW_DIR")``

.. note::
   **ASAM index modes**

   +------------------------+---------------------------------------------------+
   | ``index_mode``         | Memory layout                                     |
   +========================+===================================================+
   | ``ROW_DIR`` (default)  | C-order row-major; X increments fastest           |
   +------------------------+---------------------------------------------------+
   | ``COLUMN_DIR``         | X and Y swapped; not true Fortran for dims > 2    |
   +------------------------+---------------------------------------------------+
   | ``ALTERNATE_WITH_X``   | 2-D maps only: each X-column preceded by its      |
   |                        | X-axis coordinate value in memory                 |
   +------------------------+---------------------------------------------------+
   | ``ALTERNATE_WITH_Y``   | 2-D maps only: each Y-row preceded by its Y-axis  |
   |                        | coordinate value in memory                        |
   +------------------------+---------------------------------------------------+
   | ``ALTERNATE_CURVES``   | 1-D curves sharing a common axis, stored as       |
   |                        | Array-of-Structs (AoS).  Shape must be            |
   |                        | ``(num_curves, num_axis_points)`` in ASAM         |
   |                        | convention.  Equivalent to C-order ROW_DIR of     |
   |                        | a 2-D array; returns                              |
   |                        | ``ndarray(num_axis_points, num_curves)``.         |
   +------------------------+---------------------------------------------------+

   For ``ALTERNATE_WITH_X`` / ``ALTERNATE_WITH_Y``:

   - Pass axis values with ``x_axis=<array>`` or ``y_axis=<array>`` to
     ``write_asam_ndarray``.
   - ``read_asam_ndarray`` returns an ``AlternateArrayResult(values, axis)``
     named tuple; unpack with ``values, axis = result`` or access as
     ``result.values`` / ``result.axis``.
   - The ``length`` parameter of ``read_asam_ndarray`` is ignored for these
     modes; the byte count is derived from ``shape``.

   ``shape`` always uses **ASAM convention** ``(X, Y, Z, …)`` – reversed
   compared to numpy ``(…, Z, Y, X)``.

.. rubric:: ALTERNATE_WITH_X example (map, 5 columns × 4 rows)

.. code-block:: python

   import numpy as np
   from objutils import Image, Section

   # Value matrix: shape (4, 5) in numpy  =  ASAM shape (X=5, Y=4)
   matrix = np.array(
       [[11, 21, 31, 41, 51],
        [12, 22, 32, 42, 52],
        [13, 23, 33, 43, 53],
        [14, 24, 34, 44, 54]],
       dtype=np.uint8,
   )
   x_axis = np.array([10, 20, 30, 40, 50], dtype=np.uint8)

   # Memory: x[0]=10, col0=[11,12,13,14], x[1]=20, col1=[21,22,23,24], …
   img = Image([Section(0x8000, bytes(5 * (1 + 4) + 16))])
   img.write_asam_ndarray(0x8000, matrix, "UBYTE", "MSB_LAST",
                          index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

   result = img.read_asam_ndarray(0x8000, 0, "UBYTE",
                                  shape=(5, 4), byte_order="MSB_LAST",
                                  index_mode="ALTERNATE_WITH_X")
   assert np.array_equal(result.values, matrix)
   assert np.array_equal(result.axis, x_axis)

.. rubric:: ALTERNATE_WITH_Y example (map, 5 columns × 4 rows)

.. code-block:: python

   y_axis = np.array([1, 2, 3, 4], dtype=np.uint8)

   # Memory: y[0]=1, row0=[11,21,31,41,51], y[1]=2, row1=[12,22,32,42,52], …
   img2 = Image([Section(0x9000, bytes(4 * (1 + 5) + 16))])
   img2.write_asam_ndarray(0x9000, matrix, "UBYTE", "MSB_LAST",
                           index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

   result2 = img2.read_asam_ndarray(0x9000, 0, "UBYTE",
                                    shape=(5, 4), byte_order="MSB_LAST",
                                    index_mode="ALTERNATE_WITH_Y")
   assert np.array_equal(result2.values, matrix)
   assert np.array_equal(result2.axis, y_axis)

.. warning::
   **Frequent pitfalls**

   - Confusing element count vs. byte count for ``length``.
   - Forgetting that byte order is applied per element, not per full buffer.
   - Passing unsupported ASAM dtype names (must be values like ``UWORD``/``ULONG``).
   - Assuming MSW swapping affects 8-bit types (it does not).
   - Using ``ALTERNATE_WITH_X`` / ``ALTERNATE_WITH_Y`` with a 1-D array or
     without a 2-D ``shape`` parameter.
   - Using ``ALTERNATE_CURVES`` with a 1-D array or a non-2-D ``shape``.

.. rubric:: ALTERNATE_CURVES example (3 curves, 5 axis points)

Corresponds to the C Array-of-Structs pattern from the ASAM specification::

    typedef struct { int DT10; int DT20; int DT30; } CURVE_TYPE;
    const CURVE_TYPE DATA[5] = {
        {10, 3, 4}, {12, 2, 6}, {17, 9, 8}, {10, 1, 8}, {18, 3, 8},
    };

.. code-block:: python

   import numpy as np
   from objutils import Image, Section

   # numpy shape (5 axis_points, 3 curves); ASAM shape (X=3, Y=5)
   curves = np.array(
       [[10, 3, 4],
        [12, 2, 6],
        [17, 9, 8],
        [10, 1, 8],
        [18, 3, 8]],
       dtype=np.int32,
   )
   total = curves.nbytes
   img = Image([Section(0xC000, bytes(total + 8))])
   img.write_asam_ndarray(0xC000, curves, "SLONG", "MSB_LAST",
                          index_mode="ALTERNATE_CURVES")

   result = img.read_asam_ndarray(0xC000, 15, "SLONG",
                                  shape=(3, 5), byte_order="MSB_LAST",
                                  index_mode="ALTERNATE_CURVES")
   # result.shape == (5, 3)  –  each column is one curve
   curve_dt10 = result[:, 0]   # [10, 12, 17, 10, 18]
   curve_dt20 = result[:, 1]   # [ 3,  2,  9,  1,  3]
   curve_dt30 = result[:, 2]   # [ 4,  6,  8,  8,  8]

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
