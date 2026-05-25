"""
Function tools that agents can call during a scan, plus raw utility
functions for programmatic (non-agent) use.

The ``discover_skills`` / ``load_skill`` / ``format_skill_message`` helpers
return Python objects and are used by ai_scan.py to drive the pipeline
without needing an LLM orchestrator.  The ``@function_tool`` wrappers
expose the same logic as agent-callable tools.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from agents import function_tool

SCRIPT_EXTENSIONS = {".sh", ".py", ".js", ".ts", ".rb", ".pl"}


# ---------------------------------------------------------------------------
# Raw utility functions (return Python objects)
# ---------------------------------------------------------------------------


def discover_skills(directory: str) -> list[dict]:
    """Return a list of skill dicts found recursively under *directory*.

    Each dict has ``skill_dir`` (absolute path) and ``files`` (list of
    absolute paths to SKILL.md + scripts).
    """
    directory = os.path.abspath(os.path.expanduser(directory))
    if not os.path.isdir(directory):
        return []

    skills: list[dict] = []
    for root, _dirs, files in os.walk(directory):
        if "SKILL.md" in files:
            skill_files = [os.path.join(root, "SKILL.md")]
            scripts_dir = os.path.join(root, "scripts")
            if os.path.isdir(scripts_dir):
                for sr, _, sf in os.walk(scripts_dir):
                    for fn in sorted(sf):
                        if Path(fn).suffix.lower() in SCRIPT_EXTENSIONS:
                            skill_files.append(os.path.join(sr, fn))
            skills.append({"skill_dir": root, "files": skill_files})

    skills.sort(key=lambda s: s["skill_dir"])
    return skills


def load_skill(path: str) -> dict:
    """Load a skill's SKILL.md + scripts and return a structured dict.

    Accepts either a SKILL.md path or a skill directory path.
    Returns a dict with keys: skill_dir, skill_md_path, metadata,
    skill_md_content (line-numbered), scripts (dict of path → content).
    """
    path = os.path.expanduser(path)

    if os.path.isfile(path):
        skill_dir = os.path.dirname(os.path.abspath(path))
        skill_md_path = path
    elif os.path.isdir(path):
        skill_dir = os.path.abspath(path)
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
    else:
        return {"error": f"Path not found: {path}"}

    if not os.path.isfile(skill_md_path):
        return {"error": f"SKILL.md not found in: {skill_dir}"}

    try:
        skill_text = Path(skill_md_path).read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Could not read SKILL.md: {e}"}

    numbered = [
        f"{i:4d} | {line}"
        for i, line in enumerate(skill_text.splitlines(), start=1)
    ]

    metadata = _parse_frontmatter(skill_text)

    script_contents: dict[str, str] = {}
    scripts_dir = os.path.join(skill_dir, "scripts")
    if os.path.isdir(scripts_dir):
        for sr, _, sf in os.walk(scripts_dir):
            for fn in sorted(sf):
                if Path(fn).suffix.lower() in SCRIPT_EXTENSIONS:
                    fp = os.path.join(sr, fn)
                    try:
                        text = Path(fp).read_text(encoding="utf-8")
                        lines = [
                            f"{i:4d} | {line}"
                            for i, line in enumerate(text.splitlines(), start=1)
                        ]
                        script_contents[fp] = "\n".join(lines)
                    except Exception:
                        script_contents[fp] = "<read error>"

    return {
        "skill_dir": skill_dir,
        "skill_md_path": skill_md_path,
        "metadata": metadata,
        "skill_md_content": "\n".join(numbered),
        "scripts": script_contents,
    }


def format_skill_message(skill: dict) -> str:
    """Format a loaded skill dict into a readable message for an LLM agent."""
    parts = [f"## Skill Directory: {skill['skill_dir']}\n"]

    if skill.get("metadata"):
        parts.append("### Metadata (YAML frontmatter)")
        parts.append(f"```yaml\n{yaml.dump(skill['metadata'], default_flow_style=False)}```\n")

    parts.append("### SKILL.md")
    parts.append(f"```\n{skill['skill_md_content']}\n```\n")

    if skill.get("scripts"):
        parts.append("### Scripts")
        for script_path, content in skill["scripts"].items():
            rel = os.path.relpath(script_path, skill["skill_dir"])
            parts.append(f"#### {rel}")
            parts.append(f"```\n{content}\n```\n")

    return "\n".join(parts)


def static_scan(target_path: str) -> dict:
    """Run the regex-based static scanner and return parsed output."""
    scanner_script = Path(__file__).resolve().parent.parent / "scanner" / "scan.py"
    if not scanner_script.exists():
        return {"error": "Static scanner not found at expected path"}

    target_path = os.path.expanduser(target_path)
    try:
        result = subprocess.run(
            [sys.executable, str(scanner_script), target_path, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stdout:
            return json.loads(result.stdout)
        return {"error": result.stderr or "No output from scanner"}
    except subprocess.TimeoutExpired:
        return {"error": "Static scanner timed out"}
    except json.JSONDecodeError:
        return {"error": "Static scanner returned invalid JSON"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Agent-callable tool wrappers (return JSON strings)
# ---------------------------------------------------------------------------


@function_tool
def list_skill_files(directory: str) -> str:
    """List all skill directories found recursively under ``directory``.

    A skill directory is any folder containing a SKILL.md file.
    Returns a JSON array of objects, each with the skill directory path
    and the list of files it contains (SKILL.md + scripts/).
    """
    return json.dumps(discover_skills(directory), indent=2)


@function_tool
def read_skill_file(file_path: str) -> str:
    """Read a skill's SKILL.md and all its scripts/ files, returning them together.

    Accepts either a path to a SKILL.md or to a skill directory.
    """
    return json.dumps(load_skill(file_path), indent=2)


@function_tool
def run_static_scanner(target_path: str) -> str:
    """Run the existing regex-based static scanner on a file or directory.

    Returns the scanner's JSON output so the AI agent can compare its own
    findings against the static analysis results.
    """
    return json.dumps(static_scan(target_path), indent=2)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from a SKILL.md file."""
    stripped = text.strip()
    if not stripped.startswith("---"):
        return None
    end = stripped.find("---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(stripped[3:end])
    except yaml.YAMLError:
        return None


ALL_TOOLS = [list_skill_files, read_skill_file, run_static_scanner]
