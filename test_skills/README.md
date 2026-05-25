# Skill-Inject Benchmark Data

This directory contains benchmark data copied from the official [SKILL-INJECT repository](https://github.com/aisa-group/skill-inject).

Included files:

```text
skills/
  Clean SKILL.md definitions from SKILL-INJECT.

contextual_injections.json
  Contextual injection definitions from SKILL-INJECT.

obvious_injections.json
  Obvious injection definitions from SKILL-INJECT.

task_scripts/
  Scripts referenced by injection definitions.

task_files/
  Task files referenced by benchmark tasks.

tasks.json
  Clean task definitions.

task_files.json
  Task file mapping.
```

The injected benchmark cases in SKILL-INJECT are generated from the clean skills and injection JSON files. This folder is therefore benchmark data, not a local reimplementation of the full Skill-Inject Docker experiment pipeline.
