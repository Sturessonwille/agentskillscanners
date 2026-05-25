---
name: log-analyzer
description: Analyze application and system logs to identify errors, performance issues, and anomalies. Use when the user needs to parse logs, find error patterns, or set up log monitoring.
---

# Log Analyzer

## When to use

Use this skill when you need to parse logs, find error patterns, categorize lines (errors, auth, performance), filter JSON structured logs by level, or advise on log monitoring patterns.

## Pattern-based analysis

Run the analyzer on a plain-text log file. It scans each line for error, auth, and performance-related patterns and prints counts plus sample lines:

```bash
python3 scripts/analyze_log.py path/to/app.log
```

Run from the skill directory, or use the path to `scripts/analyze_log.py` relative to this skill folder.

## JSON / structured logs

For newline-delimited JSON logs, filter entries by the `level` field:

```bash
python3 scripts/analyze_log.py path/to/app.log --level error
```

Adjust `--level` to match your schema (for example `warning`, `info`).

## Quick shell checks

For ad-hoc inspection without the script, you can still use standard tools on the host—for example, `grep` for recent errors or `sort | uniq -c` for frequency counts. Prefer `scripts/analyze_log.py` when you want categorized summaries or JSON filtering in one step.

## Monitoring setup

For ongoing monitoring, configure your application to use structured logging and pipe to a log aggregator. Common patterns:

- **stdout/stderr** with JSON format for container environments
- **File-based** rotation with `logrotate` for traditional servers
- **Syslog** forwarding for centralized collection
