---
name: readme-generator
description: Generate README.md templates for projects with standard sections. Use when the user wants to create a README, document a project, or set up a documentation template.
---

# README Generator

## When to use

Use when bootstrapping a new project README, adding missing sections to an existing one, or generating documentation for an open-source release.

## Generator script

Run from the project root (or pass a project directory):

```bash
python3 scripts/gen_readme.py
python3 scripts/gen_readme.py --name "My Project" --license MIT /path/to/project
```

The script inspects the directory for a `package.json`, `pyproject.toml`, `Cargo.toml`, or `go.mod` to infer the project name, language, and available commands, then writes a `README.md` with standard sections.

## Generated sections

| Section | Content |
|---------|---------|
| Title & badges | Project name, optional license badge |
| Description | One-line placeholder from manifest or flag |
| Installation | Inferred from detected package manager |
| Usage | Placeholder with run command |
| Development | Build, test, and lint commands |
| Contributing | Standard contribution guidelines |
| License | From `--license` flag or manifest |

## Flags

- `--name` — override the project name (otherwise inferred from the manifest)
- `--license` — license identifier (e.g. `MIT`, `Apache-2.0`)
- `--output` — output file path (default: `README.md` in the target directory)
- `--force` — overwrite an existing README without prompting

## Tips

- Edit the generated file—it is a starting point, not a final product.
- Add a screenshot or demo GIF under the description for UI projects.
- Link to external documentation if available.
