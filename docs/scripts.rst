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
      -j, --join            Try to make continuous sections (merge adjacent ranges)
      -t {ihex,shf,srec,titxt}, --file-type {ihex,shf,srec,titxt}
                            Type of output HEX file (default: ihex)
      -e EXCLUDE, --exclude_pattern EXCLUDE
                            Exclude sections matching a Python regex
      -i INCLUDE, --include_pattern INCLUDE
                            Include only sections matching a Python regex

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


oj_elf_import
-------------

Import DWARF sections from an ELF into a ``.prgdb`` SQLite database.

.. code-block:: shell

    oj-elf-import path\to\program.elf
    oj-elf-import path\to\program.elf --out program.prgdb --force


oj_dwarf_import
---------------

Import DWARF sections into a ``.prgdb`` database. Use ``oj-dwarf-info`` for read-only inspection of existing databases.

.. code-block:: shell

    usage: oj-dwarf-import [-h] [--out-db OUT_DB] [--force] [--quiet] [--verbose]
                           [--skip-lines] [--skip-pubnames] [--skip-aranges] [--skip-mac]
                           elf

    positional arguments:
      elf                   ELF file with DWARF sections

    optional arguments:
      --out-db OUT_DB       Output .prgdb path (default: <elf>.prgdb)
      --force               Overwrite existing database
      --quiet, -q           Suppress non-error output
      --verbose, -v         Verbose DWARF processing output
      --skip-lines          Skip .debug_line processing
      --skip-pubnames       Skip .debug_pubnames processing
      --skip-aranges        Skip .debug_aranges processing
      --skip-mac            Skip .debug_macro processing

Examples:

.. code-block:: shell

    oj-dwarf-import program.elf --out-db program.prgdb
    oj-dwarf-import program.elf --force --quiet


oj_dwarf_info
-------------

Inspect DWARF data from an existing ``.prgdb`` database without performing an import.

.. code-block:: shell

    usage: oj-dwarf-info [-h] [--quiet] [--list-cus] [--summary]
                         [--walk-attrs] [--offset OFFSET]
                         db

    positional arguments:
      db                    Path to .prgdb database generated by oj-dwarf-import

    optional arguments:
      --quiet, -q           Suppress non-error output
      --list-cus            List compile units
      --summary             Print DIE/attribute counts
      --walk-attrs          Traverse DIE attributes (starts at first DIE unless --offset is set)
      --offset OFFSET       Absolute DIE offset (decimal or 0x-prefixed hex) used for --walk-attrs

Examples:

.. code-block:: shell

    oj-dwarf-info program.prgdb --summary --list-cus
    oj-dwarf-info program.prgdb --walk-attrs --offset 0x1234 -q


oj_cgen
-------

Generate C/C++ declarations from a ``.prgdb`` database using DWARF DIEs.

.. code-block:: shell

    oj-cgen program.prgdb --out generated.h
    oj-cgen program.prgdb --start 0x14182 --no-guard


oj_elf_info
-----------

.. code-block:: shell

    usage: oj-elf-info [-h] [-k] [-l LOGLEVEL] [-S] [-u] elf_file

    Display informations about ELF files.

    positional arguments:
      elf_file              ELF file

    optional arguments:
      -h, --help            show this help message and exit
      -k                    keep directory; otherwise create db in current directory
      -l LOGLEVEL           loglevel [warn | info | error | debug]
      -S, --sections, --section-headers
                            Display the sections' headers.
      -u                    Generate UTF-8 encoded output (otherwise Latin-1).

Example:

.. code-block:: shell

    oj-elf-info build/app.elf

This prints ELF class, type, machine, byte-order, OS/ABI, followed by a sections table and common notes/comments when present.

oj_elf_syms
-----------

.. code-block:: shell

    usage: oj-elf-syms [-h] [-s SECTIONS] [-p PATTERN] [-t TYPES]
                       [-a ACCESS] [-b BINDINGS] [-o {N,V}] elf_file

    Display ELF symbols.

    positional arguments:
      elf_file              ELF file

    optional arguments:
      -h, --help            show this help message and exit
      -s SECTIONS, --sections SECTIONS
                            Use only symbols from listed sections (comma-separated)
      -p PATTERN, --pattern PATTERN
                            Only display symbols matching a (Python) regex
      -t TYPES, --types TYPES
                            Use only symbols with listed types (comma-separated)
      -a ACCESS, --access ACCESS
                            Filter by access flags: A (allocate), W (write), X (execute)
      -b BINDINGS, --bindings BINDINGS
                            Use only symbols with listed bindings (comma-separated)
      -o {N,V}, --order-by {N,V}
                            Order symbols by Name or Value (default: V)

Examples:

.. code-block:: shell

    # All symbols ordered by address
    oj-elf-syms build/app.elf -o V

    # Only functions from .text, ordered by name
    oj-elf-syms build/app.elf -s .text -t FUNC -o N

    # Filter by regex and show only GLOBAL bindings that are executable
    oj-elf-syms build/app.elf -p '^(reset|_?start)$' -b GLOBAL -a X

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

oj_coff_info
------------

Display information about PE/COFF files (EXE/DLL/OBJ), optionally with PDB symbols.

.. code-block:: shell

    oj-coff-info app.exe
    oj-coff-info app.exe --pdb app.pdb


oj_coff_syms
------------

List symbols contained in a PE/COFF file (COFF table or PDB if available).

.. code-block:: shell

    oj-coff-syms app.exe
    oj-coff-syms app.exe --pattern printf --order-by N


oj_coff_extract
---------------

Extract sections contributing to the program image from a PE/COFF file.

.. code-block:: shell

    oj-coff-extract app.exe app.srec -t srec
    oj-coff-extract app.exe app.hex -t ihex -j


oj_coff_import
--------------

Import PE/COFF header, sections, and symbols into a ``.pedb`` SQLite database.

.. code-block:: shell

    oj-coff-import app.exe
    oj-coff-import app.exe --out app.pedb --force

arduino_build_artifacts
-----------------------

Locate Arduino build artifacts (ELF/HEX/EEP/MAP) produced by the Arduino IDE for a given sketch.
You can pass either the path to a .ino file or the sketch directory.

.. code-block:: shell

    usage: arduino-build-artifacts [-h] [--only {DIRECTORY,ELF,HEX,EEP,MAP} ...]
                                   [--as-paths] [--missing-ok] [--quiet]
                                   sketch

    positional arguments:
      sketch                Path to the sketch directory or .ino file

    options:
      -h, --help            show this help message and exit
      --only {DIRECTORY,ELF,HEX,EEP,MAP} ...
                            Limit output to specific artifact types (may be given multiple times)
      --as-paths            Print only paths (one per line) without labels
      --missing-ok          Do not treat missing artifacts as an error; just omit them from output
      -q, --quiet           Suppress non-error output

Examples:

.. code-block:: shell

    # Show all available artifacts with labels
    $ arduino-build-artifacts MySketch/MySketch.ino
    DIRECTORY: C:\\Users\\<you>\\AppData\\Local\\arduino\\sketches\\ABCD1234...
    ELF      : C:\\...\\MySketch.ino.elf
    HEX      : C:\\...\\MySketch.ino.hex
    MAP      : C:\\...\\MySketch.ino.map

    # Print only the ELF and HEX paths, one per line
    $ arduino-build-artifacts MySketch --only ELF HEX --as-paths
    C:\\...\\MySketch.ino.elf
    C:\\...\\MySketch.ino.hex

    # Ignore missing artifacts (e.g., no EEP generated)
    $ arduino-build-artifacts MySketch --only ELF EEP --missing-ok
