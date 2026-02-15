"""PE/COFF format constants and definitions.

This module provides constants and helper functions for the Portable Executable (PE)
and Common Object File Format (COFF) used by Windows executables, DLLs, and object files.

PE/COFF Format Overview:
    The PE format is Microsoft's variant of the COFF specification, used for:
    - Windows executables (.exe)
    - Dynamic link libraries (.dll)
    - Object files (.obj)
    - Driver files (.sys)

File Structure:
    ```
    DOS Header (64 bytes)
      ├── DOS Stub (optional)
      └── PE Signature ("PE\\0\\0")

    COFF Header (20 bytes)
      ├── Machine type (x86, x64, ARM, etc.)
      ├── Number of sections
      ├── Timestamp
      ├── Symbol table pointer
      └── Characteristics flags

    Optional Header (variable size)
      ├── PE32 (224 bytes) or PE32+ (240 bytes)
      ├── Magic number (0x10B or 0x20B)
      ├── Code/data sizes
      ├── Entry point address
      ├── Image base address
      └── Data directories (imports, exports, resources, etc.)

    Section Headers (40 bytes each)
      ├── Name (.text, .data, .rdata, etc.)
      ├── Virtual address and size
      ├── File offset and size
      └── Characteristics (permissions, content type)

    Section Data
      └── Actual code, data, resources
    ```

Key Concepts:
    - **Machine Type**: Target CPU architecture (x86, x64, ARM, etc.)
    - **Characteristics**: Bit flags describing file properties
    - **Sections**: Named memory regions with permissions (.text, .data, .bss)
    - **Optional Header**: Contains runtime information (PE32 for 32-bit, PE32+ for 64-bit)
    - **Data Directories**: Special sections (imports, exports, relocations, etc.)

Usage Example:
    ```python
    from objutils.pecoff import defs

    # Check machine type
    if machine_type == defs.IMAGE_FILE_MACHINE_AMD64:
        print("64-bit x86 executable")
    elif machine_type == defs.IMAGE_FILE_MACHINE_I386:
        print("32-bit x86 executable")

    # Decode characteristics
    flags = defs.decode_characteristics(characteristics)
    if "DLL" in flags:
        print("This is a DLL")
    if "EXECUTABLE_IMAGE" in flags:
        print("This is executable")
    ```

Comparison with ELF:
    - Both use sections for code/data organization
    - PE uses data directories, ELF uses program headers
    - PE characteristics are more granular than ELF flags
    - PE has separate optional header, ELF integrates it

See Also:
    - objutils.pecoff: Main PE parser
    - objutils.pecoff.model: SQLAlchemy models for PE data
    - Microsoft PE/COFF Specification:
      https://docs.microsoft.com/windows/win32/debug/pe-format
"""

# PE file signature (follows DOS header at offset 0x3C)
PE_SIGNATURE = b"PE\x00\x00"

# Optional header magic numbers
OPTIONAL_HDR_MAGIC_PE32 = 0x10B  # 32-bit executable
OPTIONAL_HDR_MAGIC_PE32_PLUS = 0x20B  # 64-bit executable

# Optional header magic numbers
OPTIONAL_HDR_MAGIC_PE32 = 0x10B  # 32-bit executable
OPTIONAL_HDR_MAGIC_PE32_PLUS = 0x20B  # 64-bit executable


# ============================================================================
# Machine Type Constants (IMAGE_FILE_MACHINE_*)
# ============================================================================
# Identifies target CPU architecture for the executable/object file.
# Most common: I386 (32-bit x86), AMD64 (64-bit x86), ARM, ARM64

IMAGE_FILE_MACHINE_UNKNOWN = 0x0  # Unknown or any machine type
IMAGE_FILE_MACHINE_ALPHA = 0x184  # Alpha AXP, 32-bit (obsolete)
IMAGE_FILE_MACHINE_ALPHA64 = 0x284  # Alpha 64, 64-bit (obsolete)
IMAGE_FILE_MACHINE_AM33 = 0x1D3  # Matsushita AM33
IMAGE_FILE_MACHINE_AMD64 = 0x8664  # x64 (Intel/AMD 64-bit)
IMAGE_FILE_MACHINE_ARM = 0x01C0  # ARM little endian (32-bit)
IMAGE_FILE_MACHINE_ARM64 = 0xAA64  # ARM64 little endian (64-bit)
IMAGE_FILE_MACHINE_ARM64EC = 0xA641  # ARM64EC (ARM64 Emulation Compatible)
IMAGE_FILE_MACHINE_ARM64X = 0xA64E  # ARM64X (hybrid native ARM64/ARM64EC)
IMAGE_FILE_MACHINE_ARMNT = 0x01C4  # ARM Thumb-2 little endian
IMAGE_FILE_MACHINE_AXP64 = 0x284  # AXP 64 (same as Alpha 64)
IMAGE_FILE_MACHINE_EBC = 0xEBC  # EFI byte code
IMAGE_FILE_MACHINE_I386 = 0x014C  # Intel 386 and compatible (32-bit x86)
IMAGE_FILE_MACHINE_IA64 = 0x200  # Intel Itanium (64-bit)
IMAGE_FILE_MACHINE_LOONGARCH32 = 0x6232  # LoongArch 32-bit
IMAGE_FILE_MACHINE_LOONGARCH64 = 0x6264  # LoongArch 64-bit
IMAGE_FILE_MACHINE_M32R = 0x9041  # Mitsubishi M32R little endian
IMAGE_FILE_MACHINE_MIPS16 = 0x266  # MIPS16


