Scripts provided by objutils
============================

``objutils`` contains some more or less useful scripts...

oj_elf_arm_attrs
----------------

.. code-block:: shell

    usage: oj-elf-arm-attrs [-h] elf_file

    Dump '.ARM.attributes' section.

    positional arguments:
      elf_file    .elf file

      optional arguments:
        -h, --help  show this help message and exit

You may run the following on your RaspberryPI:

.. code-block:: shell

   $ oj-elf-arm-attrs /usr/bin/gcc


   =====
   aeabi
   =====

   Name                           Value
   Description
   -------------------------------------------------------------------------------
   Tag_CPU_name                   6
   6

   Tag_CPU_arch                   6
   ARM v6

   Tag_ARM_ISA_use                1
   The user intended that this entity could use ARM instructions

   Tag_THUMB_ISA_use              1
   The user permitted this entity to use 16-bit Thumb instructions (including BL)

   Tag_FP_arch                    2
   Use of the v2 FP ISA was permitted (implies use of the v1 FP ISA)

   Tag_ABI_PCS_wchar_t            4
   The user intended the size of wchar_t to be 4

   Tag_ABI_FP_rounding            1
   The user permitted this code to choose the IEEE 754 rounding mode at run time

   Tag_ABI_FP_denormal            1
   The user permitted this code to choose the IEEE 754 rounding mode at run time

   Tag_ABI_FP_exceptions          1
   The user permitted this code to check the IEEE 754 inexact exception

   Tag_ABI_FP_number_model        3
   The user permitted this code to use all the IEEE 754-defined FP encodings

   Tag_ABI_align_needed           1
   Code was permitted to depend on the 8-byte alignment of 8-byte data items

   Tag_ABI_align8_preserved       1
   Code was required to preserve 8-byte alignment of 8-byte data objects

   Tag_ABI_enum_size              2
   The user intended Enum containers to be 32-bit

   Tag_ABI_VFP_args               1
   The user intended FP parameter/result passing to conform to AAPCS, VFP variant

   Tag_CPU_unaligned_access       1
   The user intended that this entity might make v6-style unaligned data accesses


oj_elf_extract
--------------

Extract sections from *ELF* suitible for flashing;

.. code-block:: shell

    Extract sections contributing to program image, e.g. for flash programming
    applications.

    positional arguments:
      elf_file              ELF file
      output_file_name      Output filename.

    optional arguments:
      -h, --help            show this help message and exit
      -j, --join            Try to make continuous sections.
      -t {ihex,shf,srec}, --file-type {ihex,shf,srec}
                            Type of output HEX file.

For example:

.. code-block:: shell

    $ oj-elf-extract sample_proj.elf sample_proj.srec -t srec

    Extracting from...

    Section                   Address    Length
    ---------------------------------------------
    .text                     0x00000000 46652
    .rodata                   0x0000b640 2328
    .data                     0x40002000 1996
    .sdata                    0x400027cc 16
    .eh_frame                 0x400027dc 92
    ---------------------------------------------
    HEX image written to: 'sample_proj.srec' [51084 total bytes]



oj_elf_info
-----------

oj_elf_syms
-----------

oj_hex_info
-----------

.. code-block:: shell

    usage: oj-hex-info [-h] [-d]
                       {ash,cosmac,emon52,etek,fpc,ihex,mostec,rca,shf,sig,srec,tek,titxt}
                       hex_file

    Displays informations about HEX files.

    positional arguments:
      {ash,cosmac,emon52,etek,fpc,ihex,mostec,rca,shf,sig,srec,tek,titxt}
                            file type
      hex_file              HEX file

    optional arguments:
      -h, --help            show this help message and exit
      -d, --dump            hexdump contents

Filetype is a required argument (no auto-probing yet).

Run it as follows:

Without any optional arguments just the addresses and lengths of the contained sections are shown:

.. code-block:: shell

    $ oj_hex_info srec sample.srec

    --------

    Num   Address    Length
    -------------------------------------------------------------------------------
    000   0x00001000 16
    001   0x00002000 16
    -------------------------------------------------------------------------------
                     32 total bytes

If you also want to see the contents, add *-d* option:

.. code-block:: shell

    $ oj_hex_info srec sample.srec -d

    Sections
    --------

    Num   Address    Length
    -------------------------------------------------------------------------------
    000   0x00001000 16
    001   0x00002000 16
    -------------------------------------------------------------------------------
                     32 total bytes

    Section #0000
    -------------
    00001000  48 65 6c 6c 6f 20 48 45 58 20 77 6f 72 6c 64 21  |Hello HEX world!|
    ---------------
           16 bytes
    ---------------

    Section #0001
    -------------
    00002000  01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f 10  |................|
    ---------------
           16 bytes
    ---------------
