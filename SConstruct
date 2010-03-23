
includes=Split("""
	#inc
""")


lib_source=Split("""
	#src/ElfIO.c
	#src/ElfInfo.c
	#src/MemSect.c
""")

prog_source=Split("""
	#src/yol-elf-info.c
""")

cflags='-O3 -Wall -fomit-frame-pointer'

sources=prog_source

env=Environment(CCFLAGS=cflags,CPPPATH=includes)
env.VariantDir('build','src',duplicate=0)

yol_lib=env.Library("#lib/yOBJl",source=lib_source)

target=env.Program(target="#/bin/yol-elf_info",source=sources,LIBS=[yol_lib])

"""
unix > swig -python example.i
unix > gcc -c -fpic example.c example_wrap.c -I/usr/local/include/python2.6
unix > gcc -shared example.o example_wrap.o -o _example.so
unix > python
Python 2.0 (#6, Feb 21 2001, 13:29:45)
[GCC egcs-2.91.66 19990314/Linux (egcs-1.1.2 release)] on linux2
Type "copyright", "credits" or "license" for more information.
>>> import example
>>> example.fact(4)
24
>>> example.my_mod(23,7)
2
>>> example.cvar.My_variable + 4.5
7.5
"""

"""
For Swig:
---------
PYTHON_INCLUDE : Set this to the directory that contains python.h
PYTHON_LIB : Set this to the python library including path for linking
Example using Python 2.1.1:
PYTHON_INCLUDE: D:\python21\include
PYTHON_LIB: D:\python21\libs\python21.lib
"""
