#!/usr/bin/env python

# dbghelp_symbols.py
import ctypes
import sys
from copy import copy
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import IntEnum
from functools import cached_property, lru_cache
from typing import List, Optional
from collections.abc import Generator


# DLLs
try:
    dbghelp = ctypes.WinDLL("dbghelp")  # type: ignore[attr-defined]
    kernel32 = ctypes.WinDLL("kernel32")  # type: ignore[attr-defined]
    psapi = ctypes.WinDLL("psapi")
    _WINDOWS = True
except Exception:  # pragma: no cover - non-Windows environment
    dbghelp = None  # type: ignore[assignment]
    kernel32 = None  # type: ignore[assignment]
    psapi = None
    _WINDOWS = False


@dataclass
class ModuleInfo:
    base_of_dll: int
    size_of_image: int
    entry_point: Optional[int]


# Types
HANDLE = wintypes.HANDLE
HLOCAL = wintypes.HANDLE
DWORD = wintypes.DWORD
ULONG = wintypes.ULONG
ULONG64 = ctypes.c_ulonglong
BOOL = wintypes.BOOL
LPVOID = wintypes.LPVOID
LPCWSTR = wintypes.LPCWSTR
LPCSTR = wintypes.LPCSTR

# SYMBOL_INFO struct (ANSI)
MAX_SYM_NAME = 2000


class SYMBOL_INFO(ctypes.Structure):
    def is_clr_token(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_CLR_TOKEN)

    def is_constant(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_CONSTANT)

    def is_export(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_EXPORT)

    def is_forwarder(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_FORWARDER)

    def is_framerel(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_FRAMEREL)

    def is_function(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_FUNCTION)

    def is_ilrel(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_ILREL)

    def is_local(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_LOCAL)

    def is_metadata(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_METADATA)

    def is_parameter(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_PARAMETER)

    def is_register(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_REGISTER)

    def is_regrel(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_REGREL)

    def is_slot(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_SLOT)

    def is_thunk(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_THUNK)

    def is_tlsrel(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_TLSREL)

    def is_value_present(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_VALUEPRESENT)

    def is_virtual(self) -> bool:
        return bool(self.Flags & SymFlag.SYMFLAG_VIRTUAL)

    # @cached_property
    def decode_flags(self) -> list[str]:
        return [f.name for f in SymFlag if self.Flags & f.value]

    # @cached_property
    @property
    def name(self):
        return self.Name.decode(errors="ignore")

    # @cached_property
    @property
    def tag(self):
        try:
            return SymTagEnum(self.Tag).name
        except ValueError:
            return SymTagEnum.SymTagNull.name

    # @cached_property
    @property
    def rel_address(self):
        return self.Address - (0 if self.ModBase is None else self.ModBase)

    def __repr__(self) -> str:
        name = self.Name.decode(errors="ignore")
        return f"<SYMBOL_INFO name={name} address=0x{self.Address:x} flags={self.decode_flags}>"

    _fields_ = [
        ("SizeOfStruct", ULONG),
        ("TypeIndex", ULONG),
        ("Reserved", ULONG64 * 2),
        ("Index", ULONG),
        ("Size", ULONG),
        ("ModBase", ULONG64),
        ("Flags", ULONG),
        ("Value", ULONG64),
        ("Address", ULONG64),
        ("Register", ULONG),
        ("Scope", ULONG),
        ("Tag", ULONG),
        ("NameLen", ULONG),
        ("MaxNameLen", ULONG),
        ("Name", ctypes.c_char * (MAX_SYM_NAME + 1)),
    ]


# MODULEINFO struct
class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", LPVOID),
        ("SizeOfImage", DWORD),
        ("EntryPoint", LPVOID),
    ]


class SymTagEnum(IntEnum):
    SymTagNull = 0
    SymTagExe = 1
    SymTagCompiland = 2
    SymTagCompilandDetails = 3
    SymTagCompilandEnv = 4
    SymTagFunction = 5
    SymTagBlock = 6
    SymTagData = 7
    SymTagAnnotation = 8
    SymTagLabel = 9
    SymTagPublicSymbol = 10
    SymTagUDT = 11
    SymTagEnum = 12
    SymTagFunctionType = 13
    SymTagPointerType = 14
    SymTagArrayType = 15
    SymTagBaseType = 16
    SymTagTypedef = 17
    SymTagBaseClass = 18
    SymTagFriend = 19
    SymTagFunctionArgType = 20
    SymTagFuncDebugStart = 21
    SymTagFuncDebugEnd = 22
    SymTagUsingNamespace = 23
    SymTagVTableShape = 24
    SymTagVTable = 25
    SymTagCustom = 26
    SymTagThunk = 27
    SymTagCustomType = 29
    SymTagManagedType = 30
    SymTagDimension = 31


