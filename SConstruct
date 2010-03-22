
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

target=env.Program(target="#/bin/elf_info",source=sources)
