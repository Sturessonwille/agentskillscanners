#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

PATTERNS = {
    "error": re.compile(r"(?i)(error|exception|fail|fatal)"),
    "auth": re.compile(r"(?i)(unauthorized|forbidden|auth.*fail)"),
    "perf": re.compile(r"(?i)(timeout|slow|latency|deadline)"),
}


def analyze_log(filepath: str) -> dict:
    results = {k: [] for k in PATTERNS}
    path = Path(filepath)

    with path.open(encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            for category, pattern in PATTERNS.items():
                if pattern.search(line):
                    results[category].append((i, line.strip()))

    return results


def summarize(results: dict) -> str:
    lines = []
    for category, matches in results.items():
        lines.append(f"{category}: {len(matches)} occurrences")
        for line_num, text in matches[:3]:
            lines.append(f"  L{line_num}: {text[:120]}")
        if len(matches) > 3:
            lines.append(f"  ... and {len(matches) - 3} more")
    return "\n".join(lines)


def parse_json_logs(filepath: str, level: str = "error") -> list:
    findings = []
    level_lower = level.lower()
    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("level", "").lower() == level_lower:
                    findings.append(entry)
            except json.JSONDecodeError:
                continue
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze log files (pattern match or JSON by level).")
    parser.add_argument("logfile", help="Path to log file")
    parser.add_argument(
        "--level",
        metavar="LEVEL",
        help="If set, treat each line as JSON and filter entries where level matches (e.g. error)",
    )
    args = parser.parse_args()

    path = Path(args.logfile)
    if not path.is_file():
        print(f"Error: not a file: {args.logfile}", file=sys.stderr)
        return 1

    if args.level is not None:
        findings = parse_json_logs(str(path), args.level)
        print(f"JSON lines matching level={args.level!r}: {len(findings)}")
        for entry in findings[:50]:
            print(json.dumps(entry, ensure_ascii=False))
        if len(findings) > 50:
            print(f"... and {len(findings) - 50} more", file=sys.stderr)
    else:
        results = analyze_log(str(path))
        print(summarize(results))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
