Interactive session
===================

A quick REPL walkthrough using the current API.

.. code-block:: python

    >>> from objutils import Image, Section, dumps, loads
    >>> img = Image([Section(0x1000, b"Hello HEX world")])
    >>> img.hexdump()

Serialize to a HEX format and read it back:

.. code-block:: python

    >>> data = dumps("srec", img)
    >>> img2 = loads("srec", data)
    >>> img2.hexdump()
