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
    sketch_dir = base / hashlib.md5(path_to_dir.encode("ascii")).hexdigest().upper()
    if not sketch_dir.exists():
        ValueError(f"directory {sketch_dir!r} does not exist.")
    result["DIRECTORY"] = sketch_dir
    NAMES = [f for f in sketch_dir.iterdir() if not f.is_dir() and f.suffix in SUFFIXES and "with_bootloader" not in f.name]
    for name in NAMES:
        result[name.suffix[1:].upper()] = name
    return result


# CLI entry-point moved to objutils.scripts.arduino_build_artifacts
