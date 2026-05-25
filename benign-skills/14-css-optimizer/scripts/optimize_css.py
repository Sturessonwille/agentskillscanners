#!/usr/bin/env python3
"""Lightweight CSS minifier: strip comments, collapse whitespace, remove empty rules."""

import argparse
import re
import sys
from pathlib import Path

COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
SPACE_AROUND_RE = re.compile(r"\s*([{};:,])\s*")
EMPTY_RULE_RE = re.compile(r"[^{}]+\{\s*\}")


def minify(css: str) -> str:
    out = COMMENT_RE.sub("", css)
    out = WHITESPACE_RE.sub(" ", out)
    out = SPACE_AROUND_RE.sub(r"\1", out)
    out = out.strip()
    for _ in range(5):
        cleaned = EMPTY_RULE_RE.sub("", out)
        if cleaned == out:
            break
        out = cleaned
    return out


def size_report(name: str, original: int, minified: int) -> str:
    if original == 0:
        return f"{name}: empty file"
    pct = (1 - minified / original) * 100
    return f"{name}: {original:,} → {minified:,} bytes ({pct:.1f}% saved)"


def process_file(path: Path, output: Path | None, stats_only: bool) -> int:
    css = path.read_text(encoding="utf-8")
    result = minify(css)

    orig_size = len(css.encode("utf-8"))
    min_size = len(result.encode("utf-8"))
    print(size_report(path.name, orig_size, min_size))

    if stats_only:
        return 0

    if output:
        output.write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)
        sys.stdout.write("\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize/minify CSS files.")
    parser.add_argument("paths", nargs="+", help="CSS files or directories")
    parser.add_argument("--output", "-o", help="Output file (single file mode only)")
    parser.add_argument("--stats", action="store_true", help="Print size report only")
    args = parser.parse_args()

    targets: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            targets.extend(sorted(path.rglob("*.css")))
        elif path.is_file():
            targets.append(path)
        else:
            print(f"Not found: {p}", file=sys.stderr)
            return 1

    if not targets:
        print("No CSS files found.", file=sys.stderr)
        return 1

    if args.output and len(targets) > 1:
        print("--output can only be used with a single file.", file=sys.stderr)
        return 1

    for target in targets:
        out = Path(args.output) if args.output else None
        if not out and not args.stats and len(targets) > 1:
            out = target.with_suffix(".min.css")
        process_file(target, out, args.stats)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
