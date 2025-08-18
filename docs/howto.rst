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
