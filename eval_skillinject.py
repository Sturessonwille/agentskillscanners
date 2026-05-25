#!/usr/bin/env python3
"""
Evaluate static and AI scanners against the SKILL-INJECT test corpus.

The test_skills/ directory contains:
  - clean_skills/       (5 benign skills  — ground truth: benign)
  - injected_skills/
      contextual/       (5 subtle injections — ground truth: malicious)
      obvious/          (10 blatant injections — ground truth: malicious)

Produces:
  1. Per-skill traceability table (console + optional CSV)
  2. Confusion-matrix metrics per scanner
  3. Breakdown by difficulty tier (clean / contextual / obvious)

Usage:
  # Static scanner only (no API key needed)
  python eval_skillinject.py --static-only

  # Both scanners
  python eval_skillinject.py

  # With pre-computed JSON results
  python eval_skillinject.py \\
      --static-clean  results/static_clean.json \\
      --static-inject results/static_inject.json \\
      --ai-clean      results/ai_clean.json \\
      --ai-inject     results/ai_inject.json

  # Export CSV for LaTeX tables
  python eval_skillinject.py --csv results/skillinject_eval.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _load_ai_report(path: Path) -> dict:
    """Accept pure JSON or log text with a trailing JSON object."""
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'\{\s*"scan_summary"\s*:', raw)
    if m:
        return json.loads(raw[m.start():])
    print(f"  [warn] could not parse AI JSON in {path}", file=sys.stderr)
    return {}

BASE = Path(__file__).resolve().parent
TEST_SKILLS = BASE / "test_skills"
CLEAN_DIR = TEST_SKILLS / "clean_skills"
INJECT_DIR = TEST_SKILLS / "injected_skills"
STATIC_SCANNER = BASE / "scanner" / "scan.py"
AI_SCANNER = BASE / "ai-scanner" / "ai_scan.py"
AI_VENV_PYTHON = BASE / "ai-scanner" / ".venv" / "bin" / "python"


# ── ground truth ──────────────────────────────────────────────────────
GROUND_TRUTH: dict[str, dict] = {}

def _build_ground_truth():
    for d in sorted(CLEAN_DIR.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            GROUND_TRUTH[d.name] = {"label": "benign", "tier": "clean", "path": str(d)}
    for tier in ("contextual", "obvious"):
        tier_dir = INJECT_DIR / tier
        if not tier_dir.exists():
            continue
        for d in sorted(tier_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                GROUND_TRUTH[d.name] = {"label": "malicious", "tier": tier, "path": str(d)}

_build_ground_truth()


# ── scanner runners ──────────────────────────────────────────────────
def run_static(target: Path) -> dict:
    cmd = [sys.executable, str(STATIC_SCANNER), str(target), "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  [warn] static scanner produced no valid JSON for {target}", file=sys.stderr)
        return {}


def run_ai(target: Path, *, mode: str = "deep", timeout: int = 600) -> dict:
    python = str(AI_VENV_PYTHON) if AI_VENV_PYTHON.exists() else sys.executable
    cmd = [
        python, str(AI_SCANNER), str(target),
        "--mode", mode,
        "--output", "json",
        "--timeout", str(timeout),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                       cwd=str(AI_SCANNER.parent))
    raw = r.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{\s*"scan_summary"\s*:', raw)
        if m:
            return json.loads(raw[m.start():])
        print(f"  [warn] AI scanner produced no valid JSON for {target}", file=sys.stderr)
        return {}


# ── result indexing ──────────────────────────────────────────────────
def _skill_key(skill_dir: str) -> str:
    return Path(skill_dir.rstrip("/")).name

def index_static(data: dict) -> dict[str, dict]:
    out = {}
    for s in data.get("skills", []):
        out[_skill_key(s["skill_dir"])] = s
    return out

def index_ai(data: dict) -> dict[str, dict]:
    out = {}
    for r in data.get("results", []):
        out[_skill_key(r.get("skill_dir", ""))] = r
    return out


# ── prediction helpers ───────────────────────────────────────────────
def static_positive(row: dict, min_sev: str | None = None) -> bool:
    findings = row.get("findings") or []
    count = row.get("finding_count", len(findings))
    if min_sev is None:
        return count > 0
    max_s = row.get("max_severity")
    if not max_s:
        return False
    return SEVERITY_ORDER.get(max_s, -1) >= SEVERITY_ORDER.get(min_sev, 0)

def ai_positive(row: dict) -> bool:
    v = (row.get("verdict") or "").upper()
    return v in ("MALICIOUS", "SUSPICIOUS")


# ── metrics ──────────────────────────────────────────────────────────
def confusion(y_true: list[bool], y_pred: list[bool]) -> dict:
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    fn = sum(t and not p for t, p in zip(y_true, y_pred))
    fp = sum(not t and p for t, p in zip(y_true, y_pred))
    tn = sum(not t and not p for t, p in zip(y_true, y_pred))
    n = len(y_true)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec  = tp / (tp + fn) if (tp + fn) else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "F1": round(f1, 4),
        "accuracy": round((tp + tn) / n, 4) if n else 0.0,
        "FPR": round(fp / (fp + tn), 4) if (fp + tn) else 0.0,
    }

def tier_metrics(rows: list[dict], scanner: str, tier: str) -> dict:
    filtered = [r for r in rows if r["tier"] == tier]
    y_true = [r["is_malicious"] for r in filtered]
    y_pred = [r[f"{scanner}_positive"] for r in filtered]
    return confusion(y_true, y_pred)


# ── main ─────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--static-only", action="store_true",
                   help="Run only the static scanner (no API key needed)")
    p.add_argument("--static-clean", type=Path, help="Pre-computed static JSON for clean skills")
    p.add_argument("--static-inject", type=Path, help="Pre-computed static JSON for injected skills")
    p.add_argument("--ai-clean", type=Path, help="Pre-computed AI JSON for clean skills")
    p.add_argument("--ai-inject", type=Path, help="Pre-computed AI JSON for injected skills")
    p.add_argument("--ai-mode", default="deep", choices=["triage", "deep"])
    p.add_argument("--csv", type=Path, help="Write per-skill CSV here")
    p.add_argument("--json-out", type=Path, help="Write full results as JSON here")
    args = p.parse_args()

    run_ai_scan = not args.static_only

    # ── Run or load static scanner ────────────────────────────────────
    print("=" * 70)
    print("SKILL-INJECT Evaluation")
    print("=" * 70)

    if args.static_clean and args.static_inject:
        print("\n[static] Loading pre-computed results...")
        s_clean = json.loads(args.static_clean.read_text())
        s_inject = json.loads(args.static_inject.read_text())
    else:
        print("\n[static] Scanning clean_skills/ ...")
        s_clean = run_static(CLEAN_DIR)
        print(f"  -> {len(s_clean.get('skills', []))} skills scanned")

        print("[static] Scanning injected_skills/ ...")
        s_inject_ctx = run_static(INJECT_DIR / "contextual")
        s_inject_obv = run_static(INJECT_DIR / "obvious")
        s_inject = {
            "skills": s_inject_ctx.get("skills", []) + s_inject_obv.get("skills", [])
        }
        print(f"  -> {len(s_inject.get('skills', []))} skills scanned")

    static_idx = {**index_static(s_clean), **index_static(s_inject)}

    # ── Run or load AI scanner ────────────────────────────────────────
    ai_idx: dict[str, dict] = {}
    if run_ai_scan:
        if args.ai_clean and args.ai_inject:
            print("\n[AI] Loading pre-computed results...")
            a_clean = _load_ai_report(args.ai_clean)
            a_inject = _load_ai_report(args.ai_inject)
        else:
            print("\n[AI] Scanning clean_skills/ ...")
            a_clean = run_ai(CLEAN_DIR, mode=args.ai_mode)
            print(f"  -> {len(a_clean.get('results', []))} skills scanned")

            print("[AI] Scanning injected_skills/contextual/ ...")
            a_ctx = run_ai(INJECT_DIR / "contextual", mode=args.ai_mode)
            print(f"  -> {len(a_ctx.get('results', []))} skills scanned")

            print("[AI] Scanning injected_skills/obvious/ ...")
            a_obv = run_ai(INJECT_DIR / "obvious", mode=args.ai_mode)
            print(f"  -> {len(a_obv.get('results', []))} skills scanned")

            a_inject = {"results": a_ctx.get("results", []) + a_obv.get("results", [])}

        ai_idx = {**index_ai(a_clean), **index_ai(a_inject)}

    # ── Build per-skill rows ──────────────────────────────────────────
    rows: list[dict] = []
    for skill_id, gt in GROUND_TRUTH.items():
        is_mal = gt["label"] == "malicious"
        tier = gt["tier"]

        st = static_idx.get(skill_id, {})
        st_pos = static_positive(st)
        st_sev = st.get("max_severity", "")
        st_cnt = st.get("finding_count", len(st.get("findings", [])))

        ai_row = ai_idx.get(skill_id, {})
        ai_pos = ai_positive(ai_row) if run_ai_scan else None
        ai_verd = ai_row.get("verdict", "")
        ai_conf = ai_row.get("confidence", "")

        rows.append({
            "skill_id": skill_id,
            "tier": tier,
            "expected": gt["label"],
            "is_malicious": is_mal,
            "static_positive": st_pos,
            "static_max_severity": st_sev,
            "static_finding_count": st_cnt,
            "ai_positive": ai_pos,
            "ai_verdict": ai_verd,
            "ai_confidence": ai_conf,
        })

    # ── Print traceability table ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("PER-SKILL RESULTS")
    print("=" * 70)

    hdr = f"{'Skill':<38} {'Tier':<12} {'Expected':<10} {'Static':^8} {'Sev':<10}"
    if run_ai_scan:
        hdr += f" {'AI':^8} {'Verdict':<12} {'Conf':>5}"
    print(hdr)
    print("-" * len(hdr))

    for r in rows:
        st_mark = "FLAG" if r["static_positive"] else "ok"
        line = (f"{r['skill_id']:<38} {r['tier']:<12} {r['expected']:<10} "
                f"{st_mark:^8} {r['static_max_severity'] or '-':<10}")
        if run_ai_scan:
            ai_mark = "FLAG" if r["ai_positive"] else ("ok" if r["ai_positive"] is not None else "n/a")
            line += f" {ai_mark:^8} {r['ai_verdict'] or '-':<12} {str(r['ai_confidence'] or '-'):>5}"
        print(line)

    # ── Confusion matrices ────────────────────────────────────────────
    y_true = [r["is_malicious"] for r in rows]
    y_static = [r["static_positive"] for r in rows]

    print("\n" + "=" * 70)
    print("CONFUSION MATRICES")
    print("=" * 70)

    def print_matrix(name: str, m: dict):
        print(f"\n  {name}:")
        print(f"    TP={m['TP']:>2}  FN={m['FN']:>2}")
        print(f"    FP={m['FP']:>2}  TN={m['TN']:>2}")
        print(f"    Precision={m['precision']:.4f}  Recall={m['recall']:.4f}  F1={m['F1']:.4f}")
        print(f"    Accuracy={m['accuracy']:.4f}   FPR={m['FPR']:.4f}")

    ms_all = confusion(y_true, y_static)
    print_matrix("Static Scanner — Overall (n=20)", ms_all)

    for tier in ("clean", "contextual", "obvious"):
        m = tier_metrics(rows, "static", tier)
        n = sum(1 for r in rows if r["tier"] == tier)
        print_matrix(f"Static Scanner — {tier} (n={n})", m)

    if run_ai_scan:
        y_ai = [r["ai_positive"] for r in rows]
        ma_all = confusion(y_true, y_ai)
        print_matrix("AI Scanner — Overall (n=20)", ma_all)

        for tier in ("clean", "contextual", "obvious"):
            m = tier_metrics(rows, "ai", tier)
            n = sum(1 for r in rows if r["tier"] == tier)
            print_matrix(f"AI Scanner — {tier} (n={n})", m)

    # ── Tier summary table ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("DETECTION RATE BY TIER")
    print("=" * 70)

    for tier in ("contextual", "obvious"):
        tier_rows = [r for r in rows if r["tier"] == tier]
        n = len(tier_rows)
        st_det = sum(1 for r in tier_rows if r["static_positive"])
        line = f"  {tier:<12}: Static {st_det}/{n}"
        if run_ai_scan:
            ai_det = sum(1 for r in tier_rows if r["ai_positive"])
            line += f"   AI {ai_det}/{n}"
        print(line)

    clean_rows = [r for r in rows if r["tier"] == "clean"]
    n_clean = len(clean_rows)
    st_fp = sum(1 for r in clean_rows if r["static_positive"])
    line = f"  {'false pos':<12}: Static {st_fp}/{n_clean}"
    if run_ai_scan:
        ai_fp = sum(1 for r in clean_rows if r["ai_positive"])
        line += f"   AI {ai_fp}/{n_clean}"
    print(line)

    # ── CSV export ────────────────────────────────────────────────────
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\n[csv] Wrote {args.csv}")

    # ── JSON export ───────────────────────────────────────────────────
    if args.json_out:
        out = {
            "test_corpus": "SKILL-INJECT",
            "n_skills": len(rows),
            "per_skill": rows,
            "static_overall": ms_all,
        }
        if run_ai_scan:
            out["ai_overall"] = ma_all
        args.json_out.write_text(json.dumps(out, indent=2))
        print(f"[json] Wrote {args.json_out}")

    print()


if __name__ == "__main__":
    main()
