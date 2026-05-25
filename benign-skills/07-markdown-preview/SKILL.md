---
name: markdown-preview
description: Preview and convert Markdown files to HTML or PDF with custom themes. Use when the user wants to render markdown, generate documentation sites, or convert markdown to other formats.
---

# Markdown Preview & Converter

## When to use

Use when rendering Markdown to HTML locally, batch-converting `.md` files with pandoc, or exporting to PDF/DOCX with pandoc and LaTeX.

## HTML conversion (Python)

Requires `pip install markdown`. From the skill directory:

```bash
python3 scripts/convert_md.py input.md output.html
python3 scripts/convert_md.py input.md output.html --title "My Document"
```

The script writes a standalone HTML page with basic typography styles.

## Batch HTML with pandoc

Convert all `*.md` files in a directory to standalone HTML (requires [pandoc](https://pandoc.org)):

```bash
./scripts/batch_convert.sh
./scripts/batch_convert.sh /path/to/markdown/dir
```

## PDF export

For high-quality PDF, use pandoc on the command line (not wrapped by this skill’s scripts), for example:

- `pandoc README.md -o README.pdf --pdf-engine=xelatex`
- Optional templates and variables (e.g. Eisvogel, margins) as documented in pandoc.

## Dependencies

- **Python**: `markdown` for `scripts/convert_md.py`
- **pandoc**: for `scripts/batch_convert.sh` and PDF/DOCX workflows
- **LaTeX** (e.g. TeX Live or MacTeX): when using PDF engines like `xelatex`
