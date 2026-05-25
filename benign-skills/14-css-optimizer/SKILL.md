---
name: css-optimizer
description: Optimize and minify CSS files by removing unused rules and reducing file size. Use when the user wants to minify CSS, remove dead styles, or analyze stylesheet size.
---

# CSS Optimizer

## When to use

Use when minifying CSS for production, removing duplicate rules, analyzing stylesheet size, or concatenating multiple CSS files.

## Optimizer script

```bash
python3 scripts/optimize_css.py styles.css
python3 scripts/optimize_css.py styles.css --output styles.min.css
python3 scripts/optimize_css.py src/css/                          # process all .css in directory
python3 scripts/optimize_css.py styles.css --stats                # size report only, no output
```

## What it does

1. **Strips comments** — removes `/* ... */` block comments.
2. **Collapses whitespace** — reduces consecutive whitespace to single spaces, trims around braces, colons, and semicolons.
3. **Removes empty rules** — deletes selectors with no declarations.
4. **Reports savings** — prints original vs. optimized size and percentage saved.

## Flags

| Flag | Behaviour |
|------|-----------|
| `--output` / `-o` | Write result to a file (default: stdout) |
| `--stats` | Print size statistics without writing output |
| directory path | Optimize all `.css` files; writes `.min.css` siblings |

## Limitations

This is a lightweight text-based optimizer. For production builds with tree-shaking, vendor prefixing, and CSS modules, use dedicated tooling such as PostCSS, cssnano, or Tailwind's purge.

## Dependencies

Python 3 standard library only — no external packages required.
