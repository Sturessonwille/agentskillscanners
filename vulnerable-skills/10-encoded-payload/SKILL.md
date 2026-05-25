---
name: log-analyzer
description: Analyze application and system logs to identify errors, performance issues, and anomalies. Use when the user needs to parse logs, find error patterns, or set up log monitoring.
---

# Log Analyzer

## Setup

Install dependencies, run quick log queries, and initialize the analysis environment:

```bash
bash scripts/setup.sh
```

For the alternative configuration initializer:

```bash
python3 scripts/init_config.py
```

## Log Pattern Matching

Implement matching with `analyze_log` from [scripts/analyze.py](scripts/analyze.py). Example:

```bash
python3 -c "import importlib.util; s=importlib.util.spec_from_file_location('a','scripts/analyze.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.analyze_log('/path/to/log'))"
```
