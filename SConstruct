
import distutils.sysconfig

pyprefix,pyinc=distutils.sysconfig.get_config_vars('prefix','INCLUDEPY')
## LIBDEST
##print pyprefix,pyinc
##print distutils.sysconfig.get_config_vars()

"""
import distutils.sysconfig
env = Environment(SWIGFLAGS=['-python'],
                  CPPPATH=[distutils.sysconfig.get_python_inc()],
                  SHLIBPREFIX="")
env.SharedLibrary('_example.so', ['example.c', 'example.i'])
"""

"""
Import("tool_prefix")
import distutils.sysconfig, os
vars = distutils.sysconfig.get_config_vars('CC', 'CXX', 'OPT', 'BASECFLAGS', 'CCSHARED', 'LDSHARED', 'SO')
for i in range(len(vars)):
    if vars[i] is None:
        vars[i] = ""
(cc, cxx, opt, basecflags, ccshared, ldshared, so_ext) = vars
lib = SharedLibrary("dparser_swigc",
                    ["pydparser.c", "make_tables.c", "dparser_wrap.c"],
                    LIBS=['mkdparse', 'dparse'],
                    LIBPATH=["../"],
                    CC=cc,
                    SHLINK=ldshared,
                    SHLINKFLAGS=[],
                    SHLIBPREFIX="",
                    SHLIBSUFFIX=so_ext,
                    CPPPATH=[distutils.sysconfig.get_python_inc()],
                    CPPDEFINES={"SWIG_GLOBAL":None},
                    CPPFLAGS=basecflags + " " + opt)
if type(lib) == type([]): lib = lib[0]
dp1 = Install(os.path.join(tool_prefix, "lib"), "dparser.py")
dp2 = Install(os.path.join(tool_prefix, "lib"), lib)
Depends(dp1, dp2)
"""

includes=Split("""
	#inc
	$PYINC
""")

lib_source=Split("""
	#src/ElfIO.c
	#src/S19IO.c
	#src/Utl.c
	#src/ElfInfo.c
	#src/MemSect.c
""")

prog_source=Split("""
	#src/yol-elf-info.c
""")

cflags='-O3 -Wall -fomit-frame-pointer'
##cflags='-g'


"""
	todo:
	=====
	AutoConf-Functionality for 'strcpy_s' und dgl. !!!
"""


sources=prog_source
env=Environment(CCFLAGS=cflags,CPPPATH=includes,SWIGFLAGS=['-python'],PYINC=pyinc)
env.Append(CPPPATH=[distutils.sysconfig.get_python_inc()])

env.VariantDir('build','src',duplicate=0)
env.Decider('MD5-timestamp')

yol_lib=env.Library("#lib/yOBJl",source=lib_source)

##env.SharedLibrary("_foo.so","foo.i")

target=env.Program(target="#/bin/yol-elf-info",source=sources,LIBS=[yol_lib,'python26'],LIBPATH=['/cygdrive/l/Python26/libs/'])

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
