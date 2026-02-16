#!/usr/bin/env python
"""Arduino build artifact utilities.

This module provides functions to locate Arduino build artifacts (ELF, HEX, etc.)
in the Arduino IDE's temp/cache directories.
"""

import hashlib
import tempfile
from pathlib import Path


# Arduino cache directory locations (Windows)
ARDUINO_TEMP_BASE_A = Path(tempfile.gettempdir()) / "arduino" / "sketches"
ARDUINO_TEMP_BASE_B = Path(Path.home()) / "AppData" / "Local" / "arduino" / "sketches"

# Build artifact file extensions
SUFFIXES = [".eep", ".elf", ".hex", ".map"]


def build_artifacts(sketch_name: str) -> dict[str, Path]:
    """Get paths to Arduino build artifacts for a sketch.

    Arduino stores build artifacts in a cache directory named after the
    MD5 hash of the sketch's directory path.

    Args:
        sketch_name: Path to .ino sketch file or sketch directory

    Returns:
        Dictionary mapping artifact types to paths:
            - 'DIRECTORY': Sketch build directory
            - 'EEP': EEPROM file (.eep)
            - 'ELF': Executable file (.elf)
            - 'HEX': Intel HEX file (.hex)
            - 'MAP': Map file (.map)

    Raises:
        ValueError: If sketch_name doesn't exist, isn't a .ino file,
                    or Arduino cache directory cannot be found

    Example:
        >>> artifacts = build_artifacts("MySketch.ino")
        >>> print(artifacts['HEX'])
        Path('.../arduino/sketches/ABC123/MySketch.ino.hex')
    """
    result: dict[str, Path] = {}

    # Resolve sketch path
    path = Path(sketch_name)
    if not path.exists():
        raise ValueError(f"{sketch_name} not found.")

    if path.is_file():
        if path.suffix != ".ino":
            raise ValueError("Expected file-extension '.ino'.")
        path_to_dir = str(path.parent)
    elif path.is_dir():
        path_to_dir = str(path)
    else:
        raise ValueError(f"{sketch_name} is neither file nor directory.")

    # Locate Arduino cache base directory
    if ARDUINO_TEMP_BASE_A.exists():
        base = ARDUINO_TEMP_BASE_A
    elif ARDUINO_TEMP_BASE_B.exists():
        base = ARDUINO_TEMP_BASE_B
    else:
        raise ValueError("Could not determine Arduino base directory")

    # Compute sketch cache directory name (MD5 hash of path)
    # Non-cryptographic hash used solely for cache directory naming
    try:
        # Python 3.9+: explicitly mark as non-security use
        digest = hashlib.md5(path_to_dir.encode("ascii"), usedforsecurity=False).hexdigest()  # nosec B324
    except TypeError:
        # Python < 3.9: parameter not available, still non-crypto use
        digest = hashlib.md5(path_to_dir.encode("ascii")).hexdigest()  # nosec B324

    sketch_dir = base / digest.upper()
    if not sketch_dir.exists():
        raise ValueError(f"Sketch build directory {sketch_dir!r} does not exist.")

    result["DIRECTORY"] = sketch_dir

    # Find build artifacts (exclude bootloader variants)
    artifacts = [f for f in sketch_dir.iterdir() if not f.is_dir() and f.suffix in SUFFIXES and "with_bootloader" not in f.name]

    for artifact in artifacts:
        # Map extension to uppercase key (e.g., ".hex" -> "HEX")
        result[artifact.suffix[1:].upper()] = artifact

    return result


# CLI entry-point moved to objutils.scripts.arduino_build_artifacts