class IMAGEHLP_SYMBOL_TYPE_INFO(IntEnum):
    TI_GET_SYMTAG = 0
    TI_GET_SYMNAME = 1
    TI_GET_LENGTH = 2
    TI_GET_TYPE = 3
    TI_GET_TYPEID = 4
    TI_GET_BASETYPE = 5
    TI_GET_ARRAYINDEXTYPEID = 6
    TI_FINDCHILDREN = 7
    TI_GET_DATAKIND = 8
    TI_GET_ADDRESSOFFSET = 9
    TI_GET_OFFSET = 10
    TI_GET_VALUE = 11
    TI_GET_COUNT = 12
    TI_GET_CHILDRENCOUNT = 13
    TI_GET_BITPOSITION = 14
    TI_GET_VIRTUALBASECLASS = 15
    TI_GET_VIRTUALTABLESHAPEID = 16
    TI_GET_VIRTUALBASEPOINTEROFFSET = 17
    TI_GET_CLASSTYPEID = 18
    TI_GET_NESTED = 19
    TI_GET_SYMINDEX = 20
    TI_GET_LEXICALPARENT = 21
    TI_GET_ADDRESS = 22
    TI_GET_THISADJUST = 23
    TI_GET_UDTKIND = 24
    TI_IS_EQUIV_TO = 25
    TI_GET_CALLING_CONVENTION = 26
    TI_IS_CLOSE_EQUIV_TO = 27
    TI_GTIEX_REQS_VALID = 28
    TI_GET_VIRTUALBASEOFFSET = 29
    TI_GET_VIRTUALBASEDISPINDEX = 30
    TI_GET_IS_REFERENCE = 31
    TI_GET_INDIRECTVIRTUALBASEDISPINDEX = 32
    TI_GET_VIRTUALBASETABLETYPEID = 33
    TI_GET_OBJECTPOINTERTYPEID = 34
    TI_GET_IS_CONST = 35
    TI_GET_IS_VOLATILE = 36
    TI_GET_IS_UNALIGNED = 37


class BasicType(IntEnum):
    btNoType = 0
    btVoid = 1
    btChar = 2
    btWChar = 3
    btInt = 6
    btUInt = 7
    btFloat = 8
    btBCD = 9
    btBool = 10
    btLong = 13
    btULong = 14
    btCurrency = 25
    btDate = 26
    btVariant = 27
    btComplex = 28
    btBit = 29
    btBSTR = 30
    btHresult = 31
    btChar16 = 32
    btChar32 = 33
    btChar8 = 34


class SymFlag(IntEnum):
    SYMFLAG_VALUEPRESENT = 0x00000001
    SYMFLAG_REGISTER = 0x00000008
    SYMFLAG_REGREL = 0x00000010
    SYMFLAG_FRAMEREL = 0x00000020
    SYMFLAG_PARAMETER = 0x00000040
    SYMFLAG_LOCAL = 0x00000080
    SYMFLAG_CONSTANT = 0x00000100
    SYMFLAG_EXPORT = 0x00000200
    SYMFLAG_FORWARDER = 0x00000400
    SYMFLAG_FUNCTION = 0x00000800
    SYMFLAG_VIRTUAL = 0x00001000
    SYMFLAG_THUNK = 0x00002000
    SYMFLAG_TLSREL = 0x00004000
    SYMFLAG_SLOT = 0x00008000
    SYMFLAG_ILREL = 0x00010000
    SYMFLAG_METADATA = 0x00020000
    SYMFLAG_CLR_TOKEN = 0x00040000


