# AI-Assisted Skill Scanner

Uses the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) to analyze SKILL.md files for security vulnerabilities with LLM-powered reasoning — catching things that static regex scanning misses.

## Why AI scanning?

The static scanner (`../scanner/scan.py`) is fast and catches known patterns, but it has blind spots:

- **Novel prompt injections** that don't match existing regex patterns
- **Semantic attacks** — instructions that are malicious in context but look innocent in isolation
- **Social engineering** — subtle manipulation of AI behavior without obvious keywords
- **Obfuscated multi-stage attacks** where each step appears benign

The AI scanner understands *intent*, not just patterns.

## Setup

```bash
cd ai-scanner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then add your API key. Either copy the example and fill it in:

```bash
cp .env.example .env
# edit .env and set your real key
```

Or export it in your shell:

```bash
export OPENAI_API_KEY=sk-...
```

The `.env` file is gitignored so your key stays local.

## Usage

```bash
# Scan a directory (triage mode — fast pass, then deep analysis on flagged files)
python ai_scan.py ../vulnerable-skills/

# Scan a single file
python ai_scan.py ../vulnerable-skills/01-direct-prompt-injection/SKILL.md

# Deep mode — thorough analysis on every file (slower, more expensive)
python ai_scan.py ../vulnerable-skills/ --mode deep

# Compare AI results against the static regex scanner
python ai_scan.py ../vulnerable-skills/ --compare

# Use a different model (default is gpt-5.4 — see agent_defs/shared.py DEFAULT_MODEL)
python ai_scan.py ../vulnerable-skills/ --model gpt-4o

# JSON output
python ai_scan.py ../vulnerable-skills/ --output json
```

## Architecture

```
ai_scan.py       CLI entry point
agent_defs/      Agent definitions (triage, specialists, aggregator)
agents_def.py    Legacy monolithic agent definitions
tools.py         Function tools for file I/O and static scanner integration
```

### Multi-agent pipeline

1. **Orchestrator** — discovers SKILL.md files and coordinates the pipeline
2. **Triage Agent** (default: gpt-5.4) — fast first-pass classification: BENIGN / SUSPICIOUS / MALICIOUS
3. **Specialists + aggregator** (same default model) — thorough review of flagged skills

In `--mode deep`, the triage step is skipped and every file gets the full deep analysis.

### Function tools

| Tool | Description |
|------|-------------|
| `list_skill_files` | Recursively find all SKILL.md files in a directory |
| `read_skill_file` | Read a file with line numbers and parsed frontmatter |
| `run_static_scanner` | Run the regex scanner for comparison (used with `--compare`) |

## If a run looks stuck

There is no built-in API deadline unless you set one. **Deep mode** on many skills can take a long time (sequential skills × several model calls each). Invalid or overloaded models can also block until the HTTP layer gives up.

- **`--timeout`** (default **600** seconds per model call): aborts a single call and records a timeout result instead of hanging. Use `--timeout 0` for no limit (old behavior).
- **`--concurrency 1`**: easier on rate limits; slower but fewer parallel in-flight requests.
- Run with **`python -u`** or set **`PYTHONUNBUFFERED=1`** so log lines appear immediately when redirecting output.

## Traces

View agent execution traces in the [OpenAI Dashboard](https://platform.openai.com/traces).
