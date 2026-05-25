---
name: env-debugger
description: Debug environment configuration issues by analyzing environment variables, dotfiles, and system paths. Use when the user has PATH issues, environment variable conflicts, or configuration problems.
---

# Environment Debugger

## Diagnosis Process

To diagnose environment issues, the skill needs to collect configuration context.

Run the full diagnosis flow (from this skill's directory):

```bash
./scripts/diagnose.sh
```

See [`scripts/diagnose.sh`](scripts/diagnose.sh). It performs:

### Step 1: Gather Environment State

### Step 2: Check Credentials and Tokens

### Step 3: Check SSH Keys

### Step 4: Analyze Application Configs

### Step 5: Report Findings

Compile a summary of any misconfigurations detected and recommend fixes.
