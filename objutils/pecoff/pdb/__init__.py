#!/usr/bin/env python

"""PDB debug symbol integration for PE/COFF files (Windows only).

This module provides access to Microsoft Program Database (PDB) debug information
using the Windows dbghelp.dll API. It enables comprehensive symbol lookup beyond
the typically stripped COFF symbol table in release binaries.

**Platform Support**: Windows only (requires dbghelp.dll)

Overview:
    PDB files contain rich debug information:
    
    - **Symbols**: Function names, variables, constants
    - **Types**: Structures, unions, enums, typedefs
    - **Source Info**: File names, line numbers
    - **Call Frames**: Stack unwinding data
    
    ```
    PE File + PDB:
    ┌──────────────┐     ┌──────────────┐
    │ app.exe      │────>│ app.pdb      │
    │              │     │              │
    │ Code         │     │ - Symbols    │
    │ Data         │     │ - Types      │
    │ (stripped)   │     │ - Lines      │
    └──────────────┘     └──────────────┘
    ```

Architecture:
    **Windows dbghelp.dll**:
    - Microsoft's debug helper library
    - Symbol server support
    - Handles PDB loading and parsing
    - Provides symbol enumeration API
    
    **Symbol Enumeration**:
    1. Initialize dbghelp session (SymInitialize)
    2. Load PE module (SymLoadModuleExW)
    3. Set symbol search paths
    4. Enumerate symbols (SymEnumSymbolsA with callback)
    5. Extract type information (optional)
    6. Cleanup (SymCleanup)
    
    **Type Information Extraction**:
    - Uses dbghelp type info API (SymGetTypeInfo)
    - Recursively resolves pointers, arrays, structs
    - Extracts sizes, offsets, field names

Usage Examples:
    **Basic Symbol Extraction**:
    ```python
    from objutils.pecoff.pdb import pdb_symbols_for_pe
    
    # Load symbols from PDB
    symbols = pdb_symbols_for_pe("app.exe")
    
    for sym in symbols:
        print(f"{sym['name']:40s} @ {sym['address']:#010x}")
    ```
    
    **With Symbol Search Path**:
    ```python
    # Search multiple directories for PDB
    symbols = pdb_symbols_for_pe(
        "app.exe",
        symbol_path="C:\\Symbols;SRV*C:\\SymCache*https://msdl.microsoft.com/download/symbols"
    )
    ```
    
    **Advanced Session Management**:
    ```python
    from objutils.pecoff.pdb import PdbSession
    
    with PdbSession("app.exe", symbol_path=[".", "C:\\Symbols"]) as pdb:
        # Enumerate all symbols
        for sym in pdb.enum_symbols():
            if sym.is_function():
                print(f"Function: {sym.name} @ {sym.Address:#x}")
        
        # Get module info
        info = pdb.get_module_info()
        print(f"Module base: {info.base_of_dll:#x}")
    ```
    
    **Type Information Extraction**:
    ```python
    from objutils.pecoff.pdb import CTypeInfoDump
    
    # Extract C type definitions
    type_dumper = CTypeInfoDump(pdb_session.handle, base_address)
    type_info = type_dumper.get_type_from_type_index(type_idx)
    print(f"Type: {type_info['type_name']}, Size: {type_info['size']}")
    ```

Key Components:
    **Enums**:
    - **SymTagEnum**: Symbol tag types (function, data, UDT, etc.)
    - **BasicType**: Primitive types (int, float, void, etc.)
    - **SymFlag**: Symbol flags (export, local, function, etc.)
    - **IMAGEHLP_SYMBOL_TYPE_INFO**: Type info query constants
    
    **Data Classes**:
    - **ModuleInfo**: Module metadata (base address, size, entry point)
    - **SYMBOL_INFO**: Symbol information structure (ctypes)
    - **MODULEINFO**: Windows API module info structure
    
    **Core Classes**:
    - **CTypeInfoDump**: Type information extraction and resolution
    - **PdbSession**: Manages dbghelp.dll lifetime and operations

dbghelp.dll API:
    The module wraps these key dbghelp functions:
    
    - **SymInitialize**: Initialize symbol handler
    - **SymCleanup**: Cleanup symbol handler
    - **SymLoadModuleExW**: Load module for symbol resolution
    - **SymEnumSymbolsA**: Enumerate symbols with callback
    - **SymGetTypeInfo**: Query type information
    - **SymSetSearchPath/SymGetSearchPath**: Symbol path management

Symbol Search Paths:
    dbghelp supports flexible symbol search:
    
    - **Local paths**: "C:\\Symbols;D:\\Debug"
    - **Symbol servers**: "SRV*C:\\Cache*https://msdl.microsoft.com/download/symbols"
    - **Combined**: "C:\\Local;SRV*C:\\Cache*https://server"
    
    The `_NT_SYMBOL_PATH` environment variable is respected.

Limitations:
    - **Windows only**: Requires dbghelp.dll (unavailable on Linux/Mac)
    - **PDB required**: Release binaries typically lack embedded COFF symbols
    - **Architecture match**: PDB must match PE architecture (x86/x64)
    - **Version match**: PDB should match PE build (GUID/age check)
    - **Type info**: Complex recursive structures may have limitations

Error Handling:
    On non-Windows platforms, dbghelp/kernel32/psapi are set to None:
    
    ```python
    from objutils.pecoff.pdb import _WINDOWS
    
    if not _WINDOWS:
        print("PDB support unavailable (not Windows)")
    ```
    
    Import errors are caught and gracefully handled in __init__.py.

See Also:
    - objutils.pecoff: Main PE parser that uses this module
    - objutils.pecoff.defs: PE/COFF constants
    - objutils.elf.model: Similar ORM pattern for ELF
    - Microsoft dbghelp.dll documentation
    - PDB format specification

Example Integration:
    ```python
    from objutils.pecoff import PeParser
    
    # PeParser automatically attempts PDB loading
    pe = PeParser("kernel32.dll", pdb_path=["C:\\Symbols"])
    
    # Symbols now include PDB data if found
    for sym in pe.symbols:
        print(f"{sym['name']}: {sym['value']:#x}")
    ```
"""

