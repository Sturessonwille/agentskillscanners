#!/usr/bin/env python3
"""Generate a changelog from git log between two refs using conventional commit prefixes."""

import argparse
import re
import subprocess
import sys
from collections import defaultdict

CATEGORIES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Tests",
    "chore": "Chores",
    "ci": "CI",
    "style": "Style",
    "build": "Build",
}

CONV_RE = re.compile(r"^(\w+)(?:\(.+?\))?!?:\s*(.+)$")


def get_latest_tag() -> str | None:
    """Return the most recent reachable tag, or None."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits(from_ref: str | None, to_ref: str) -> list[tuple[str, str]]:
    """Return list of (short_hash, subject) tuples between two refs."""
    range_spec = f"{from_ref}..{to_ref}" if from_ref else to_ref
    result = subprocess.run(
        ["git", "log", range_spec, "--pretty=format:%h %s"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"git log failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    commits = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        hash_part, _, subject = line.partition(" ")
        commits.append((hash_part, subject))
    return commits


def categorize(commits: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    """Group commits by conventional-commit type."""
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for short_hash, subject in commits:
        m = CONV_RE.match(subject)
        if m:
            ctype = m.group(1).lower()
            label = CATEGORIES.get(ctype, "Other")
            groups[label].append((short_hash, m.group(2)))
        else:
            groups["Other"].append((short_hash, subject))
    return groups


def render(groups: dict[str, list[tuple[str, str]]], from_ref: str | None, to_ref: str) -> str:
    """Render the changelog as Markdown."""
    title = f"## {to_ref}"
    if from_ref:
        title += f" (since {from_ref})"
    lines = [title, ""]
    order = list(CATEGORIES.values()) + ["Other"]
    for section in order:
        entries = groups.get(section)
        if not entries:
            continue
        lines.append(f"### {section}")
        lines.append("")
        for short_hash, msg in entries:
            lines.append(f"- {msg} (`{short_hash}`)")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate changelog from git history.")
    parser.add_argument("--from", dest="from_ref", default=None, help="Start ref (default: latest tag)")
    parser.add_argument("--to", default="HEAD", help="End ref (default: HEAD)")
    parser.add_argument("--output", "-o", help="Write to file instead of stdout")
    args = parser.parse_args()

    from_ref = args.from_ref or get_latest_tag()
    commits = get_commits(from_ref, args.to)
    if not commits:
        print("No commits found in range.", file=sys.stderr)
        return 0

    groups = categorize(commits)
    text = render(groups, from_ref, args.to)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Changelog written to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
