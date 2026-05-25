# Vulnerable Skills Scanner

This repository contains the prototype and evaluation material for a master's thesis project on detecting security risks in AI agent skills. The project combines a static rule-based scanner with an AI-assisted scanner and evaluates both approaches against benign, vulnerable, and injected skill examples.

## Safety Notice

Some folders intentionally contain vulnerable or malicious examples for research and evaluation purposes. These examples include prompt injection, data exfiltration patterns, suspicious shell commands, and other unsafe behavior. Do not run scripts from the vulnerable or injected skill folders on a real system unless you fully understand what they do and are using an isolated test environment.

## Repository Structure

```text
scanner/
  Static Python scanner for SKILL.md files and bundled scripts.

ai-scanner/
  AI-assisted scanner using the OpenAI Agents SDK.

benign-skills/
  Benign sample skills used as part of the evaluation.

public-skills/
  Publicly available skills collected for real-world scanner evaluation.

vulnerable-skills/
  Intentionally vulnerable sample skills used for scanner testing.

test_skills/
  Exact benchmark data copied from the SKILL-INJECT repository.

results/
  Saved evaluation outputs.

eval_labeled_skills.py
  Evaluation script for labeled benign and vulnerable skills.

eval_skillinject.py
  Evaluation script for the injected skill test corpus.
```

## Setup

The static scanner only requires Python and PyYAML:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyyaml
```

The AI-assisted scanner has its own requirements:

```bash
cd ai-scanner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then add an OpenAI API key to `ai-scanner/.env`, or export it in your shell:

```bash
export OPENAI_API_KEY=your_api_key_here
```

The real `.env` file and virtual environments are excluded from Git.

## Usage

Run the static scanner on a skill directory:

```bash
python scanner/scan.py vulnerable-skills/
```

Scan the publicly available skill corpus:

```bash
python scanner/scan.py public-skills/
```

Run the AI-assisted scanner:

```bash
cd ai-scanner
python ai_scan.py ../vulnerable-skills/
```

Scan the clean skills copied from SKILL-INJECT:

```bash
python scanner/scan.py test_skills/skills/
```

Run evaluation using existing result files:

```bash
python eval_labeled_skills.py \
  --vuln-static vulnerable_static_results.json \
  --benign-static benign_static_results.json \
  --vuln-ai vulnerable_ai_results.json \
  --benign-ai benign_ai_results.json \
  --csv traceability.csv
```

## Notes for Reviewers

This repository is intended to support a thesis presentation and make the prototype reproducible. The generated result files are included to document the evaluation, while local secrets, virtual environments, caches, and editor state are excluded.

The `test_skills/` directory contains benchmark data copied from the [SKILL-INJECT benchmark](https://github.com/aisa-group/skill-inject), including its clean skill definitions, injection definition files, task scripts, and task files. SKILL-INJECT should be cited when using this corpus.
