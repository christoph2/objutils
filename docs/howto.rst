HOW-TOs
=======

Task-oriented examples and small recipes for common workflows.

Convert between HEX formats (API)
---------------------------------

.. code-block:: python

   from objutils import load, dump
   img = load("ihex", "in.hex")
   dump("srec", "out.srec", img)

Convert between HEX formats (CLI)
---------------------------------

.. code-block:: shell

   # Inspect input
   oj-hex-info ihex in.hex

   # Convert via a temporary Image in Python (see API example above), or use
   # your own small script to wire load/dump in CI.

Join or keep separate sections
------------------------------

By default, adjacent/overlapping sections may be merged. Disable joining to keep boundaries:

.. code-block:: python

   from objutils import Image, Section
   img = Image([Section(0x100, range(8)), Section(0x108, range(8))], join=False)
   img.hexdump()

Pretty hexdumps for reviews
---------------------------

.. code-block:: python

   from objutils import Image, Section
   Image([Section(0x1000, b"example")]).hexdump()

Read/write typed values at absolute addresses
---------------------------------------------

.. code-block:: python

   from objutils import Image, Section
   img = Image([Section(0x2000, bytes(32))])
   img.write_numeric(0x2000, 0x12345678, "uint32_be")
   img.write_numeric_array(0x2004, [1, 2, 3, 4], "uint16_le")
   img.write_string(0x2010, "hello")

Read/write ASAM values (incl. word-swap byte orders)
-----------------------------------------------------

Use these helpers when your calibration metadata uses ASAM type names
(``ULONG``, ``UWORD``, ``FLOAT32_IEEE``) and ECU byte-order terms
(``MSB_FIRST``, ``MSB_LAST_MSW_FIRST``).

.. rubric:: Scalar and string quick reference

- ``read_asam_numeric(addr, dtype, byte_order="MSB_LAST")``
- ``write_asam_numeric(addr, value, dtype, byte_order="MSB_LAST")``
- ``read_asam_string(addr, dtype, length=-1)``
- ``write_asam_string(addr, value, dtype)``

Array-specific ASAM methods are summarized in the ``ASAM Array Cheat Sheet`` below.

The example below shows ASAM scalars, Python arrays, NumPy arrays, and strings
side by side in one small image.

.. code-block:: python

   from objutils import Image, Section
   import numpy as np

   img = Image([Section(0x3000, bytes(96))])

   # ASAM numeric helpers
   img.write_asam_numeric(0x3000, 0x11223344, "ULONG", "MSB_FIRST")
   img.write_asam_numeric(0x3004, 0x11223344, "ULONG", "MSB_FIRST_MSW_LAST")
   img.write_asam_numeric(0x3008, 0x11223344, "ULONG", "MSB_LAST_MSW_FIRST")

   value0 = img.read_asam_numeric(0x3000, "ULONG", "MSB_FIRST")
   value1 = img.read_asam_numeric(0x3004, "ULONG", "MSB_FIRST_MSW_LAST")
   value2 = img.read_asam_numeric(0x3008, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM numeric array helpers
   img.write_asam_numeric_array(0x3020, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")
   values = img.read_asam_numeric_array(0x3020, 2, "ULONG", "MSB_LAST_MSW_FIRST")

   # ASAM ndarray helpers
   arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x3040, arr, "UWORD", "MSB_FIRST", order="F")
   arr2 = img.read_asam_ndarray(0x3040, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")

   # ASAM string helpers
   img.write_asam_string(0x3010, "MOTOR", "ASCII")
   img.write_asam_string(0x3030, "Drehzahl", "UTF8")
   name = img.read_asam_string(0x3010, "ASCII")
   label = img.read_asam_string(0x3030, "UTF8")

.. note::
   **Length semantics**

   - ``read_asam_numeric_array(..., length=2, dtype="ULONG")`` means 2 elements.
   - ``read_asam_ndarray(..., length=12, dtype="UWORD")`` means 12 raw bytes.

.. note::
   **Byte-order notes**

   - ``MSB_FIRST``: big-endian element storage.
   - ``MSB_LAST``: little-endian element storage.
   - ``*_MSW_*`` variants: additional 16-bit word swapping for 32/64-bit values.
   - For 8-bit datatypes (``UBYTE``, ``SBYTE``), byte-order has no practical effect.


ASAM Array Cheat Sheet (HOW-TO)
-------------------------------

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

.. rubric:: Supported byte orders

- ``MSB_FIRST`` (big-endian)
- ``MSB_LAST`` (little-endian)
- ``MSB_FIRST_MSW_LAST`` (word-swapped)
- ``MSB_LAST_MSW_FIRST`` (word-swapped)
- ``BIG_ENDIAN`` / ``LITTLE_ENDIAN`` (legacy aliases)

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

Extract loadable image from ELF
-------------------------------

Use the CLI to generate HEX for flashing:

.. code-block:: shell

   oj-elf-extract build/app.elf app.srec -t srec

Inspect HEX files
-----------------

.. code-block:: shell

   # Show section addresses and lengths only
   oj-hex-info srec app.srec

   # Include a hexdump of sections
   oj-hex-info srec app.srec -d

Where to go next
----------------

- See the Tutorial for a guided walk-through.
- Refer to Scripts for comprehensive CLI usage and options.
