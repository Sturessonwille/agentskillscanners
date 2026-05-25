#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


def convert_md_to_html(input_file: str, output_file: str, title: str = "Document") -> None:
    try:
        import markdown
    except ImportError:
        print("Install the markdown package: pip install markdown", file=sys.stderr)
        raise SystemExit(1) from None

    content = Path(input_file).read_text(encoding="utf-8")
    html_body = markdown.markdown(content, extensions=["tables", "fenced_code", "toc"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 48rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }}
    pre code {{ display: block; padding: 1em; overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5em; text-align: left; }}
  </style>
</head>
<body>{html_body}</body>
</html>"""

    Path(output_file).write_text(html, encoding="utf-8")
    print(f"Converted {input_file} -> {output_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown to a standalone HTML page.")
    parser.add_argument("input", help="Input .md file")
    parser.add_argument("output", help="Output .html file")
    parser.add_argument("--title", default="Document", help="HTML document title")
    args = parser.parse_args()

    inp = Path(args.input)
    if not inp.is_file():
        print(f"Error: not a file: {args.input}", file=sys.stderr)
        return 1

    convert_md_to_html(str(inp), args.output, title=args.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
