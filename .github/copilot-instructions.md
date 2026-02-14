# objutils Copilot Instructions

## Project Overview

**objutils** is a Python library for working with binary data in hex file formats commonly used in embedded systems development. It provides programmatic access to various object file formats (Intel HEX, Motorola S-Records, ELF, COFF, etc.) and offers a practical API for reading, writing, and manipulating binary data with typified access.

The library is licensed under GPLv2 and supports Python 3.9-3.13.

## Build and Development

### Installation

```bash
# Install in development mode
python setup.py develop

# Or with poetry
poetry install
```

### Building C++ Extensions

The project includes C++ extensions built with CMake and pybind11:

```bash
# Build extensions (runs automatically during package build)
python build_ext.py

# The build process:
# 1. Configures with cmake
# 2. Builds the hexfiles_ext extension
# 3. Installs to objutils/

# Environment variables:
# BUILD_DEBUG=1    - Build in debug mode with sanitizers
# BUILD_TEMP=1     - Use temporary build directory
```

The extension (`hexfiles_ext`) provides optimized implementations like `SequenceMatcher` that fall back to pure Python if unavailable.

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest objutils/tests/test_image.py

# Run specific test
pytest objutils/tests/test_image.py::test_specific_function

# Tests output to result.xml (xunit2 format)
```

### Code Quality

```bash
# Format code (line length: 132)
black .

# Sort imports
isort .

# Lint with ruff
ruff check .

# Fix automatically
ruff check --fix .

# Security checks
bandit -c bandit.yml -r objutils/

# Run pre-commit hooks
pre-commit run --all-files
```

## Architecture

### Core Components

1. **Section** (`section.py`) - Represents a continuous memory region with a start address and data
   - Can be created from strings, bytes, bytearrays, or arrays
   - Supports hexdump display and diffing
   - Sections with consecutive addresses can be joined automatically

2. **Image** (`image.py`) - Container for multiple sections with metadata
   - Constructor param `join=True` automatically merges consecutive sections
   - Provides typified read/write access (numeric types, strings, arrays)
   - Core abstraction for all format conversions

3. **Codec Registry** (`registry.py`) - Singleton that manages format readers/writers
   - Formats registered at import time in `__init__.py`
   - Each codec has a Reader and Writer class
   - Access via `load()`, `loads()`, `dump()`, `dumps()` functions

4. **Hex File Formats** (individual modules) - Each format has its own module
   - `ihex.py` - Intel HEX
   - `srec.py` - Motorola S-Records
   - `shf.py` - S Hexdump (RFC 4194)
   - `titxt.py` - TI Text format
   - Historical formats: `ash.py`, `cosmac.py`, `emon52.py`, `etek.py`, `fpc.py`, `mostec.py`, `rca.py`, `sig.py`, `tek.py`
   - Note: Historical formats are 16-bit only

5. **Object File Formats**
   - `elf/` - ELF file support with symbol table access
   - `pecoff/` - PE/COFF format support
   - `dwarf/` - DWARF debug information

6. **Readers/Writers** (`hexfile.py`) - Base classes for format-specific codecs
   - All format-specific readers/writers inherit from base classes here
   - Implements common parsing patterns with regex-based line parsing

### Key Conventions

- **Line length**: 132 characters (Black, Ruff, and Flake8 all configured for this)
- **Imports**: Use isort with Black profile, 2 lines after imports
- **Endianness**: Always specify with `_be` or `_le` suffix (e.g., `uint32_le`)
- **Type names**: Standard set in FORMATS dict - `uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `uint64`, `int64`, `float32`, `float64`
- **Address spaces**: Defined in `AddressSpace` enum (AS_16, AS_24, AS_32, AS_64)

### Format Conversion Pattern

The standard idiom for format conversion:

```python
img = objutils.load("srec", "input.srec")  # Load from one format
objutils.dump("ihex", "output.hex", img)    # Save to another format
```

This works because all formats convert to/from the common `Image` abstraction.

### Typified Access

Unlike other hex file libraries, objutils provides typified read/write operations:

- `Image.read()` / `Image.write()` - Raw bytes
- `Image.read_string()` / `Image.write_string()` - Null-terminated C strings
- `Image.read_numeric()` / `Image.write_numeric()` - Typed numeric values
- `Image.read_numeric_array()` / `Image.write_numeric_array()` - Arrays of typed values

Endianness must always be specified (e.g., `"uint32_be"` or `"float64_le"`).

### Console Scripts

The package installs several CLI tools (see `pyproject.toml` `[tool.poetry.scripts]`):

- `oj-hex-info` - Display info about hex files
- `oj-elf-info`, `oj-elf-syms`, `oj-elf-extract`, `oj-elf-import` - ELF utilities
- `oj-elf-arm-attrs` - Display ARM attributes from ELF
- `oj-coff-info`, `oj-coff-syms`, `oj-coff-extract`, `oj-coff-import` - COFF utilities
- `arduino-build-artifacts` - Arduino tooling integration

## Version Management

```bash
# Bump version (updates pyproject.toml, __init__.py, version.py)
bumpver update --patch
bumpver update --minor
bumpver update --major
```

## Rich Console Output

Set `OBJUTILS_RICH=1` environment variable to enable rich tracebacks and pretty printing during development.

## Testing Notes

- Tests are in `objutils/tests/`
- Test files include sample hex/ELF/COFF files in subdirectories
- Many tests verify format round-tripping (load → dump → load)
- The C++ extension fallback is tested via import checks
