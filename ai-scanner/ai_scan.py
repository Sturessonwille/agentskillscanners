#!/usr/bin/env python3
"""
AI-assisted security scanner for Agent Skills.

Uses a multi-specialist pipeline to analyze skill directories
(SKILL.md + scripts/) for vulnerabilities:

  Phase 1 – Triage:     fast first pass on every skill (parallel)
  Phase 2 – Specialize: four focused specialists run in parallel on flagged skills
  Phase 3 – Aggregate:  merge specialist findings into a single verdict

Usage:
    python ai_scan.py <path>                  # scan a directory of skills
    python ai_scan.py <path> --mode deep      # skip triage, deep-scan everything
    python ai_scan.py <path> --compare        # also run static scanner for comparison
    python ai_scan.py <path> --model gpt-4o   # override DEFAULT_MODEL for all agents
    python ai_scan.py <path> --concurrency 3  # limit parallel API calls
    python ai_scan.py <path> --timeout 0      # no per-call timeout (default: 600s)
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agents import Runner

from agent_defs import (
    SPECIALISTS,
    aggregator_agent,
    triage_agent,
)
from tools import discover_skills, format_skill_message, load_skill, static_scan

DEFAULT_CONCURRENCY = 5


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------


def _override_model(agent, model: str | None):
    """Return a clone of *agent* with *model* overridden (if given)."""
    if not model:
        return agent
    from agents import Agent

    return Agent(
        name=agent.name,
        instructions=agent.instructions,
        model=model,
    )


def _final_output_to_str(result) -> str:
    """Normalize RunResult.final_output to a string for JSON parsing."""
    out = result.final_output
    if out is None:
        return ""
    if isinstance(out, str):
        return out
    return str(out)


async def _run_with_semaphore(
    sem: asyncio.Semaphore,
    agent,
    message: str,
    *,
    timeout_sec: float | None = None,
) -> str:
    """Run a single agent under a concurrency semaphore.

    If *timeout_sec* is set, the model call is cancelled after that many seconds
    (OpenAI calls otherwise have no default deadline and can appear to hang).
    """
    async with sem:

        async def _call():
            result = await Runner.run(agent, message)
            return _final_output_to_str(result)

        if timeout_sec is not None and timeout_sec > 0:
            try:
                return await asyncio.wait_for(_call(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                return (
                    '{"verdict": "UNKNOWN", "confidence": 0, "summary": "Model request timed out", '
                    '"findings": [], "error": "timeout"}'
                )
        return await _call()


def _try_parse_json(text: str) -> dict | None:
    """Best-effort extraction of a JSON object from agent output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Phase 1 – Triage
# ---------------------------------------------------------------------------


async def phase_triage(
    skills: list[dict],
    messages: list[str],
    sem: asyncio.Semaphore,
    model: str | None = None,
    timeout_sec: float | None = None,
) -> list[dict | None]:
    """Run the triage agent on every skill in parallel.

    Returns a list aligned with *skills*: parsed JSON result or None on failure.
    """
    agent = _override_model(triage_agent, model)
    print(f"[triage] Analyzing {len(skills)} skills …", flush=True)

    raw_outputs = await asyncio.gather(
        *[
            _run_with_semaphore(sem, agent, msg, timeout_sec=timeout_sec)
            for msg in messages
        ]
    )

    results: list[dict | None] = []
    for skill, output in zip(skills, raw_outputs):
        parsed = _try_parse_json(output)
        if parsed:
            label = parsed.get("verdict", "?")
        else:
            label = "PARSE_ERROR"
        name = os.path.basename(skill["skill_dir"])
        print(f"  {name}: {label}", flush=True)
        results.append(parsed)

    return results


# ---------------------------------------------------------------------------
# Phase 2 – Specialist deep analysis
# ---------------------------------------------------------------------------


async def phase_specialists(
    skill: dict,
    message: str,
    sem: asyncio.Semaphore,
    model: str | None = None,
    timeout_sec: float | None = None,
) -> list[str]:
    """Run all four specialists on a single skill in parallel."""
    agents = [_override_model(s, model) for s in SPECIALISTS]
    outputs = await asyncio.gather(
        *[
            _run_with_semaphore(sem, agent, message, timeout_sec=timeout_sec)
            for agent in agents
        ]
    )
    return list(outputs)


# ---------------------------------------------------------------------------
# Phase 3 – Aggregation
# ---------------------------------------------------------------------------


