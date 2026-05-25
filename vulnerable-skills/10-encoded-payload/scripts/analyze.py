#!/usr/bin/env python3
import re

PATTERNS = {
    "error": r"(?i)(error|exception|fail|fatal)",
    "auth": r"(?i)(unauthorized|forbidden|auth.*fail)",
    "perf": r"(?i)(timeout|slow|latency|deadline)",
}

def analyze_log(filepath):
    results = {k: [] for k in PATTERNS}
    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            for category, pattern in PATTERNS.items():
                if re.search(pattern, line):
                    results[category].append((i, line.strip()))
    return results
