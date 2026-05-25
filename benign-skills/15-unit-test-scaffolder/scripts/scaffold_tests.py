#!/usr/bin/env python3
"""Generate unit test boilerplate from Python source files using AST inspection."""

import argparse
import ast
import sys
from pathlib import Path


def extract_signatures(source: str) -> list[dict]:
    """Extract top-level functions and class methods from Python source."""
    tree = ast.parse(source)
    items = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                items.append({"type": "function", "name": node.name})
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    if not child.name.startswith("_") or child.name == "__init__":
                        methods.append(child.name)
            items.append({"type": "class", "name": node.name, "methods": methods})
    return items


def render_pytest(module_name: str, items: list[dict]) -> str:
    """Render pytest-style test stubs."""
    lines = [f'"""Tests for {module_name}."""', ""]

    has_functions = any(i["type"] == "function" for i in items)
    has_classes = any(i["type"] == "class" for i in items)

    imports = []
    func_names = [i["name"] for i in items if i["type"] == "function"]
    class_names = [i["name"] for i in items if i["type"] == "class"]
    if func_names:
        imports.append(", ".join(func_names))
    if class_names:
        imports.append(", ".join(class_names))
    if imports:
        lines.append(f"# from {module_name} import {', '.join(imports)}")
        lines.append("")

    for item in items:
        if item["type"] == "function":
            lines.append("")
            lines.append(f"def test_{item['name']}():")
            lines.append(f"    # TODO: test {item['name']}")
            lines.append(f"    assert True")
        elif item["type"] == "class":
            lines.append("")
            lines.append(f"class Test{item['name']}:")
            public_methods = [m for m in item.get("methods", []) if m != "__init__"]
            if not public_methods:
                lines.append(f"    def test_create(self):")
                lines.append(f"        # TODO: test {item['name']} instantiation")
                lines.append(f"        assert True")
            for method in public_methods:
                lines.append("")
                lines.append(f"    def test_{method}(self):")
                lines.append(f"        # TODO: test {item['name']}.{method}")
                lines.append(f"        assert True")

    lines.append("")
    return "\n".join(lines)


def render_unittest(module_name: str, items: list[dict]) -> str:
    """Render unittest-style test stubs."""
    lines = [f'"""Tests for {module_name}."""', "", "import unittest", ""]

    lines.append(f"class Test{module_name.replace('_', ' ').title().replace(' ', '')}(unittest.TestCase):")
    lines.append("")

    for item in items:
        if item["type"] == "function":
            lines.append(f"    def test_{item['name']}(self):")
            lines.append(f"        # TODO: test {item['name']}")
            lines.append(f"        self.assertTrue(True)")
            lines.append("")
        elif item["type"] == "class":
            for method in item.get("methods", []):
                if method == "__init__":
                    continue
                lines.append(f"    def test_{item['name']}_{method}(self):")
                lines.append(f"        # TODO: test {item['name']}.{method}")
                lines.append(f"        self.assertTrue(True)")
                lines.append("")

    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    unittest.main()")
    lines.append("")
    return "\n".join(lines)


def process_file(source_path: Path, output_path: Path | None, framework: str) -> int:
    """Generate test file for a single source file."""
    source = source_path.read_text(encoding="utf-8")
    try:
        items = extract_signatures(source)
    except SyntaxError as e:
        print(f"  SKIP  {source_path}: syntax error ({e})", file=sys.stderr)
        return 1

    if not items:
        print(f"  SKIP  {source_path}: no public functions or classes found")
        return 0

    module_name = source_path.stem
    if framework == "unittest":
        text = render_unittest(module_name, items)
    else:
        text = render_pytest(module_name, items)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"  WROTE {output_path} ({len(items)} items)")
    else:
        print(text)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold unit tests from Python source files.")
    parser.add_argument("paths", nargs="+", help="Python source files or directories")
    parser.add_argument("--output", "-o", help="Output file (single source only)")
    parser.add_argument("--framework", choices=["pytest", "unittest"], default="pytest")
    args = parser.parse_args()

    sources: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            sources.extend(sorted(path.rglob("*.py")))
        elif path.is_file() and path.suffix == ".py":
            sources.append(path)
        else:
            print(f"  SKIP  {p}: not a Python file", file=sys.stderr)

    sources = [s for s in sources if not s.name.startswith("test_") and s.name != "__init__.py"]

    if not sources:
        print("No source files found.", file=sys.stderr)
        return 1

    if args.output and len(sources) > 1:
        print("--output can only be used with a single source file.", file=sys.stderr)
        return 1

    errors = 0
    for src in sources:
        out = Path(args.output) if args.output else None
        if not out and len(sources) > 1:
            tests_dir = src.parent.parent / "tests"
            out = tests_dir / f"test_{src.name}"
        errors += process_file(src, out, args.framework)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