async def phase_aggregate(
    skill: dict,
    specialist_outputs: list[str],
    sem: asyncio.Semaphore,
    model: str | None = None,
    timeout_sec: float | None = None,
) -> dict | None:
    """Merge specialist findings via the aggregator agent."""
    agent = _override_model(aggregator_agent, model)

    sections = []
    for specialist, output in zip(SPECIALISTS, specialist_outputs):
        sections.append(f"## {specialist.name}\n{output}")

    prompt = (
        f"Merge the following specialist analyses for skill "
        f"directory: {skill['skill_dir']}\n\n"
        + "\n\n---\n\n".join(sections)
    )

    raw = await _run_with_semaphore(sem, agent, prompt, timeout_sec=timeout_sec)
    return _try_parse_json(raw) or {"raw_output": raw, "skill_dir": skill["skill_dir"]}


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------


async def run_scan(
    target: str,
    model: str | None,
    mode: str,
    compare: bool,
    concurrency: int,
    timeout_sec: float | None = None,
) -> dict:
    """Execute the full scan pipeline and return the report as a dict."""
    target = os.path.abspath(os.path.expanduser(target))

    if not os.path.exists(target):
        print(f"Error: '{target}' does not exist", file=sys.stderr)
        sys.exit(1)

    sem = asyncio.Semaphore(concurrency)

    # ── Discover skills ──────────────────────────────────────────────────
    if os.path.isfile(target):
        target = os.path.dirname(target)

    skills = discover_skills(target)
    if not skills:
        return {"error": f"No skills found under {target}"}

    print(f"Found {len(skills)} skill(s) in {target}", flush=True)
    to_msg = "none (calls may hang indefinitely)" if timeout_sec is None else f"{timeout_sec:g}s"
    print(f"[config] Per-call timeout: {to_msg}, concurrency: {concurrency}\n", flush=True)

    # ── Load all skill contents ──────────────────────────────────────────
    loaded = [load_skill(s["skill_dir"]) for s in skills]
    messages = [format_skill_message(sk) for sk in loaded]

    # ── Phase 1: Triage (unless --mode deep) ─────────────────────────────
    if mode == "deep":
        flagged_indices = list(range(len(skills)))
        triage_results: list[dict | None] = [None] * len(skills)
        print("[triage] Skipped (--mode deep)\n", flush=True)
    else:
        triage_results = await phase_triage(
            skills, messages, sem, model, timeout_sec=timeout_sec
        )
        flagged_indices = [
            i
            for i, r in enumerate(triage_results)
            if r is None or r.get("verdict") in ("SUSPICIOUS", "MALICIOUS")
        ]
        benign_count = len(skills) - len(flagged_indices)
        print(
            f"\n[triage] {benign_count} benign, {len(flagged_indices)} flagged for deep analysis\n",
            flush=True,
        )

    # ── Phase 2 + 3: Specialists → Aggregation (parallel per skill) ─────
    final_results: list[dict] = []

    for i in range(len(skills)):
        name = os.path.basename(loaded[i]["skill_dir"])
        if i not in flagged_indices:
            final_results.append(triage_results[i] or {"skill_dir": loaded[i]["skill_dir"], "verdict": "BENIGN"})
            continue

        print(f"[deep] Analyzing {name} with {len(SPECIALISTS)} specialists …", flush=True)
        specialist_outputs = await phase_specialists(
            loaded[i], messages[i], sem, model, timeout_sec=timeout_sec
        )

        for specialist, output in zip(SPECIALISTS, specialist_outputs):
            parsed = _try_parse_json(output)
            label = parsed.get("verdict", "?") if parsed else "raw"
            print(f"  {specialist.name}: {label}", flush=True)

        print(f"[aggregate] Merging findings for {name} …", flush=True)
        merged = await phase_aggregate(
            loaded[i], specialist_outputs, sem, model, timeout_sec=timeout_sec
        )
        final_results.append(merged)
        print(f"  -> {merged.get('verdict', '?')}\n", flush=True)

    # ── Optional: static scanner comparison ──────────────────────────────
    static_results = None
    if compare:
        print("[static] Running regex-based static scanner …", flush=True)
        static_results = static_scan(target)
        print("[static] Done\n", flush=True)

    # ── Compile final report ─────────────────────────────────────────────
    verdicts = [r.get("verdict", "UNKNOWN") for r in final_results]
    report = {
        "scan_summary": {
            "total_skills": len(skills),
            "malicious": verdicts.count("MALICIOUS"),
            "suspicious": verdicts.count("SUSPICIOUS"),
            "benign": verdicts.count("BENIGN"),
        },
        "results": final_results,
    }

    if static_results:
        report["static_scanner_results"] = static_results

    return report


