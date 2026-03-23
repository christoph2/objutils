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

ASAM API quick reference:

- ``read_asam_numeric(addr, dtype, byte_order="MSB_LAST")``
- ``write_asam_numeric(addr, value, dtype, byte_order="MSB_LAST")``
- ``read_asam_numeric_array(addr, length, dtype, byte_order="MSB_LAST")``
- ``write_asam_numeric_array(addr, data, dtype, byte_order="MSB_LAST")``
- ``read_asam_ndarray(addr, length, dtype, shape=None, order=None, byte_order="MSB_LAST")``
- ``write_asam_ndarray(addr, array, dtype, byte_order="MSB_LAST", order=None)``
- ``read_asam_string(addr, dtype, length=-1)``
- ``write_asam_string(addr, value, dtype)``

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x3000, bytes(64))])

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
   import numpy as np

   arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
   img.write_asam_ndarray(0x3040, arr, "UWORD", "MSB_FIRST", order="F")
   arr2 = img.read_asam_ndarray(0x3040, 12, "UWORD", shape=(3, 2), order="F", byte_order="MSB_FIRST")

   # ASAM string helpers
   img.write_asam_string(0x3010, "MOTOR", "ASCII")
   name = img.read_asam_string(0x3010, "ASCII")

Why ``length`` is in bytes for ndarrays:

- ``read_asam_numeric_array(..., length=2, dtype="ULONG")`` means 2 elements.
- ``read_asam_ndarray(..., length=12, dtype="UWORD")`` means 12 raw bytes.

Byte-order notes:

- ``MSB_FIRST``: big-endian element storage.
- ``MSB_LAST``: little-endian element storage.
- ``*_MSW_*`` variants: additional 16-bit word swapping for 32/64-bit values.
- For 8-bit datatypes (``UBYTE``, ``SBYTE``), byte-order has no practical effect.

Complete ASAM array roundtrip with raw-byte check:

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x4000, bytes(32))])

   # Write two ULONG values using word-swapped little-endian semantics.
   img.write_asam_numeric_array(0x4000, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")

   # Verify binary layout in memory.
   assert img.read(0x4000, 8) == b"\x33\x44\x11\x22\x77\x88\x55\x66"

   # Roundtrip back to logical values.
   values = img.read_asam_numeric_array(0x4000, 2, "ULONG", "MSB_LAST_MSW_FIRST")
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

Next steps
----------

- See the Tutorial for a guided walk-through.
- Refer to Scripts for comprehensive CLI usage and options.