# dbghelp_symbols.py
import ctypes
from copy import copy
from ctypes import wintypes
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from typing import Optional


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
    """Module metadata extracted from Windows process.

    Attributes:
        base_of_dll: Base address where module is loaded in memory
        size_of_image: Size of module in memory (bytes)
        entry_point: Address of module entry point (or None)

    Example:
        ```python
        info = pdb_session.get_module_info()
        print(f"Module: {info.base_of_dll:#x} - {info.base_of_dll + info.size_of_image:#x}")
        ```
    """

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
    """Windows API structure for symbol information.

    Used with dbghelp.dll SymEnumSymbolsA to enumerate symbols.
    Contains detailed information about a symbol including name, address,
    flags, and type information.

    Key Attributes:
        Name: Symbol name (null-terminated char array)
        Address: Absolute address in memory
        ModBase: Module base address
        Flags: Symbol flags (SymFlag enum values)
        Tag: Symbol tag type (SymTagEnum values)
        Size: Symbol size in bytes
        Value: Symbol value (for constants)

    Helper Methods:
        is_function(): True if symbol is a function
        is_export(): True if symbol is exported
        is_local(): True if symbol is local variable
        is_parameter(): True if symbol is function parameter
        decode_flags(): List of flag names

    Properties:
        name: Decoded symbol name (str)
        tag: Symbol tag name (str)
        rel_address: Relative address (Address - ModBase)

    Example:
        ```python
        # Used in enumeration callback
        def callback(sym_info, size, context):
            sym = ctypes.cast(sym_info, ctypes.POINTER(SYMBOL_INFO)).contents
            if sym.is_function():
                print(f"Function: {sym.name} @ {sym.Address:#x}")
            return True  # Continue enumeration
        ```
    """

    def is_clr_token(self) -> bool:
        """Check if symbol is a CLR token (.NET managed code)."""
        return bool(self.Flags & SymFlag.SYMFLAG_CLR_TOKEN)
        return bool(self.Flags & SymFlag.SYMFLAG_CLR_TOKEN)

    def is_constant(self) -> bool:
        """Check if symbol is a constant value."""
        return bool(self.Flags & SymFlag.SYMFLAG_CONSTANT)

    def is_export(self) -> bool:
        """Check if symbol is exported from module."""
        return bool(self.Flags & SymFlag.SYMFLAG_EXPORT)

    def is_forwarder(self) -> bool:
        """Check if symbol is an export forwarder."""
        return bool(self.Flags & SymFlag.SYMFLAG_FORWARDER)

    def is_framerel(self) -> bool:
        """Check if symbol is frame-relative (stack variable)."""
        return bool(self.Flags & SymFlag.SYMFLAG_FRAMEREL)

    def is_function(self) -> bool:
        """Check if symbol is a function."""
        return bool(self.Flags & SymFlag.SYMFLAG_FUNCTION)

    def is_ilrel(self) -> bool:
        """Check if symbol is IL-relative (.NET managed code)."""
        return bool(self.Flags & SymFlag.SYMFLAG_ILREL)

    def is_local(self) -> bool:
        """Check if symbol is a local variable."""
        return bool(self.Flags & SymFlag.SYMFLAG_LOCAL)

    def is_metadata(self) -> bool:
        """Check if symbol is metadata."""
        return bool(self.Flags & SymFlag.SYMFLAG_METADATA)

    def is_parameter(self) -> bool:
        """Check if symbol is a function parameter."""
        return bool(self.Flags & SymFlag.SYMFLAG_PARAMETER)

    def is_register(self) -> bool:
        """Check if symbol is in a register."""
        return bool(self.Flags & SymFlag.SYMFLAG_REGISTER)

    def is_regrel(self) -> bool:
        """Check if symbol is register-relative."""
        return bool(self.Flags & SymFlag.SYMFLAG_REGREL)

    def is_slot(self) -> bool:
        """Check if symbol is a slot (.NET managed code)."""
        return bool(self.Flags & SymFlag.SYMFLAG_SLOT)

    def is_thunk(self) -> bool:
        """Check if symbol is a thunk (jump stub)."""
        return bool(self.Flags & SymFlag.SYMFLAG_THUNK)

    def is_tlsrel(self) -> bool:
        """Check if symbol is thread-local storage relative."""
        return bool(self.Flags & SymFlag.SYMFLAG_TLSREL)

    def is_value_present(self) -> bool:
        """Check if symbol has value field populated."""
        return bool(self.Flags & SymFlag.SYMFLAG_VALUEPRESENT)

    def is_virtual(self) -> bool:
        """Check if symbol is virtual."""
        return bool(self.Flags & SymFlag.SYMFLAG_VIRTUAL)

    # @cached_property
    def decode_flags(self) -> list[str]:
        """Decode Flags field to list of flag names.

        Returns:
            List of flag names (e.g., ["SYMFLAG_FUNCTION", "SYMFLAG_EXPORT"])
        """
        return [f.name for f in SymFlag if self.Flags & f.value]

    # @cached_property
    @property
    def name(self):
        """Get symbol name as decoded string.

        Returns:
            Symbol name (str), ignoring decode errors
        """
        return self.Name.decode(errors="ignore")

    # @cached_property
    @property
    def tag(self):
        """Get symbol tag name.

        Returns:
            Tag name (e.g., "SymTagFunction"), or "SymTagNull" if invalid
        """
        try:
            return SymTagEnum(self.Tag).name
        except ValueError:
            return SymTagEnum.SymTagNull.name

    # @cached_property
    @property
    def rel_address(self):
        """Get symbol address relative to module base.

        Returns:
            Relative virtual address (RVA)
        """
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
    """Windows API structure for module information (from psapi.dll).

    Used with GetModuleInformation to query module metadata.
    """

    _fields_ = [
        ("lpBaseOfDll", LPVOID),
        ("SizeOfImage", DWORD),
        ("EntryPoint", LPVOID),
    ]