# ---------------------------------------------------------------------------
# Text report formatter
# ---------------------------------------------------------------------------

_VERDICT_ORDER = {"MALICIOUS": 0, "SUSPICIOUS": 1, "BENIGN": 2, "UNKNOWN": 3}
_SEP = "-" * 60


def _truncate(text: str, maxlen: int = 120) -> str:
    """Collapse whitespace and truncate with ellipsis."""
    text = " ".join(text.split())
    if len(text) <= maxlen:
        return text
    return text[: maxlen - 3] + "..."


def format_text_report(report: dict) -> str:
    """Render the scan report as a compact, human-readable string."""
    lines: list[str] = []

    summary = report.get("scan_summary", {})
    total = summary.get("total_skills", 0)

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Skill Security Scan  --  {total} skill(s) analyzed")
    lines.append("=" * 60)
    lines.append("")
    lines.append(
        f"  MALICIOUS: {summary.get('malicious', 0)}"
        f"  |  SUSPICIOUS: {summary.get('suspicious', 0)}"
        f"  |  BENIGN: {summary.get('benign', 0)}"
    )

    results = sorted(
        report.get("results", []),
        key=lambda r: _VERDICT_ORDER.get(r.get("verdict", "UNKNOWN"), 99),
    )

    benign_names: list[str] = []

    for r in results:
        verdict = r.get("verdict", "UNKNOWN")
        skill_dir = r.get("skill_dir", "?")
        name = os.path.basename(skill_dir)

        if verdict == "BENIGN":
            benign_names.append(name)
            continue

        confidence = r.get("confidence")
        conf_str = f"confidence: {confidence:.2f}" if confidence is not None else ""

        lines.append("")
        lines.append(_SEP)
        lines.append(f"[{verdict}]  {name}    {conf_str}".rstrip())

        skill_summary = r.get("summary")
        if skill_summary:
            lines.append(f"  {_truncate(skill_summary, 200)}")

        findings = r.get("findings", [])
        if findings:
            lines.append("")
        for f in findings:
            severity = f.get("severity", "?")
            category = f.get("category", "?")
            source = f.get("source_file", "")
            line_hint = f.get("line_hint", "")
            loc = source
            if line_hint:
                loc = f"{source}:{line_hint}"

            lines.append(f"  {severity:<9s} {category}  --  {loc}")
            desc = f.get("description", "")
            if desc:
                lines.append(f"           {_truncate(desc)}")
            evidence = f.get("evidence", "")
            if evidence:
                lines.append(f"           > {_truncate(evidence)}")
            lines.append("")

    if benign_names:
        lines.append("")
        lines.append(_SEP)
        for name in benign_names:
            lines.append(f"[BENIGN]   {name}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted security scanner for Agent Skills (SKILL.md + scripts/)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python ai_scan.py ../vulnerable-skills/
  python ai_scan.py ../vulnerable-skills/ --mode deep
  python ai_scan.py ../vulnerable-skills/ --compare
  python ai_scan.py ../benign-skills/01-code-formatter/
  python ai_scan.py ../vulnerable-skills/ --model gpt-4o
  python ai_scan.py ../vulnerable-skills/ --concurrency 3
        """,
    )
    parser.add_argument(
        "path",
        help="Path to a skill directory or parent directory containing skill folders",
    )
    parser.add_argument(
        "--mode",
        choices=["triage", "deep"],
        default="triage",
        help="Scan mode: 'triage' (fast pass then deep on flagged) or "
        "'deep' (thorough analysis on everything). Default: triage",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Also run the static regex scanner and include a comparison",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the OpenAI model for all agents (default: see agent_defs.shared.DEFAULT_MODEL)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max parallel API calls (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Seconds per model call before cancelling (0 = no limit). "
        "The OpenAI SDK has no default deadline; long or stuck calls otherwise run forever. "
        "Default: 600.",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: OPENAI_API_KEY environment variable is not set.\n"
            "  export OPENAI_API_KEY=sk-...",
            file=sys.stderr,
        )
        sys.exit(1)

    timeout_sec = None if args.timeout <= 0 else args.timeout

    report = asyncio.run(
        run_scan(
            args.path,
            model=args.model,
            mode=args.mode,
            compare=args.compare,
            concurrency=args.concurrency,
            timeout_sec=timeout_sec,
        )
    )

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text_report(report))


if __name__ == "__main__":
    main()
