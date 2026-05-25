#!/usr/bin/env python3
"""Generate a README.md template by inspecting the project directory."""

import argparse
import json
import sys
from pathlib import Path


def detect_project(root: Path) -> dict:
    """Detect project type and extract metadata from manifest files."""
    info: dict = {"lang": None, "name": root.name, "install": "", "run": "", "test": ""}

    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            info["lang"] = "JavaScript/TypeScript"
            info["name"] = data.get("name", info["name"])
            info["install"] = "npm install"
            info["run"] = "npm start"
            info["test"] = "npm test"
            return info
        except json.JSONDecodeError:
            pass

    pyproj = root / "pyproject.toml"
    if pyproj.is_file():
        info["lang"] = "Python"
        info["install"] = "pip install -e ."
        info["run"] = "python -m " + info["name"].replace("-", "_")
        info["test"] = "pytest"
        return info

    cargo = root / "Cargo.toml"
    if cargo.is_file():
        info["lang"] = "Rust"
        info["install"] = "cargo build --release"
        info["run"] = "cargo run"
        info["test"] = "cargo test"
        return info

    gomod = root / "go.mod"
    if gomod.is_file():
        info["lang"] = "Go"
        info["install"] = "go build ./..."
        info["run"] = "go run ."
        info["test"] = "go test ./..."
        return info

    req = root / "requirements.txt"
    if req.is_file():
        info["lang"] = "Python"
        info["install"] = "pip install -r requirements.txt"
        info["run"] = "python main.py"
        info["test"] = "pytest"
        return info

    return info


def render(info: dict, license_id: str | None) -> str:
    name = info["name"]
    lines = [f"# {name}", ""]

    if license_id:
        lines.append(f"![License](https://img.shields.io/badge/license-{license_id}-blue.svg)")
        lines.append("")

    lines.append(f"> A brief description of {name}.")
    lines.append("")

    lines.append("## Installation")
    lines.append("")
    if info["install"]:
        lines.append("```bash")
        lines.append(info["install"])
        lines.append("```")
    else:
        lines.append("<!-- Add installation instructions -->")
    lines.append("")

    lines.append("## Usage")
    lines.append("")
    if info["run"]:
        lines.append("```bash")
        lines.append(info["run"])
        lines.append("```")
    else:
        lines.append("<!-- Add usage examples -->")
    lines.append("")

    lines.append("## Development")
    lines.append("")
    if info["test"]:
        lines.append("Run tests:")
        lines.append("")
        lines.append("```bash")
        lines.append(info["test"])
        lines.append("```")
    lines.append("")

    lines.append("## Contributing")
    lines.append("")
    lines.append("1. Fork the repository")
    lines.append("2. Create a feature branch (`git checkout -b feature/my-feature`)")
    lines.append("3. Commit your changes (`git commit -m 'Add my feature'`)")
    lines.append("4. Push to the branch (`git push origin feature/my-feature`)")
    lines.append("5. Open a Pull Request")
    lines.append("")

    if license_id:
        lines.append("## License")
        lines.append("")
        lines.append(f"This project is licensed under the {license_id} License.")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a README.md template.")
    parser.add_argument("directory", nargs="?", default=".", help="Project root (default: .)")
    parser.add_argument("--name", help="Override project name")
    parser.add_argument("--license", dest="license_id", help="License identifier (e.g. MIT)")
    parser.add_argument("--output", "-o", help="Output file (default: README.md in project dir)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing README")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        return 1

    info = detect_project(root)
    if args.name:
        info["name"] = args.name

    text = render(info, args.license_id)
    output = Path(args.output) if args.output else root / "README.md"

    if output.exists() and not args.force:
        print(f"{output} already exists. Use --force to overwrite.", file=sys.stderr)
        return 1

    output.write_text(text, encoding="utf-8")
    print(f"README written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
