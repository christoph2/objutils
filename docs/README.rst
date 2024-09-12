
objutils
========

.. image:: https://codeclimate.com/github/christoph2/objutils/badges/gpa.svg
   :target: https://codeclimate.com/github/christoph2/objutils

.. image:: https://coveralls.io/repos/github/christoph2/objutils/badge.svg?branch=master
    :target: https://coveralls.io/github/christoph2/objutils?branch=master

.. image:: https://github.com/christoph2/objutils/workflows/objutils/badge.svg
    :target: https://github.com/christoph2/objutils

.. image:: https://ci.appveyor.com/api/projects/status/owpi324b6wbwocq9?svg=true
    :target: https://ci.appveyor.com/project/christoph2/objutils

.. image:: https://results.pre-commit.ci/badge/github/christoph2/objutils/master.svg
   :target: https://results.pre-commit.ci/latest/github/christoph2/objutils/master
   :alt: pre-commit.ci status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: http://img.shields.io/badge/license-GPL-blue.svg
   :target: http://opensource.org/licenses/GPL-2.0


Binary data stored in hex-files is in widespread use especially in embedded systems applications.
``objutils`` gives you programmatic access to a wide array of formats and offers an practical API
to work with such data.

Get the latest version from `Github <https://github.com/christoph2/objutils>`_


Installation
------------

.. code-block:: shell

   pip install objutils

or run

.. code-block:: shell

   python setup.py develop

on your local installation.

Prerequisites
-------------

- Python >= 3.4

Features
--------

- ELF files could read, including symbols.
- Typified access (scalar and arrays) to binaray data.

Supported HEX formats
^^^^^^^^^^^^^^^^^^^^^
``objutils`` supports a bunch of HEX formats...

Current
~~~~~~~

- codec / format name

* ihex (Intel HEX)
* shf (S Hexdump (`rfc4194 <https://tools.ietf.org/html/rfc4194>`_))
* srec (Motorola S-Records)
* titxt (Texas Instruments Text)

Historical
~~~~~~~~~~

- codec / format name

* ash (ASCII Space Hex)
* cosmac (RCA Cosmac)
* emon52 (Elektor EMON52)
* etek (Tektronix Extended Hexadecimal)
* fpc (Four Packed Code)
* mostec (MOS Technology)
* rca (RCA)
* sig (Signetics)
* tek (Tektronix Hexadecimal)

**codec** is the first parameter to dump() / load() functions, e.g.:

.. code-block:: python

   img = objutils.load("ihex", "myHexFile.hex")     # Load an Intel HEX file...
   objutils.dump("srec", "mySRecFile.srec", img)    # and save it as S-Records.

First steps
-----------

If you are interested, what ``objutils`` provides to you out-of-the-box, refer to `Scripts <scripts.rst>`_ documentation.

In any case, you should work through the following tutorial:

First import all classes and functions used in this tutorial.

.. code-block:: python

   from objutils import Image, Section, dump, dumps, load, loads

Everything starts with hello world...

.. code-block:: python

   sec0 = Section(start_address = 0x1000, data = "Hello HEX world!")

The constructor parameters to `Section` reflect what they are about:
A continuous area of memory with an start address.

**data** is not necessarily a string, **array.array**s, **byte**, **bytearray** will also do,
or from an internal point of view: everything that is convertible to **bytearray** could be used.

Note: **start_address** and **data** are positional arguments, so there is no need to use them as keywords (just for the sake of illustration).


Now let's inspect our section.

.. code-block:: python

    sec0.hexdump()

    00001000  48 65 6c 6c 6f 20 48 45 58 20 77 6f 72 6c 64 21  |Hello HEX world!|
    ---------------
           16 bytes
    ---------------

**hexdump()** gives us, what in the world of hackers is known as a canonical hexdump.

HEX files usually consist of more than one section, so let's create another one.

.. code-block:: python

    sec1 = Section(0x2000, range(1, 17))
    sec1.hexdump()

    00002000  01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10  |................|
    ---------------
           16 bytes
    ---------------

Now, let's glue together our sections.

