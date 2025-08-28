import argparse
from pathlib import Path
from typing import Any, Dict

from objutils.utils.arduino import build_artifacts


def positive_path(value: str) -> str:
    p = Path(value)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Path not found: {value}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="arduino-build-artifacts",
        description=(
            "Locate Arduino build artifacts (elf/hex/eep/map) for a given sketch.\n"
            "You can pass either the path to a .ino file or the sketch directory."
        ),
    )
    parser.add_argument(
        "sketch",
        type=positive_path,
        help="Path to the sketch directory or .ino file",
    )
    parser.add_argument(
        "--only",
        choices=["DIRECTORY", "ELF", "HEX", "EEP", "MAP"],
        nargs="+",
        help="Limit output to specific artifact types (may be given multiple times)",
    )
    parser.add_argument(
        "--as-paths",
        action="store_true",
        help="Print only paths (one per line) without labels",
    )
    parser.add_argument(
        "--missing-ok",
        action="store_true",
        help="Do not treat missing artifacts as an error; just omit them from output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    args = parser.parse_args()

    try:
        artifacts: Dict[str, Any] = build_artifacts(args.sketch)
    except ValueError as exc:
        if not args.quiet:
            print(str(exc))
        return 1

    selected = artifacts
    if args.only:
        selected = {k: v for k, v in artifacts.items() if k in set(args.only)}
        if not args.missing_ok:
            missing = [name for name in args.only if name not in artifacts]
            if missing:
                if not args.quiet:
                    print("Missing artifacts: " + ", ".join(missing))
                return 2

    if not args.quiet:
        if args.as_paths:
            for value in selected.values():
                print(value)
        else:
            for name, value in selected.items():
                print(f"{name:9s}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
