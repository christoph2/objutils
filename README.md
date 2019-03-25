pyObjUtils
==========

[![Code Climate](https://codeclimate.com/github/christoph2/objutils/badges/gpa.svg)](https://codeclimate.com/github/christoph2/objutils)
[![Coverage Status](https://coveralls.io/repos/github/christoph2/objutils/badge.svg?branch=master)](https://coveralls.io/github/christoph2/objutils?branch=master)
[![Build Status](https://travis-ci.org/christoph2/objutils.svg)](https://travis-ci.org/christoph2/objutils)
[![Build status](https://ci.appveyor.com/api/projects/status/owpi324b6wbwocq9?svg=true)](https://ci.appveyor.com/project/christoph2/objutils)
[![GPL License](http://img.shields.io/badge/license-GPL-blue.svg)](http://opensource.org/licenses/GPL-2.0)

### Welcome to objutils!
obutils is a Python library to process/parse 
object files (ELF, IEEE695, S19, iHex, Tektronix...)

you really like readelf, objdump, and objcopy, don't you?

to help you handle this daunting task.
especially embedded systems developers are often in need to do
strange things with object files...

### Features at a glance

- Write programs faster than you sreen-scrape readelf/objdump.
- Create and process ..., like Intel hex, Motorola srec, 
  Texas Instruments Text (MSP430), and some historical (text) formats.
- Decent AAABI (Arm Architecture Application Binary Interface) support.


### Basic Examples


First of all, you need to import the library (of cause...)
 
``` python
>>> import objutils
```

Ok, let's start with the obligatory hello world:

``` python
>>> builder.addSection("Hello, world")
>>> builder.image
Section(address = 0X00000000, length = 12, data = 'Hello, world')

```

Let's have a look what we've just created:

```python

>>> image = builder.image # Create a shortcut.
>>> image.hexdump()

Section #0000
-------------
00000000  48 65 6c 6c 6f 2c 20 77 6f 72 6c 64 21           |Hello, world!   |
---------------
       13 bytes
---------------
```


You may ask, what about addresses?


For a list of supported `codecs` run the following command:


