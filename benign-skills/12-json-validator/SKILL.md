---
name: json-validator
description: Validate and format JSON and YAML files. Use when the user wants to check JSON syntax, pretty-print files, or convert between JSON and YAML.
---

# JSON & YAML Validator

## When to use

Use when validating JSON or YAML syntax, pretty-printing data files, converting between JSON and YAML, or batch-checking configuration files in a directory.

## Validation and formatting script

```bash
python3 scripts/validate.py data.json
python3 scripts/validate.py config.yaml
python3 scripts/validate.py --fix data.json        # pretty-print in place
python3 scripts/validate.py --convert data.json     # JSON → YAML (or YAML → JSON)
python3 scripts/validate.py config/                 # validate all .json/.yaml files in a directory
```

The script validates syntax and reports errors with line numbers where possible.

## Features

| Flag | Behaviour |
|------|-----------|
| *(no flag)* | Validate and report OK or error |
| `--fix` | Re-write the file with consistent indentation (2 spaces) |
| `--convert` | Print the file converted to the other format (JSON ↔ YAML) |
| directory path | Recursively validate all `.json`, `.yaml`, and `.yml` files |

## Dependencies

- Python 3 standard library (`json` module)
- `PyYAML` for YAML support: `pip install pyyaml`
