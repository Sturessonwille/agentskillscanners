#!/usr/bin/env python3
"""Validate, format, and convert JSON and YAML files."""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def detect_format(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".yaml", ".yml"):
        return "yaml"
    return None


def load_file(path: Path, fmt: str) -> tuple[object, str | None]:
    """Load a file and return (data, error_message)."""
    text = path.read_text(encoding="utf-8")
    try:
        if fmt == "json":
            return json.loads(text), None
        elif fmt == "yaml":
            if not HAS_YAML:
                return None, "PyYAML not installed (pip install pyyaml)"
            return yaml.safe_load(text), None
    except json.JSONDecodeError as e:
        return None, f"JSON error: {e}"
    except yaml.YAMLError as e:
        return None, f"YAML error: {e}"
    return None, f"Unsupported format: {fmt}"


def format_file(path: Path, fmt: str, data: object) -> None:
    """Write data back to file with consistent formatting."""
    with path.open("w", encoding="utf-8") as f:
        if fmt == "json":
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        elif fmt == "yaml" and HAS_YAML:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def convert(data: object, source_fmt: str) -> str:
    """Convert data from one format to the other."""
    if source_fmt == "json":
        if not HAS_YAML:
            return "PyYAML not installed (pip install pyyaml)"
        return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def validate_path(path: Path, fix: bool, do_convert: bool) -> int:
    """Validate a single file. Returns 0 on success, 1 on error."""
    fmt = detect_format(path)
    if fmt is None:
        print(f"  SKIP  {path} (unknown extension)")
        return 0

    data, err = load_file(path, fmt)
    if err:
        print(f"  FAIL  {path}: {err}")
        return 1

    print(f"  OK    {path}")

    if fix:
        format_file(path, fmt, data)
        print(f"        → formatted in place")

    if do_convert:
        print(convert(data, fmt))

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and format JSON/YAML files.")
    parser.add_argument("paths", nargs="+", help="Files or directories to validate")
    parser.add_argument("--fix", action="store_true", help="Pretty-print files in place")
    parser.add_argument("--convert", action="store_true", help="Print converted output (JSON↔YAML)")
    args = parser.parse_args()

    errors = 0
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and detect_format(child):
                    errors += validate_path(child, args.fix, args.convert)
        elif path.is_file():
            errors += validate_path(path, args.fix, args.convert)
        else:
            print(f"  MISS  {p}: not found", file=sys.stderr)
            errors += 1

    total_label = "error" if errors == 1 else "errors"
    if errors:
        print(f"\n{errors} {total_label} found.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
