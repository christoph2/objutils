Interactive session
===================

A guided REPL walkthrough using the current API.
All snippets can be pasted directly into a Python interpreter.

Imports
-------

.. code-block:: python

    >>> from objutils import Image, Section, dump, dumps, load, loads

Hello, HEX world
----------------

Create a section and inspect it:

.. code-block:: python

    >>> sec0 = Section(start_address=0x1000, data=b"Hello HEX world!")
    >>> sec0.hexdump()
    00001000  48 65 6c 6c 6f 20 48 45 58 20 77 6f 72 6c 64 21  |Hello HEX world!|
    ---------------
           16 bytes
    ---------------

A second section with byte values 1–16:

.. code-block:: python

    >>> sec1 = Section(0x2000, range(1, 17))
    >>> sec1.hexdump()
    00002000  01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10  |................|
    ---------------
           16 bytes
    ---------------

Combine sections into an image and print it:

.. code-block:: python

    >>> img = Image([sec0, sec1])
    >>> print(img)
    Section(address = 0X00001000, length = 16, data = b'Hello HEX world!')
    Section(address = 0X00002000, length = 16, data = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10')

Format conversion
-----------------

Serialize to Motorola S‑Records and read back:

.. code-block:: python

    >>> dump("srec", "example.srec", img)
    >>> img2 = load("srec", "example.srec")
    >>> print(img2)
    Section(address = 0X00001000, length = 16, data = b'Hello HEX world!')
    Section(address = 0X00002000, length = 16, data = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10')

Convert to Intel HEX:

.. code-block:: python

    >>> dump("ihex", "example.hex", img2)

In-memory round-trip with ``dumps``/``loads``:

.. code-block:: python

    >>> raw = dumps("srec", img)
    >>> img3 = loads("srec", raw)
    >>> img3.hexdump()

Join vs. no-join
----------------

Adjacent sections are merged by default (``join=True``).
Pass ``join=False`` to keep boundaries intact:

.. code-block:: python

    >>> s0 = Section(0x100, range(1, 9))
    >>> s1 = Section(0x108, range(9, 17))

    >>> img_joined = Image([s0, s1])            # join=True (default)
    >>> img_nojoin = Image([s0, s1], join=False)

    >>> len(img_joined)
    1
    >>> len(img_nojoin)
    2

    >>> img_joined.hexdump()
    00000100  01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10  |................|
    ---------------
           16 bytes
    ---------------

Typed access — scalars
----------------------

.. code-block:: python

    >>> img = Image([Section(0x1000, bytes(64))])

    >>> img.write_numeric(0x1000, 0x10203040, "uint32_be")
    >>> img.write_numeric(0x1004, 0x50607080, "uint32_le")
    >>> img.read_numeric(0x1000, "uint32_be")
    270544960
    >>> img.read_numeric(0x1004, "uint32_le")
    1348861056

Typed access — arrays
---------------------

.. code-block:: python

    >>> img.write_numeric_array(0x1010, [0x1000, 0x2000, 0x3000], "uint16_le")
    >>> img.read_numeric_array(0x1010, 3, "uint16_le")
    [4096, 8192, 12288]

Typed access — strings
----------------------

.. code-block:: python

    >>> img.write_string(0x1020, "objutils")
    >>> img.read_string(0x1020)
    'objutils'

ASAM scalars
------------

ASAM helper methods accept ASAM/A2L type names (``ULONG``, ``UWORD``, …) and
ECU byte-order terms (``MSB_FIRST``, ``MSB_LAST``, ``MSB_FIRST_MSW_LAST``, …):

.. code-block:: python

    >>> img = Image([Section(0x3000, bytes(64))])

    >>> img.write_asam_numeric(0x3000, 0x11223344, "ULONG", "MSB_FIRST")
    >>> img.write_asam_numeric(0x3004, 0x11223344, "ULONG", "MSB_FIRST_MSW_LAST")
    >>> img.write_asam_numeric(0x3008, 0x11223344, "ULONG", "MSB_LAST_MSW_FIRST")

    >>> img.read_asam_numeric(0x3000, "ULONG", "MSB_FIRST")
    287454020
    >>> img.read_asam_numeric(0x3004, "ULONG", "MSB_FIRST_MSW_LAST")
    287454020
    >>> img.read_asam_numeric(0x3008, "ULONG", "MSB_LAST_MSW_FIRST")
    287454020

ASAM strings
------------

.. code-block:: python

    >>> img.write_asam_string(0x3010, "MOTOR",    "ASCII")
    >>> img.write_asam_string(0x3020, "Drehzahl", "UTF8")

    >>> img.read_asam_string(0x3010, "ASCII")
    'MOTOR'
    >>> img.read_asam_string(0x3020, "UTF8")
    'Drehzahl'

ASAM numeric arrays
-------------------

``length`` is the **element count**:

.. code-block:: python

    >>> img = Image([Section(0x6000, bytes(32))])
    >>> img.write_asam_numeric_array(0x6000, [0x11223344, 0x55667788], "ULONG", "MSB_LAST_MSW_FIRST")
    >>> img.read_asam_numeric_array(0x6000, 2, "ULONG", "MSB_LAST_MSW_FIRST")
    (287454020, 1432778632)

Verify the raw bytes to understand word-swap layout:

.. code-block:: python

    >>> img.read(0x6000, 8)
    b'\x33\x44\x11\x22\x77\x88\x55\x66'

ASAM ndarrays (NumPy)
---------------------

``length`` is the **element count** for ``read_asam_ndarray``.
``shape`` uses **ASAM** dimension order ``(X, Y, Z, …)``.

.. code-block:: python

    >>> import numpy as np
    >>> img = Image([Section(0x5000, bytes(64))])

    >>> matrix = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
    >>> img.write_asam_ndarray(0x5000, matrix, "UWORD", "MSB_FIRST", index_mode="COLUMN_DIR")

    >>> matrix_rt = img.read_asam_ndarray(
    ...     0x5000, 6, "UWORD", shape=(3, 2), index_mode="COLUMN_DIR", byte_order="MSB_FIRST"
    ... )
    >>> np.array_equal(matrix_rt, matrix)
    True

What next?
----------

- See the :doc:`tutorial` for a step-by-step guide through every feature.
- See :doc:`howto` for task-oriented recipes.
- See :doc:`scripts` for all CLI tools and their options.
- See :doc:`modules` for the full auto-generated API reference.