.. code-block:: python

   img0 = Image([sec0, sec1])
   print(img0)

   Section(address = 0X00001000, length = 16, data = b'Hello HEX world!')
   Section(address = 0X00002000, length = 16, data = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10')


Images are obviously a container for sections, and they are always involved if you are interacting with disk based HEX files.

.. code-block:: python

   dump("srec", "example0.srec", img0)

The resulting file could be inspected from command line.

.. code-block:: shell

    $ cat example0.srec
    S113100048656C6C6F2048455820776F726C64217A
    S11320000102030405060708090A0B0C0D0E0F1044


And loaded again...

.. code-block:: python

   img1 = load("srec", "example0.srec")
   print(img1)

   Section(address = 0X00001000, length = 16, data = b'Hello HEX world!')
   Section(address = 0X00002000, length = 16, data = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10')

This leads to the conversion idiom.

.. code-block:: python

   img1 = load("srec", "example0.srec")
   dump("ihex", "example0.hex", img1)


Note: the formats above listed as historical are for one good reason historical: they are only 16bit wide, so if you want to convert,
say a **srec** file for a 32bit MCU to them, you're out of luck.

OK, we're starting another session.

.. code-block:: python

   sec0 = Section(0x100, range(1, 9))
   sec1 = Section(0x108, range(9, 17))
   img0 = Image([sec0, sec1])
   print(img0)

   Section(address = 0X00000100, length = 16, data = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10')

   img0.hexdump()

   Section #0000
   -------------
   00000100  01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10  |................|
   ---------------
          16 bytes
   ---------------

Two sections with consecutive address ranges concatenated to one, this may or may not what you are expected.

For this reason **Image** has a **join** parameter.

.. code-block:: python

   sec0 = Section(0x100, range(1, 9))
   sec1 = Section(0x108, range(9, 17))
   img0 = Image([sec0, sec1], join = False)
   print(img0)

   Section(address = 0X00000100, length = 8, data = b'\x01\x02\x03\x04\x05\x06\x07\x08')
   Section(address = 0X00000108, length = 8, data = b'\t\n\x0b\x0c\r\x0e\x0f\x10')

   img0.hexdump()

   Section #0000
   -------------
   00000100  01 02 03 04 05 06 07 08                          |........        |
   ---------------
           8 bytes
   ---------------

   Section #0001
   -------------
   00000108  09 0a 0b 0c 0d 0e 0f 10                          |........        |
   ---------------
           8 bytes
   ---------------


One feature that sets **objutils** apart from other libraries of this breed is typified access.

We are starting with a new image.

.. code-block:: python

   img0 = Image([Section(0x1000, bytes(64))])
   print(img0)

   Section(address = 0X00001000, length = 64, data = b'\x00\x00\x00\x00\x00\x00\x00...00\x00\x00\x00\x00\x00\x00\x00')

We are now writing a string to our image.

.. code-block:: python

   img0 = Image([Section(0x1000, bytes(64))])
   img0.write(0x1010, [0xff])
   img0.hexdump()

   Section #0000
   -------------
   00001000  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   00001010  ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   00001020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   00001030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|

   img0.write_string(0x1000, "Hello HEX world!")
   img0.hexdump()

   Section #0000
   -------------
   00001000  48 65 6c 6c 6f 20 48 45 58 20 77 6f 72 6c 64 21  |Hello HEX world!|
   00001010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
             *
   00001030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   ---------------
          64 bytes
   ---------------

Notice the difference? In our **Section** example above, the string passed as a **data** parameter
was just a bunch of bytes, but now it is a "real" C-string (there is a opposite function, **read_string**,
that scans for a terminating **NULL** character).

Use **write()** and **read()** functions, if you want to access plain bytes.

But there is also support for numerical types.

.. code-block:: python

   img0 = Image([Section(0x1000, bytes(64))])
   img0.write_numeric(0x1000, 0x10203040, "uint32_be")
   img0.write_numeric(0x1004, 0x50607080, "uint32_le")
   img0.hexdump()

   Section #0000
   -------------
   00001000  10 20 30 40 80 70 60 50 00 00 00 00 00 00 00 00  |. 0@.p`P........|
   00001010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
             *
   00001030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   ---------------
          64 bytes
   ---------------


The folling types are supported:

* uint8
* int8
* uint16
* int16
* uint32
* int32
* uint64
* int64
* float32
* float64

In any case, endianess suffixes **_be** or **_le** are required.

Arrays are also supported.

.. code-block:: python

   img0 = Image([Section(0x1000, bytes(64))])
   img0.write_numeric_array(0x1000, [0x1000, 0x2000, 0x3000, 0x4000, 0x5000, 0x6000, 0x7000, 0x8000], "uint16_le")
   img0.hexdump()

   Section #0000
   -------------
   00001000  00 10 00 20 00 30 00 40 00 50 00 60 00 70 00 80  |... .0.@.P.`.p..|
   00001010  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
             *
   00001030  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  |................|
   ---------------
          64 bytes
   ---------------


This concludes our tutorial for now, but there is more stuff to follow...

Documentation
-------------

For full documentation, including installation, tutorials and PDF documents, please see `Readthedocs <https://objutils.rtfd.org>`_

Bugs/Requests
-------------

Please use the `GitHub issue tracker <https://github.com/christoph2/objutils/issues>`_ to submit bugs or request features


References
----------

`Here <https://github.com/christoph2/objutils/blob/master/docs/Data_Formats.pdf>`_ is an overview of some of the classic hex-file formats.

Authors
-------

-  `Christoph Schueler <cpu12.gems@googlemail.com>`_ - Initial work and project lead.


License
-------

This project is licensed under the GNU General Public License v2.0

Contribution
------------

If you contribute code to this project, you are implicitly allowing your code to be distributed under the GNU General Public License v2.0. You are also implicitly verifying that all code is your original work.
