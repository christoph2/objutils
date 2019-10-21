
First import some stuff we need in this tutorial:

.. code-block:: python

    >>> from objutils import dump, dumps, image, load, loads, registry

And now get ready for the usual hello world example!

Create a builder object

.. code-block:: python

   >>> builder = image.Builder()

Add our message

.. code-block:: python

   >>> builder.add_section("Hello HEX world", 0x1000)


And finally display it

.. code-block:: python

   >>> builder.hexdump()

::

   Section #0000
   -------------
   00001000  48 65 6c 6c 6f 20 48 45 58 20 77 6f 72 6c 64     |Hello HEX world |
   ---------------
   15 bytes
   ---------------


.. code-block:: python

    >>> dumps("srec", builder)

::

    b'S112100048656C6C6F2048455820776F726C649C'

So what have we done here?

(And yes, loading HEX files is also possible with `objutils`!)

As you may guess, the process is reversible

.. code-block:: python

    >>> loads("srec", dumps("srec", builder))

::

    Section(address = 0X00001000, length = 15, data = b'Hello HEX world')

HI!