# Prototypes
if _WINDOWS:
    dbghelp.SymInitialize.argtypes = [HANDLE, LPCWSTR, BOOL]
    dbghelp.SymInitialize.restype = BOOL

    dbghelp.SymCleanup.argtypes = [HANDLE]
    dbghelp.SymCleanup.restype = BOOL

    dbghelp.SymSetOptions.argtypes = [DWORD]
    dbghelp.SymSetOptions.restype = DWORD

    dbghelp.SymGetOptions.argtypes = []
    dbghelp.SymGetOptions.restype = DWORD

    dbghelp.SymLoadModuleExW.argtypes = [HANDLE, HANDLE, LPCWSTR, LPCWSTR, ULONG64, DWORD, LPVOID, DWORD]
    dbghelp.SymLoadModuleExW.restype = ULONG64  # returns base

    dbghelp.SymSetSearchPath.argtypes = [HANDLE, LPCSTR]
    dbghelp.SymSetSearchPath.restype = BOOL

    dbghelp.SymGetSearchPath.argtypes = [HANDLE, ctypes.c_char_p, DWORD]
    dbghelp.SymGetSearchPath.restype = BOOL

# SymEnumSymbolsA callback and function
if _WINDOWS:
    PSYM_ENUMERATESYMBOLS_CALLBACK = ctypes.WINFUNCTYPE(
        BOOL,
        ctypes.POINTER(SYMBOL_INFO),
        ULONG,
        LPVOID,
    )

if _WINDOWS:
    dbghelp.SymEnumSymbols.argtypes = [HANDLE, ULONG64, LPCSTR, PSYM_ENUMERATESYMBOLS_CALLBACK, LPVOID]
    dbghelp.SymEnumSymbols.restype = BOOL

# SymFromAddr
if _WINDOWS:
    dbghelp.SymFromAddr.argtypes = [HANDLE, ULONG64, ctypes.POINTER(ULONG64), ctypes.POINTER(SYMBOL_INFO)]
    dbghelp.SymFromAddr.restype = BOOL

    dbghelp.SymGetTypeInfo.argtypes = [HANDLE, ULONG64, ULONG, ctypes.c_int, LPVOID]
    dbghelp.SymGetTypeInfo.restype = BOOL

# Kernel32 helpers
if _WINDOWS:
    kernel32.GetCurrentProcess.restype = HANDLE
    psapi.GetModuleInformation.argtypes = [HANDLE, HANDLE, ctypes.POINTER(MODULEINFO), DWORD]
    psapi.GetModuleInformation.restype = BOOL
    kernel32.GetLastError.restype = DWORD
    kernel32.LoadLibraryA.argtypes = [LPCSTR]
    kernel32.LoadLibraryA.restype = HANDLE
    kernel32.FreeLibrary.argtypes = [HANDLE]
    kernel32.FreeLibrary.restype = BOOL
    kernel32.LocalFree.argtypes = [HLOCAL]
    kernel32.LocalFree.restype = HLOCAL


def last_error():
    if not _WINDOWS:
        return 0
    return kernel32.GetLastError()


# SYMOPT flags (subset)
SYMOPT_DEFERRED_LOADS = 0x00000004
SYMOPT_UNDNAME = 0x00000002
SYMOPT_LOAD_LINES = 0x00000010


def load_library(lib_path: str) -> HANDLE:
    """Loads the specified module into the address space of the calling process."""
    if not _WINDOWS:
        raise OSError("PDB support requires Windows (kernel32.dll)")
    handle = kernel32.LoadLibraryA(lib_path.encode("ascii"))
    if not handle:
        raise OSError(f"LoadLibraryA failed for {lib_path}, error={last_error()}")
    return handle


def free_library(hmod: HANDLE) -> None:
    """Frees the loaded dynamic-link library (DLL) module."""
    if not _WINDOWS:
        raise OSError("PDB support requires Windows (kernel32.dll)")
    if not kernel32.FreeLibrary(hmod):
        raise OSError(f"FreeLibrary failed, error={last_error()}")