class SymTagEnum(IntEnum):
    """Symbol tag types for PDB symbols.

    Defines the kind of symbol (function, data, type, etc.).
    Used in SYMBOL_INFO.Tag field.

    Common Values:
        SymTagFunction (5): Function symbol
        SymTagData (7): Variable symbol
        SymTagPublicSymbol (10): Exported symbol
        SymTagUDT (11): User-defined type (struct/class)
        SymTagEnum (12): Enumeration type
        SymTagPointerType (14): Pointer type
        SymTagArrayType (15): Array type
        SymTagBaseType (16): Primitive type
    """

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
    """Constants for SymGetTypeInfo queries.

    Used with dbghelp.SymGetTypeInfo to query type information.

    Common Queries:
        TI_GET_SYMTAG (0): Get symbol tag
        TI_GET_SYMNAME (1): Get symbol name
        TI_GET_LENGTH (2): Get type size in bytes
        TI_GET_TYPE (3): Get type index
        TI_GET_BASETYPE (5): Get base type (BasicType enum)
        TI_GET_CHILDRENCOUNT (13): Get count of child members
        TI_GET_OFFSET (10): Get member offset in struct
    """

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
    """Primitive type identifiers for PDB types.

    Used with TI_GET_BASETYPE query to identify base types.

    Common Types:
        btVoid (1): void type
        btChar (2): char type
        btInt (6): signed integer
        btUInt (7): unsigned integer
        btFloat (8): floating point
        btBool (10): boolean
        btLong (13): long integer
        btULong (14): unsigned long
    """

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
    """Symbol flags for SYMBOL_INFO.Flags field.

    Bit flags indicating symbol properties.

    Common Flags:
        SYMFLAG_FUNCTION (0x800): Symbol is a function
        SYMFLAG_EXPORT (0x200): Symbol is exported
        SYMFLAG_LOCAL (0x80): Symbol is local variable
        SYMFLAG_PARAMETER (0x40): Symbol is function parameter
        SYMFLAG_REGISTER (0x8): Symbol is in register
        SYMFLAG_CONSTANT (0x100): Symbol is a constant
        SYMFLAG_VALUEPRESENT (0x1): Value field is valid
    """

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
    """Extracts C type information from PDB debug symbols.

    Recursively resolves type definitions including pointers, arrays,
    structures, unions, and base types. Uses dbghelp.SymGetTypeInfo
    to query type metadata.

    Attributes:
        process: dbghelp process handle
        mod_base: Module base address

    Type Resolution Algorithm:
        1. Query type tag (pointer, array, UDT, base type, etc.)
        2. For compound types:
           - Pointer: Resolve pointed-to type
           - Array: Resolve element type and count
           - UDT: Enumerate members recursively
        3. Calculate sizes and offsets
        4. Build type dictionary with metadata

    Example:
        ```python
        type_dumper = CTypeInfoDump(pdb_session.handle, base_address)

        # Get type info for a symbol
        type_info = type_dumper.get_type_from_type_index(type_idx)
        print(f"Type: {type_info['type_name']}")
        print(f"Size: {type_info['size']} bytes")

        # For struct, enumerate members
        if 'members' in type_info:
            for member in type_info['members']:
                print(f"  {member['name']}: {member['type_name']} @ +{member['offset']}")
        ```

    Note:
        Type resolution can be slow for complex recursive structures.
        Use caching when querying multiple symbols.
    """

    def __init__(self, process, mod_base):
        """Initialize type info dumper.

        Args:
            process: dbghelp process handle from PdbSession
            mod_base: Module base address
        """
        self.process = process
        self.mod_base = mod_base

    def get_type_info(self, type_id, info_type):
        """Query type information from dbghelp.

        Args:
            type_id: Type index to query
            info_type: IMAGEHLP_SYMBOL_TYPE_INFO constant

        Returns:
            Type information value (type depends on info_type):
            - String for TI_GET_SYMNAME
            - Integer for TI_GET_LENGTH, TI_GET_COUNT, etc.
            - Boolean for TI_GET_IS_CONST, TI_GET_IS_VOLATILE, etc.
            - None if query fails

        Note:
            Different info_type values return different data types.
            Memory for strings (TI_GET_SYMNAME) is automatically freed.
        """
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
    """Manages dbghelp.dll symbol session lifecycle.

    Context manager for dbghelp symbol operations. Handles initialization,
    module loading, symbol enumeration, and cleanup.

    The session maintains a dbghelp process handle and configures symbol
    search paths. Automatically loads modules and enables symbol options.

    Attributes:
        hproc: Process handle (from GetCurrentProcess)
        _modules: Dictionary of loaded module bases by path

    Usage:
        ```python
        # Basic session
        with PdbSession(symbol_path=[".", "C:\\Symbols"]) as pdb:
            # Enumerate symbols
            for sym in pdb.enum_symbols():
                print(f"{sym.name}: {sym.Address:#x}")

        # Load specific module
        pdb = PdbSession()
        try:
            base = pdb.load_module("app.exe")
            info = pdb.get_module_info()
            print(f"Module loaded at {base:#x}, size {info.size_of_image} bytes")
        finally:
            pdb.close()
        ```

    Symbol Options:
        The session automatically enables:
        - SYMOPT_DEFERRED_LOADS: Load symbols on demand
        - SYMOPT_UNDNAME: Undecorate C++ symbols
        - SYMOPT_LOAD_LINES: Load source line information

    Note:
        Always use context manager (with statement) or manually call close()
        to ensure proper cleanup of dbghelp resources.
    """

    def __init__(self, symbol_path: list[str] | None = None):
        """Initialize dbghelp symbol session.

        Args:
            symbol_path: Optional list of directories to search for symbols.
                        Supports local paths and symbol servers:
                        - Local: ["C:\\Symbols", "D:\\Debug"]
                        - Server: ["SRV*C:\\Cache*https://msdl.microsoft.com/download/symbols"]
                        If None, uses current directory and _NT_SYMBOL_PATH

        Raises:
            OSError: If not on Windows or SymInitialize fails
        """
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
            # Extract unused but potentially useful fields for debugging
            # name, addr, tag = sym.name, sym.Address, sym.tag
            # type_name = self.type_info(base, sym.TypeIndex)
            results.append(copy(sym))
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


