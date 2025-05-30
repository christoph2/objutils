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


def main():
    import sys

    if len(sys.argv) != 2:
        print("usage: arduino-build-artifacts <sketch-name>")
        sys.exit(1)
    try:
        artifacts = build_artifacts(sys.argv[1])
    except FileNotFoundError:
        print(f"could not find sketch {sys.argv[1]!r}")
        sys.exit(1)
    print()
    for name, value in artifacts.items():
        print(f"{name:9s}: {value}")


if __name__ == "__main__":
    main()
