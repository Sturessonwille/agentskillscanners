---
name: unit-test-scaffolder
description: Generate unit test boilerplate for Python and JavaScript/TypeScript source files. Use when the user wants to create test stubs, set up a testing structure, or bootstrap test files for existing code.
---

# Unit Test Scaffolder

## When to use

Use when creating test files for existing source code, setting up a test directory structure, or generating pytest / Jest test stubs from function signatures.

## Scaffolding script

```bash
python3 scripts/scaffold_tests.py src/utils.py
python3 scripts/scaffold_tests.py src/utils.py --output tests/test_utils.py
python3 scripts/scaffold_tests.py src/                  # scaffold tests for all .py files
```

The script reads Python source files, extracts top-level function and class definitions, and generates test stubs with `pytest` conventions.

## What it generates

For each function `def foo(a, b):` the script creates:

```python
def test_foo():
    # TODO: test foo
    result = foo()
    assert result is not None
```

For classes, it generates a test class with one stub method per public method.

## Flags

| Flag | Behaviour |
|------|-----------|
| `--output` / `-o` | Write to a specific file (single source file only) |
| `--framework` | `pytest` (default) or `unittest` |
| directory path | Generate test files mirroring the source tree under `tests/` |

## Best practices

1. **Fill in the stubs** — the generated tests are placeholders; add real assertions.
2. **Follow naming conventions** — `test_<module>.py` for files, `test_<function>` for functions.
3. **Keep tests close to code** or in a parallel `tests/` directory.
4. **Run tests immediately** after scaffolding to confirm the file structure is correct.

## Dependencies

Python 3 standard library only (uses the `ast` module for parsing).
