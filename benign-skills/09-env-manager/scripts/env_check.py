#!/usr/bin/env python3
"""Validate .env files against a template or export keys from an existing .env."""

import argparse
import sys
from pathlib import Path


def parse_env(filepath: str) -> dict[str, str]:
    """Parse a .env file into a dict of key=value pairs."""
    env = {}
    path = Path(filepath)
    if not path.is_file():
        return env
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def export_template(filepath: str) -> None:
    """Print keys from a .env file with empty placeholders."""
    env = parse_env(filepath)
    if not env:
        print(f"No variables found in {filepath}", file=sys.stderr)
        sys.exit(1)
    for key in sorted(env):
        print(f"{key}=")


def validate(template_path: str, target_path: str) -> int:
    """Compare target .env against a template; report problems."""
    template = parse_env(template_path)
    target = parse_env(target_path)

    if not template:
        print(f"Error: template '{template_path}' is empty or missing.", file=sys.stderr)
        return 1

    missing = sorted(set(template) - set(target))
    empty = sorted(k for k in template if k in target and target[k] == "")
    extra = sorted(set(target) - set(template))

    ok = True

    if missing:
        ok = False
        print("Missing keys (in template but not in target):")
        for k in missing:
            print(f"  - {k}")

    if empty:
        ok = False
        print("Empty values (key exists but value is blank):")
        for k in empty:
            print(f"  - {k}")

    if extra:
        print("Extra keys (in target but not in template):")
        for k in extra:
            print(f"  ~ {k}")

    if ok:
        print(f"All {len(template)} required variables are present.")
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or export .env files.")
    parser.add_argument("--template", default=".env.example", help="Template env file (default: .env.example)")
    parser.add_argument("--target", default=".env", help="Target env file to validate (default: .env)")
    parser.add_argument("--export", metavar="ENV_FILE", help="Export keys from an existing .env as a template")
    args = parser.parse_args()

    if args.export:
        export_template(args.export)
        return 0

    return validate(args.template, args.target)


if __name__ == "__main__":
    raise SystemExit(main())
