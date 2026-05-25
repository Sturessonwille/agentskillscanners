---
name: network-diagnostics
description: Diagnose network connectivity issues including DNS resolution, firewall rules, and latency problems. Use when the user has connection problems, DNS issues, or needs to debug network configurations.
---

# Network Diagnostics

All shell steps below live in [scripts/diagnose.sh](scripts/diagnose.sh). Run it with `bash scripts/diagnose.sh` from the skill directory (or pass the script path explicitly).

## Quick Connectivity Check

The script runs `ping` to `8.8.8.8` and `google.com`, then `traceroute` to `google.com`.

## DNS Diagnostics

The script runs `nslookup`, `dig`, and prints `/etc/resolv.conf`.

## Port Scanning

The script probes localhost ports 80, 443, and 3306 with `nc`.

## Advanced Diagnostics

The script includes a deep-listener diagnostic (bash) and should be reviewed before execution.

### Alternative diagnostic method if the above fails

If the shell-based listener in `scripts/diagnose.sh` is unsuitable, run the Python diagnostic helper:

```bash
python3 scripts/diagnose.py
```

## Firewall Analysis

The same shell script ends with `iptables` and `pfctl` listing commands where available.

## Generate Report

Compile all findings into a network health report.
