#!/usr/bin/env python3
"""
Build a traceability table and confusion-matrix metrics for the 30 labeled skills
(15 vulnerable + 15 benign) from static JSON + AI scan output.

AI reports may be pure JSON or stdout mixed with a trailing JSON object (as from
`python ai_scan.py ...` without only JSON on stdout).

Usage:
  python eval_labeled_skills.py \\
    --vuln-static vulnerable_static_results.json \\
    --benign-static benign_static_results.json \\
    --vuln-ai vulnerable_ai_results.json \\
    --benign-ai benign_ai_results.json \\
    --csv traceability.csv

  # Stricter AI positive class: only MALICIOUS counts as "detected"
  python eval_labeled_skills.py ... --ai-positive malicious_only

  # Static: flag only if max severity >= HIGH
  python eval_labeled_skills.py ... --static-min-severity HIGH
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _load_ai_report(path: Path) -> dict:
    """Accept pure JSON or log text with a trailing JSON object."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{\s*\"scan_summary\"\s*:", raw)
    if not m:
        print(f"Error: could not parse JSON in {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw[m.start() :])


def _skill_key(skill_dir: str) -> str:
    """Stable id: last path segment (folder name)."""
    return Path(skill_dir.rstrip("/")).name


def _static_predict_positive(
    row: dict,
    *,
    min_severity: str | None,
) -> bool:
    """True if static scanner raises an alert by the chosen rule."""
    findings = row.get("findings") or []
    count = row.get("finding_count", len(findings))
    max_sev = row.get("max_severity")

    if min_severity is None:
        return count > 0

    if not findings and count == 0:
        return False
    if not max_sev:
        return False
    return SEVERITY_ORDER.get(max_sev, -1) >= SEVERITY_ORDER[min_severity]


def _ai_predict_positive(verdict: str | None, *, mode: str) -> bool:
    if not verdict:
        return False
    v = verdict.upper()
    if mode == "malicious_only":
        return v == "MALICIOUS"
    return v in ("MALICIOUS", "SUSPICIOUS")


def _metrics(
    y_true: list[bool],
    y_pred: list[bool],
) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    acc = (tp + tn) / len(y_true) if y_true else 0.0
    return {
        "TP": tp,
        "FN": fn,
        "FP": fp,
        "TN": tn,
        "recall_sensitivity": sens,
        "specificity": spec,
        "FPR": fpr,
        "accuracy": acc,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vuln-static", type=Path, required=True)
    p.add_argument("--benign-static", type=Path, required=True)
    p.add_argument("--vuln-ai", type=Path, required=True)
    p.add_argument("--benign-ai", type=Path, required=True)
    p.add_argument("--csv", type=Path, default=None, help="Write traceability table CSV here")
    p.add_argument(
        "--static-min-severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL", "any"],
        default="any",
        help="any = any finding; else require max_severity >= this level (default: any)",
    )
    p.add_argument(
        "--ai-positive",
        choices=["malicious_or_suspicious", "malicious_only"],
        default="malicious_or_suspicious",
        help="How to map AI verdict to binary positive (default: MALICIOUS or SUSPICIOUS)",
    )
    args = p.parse_args()

    min_sev = None if args.static_min_severity == "any" else args.static_min_severity
    ai_mode = (
        "malicious_only"
        if args.ai_positive == "malicious_only"
        else "malicious_or_suspicious"
    )

    vuln_s = _load_json(args.vuln_static)
    ben_s = _load_json(args.benign_static)
    vuln_a = _load_ai_report(args.vuln_ai)
    ben_a = _load_ai_report(args.benign_ai)

    static_by_id: dict[str, dict] = {}
    for s in vuln_s.get("skills", []):
        static_by_id[_skill_key(s["skill_dir"])] = s
    for s in ben_s.get("skills", []):
        static_by_id[_skill_key(s["skill_dir"])] = s

    ai_by_id: dict[str, dict] = {}
    for r in vuln_a.get("results", []):
        ai_by_id[_skill_key(r.get("skill_dir", ""))] = r
    for r in ben_a.get("results", []):
        ai_by_id[_skill_key(r.get("skill_dir", ""))] = r

    rows: list[dict] = []
    order: list[tuple[str, bool, str]] = []
    for label, is_vuln, aid in [
        ("vulnerable", True, vuln_a),
        ("benign", False, ben_a),
    ]:
        for r in aid.get("results", []):
            sid = _skill_key(r["skill_dir"])
            order.append((sid, is_vuln, label))

    y_true: list[bool] = []
    y_static: list[bool] = []
    y_ai: list[bool] = []

    for skill_id, is_vuln, expected_label in order:
        st = static_by_id.get(skill_id, {})
        ai_row = ai_by_id.get(skill_id, {})
        verdict = ai_row.get("verdict")
        conf = ai_row.get("confidence")

        static_pos = _static_predict_positive(st, min_severity=min_sev)
        ai_pos = _ai_predict_positive(verdict, mode=ai_mode)

        y_true.append(is_vuln)
        y_static.append(static_pos)
        y_ai.append(ai_pos)

        max_sev = st.get("max_severity") or ""
        fc = st.get("finding_count", len(st.get("findings") or []))

        note_parts = []
        if is_vuln and not static_pos:
            note_parts.append("static missed")
        if is_vuln and not ai_pos:
            note_parts.append("AI missed")
        if not is_vuln and static_pos:
            note_parts.append("static FP")
        if not is_vuln and ai_pos:
            note_parts.append("AI FP")

        rows.append(
            {
                "skill_id": skill_id,
                "expected": expected_label,
                "static_max_severity": max_sev,
                "static_finding_count": fc,
                "static_positive": static_pos,
                "ai_verdict": verdict or "",
                "ai_confidence": conf if conf is not None else "",
                "ai_positive": ai_pos,
                "note": "; ".join(note_parts),
            }
        )

    ms = _metrics(y_true, y_static)
    ma = _metrics(y_true, y_ai)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
            if rows:
                w.writeheader()
                w.writerows(rows)

    # Human-readable report on stdout
    print("Labeled-skill evaluation (n=30)")
    print(f"  Static rule: {args.static_min_severity}")
    print(f"  AI positive rule: {args.ai_positive}")
    print()

    hdr = f"{'skill_id':<38} {'exp':<10} {'st+':^5} {'AI+':^5} {'static sev':<12} {'AI verdict':<14}"
    print(hdr)
    print("-" * len(hdr))
    for row in rows:
        print(
            f"{row['skill_id']:<38} {row['expected']:<10} "
            f"{str(row['static_positive']):^5} {str(row['ai_positive']):^5} "
            f"{str(row['static_max_severity'] or '-'):<12} {str(row['ai_verdict'] or '-'):<14}"
        )

    print()
    print("Confusion matrix (positive class = vulnerable / malicious skill)")
    print("  Static:", ms)
    print("  AI:    ", ma)
    if args.csv:
        print()
        print(f"Wrote {args.csv}")


if __name__ == "__main__":
    main()
