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

   # ASAM string helpers
   img.write_asam_string(0x3010, "MOTOR", "ASCII")
   name = img.read_asam_string(0x3010, "ASCII")

Read/write ASAM strings with encoding override
----------------------------------------------

Some ECUs store Latin-1 (or other non-UTF-8) characters in a field that is
declared ``ASCII`` in the A2L description.  Use the ``encoding`` keyword to
override the codec without changing the ASAM dtype name:

.. code-block:: python

   from objutils import Image, Section

   img = Image([Section(0x4000, bytes(64))])

   # The string contains "Ü" (0xDC in Latin-1) – would fail with plain ASCII
   img.write_asam_string(0x4000, "MOTOR_ÜBERDREHZAHL", "ASCII", encoding="latin-1")
   name = img.read_asam_string(0x4000, "ASCII", encoding="latin-1")
   # name == 'MOTOR_ÜBERDREHZAHL'

The ``encoding`` parameter is accepted by both ``read_asam_string`` and
``write_asam_string`` on ``Section`` as well as ``Image``.

Read/write ASAM characteristic maps with ALTERNATE_WITH_X
---------------------------------------------------------

``ALTERNATE_WITH_X`` stores each X-column preceded by its X-axis coordinate:
``[x[0], f(0,0), f(0,1), …, x[1], f(1,0), f(1,1), …]``.

.. code-block:: python

   import numpy as np
   from objutils import Image, Section

   # ASAM shape (X=3, Y=4) → numpy shape (4, 3)
   matrix = np.array(
       [[11, 21, 31],
        [12, 22, 32],
        [13, 23, 33],
        [14, 24, 34]],
       dtype=np.uint8,
   )
   x_axis = np.array([10, 20, 30], dtype=np.uint8)

   total = 3 * (1 + 4)   # num_x * (axis_byte + num_y * element_byte)
   img = Image([Section(0x8000, bytes(total + 8))])

   img.write_asam_ndarray(0x8000, matrix, "UBYTE", "MSB_LAST",
                          index_mode="ALTERNATE_WITH_X", x_axis=x_axis)

   result = img.read_asam_ndarray(0x8000, 0, "UBYTE",
                                  shape=(3, 4), byte_order="MSB_LAST",
                                  index_mode="ALTERNATE_WITH_X")
   # result.values  →  matrix
   # result.axis    →  x_axis

Read/write ASAM characteristic maps with ALTERNATE_WITH_Y
---------------------------------------------------------

``ALTERNATE_WITH_Y`` stores each Y-row preceded by its Y-axis coordinate:
``[y[0], f(0,0), f(1,0), …, y[1], f(0,1), f(1,1), …]``.

.. code-block:: python

   y_axis = np.array([1, 2, 3, 4], dtype=np.uint8)

   total_y = 4 * (1 + 3)   # num_y * (axis_byte + num_x * element_byte)
   img2 = Image([Section(0x9000, bytes(total_y + 8))])

   img2.write_asam_ndarray(0x9000, matrix, "UBYTE", "MSB_LAST",
                           index_mode="ALTERNATE_WITH_Y", y_axis=y_axis)

   result2 = img2.read_asam_ndarray(0x9000, 0, "UBYTE",
                                    shape=(3, 4), byte_order="MSB_LAST",
                                    index_mode="ALTERNATE_WITH_Y")
   # result2.values  →  matrix
   # result2.axis    →  y_axis

Extract loadable image from ELF
-------------------------------

Use the CLI to generate HEX for flashing:

.. code-block:: shell

   oj-elf-extract build/app.elf app.srec -t srec

Analyse ELF without writing a .prgdb file (in-memory database)
---------------------------------------------------------------

By default ``ElfParser`` creates a ``<name>.prgdb`` SQLite cache file next to
the ELF file.  Pass ``in_memory=True`` to keep everything in memory – useful
for read-only scripting, CI pipelines, or unit tests where disk writes are
undesirable.

.. code-block:: python

   from objutils.elf import ElfParser

   # No .prgdb file is created – database lives only in RAM
   with ElfParser('build/app.elf', in_memory=True) as parser:
       print(f"Machine: {parser.e_machine}")
       image = parser.create_image()

.. note::

   The in-memory database is rebuilt on every instantiation (no caching
   benefit).  Use the default on-disk mode if you parse the same file
   repeatedly and want fast cached access.

Extract loadable image from PE/COFF (32-bit and 64-bit)
-------------------------------------------------------

For 32-bit PE files the default behaviour works out of the box:

.. code-block:: shell

   oj-coff-extract app32.exe app32.hex -t ihex

64-bit PE files typically have an image base of ``0x140000000`` or higher.
When the image base is added to section RVAs, the resulting absolute addresses
exceed the 32-bit limit (``0xFFFFFFFF``) that Intel HEX and Motorola S-Record
formats can represent. The tool will abort with an *"address too large"* error
in that case.

Use the ``--no-image-base`` (``-r``) flag to emit **relative virtual
addresses** (RVAs) instead.  RVAs start at zero and therefore stay well within
32-bit range:

.. code-block:: shell

   # Will fail for a typical 64-bit PE (image base 0x140000000)
   oj-coff-extract app64.exe app64.hex

   # Use --no-image-base to subtract the image base
   oj-coff-extract app64.exe app64.hex --no-image-base

The tool prints which mode is active so you can verify:

.. code-block:: text

   Using relative addresses (image base 0x140000000 subtracted).

.. note::

   When ``--no-image-base`` is used, the addresses in the output file are
   offsets from the PE image base.  Your flash-programming tool or linker
   script must account for this by adding the base back at load time.

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