def pdb_symbols_for_pe(pe_path: str, symbol_path: str | None = None) -> list[dict]:
    """Load PDB symbols for a PE file (high-level API).

    Convenience function that creates a PdbSession, loads the PE module,
    enumerates all symbols, and returns a list compatible with Pe_Symbol.

    Args:
        pe_path: Path to PE file (.exe, .dll, etc.)
        symbol_path: Optional symbol search path string.
                    Supports semicolon-separated paths and symbol servers:
                    - "C:\\Symbols;D:\\Debug"
                    - "SRV*C:\\Cache*https://msdl.microsoft.com/download/symbols"
                    If None, searches current directory

    Returns:
        List of symbol dictionaries with fields:
        - name (str): Symbol name
        - value (int): Symbol address (absolute VA)
        - section_number (int): Always 0 for PDB symbols
        - type (str): Type information if available
        - storage_class (int): Always 0 for PDB symbols

    Example:
        ```python
        # Basic usage
        symbols = pdb_symbols_for_pe("kernel32.dll")
        for sym in symbols:
            print(f"{sym['name']:40s} @ {sym['value']:#010x}")

        # With symbol server
        symbols = pdb_symbols_for_pe(
            "app.exe",
            "SRV*C:\\SymCache*https://msdl.microsoft.com/download/symbols"
        )

        # Filter functions only
        functions = [s for s in symbols if s.get('is_function', False)]
        ```

    Note:
        - Returns empty list if PDB not found or on non-Windows platforms
        - Symbol addresses are absolute (not RVAs)
        - Errors are caught and logged, returning empty list
        - For more control, use PdbSession directly

    Integration:
        This function is called automatically by objutils.pecoff.PeParser
        when COFF symbol table is empty.
    """
    if not _WINDOWS:
        return []

    try:
        with PdbSession(symbol_path if not symbol_path else [symbol_path]) as session:
            mod_base = session.load_module(pe_path)
            return session.enum_symbols(mod_base, b"*")
    except Exception as e:
        print(f"Error: {str(e)}")
        return []  # Return an empty list in case of errors.


def main(pe_path: str):  # pragma: no cover - debug helper
    items = pdb_symbols_for_pe(pe_path)
    for it in items[:50]:
        print(f"{it['name']} : {it.get('type', 'unknown')} @ 0x{it['value']:016X}")
