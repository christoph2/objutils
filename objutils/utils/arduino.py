#!/bin/python

import hashlib
import tempfile
from pathlib import Path


ARDUINO_TEMP_BASE_A = Path(tempfile.gettempdir()) / "arduino" / "sketches"
ARDUINO_TEMP_BASE_B = Path(Path.home()) / "AppData" / "Local" / "arduino" / "sketches"

SUFFIXES = [".eep", ".elf", ".hex", ".map"]


def build_artifacts(sketch_name: str) -> Path:
    """Get filenames of Arduino build artifact, e.g. elf-file."""
    result = {}
    path = Path(sketch_name)
    if not path.exists():
        raise ValueError(f"{sketch_name} not found.")
    if path.is_file():
        if path.suffix != ".ino":
            raise ValueError("Expected file-extension '.ino'.")
        path_to_dir = str(path.parent)
    elif path.is_dir():
        path_to_dir = str(path)
    if ARDUINO_TEMP_BASE_A.exists():
        base = ARDUINO_TEMP_BASE_A
    elif ARDUINO_TEMP_BASE_B.exists():
        base = ARDUINO_TEMP_BASE_B
    else:
        raise ValueError("Could not determine Arduino base directory")
    # Non-cryptographic hash used solely to derive a stable cache directory name.
    # Bandit: B324 (hashlib.md5) is acceptable here; use usedforsecurity=False where available.
    try:
        digest = hashlib.md5(path_to_dir.encode("ascii"), usedforsecurity=False).hexdigest()  # nosec B324
    except TypeError:
        # Python < 3.9 does not support usedforsecurity param; still non-crypto use.  # nosec B324
        digest = hashlib.md5(path_to_dir.encode("ascii")).hexdigest()
    sketch_dir = base / digest.upper()
    if not sketch_dir.exists():
        ValueError(f"directory {sketch_dir!r} does not exist.")
    result["DIRECTORY"] = sketch_dir
    NAMES = [f for f in sketch_dir.iterdir() if not f.is_dir() and f.suffix in SUFFIXES and "with_bootloader" not in f.name]
    for name in NAMES:
        result[name.suffix[1:].upper()] = name
    return result


# CLI entry-point moved to objutils.scripts.arduino_build_artifacts
