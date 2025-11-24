Installation and Getting Started
================================

Supported Python and platforms
------------------------------

- Python >= 3.4 (CPython; PyPy not tested)
- Cross-platform; no OS-specific restrictions

Install
-------

From PyPI:

.. code-block:: shell

   pip install objutils

For development (editable install):

.. code-block:: shell

   python setup.py develop

Quick verification
------------------

Open a Python REPL and run:

.. code-block:: python

   from objutils import Image, Section, dump
   img = Image([Section(0x1000, b"hi")])
   dump("srec", "verify.srec", img)
   print("Wrote verify.srec")

Next steps
----------

- Read the Tutorial for a guided introduction.
- See HOW-TOs for task-oriented examples.
- Check Scripts for CLI utilities.
- Full docs: `latest on Read the Docs <https://objutils.rtfd.org>`_.
