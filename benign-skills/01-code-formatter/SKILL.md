---
name: code-formatter
description: Format and lint source code files. Use when the user asks to format, beautify, or lint code in Python, JavaScript, TypeScript, Go, or Rust.
---

# Code Formatter

## When to use

Apply when the user wants consistent formatting, a format check in CI, or help choosing tooling per language.

## Script

Run [`scripts/format.sh`](scripts/format.sh) from the repo or project root (or pass a path). It scans the target tree and runs only the formatters that match files present (Python → black, JS/TS → Prettier via `npx`, Go → gofmt, Rust → `cargo fmt` from the nearest `Cargo.toml`).

- Check without writing: `./scripts/format.sh --check [DIR]`
- Format in place: `./scripts/format.sh [DIR]`
- Default `DIR` is `.`

Requires the relevant tools installed (`black`, Node/npx for Prettier, `gofmt`, Rust toolchain with `rustfmt`).

## Supported languages (reference)

| Language | Formatter | Install |
|----------|-----------|---------|
| Python | black | `pip install black` |
| JavaScript/TypeScript | prettier | `npm install --save-dev prettier` (or rely on `npx`) |
| Go | gofmt | built-in |
| Rust | rustfmt | `rustup component add rustfmt` |

## Configuration

Keep formatting consistent with project-level config:

- **Python**: `pyproject.toml` with `[tool.black]`
- **JS/TS**: `.prettierrc` (example below)
- **Go**: no extra config; gofmt is canonical
- **Rust**: `rustfmt.toml`

Example `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```