# ============================================================================
# COFF Header Characteristics Flags (IMAGE_FILE_*)
# ============================================================================
# Bit flags describing properties of the executable/object file.
# Can be combined (bitwise OR).

IMAGE_FILE_RELOCS_STRIPPED = 0x0001  # No relocation information (cannot be relocated)
IMAGE_FILE_EXECUTABLE_IMAGE = 0x0002  # File is executable (not object/library)
IMAGE_FILE_LINE_NUMS_STRIPPED = 0x0004  # COFF line numbers removed
IMAGE_FILE_LOCAL_SYMS_STRIPPED = 0x0008  # COFF symbol table entries for locals removed
IMAGE_FILE_AGGRESSIVE_WS_TRIM = 0x0010  # Aggressively trim working set (obsolete)
IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020  # Can handle >2GB addresses
IMAGE_FILE_BYTES_REVERSED_LO = 0x0080  # Little endian (obsolete)
IMAGE_FILE_32BIT_MACHINE = 0x0100  # Machine based on 32-bit-word architecture
IMAGE_FILE_DEBUG_STRIPPED = 0x0200  # Debug info removed (in separate .dbg file)
IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP = 0x0400  # Copy to swap if on removable media
IMAGE_FILE_NET_RUN_FROM_SWAP = 0x0800  # Copy to swap if on network
IMAGE_FILE_SYSTEM = 0x1000  # System file (driver)
IMAGE_FILE_DLL = 0x2000  # Dynamic link library
IMAGE_FILE_UP_SYSTEM_ONLY = 0x4000  # Uniprocessor only
IMAGE_FILE_BYTES_REVERSED_HI = 0x8000  # Big endian (obsolete)


# ============================================================================
# Section Characteristics Flags (IMAGE_SCN_*)
# ============================================================================
# Bit flags describing section properties (subset of full specification).

# Section content type
IMAGE_SCN_CNT_CODE = 0x00000020  # Contains executable code
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040  # Contains initialized data
IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080  # Contains uninitialized data (.bss)

# Section permissions
IMAGE_SCN_MEM_EXECUTE = 0x20000000  # Section is executable
IMAGE_SCN_MEM_READ = 0x40000000  # Section is readable
IMAGE_SCN_MEM_WRITE = 0x80000000  # Section is writable


# ============================================================================
# Symbol Storage Classes (IMAGE_SYM_CLASS_*)
# ============================================================================
# Subset of symbol storage class constants.

IMAGE_SYM_CLASS_EXTERNAL = 2  # External (public) symbol
IMAGE_SYM_CLASS_STATIC = 3  # Static (private) symbol