class CTypeInfoDump:

    def __init__(self, process, mod_base):
        self.process = process
        self.mod_base = mod_base

    def get_type_info(self, type_id, info_type):
        if not _WINDOWS:
            return None
        if info_type in (IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME,):
            ptr = ctypes.c_void_p()
            if dbghelp.SymGetTypeInfo(self.process, self.mod_base, type_id, info_type.value, ctypes.byref(ptr)):
                if ptr.value:
                    name = ctypes.wstring_at(ptr)
                    kernel32.LocalFree(ptr)
                    return name
        elif info_type in (
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_BASETYPE,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_ARRAYINDEXTYPEID,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_COUNT,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_CHILDRENCOUNT,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_OFFSET,
        ):
            out = DWORD()
            if dbghelp.SymGetTypeInfo(self.process, self.mod_base, type_id, info_type.value, ctypes.byref(out)):
                return out.value
        elif info_type in (IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH,):
            out = ULONG64()
            if dbghelp.SymGetTypeInfo(self.process, self.mod_base, type_id, info_type.value, ctypes.byref(out)):
                return out.value
        elif info_type in (
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_CONST,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_VOLATILE,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_UNALIGNED,
            IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_REFERENCE,
        ):
            out = BOOL()
            if dbghelp.SymGetTypeInfo(self.process, self.mod_base, type_id, info_type.value, ctypes.byref(out)):
                return bool(out.value)
        return None

    def get_full_type_name(self, type_id) -> str:
        tag_val = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMTAG)
        if tag_val is None:
            return "unknown"

        try:
            tag = SymTagEnum(tag_val)
        except ValueError:
            return f"unknown_tag_{tag_val}"

        prefix = ""
        if self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_CONST):
            prefix += "const "
        if self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_VOLATILE):
            prefix += "volatile "

        if tag == SymTagEnum.SymTagBaseType:
            bt = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_BASETYPE)
            length = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_LENGTH)
            if bt is not None:
                try:
                    bt_name = BasicType(bt).name.lstrip("bt")
                except ValueError:
                    bt_name = f"base_{bt}"
                if length:
                    # Map some common lengths to standard names if possible, but bit length is fine
                    if bt_name == "Int" or bt_name == "UInt":
                        bt_name = f"{bt_name.lower()}{length*8}_t"
                    else:
                        bt_name = f"{bt_name}{length*8}"
                return prefix + bt_name
            return prefix + "void"

        if tag == SymTagEnum.SymTagPointerType:
            child_id = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID)
            is_ref = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_IS_REFERENCE)
            suffix = "&" if is_ref else "*"
            return self.get_full_type_name(child_id) + suffix

        if tag == SymTagEnum.SymTagArrayType:
            child_id = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_TYPEID)
            count = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_COUNT)
            if count is not None:
                return f"{self.get_full_type_name(child_id)}[{count}]"
            return f"{self.get_full_type_name(child_id)}[]"

        if tag in (SymTagEnum.SymTagUDT, SymTagEnum.SymTagEnum, SymTagEnum.SymTagTypedef):
            name = self.get_type_info(type_id, IMAGEHLP_SYMBOL_TYPE_INFO.TI_GET_SYMNAME)
            if name:
                return prefix + name
            return prefix + tag.name.lstrip("SymTag")

        if tag == SymTagEnum.SymTagFunctionType:
            return prefix + "function"

        return prefix + tag.name.lstrip("SymTag")