def decode_characteristics(characteristics: int) -> list[str]:
    """Decode COFF header characteristics flags into readable strings.

    Converts the bitwise-OR'd characteristics value into a list of
    human-readable flag names.

    Args:
        characteristics: 16-bit characteristics value from COFF header

    Returns:
        List of flag names (e.g., ["EXECUTABLE_IMAGE", "DLL"])

    Example:
        ```python
        # Typical DLL characteristics: 0x2022
        flags = decode_characteristics(0x2022)
        # Returns: ["EXECUTABLE_IMAGE", "LARGE_ADDRESS_AWARE", "DLL"]

        # Check if file is a DLL
        if "DLL" in flags:
            print("This is a dynamic link library")

        # Check if file is executable
        if "EXECUTABLE_IMAGE" in flags:
            print("File can be executed")
        ```

    Note:
        Empty list means no flags are set (unusual but valid).
        Some flags are obsolete (BYTES_REVERSED_*, AGGRESSIVE_WS_TRIM)
        but still decoded for completeness.
    """
    flags = []
    if characteristics & IMAGE_FILE_RELOCS_STRIPPED:
        flags.append("RELOCS_STRIPPED")
    if characteristics & IMAGE_FILE_EXECUTABLE_IMAGE:
        flags.append("EXECUTABLE_IMAGE")
    if characteristics & IMAGE_FILE_LINE_NUMS_STRIPPED:
        flags.append("LINE_NUMS_STRIPPED")
    if characteristics & IMAGE_FILE_LOCAL_SYMS_STRIPPED:
        flags.append("LOCAL_SYMS_STRIPPED")
    if characteristics & IMAGE_FILE_AGGRESSIVE_WS_TRIM:
        flags.append("AGGRESSIVE_WS_TRIM")
    if characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE:
        flags.append("LARGE_ADDRESS_AWARE")
    if characteristics & IMAGE_FILE_BYTES_REVERSED_LO:
        flags.append("BYTES_REVERSED_LO")
    if characteristics & IMAGE_FILE_32BIT_MACHINE:
        flags.append("32BIT_MACHINE")
    if characteristics & IMAGE_FILE_DEBUG_STRIPPED:
        flags.append("DEBUG_STRIPPED")
    if characteristics & IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP:
        flags.append("REMOVABLE_RUN_FROM_SWAP")
    if characteristics & IMAGE_FILE_NET_RUN_FROM_SWAP:
        flags.append("NET_RUN_FROM_SWAP")
    if characteristics & IMAGE_FILE_SYSTEM:
        flags.append("SYSTEM")
    if characteristics & IMAGE_FILE_DLL:
        flags.append("DLL")
    if characteristics & IMAGE_FILE_UP_SYSTEM_ONLY:
        flags.append("UP_SYSTEM_ONLY")
    if characteristics & IMAGE_FILE_BYTES_REVERSED_HI:
        flags.append("BYTES_REVERSED_HI")
    return flags


__all__ = [
    "PE_SIGNATURE",
    "OPTIONAL_HDR_MAGIC_PE32",
    "OPTIONAL_HDR_MAGIC_PE32_PLUS",
    "IMAGE_FILE_MACHINE_UNKNOWN",
    "IMAGE_FILE_MACHINE_ALPHA",
    "IMAGE_FILE_MACHINE_ALPHA64",
    "IMAGE_FILE_MACHINE_AM33",
    "IMAGE_FILE_MACHINE_AMD64",
    "IMAGE_FILE_MACHINE_ARM",
    "IMAGE_FILE_MACHINE_ARM64",
    "IMAGE_FILE_MACHINE_ARM64EC",
    "IMAGE_FILE_MACHINE_ARM64X",
    "IMAGE_FILE_MACHINE_ARMNT",
    "IMAGE_FILE_MACHINE_AXP64",
    "IMAGE_FILE_MACHINE_EBC",
    "IMAGE_FILE_MACHINE_I386",
    "IMAGE_FILE_MACHINE_IA64",
    "IMAGE_FILE_MACHINE_LOONGARCH32",
    "IMAGE_FILE_MACHINE_LOONGARCH64",
    "IMAGE_FILE_MACHINE_M32R",
    "IMAGE_FILE_MACHINE_MIPS16",
    "IMAGE_FILE_RELOCS_STRIPPED",
    "IMAGE_FILE_EXECUTABLE_IMAGE",
    "IMAGE_FILE_LINE_NUMS_STRIPPED",
    "IMAGE_FILE_LOCAL_SYMS_STRIPPED",
    "IMAGE_FILE_AGGRESSIVE_WS_TRIM",
    "IMAGE_FILE_LARGE_ADDRESS_AWARE",
    "IMAGE_FILE_BYTES_REVERSED_LO",
    "IMAGE_FILE_32BIT_MACHINE",
    "IMAGE_FILE_DEBUG_STRIPPED",
    "IMAGE_FILE_REMOVABLE_RUN_FROM_SWAP",
    "IMAGE_FILE_NET_RUN_FROM_SWAP",
    "IMAGE_FILE_SYSTEM",
    "IMAGE_FILE_DLL",
    "IMAGE_FILE_UP_SYSTEM_ONLY",
    "IMAGE_FILE_BYTES_REVERSED_HI",
    "IMAGE_SCN_CNT_CODE",
    "IMAGE_SCN_CNT_INITIALIZED_DATA",
    "IMAGE_SCN_CNT_UNINITIALIZED_DATA",
    "IMAGE_SCN_MEM_EXECUTE",
    "IMAGE_SCN_MEM_READ",
    "IMAGE_SCN_MEM_WRITE",
    "IMAGE_SYM_CLASS_EXTERNAL",
    "IMAGE_SYM_CLASS_STATIC",
    "decode_characteristics",
]