class PdbSession:
    """
    Manages a dbghelp symbol session.
    """

    def __init__(self, symbol_path: list[str] | None = None):
        if not _WINDOWS:
            raise OSError("PDB support requires Windows (dbghelp.dll)")

        self.hproc = kernel32.GetCurrentProcess()
        if symbol_path:
            symbol_path_str = ";".join(symbol_path)
        else:
            symbol_path_str = None

        if not dbghelp.SymInitialize(self.hproc, symbol_path_str, True):
            raise OSError(f"SymInitialize failed, error={last_error()}")

        opts = dbghelp.SymGetOptions()
        opts |= SYMOPT_DEFERRED_LOADS | SYMOPT_UNDNAME | SYMOPT_LOAD_LINES
        dbghelp.SymSetOptions(opts)
        self.type_dumper_cache = {}

    @lru_cache
    def type_info(self, base: int, type_index: int) -> str:
        if type_index:
            if base in self.type_dumper_cache:
                type_dumper = self.type_dumper_cache[base]
            else:
                type_dumper = CTypeInfoDump(self.hproc, base)
                self.type_dumper_cache[base] = type_dumper
            return type_dumper.get_full_type_name(type_index)
        return "unknown"

    def cleanup(self) -> None:
        """Cleans up the dbghelp session."""
        if _WINDOWS and hasattr(self, "hproc"):
            dbghelp.SymCleanup(self.hproc)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def set_search_path(self, search_path: str) -> None:
        """Sets the symbol search path for the current session."""
        if not dbghelp.SymSetSearchPath(self.hproc, search_path.encode("ascii")):
            raise OSError(f"SymSetSearchPath failed, error={last_error()}")

    def get_search_path(self) -> str:
        """Gets the symbol search path for the current session."""
        buffer = ctypes.create_string_buffer(2048)
        if not dbghelp.SymGetSearchPath(self.hproc, buffer, ctypes.sizeof(buffer)):
            raise OSError(f"SymGetSearchPath failed, error={last_error()}")
        return buffer.value.decode("ascii")

    def load_module(self, file_path: str) -> int:
        """Loads a module for the current session."""
        file_path = str(file_path)
        base = dbghelp.SymLoadModuleExW(self.hproc, None, file_path, None, 0, 0, None, 0)
        if base == 0:
            raise OSError(f"SymLoadModuleExW failed for {file_path}, error={last_error()}")
        return base

    def enum_symbols(self, base: int, pattern: bytes = b"*") -> list[dict]:  # Generator[]:
        """Enumerates symbols in a loaded module."""
        results: list[dict] = []

        def _cb(pSymInfo, size, ctx):
            sym = pSymInfo.contents
            name = sym.name
            addr = sym.Address
            tag = sym.tag

            type_name = self.type_info(base, sym.TypeIndex)
            results.append(copy(sym))
            # results.append({
            #    "name": name,
            #    "address": int(addr),
            #    "tag": tag.name.lstrip("SymTag"),
            #    "flags": sym.Flags,
            #    "decoded_flags": sym.decode_flags,
            #    "type": type_name,
            # })
            return True

        cb = PSYM_ENUMERATESYMBOLS_CALLBACK(_cb)
        if not dbghelp.SymEnumSymbols(self.hproc, base, pattern, cb, None):
            raise OSError(f"SymEnumSymbols failed, error={last_error()}")
        return results

    def sym_from_addr(self, addr: int):
        """Retrieves symbol information for the specified address."""
        displacement = ULONG64(0)
        info = SYMBOL_INFO()
        info.SizeOfStruct = ctypes.sizeof(SYMBOL_INFO)
        info.MaxNameLen = MAX_SYM_NAME
        if not dbghelp.SymFromAddr(self.hproc, ULONG64(addr), ctypes.byref(displacement), ctypes.byref(info)):
            raise OSError(f"SymFromAddr failed, error={last_error()}")
        return info.Name.decode(errors="ignore"), int(info.Address), int(displacement.value)

    def get_module_information(self, hmod: HANDLE) -> ModuleInfo:
        """Gets module information for the given module handle."""
        modinfo = MODULEINFO()
        if not psapi.GetModuleInformation(self.hproc, hmod, ctypes.byref(modinfo), ctypes.sizeof(modinfo)):
            raise OSError(f"GetModuleInformation failed, error={last_error()}")
        return ModuleInfo(modinfo.lpBaseOfDll, modinfo.SizeOfImage, modinfo.EntryPoint)


def load_library(lib_path: str) -> HANDLE:
    """Loads the specified module into the address space of the calling process."""
    if not _WINDOWS:
        raise OSError("PDB support requires Windows (kernel32.dll)")
    handle = kernel32.LoadLibraryA(lib_path.encode("ascii"))
    if not handle:
        raise OSError(f"LoadLibraryA failed for {lib_path}, error={last_error()}")
    return handle


def free_library(hmod: HANDLE) -> None:
    """Frees the loaded dynamic-link library (DLL) module."""
    if not _WINDOWS:
        raise OSError("PDB support requires Windows (kernel32.dll)")
    if not kernel32.FreeLibrary(hmod):
        raise OSError(f"FreeLibrary failed, error={last_error()}")


def pdb_symbols_for_pe(pe_path: str, symbol_path: str | None = None) -> list[dict]:
    """
    High-level helper: load symbols for a PE image via dbghelp and return
    a list of dictionaries with fields compatible to Pe_Symbol.
    Fields: name, value (address RVA or VA), section_number, type, storage_class.
    For PDB-derived symbols, section_number/type/storage_class are set to 0.
    """
    if not _WINDOWS:
        return []

    try:
        with PdbSession(symbol_path if not symbol_path else [symbol_path]) as session:
            mod_base = session.load_module(pe_path)
            return session.enum_symbols(mod_base, b"*")
            # dbghelp returns absolute addresses (load address); we keep as 'value'
            result: list[dict] = []
            for it in items:
                result.append(
                    {
                        "name": it["name"],
                        "value": int(it["address"]),
                        "section_number": 0,
                        "type": it["type"],
                        "storage_class": 0,
                    }
                )
            return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return []  # Return an empty list in case of errors.


def main(pe_path: str):  # pragma: no cover - debug helper
    items = pdb_symbols_for_pe(pe_path)
    for it in items[:50]:
        print(f"{it['name']} : {it.get('type', 'unknown')} @ 0x{it['value']:016X}")
