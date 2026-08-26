#!/usr/bin/env python3
"""
CANIS-EVAL-001 — grader and report generator (CE-01 compliant).

Reads results_canis_eval001_{model}.jsonl for each model and produces:
  - 8×8 confusion matrices  (2 models × 4 arms, arm0 and arm2 shown)
  - Per-class recall with 95% Wilson CI  (n=50 positive per class → ±14pp)
  - FP rate per axis with 95% Wilson CI  (n=20 negatives per class → ±22pp)
  - Idle accuracy (n=50 idle prompts → ±14pp)
  - Arm comparison table with statistical verdict

CE-01 key question answered in the report:
    Does J-space (arm1/arm2) beat the lexical seed-anchor baseline (arm3)?
    Primary comparison: arm1 vs arm3  (both entropy-free — isolates classifier path)
    Secondary:          arm2 vs arm3  (full pipeline vs lexical baseline)
    arm0 establishes the entropy-only FLOOR.

    If Δ(arm1 − arm3) > CI_half for BOTH models → J-space beats lexical baseline.
    If Δ ≤ CI → within noise; the claim that J-space adds value collapses.

Usage:
    python3 eval/grade_canis_eval001.py \\
        [--results-dir eval/] \\
        [--models apertus,ministral] \\
        [--out eval/canis_eval001_report.md]
"""
import argparse
import json
import math
import pathlib
import sys
from collections import defaultdict

CLASSES = ["confident", "uncertain", "curious", "concern", "reluctant", "warm", "mischief"]
ARMS = ["arm0", "arm1", "arm2", "arm3"]
ARM_LABELS = {
    "arm0": "Entropy-only (FLOOR)",
    "arm1": "J-space-only (no entropy)",
    "arm2": "Full pipeline  [production]",
    "arm3": "Lexical baseline (seed anchors)",
}
ALL_STATES = CLASSES + ["idle"]


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple:
    """Wilson score interval for proportion k/n.  Returns (lo, hi, mid) in [0,1]."""
    if n == 0:
        return (0.0, 1.0, 0.5)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - margin), min(1.0, centre + margin), centre)


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def ci_str(lo: float, hi: float) -> str:
    return f"[{pct(lo)}, {pct(hi)}]"


# ---------------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------------

def build_confusion(rows: list, arm: str) -> dict:
    """8×8 confusion matrix: actual_state → {predicted_state: count}. Positives only."""
    mat = defaultdict(lambda: defaultdict(int))
    for row in rows:
        if row["split"] == "negative":
            continue
        actual = row["target_class"]
        predicted = row[arm]
        mat[actual][predicted] += 1
    return mat


def format_confusion_table(mat: dict) -> str:
    header = "| actual \\ pred | " + " | ".join(s[:8] for s in ALL_STATES) + " |"
    sep    = "| --- | " + " | ".join("---" for _ in ALL_STATES) + " |"
    lines  = [header, sep]
    for actual in ALL_STATES:
        row_counts = [str(mat[actual].get(pred, 0)) for pred in ALL_STATES]
        lines.append(f"| **{actual}** | " + " | ".join(row_counts) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-arm metrics
# ---------------------------------------------------------------------------

def compute_metrics(rows: list, arm: str) -> dict:
    """
    Returns dict with:
      recall[class]      : (k, n, lo, hi, mid)   — positives only
      fp_rate[class]     : (k, n, lo, hi, mid)   — negatives only
      idle_acc           : (k, n, lo, hi, mid)   — idle split
      overall_pos_acc    : (k, n, lo, hi, mid)   — all positives pooled
    """
    pos_rows  = [r for r in rows if r["split"] == "positive"]
    neg_rows  = [r for r in rows if r["split"] == "negative"]
    idle_rows = [r for r in rows if r["split"] == "idle"]

    recall: dict = {}
    for cls in CLASSES:
        cls_rows = [r for r in pos_rows if r["target_class"] == cls]
        k = sum(1 for r in cls_rows if r[arm] == cls)
        n = len(cls_rows)
        recall[cls] = (k, n) + wilson_ci(k, n)

    fp_rate: dict = {}
    for cls in CLASSES:
        cls_neg = [r for r in neg_rows if r["target_class"] == cls]
        k = sum(1 for r in cls_neg if r[arm] == cls)
        n = len(cls_neg)
        fp_rate[cls] = (k, n) + wilson_ci(k, n)

    k_idle = sum(1 for r in idle_rows if r[arm] == "idle")
    n_idle = len(idle_rows)
    idle_acc = (k_idle, n_idle) + wilson_ci(k_idle, n_idle)

    k_all = sum(1 for r in pos_rows if r[arm] == r["target_class"])
    n_all = len(pos_rows)
    overall_pos_acc = (k_all, n_all) + wilson_ci(k_all, n_all)

    return {
        "recall": recall,
        "fp_rate": fp_rate,
        "idle_acc": idle_acc,
        "overall_pos_acc": overall_pos_acc,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(model_results: dict, out_path: pathlib.Path) -> None:
    """model_results: {model_key: list_of_rows}"""
    lines = []

    lines += [
        "# CANIS-EVAL-001 — Disposition Evaluation Report (CE-01)",
        "",
        "**WP2-EPIC | Owner: Miguel | Generated by eval/grade_canis_eval001.py**",
        "",
        "## Matrix",
        "",
        "| Split | N per class | N total |",
        "| --- | --- | --- |",
        "| Positive (7 elicitable classes) | 50 | 350 |",
        "| Idle baseline | — | 50 |",
        "| Negative controls (FP test, 7 classes) | 20 | 140 |",
        "| **Total** | | **540** |",
        "",
        "## Arms (CE-01 spec)",
        "",
        "| Arm | Name | Description |",
        "| --- | --- | --- |",
        "| arm0 | Entropy-only (FLOOR) | Ignore J-space; entropy alone classifies |",
        "| arm1 | J-space-only | Seed-vector cosine; no entropy gate |",
        "| arm2 | Full pipeline ← production | Seed-vector cosine + entropy blending |",
        "| arm3 | Lexical baseline | Keyword match on seed-anchor words (adversarial control) |",
        "",
        "95% CI method: Wilson score interval.  n=50 → ±14pp;  n=20 → ±22pp.",
        "",
    ]

    for model_key, rows in model_results.items():
        model_label = {"apertus": "Apertus-4B", "ministral": "Ministral-3B"}.get(model_key, model_key)
        lines += ["---", "", f"## Model: {model_label}", ""]

        arm_metrics = {arm: compute_metrics(rows, arm) for arm in ARMS}

        # Pooled positive accuracy summary
        lines += [
            "### Pooled Positive Accuracy (all 7 classes, n=350)",
            "",
            "| Arm | Correct/N | Accuracy | 95% CI |",
            "| --- | --- | --- | --- |",
        ]
        for arm in ARMS:
            m = arm_metrics[arm]
            k, n, lo, hi, mid = m["overall_pos_acc"]
            lines.append(
                f"| {arm} ({ARM_LABELS[arm]}) | {k}/{n} | {pct(mid)} | {ci_str(lo, hi)} |"
            )
        lines.append("")

        # Idle accuracy
        lines += [
            "### Idle Baseline Accuracy (n=50)",
            "",
            "| Arm | Idle/N | Accuracy | 95% CI |",
            "| --- | --- | --- | --- |",
        ]
        for arm in ARMS:
            m = arm_metrics[arm]
            k, n, lo, hi, mid = m["idle_acc"]
            lines.append(f"| {arm} | {k}/{n} | {pct(mid)} | {ci_str(lo, hi)} |")
        lines.append("")

        # Per-class recall
        lines += [
            "### Per-Class Recall (n=50 per class)",
            "",
            "| Class | arm0 k/n | arm0 rec | arm0 CI | arm1 rec | arm1 CI"
            " | arm2 rec | arm2 CI | arm3 rec | arm3 CI |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for cls in CLASSES:
            row_parts = [f"**{cls}**"]
            k0, n0 = arm_metrics["arm0"]["recall"][cls][:2]
            row_parts.append(f"{k0}/{n0}")
            for arm in ARMS:
                k, n, lo, hi, mid = arm_metrics[arm]["recall"][cls]
                row_parts.append(pct(mid))
                row_parts.append(ci_str(lo, hi))
            lines.append("| " + " | ".join(row_parts) + " |")
        lines.append("")

        # FP rates
        lines += [
            "### FP Rate per Axis (n=20 negatives per class)",
            "",
            "FP = classifier fires target_class on a prompt designed NOT to elicit it.",
            "",
            "| Class | arm0 FP | arm0 CI | arm1 FP | arm1 CI"
            " | arm2 FP | arm2 CI | arm3 FP | arm3 CI |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for cls in CLASSES:
            row_parts = [f"**{cls}**"]
            for arm in ARMS:
                k, n, lo, hi, mid = arm_metrics[arm]["fp_rate"][cls]
                row_parts.append(pct(mid))
                row_parts.append(ci_str(lo, hi))
            lines.append("| " + " | ".join(row_parts) + " |")
        lines.append("")

        # Confusion matrices for arm0 (FLOOR) and arm2 (production)
        for arm in ["arm0", "arm2"]:
            lines += [f"### Confusion Matrix — {arm} ({ARM_LABELS[arm]})", ""]
            mat = build_confusion(rows, arm)
            lines.append(format_confusion_table(mat))
            lines.append("")

    # ---------------------------------------------------------------------------
    # CE-01 key question: does J-space beat the lexical seed-anchor baseline?
    # ---------------------------------------------------------------------------
    lines += [
        "---",
        "",
        "## CE-01 Key Question: Does J-Space Beat the Lexical Seed-Anchor Baseline?",
        "",
        "**arm0** = entropy-only FLOOR (no J-space, no lexicon).",
        "**arm1** = J-space-only (seed-vector cosine, no entropy) — the J-space claim.",
        "**arm3** = lexical seed-anchor baseline (keyword match on words from SEED_PHRASES, no entropy).",
        "**arm2** = full pipeline (arm1 + entropy blending) — production path.",
        "",
        "Primary comparison: **arm1 vs arm3** (entropy-free, isolates classifier path).",
        "Secondary:          **arm2 vs arm3** (full pipeline vs lexical baseline).",
        "",
        "Definition of *beats the baseline*: Δ > half-width of the 95% CI on the difference.",
        "With n=350 positives, CI_half ≈ 1.96 × √(p̂(1−p̂)/350) ≈ ±5pp at p̂=0.5.",
        "",
        "### Primary: J-space-only (arm1) vs Lexical baseline (arm3)",
        "",
        "| Model | arm1 acc | arm3 acc | Δ (arm1−arm3) | CI half-width | J-space beats lexical? |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    primary_verdicts = []
    for model_key, rows in model_results.items():
        model_label = {"apertus": "Apertus-4B", "ministral": "Ministral-3B"}.get(model_key, model_key)
        m1 = compute_metrics(rows, "arm1")
        m3 = compute_metrics(rows, "arm3")
        _, n1, _, _, acc1 = m1["overall_pos_acc"]
        _, n3, _, _, acc3 = m3["overall_pos_acc"]
        delta = acc1 - acc3
        n = (n1 + n3) // 2
        p_avg = (acc1 + acc3) / 2
        ci_half = 1.96 * math.sqrt(p_avg * (1 - p_avg) / n) if n > 0 else 1.0
        beats = "**YES**" if abs(delta) > ci_half else "NO (within noise)"
        direction = "↑ J-space better" if delta > 0 else ("↓ lexical better" if delta < 0 else "=")
        lines.append(
            f"| {model_label} | {pct(acc1)} | {pct(acc3)} | "
            f"{'+' if delta >= 0 else ''}{pct(delta)} {direction} | ±{pct(ci_half)} | {beats} |"
        )
        primary_verdicts.append((model_label, delta, ci_half, beats))

    lines += [
        "",
        "### Secondary: Full pipeline (arm2) vs Lexical baseline (arm3)",
        "",
        "| Model | arm2 acc | arm3 acc | Δ (arm2−arm3) | CI half-width | Pipeline beats lexical? |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for model_key, rows in model_results.items():
        model_label = {"apertus": "Apertus-4B", "ministral": "Ministral-3B"}.get(model_key, model_key)
        m2 = compute_metrics(rows, "arm2")
        m3 = compute_metrics(rows, "arm3")
        _, n2, _, _, acc2 = m2["overall_pos_acc"]
        _, n3, _, _, acc3 = m3["overall_pos_acc"]
        delta = acc2 - acc3
        n = (n2 + n3) // 2
        p_avg = (acc2 + acc3) / 2
        ci_half = 1.96 * math.sqrt(p_avg * (1 - p_avg) / n) if n > 0 else 1.0
        beats = "**YES**" if abs(delta) > ci_half else "NO (within noise)"
        direction = "↑ pipeline better" if delta > 0 else ("↓ lexical better" if delta < 0 else "=")
        lines.append(
            f"| {model_label} | {pct(acc2)} | {pct(acc3)} | "
            f"{'+' if delta >= 0 else ''}{pct(delta)} {direction} | ±{pct(ci_half)} | {beats} |"
        )

    lines += [
        "",
        "### Entropy floor: arm0 vs arm3 (entropy-only vs lexical baseline)",
        "",
        "| Model | arm0 acc (floor) | arm3 acc | Δ (arm3−arm0) | CI half-width | Lexical lifts above floor? |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for model_key, rows in model_results.items():
        model_label = {"apertus": "Apertus-4B", "ministral": "Ministral-3B"}.get(model_key, model_key)
        m0 = compute_metrics(rows, "arm0")
        m3 = compute_metrics(rows, "arm3")
        _, n0, _, _, acc0 = m0["overall_pos_acc"]
        _, n3, _, _, acc3 = m3["overall_pos_acc"]
        delta = acc3 - acc0
        n = (n0 + n3) // 2
        p_avg = (acc0 + acc3) / 2
        ci_half = 1.96 * math.sqrt(p_avg * (1 - p_avg) / n) if n > 0 else 1.0
        beats = "**YES**" if abs(delta) > ci_half else "NO (within noise)"
        direction = "↑ lexical above floor" if delta > 0 else ("↓ lexical below floor" if delta < 0 else "=")
        lines.append(
            f"| {model_label} | {pct(acc0)} | {pct(acc3)} | "
            f"{'+' if delta >= 0 else ''}{pct(delta)} {direction} | ±{pct(ci_half)} | {beats} |"
        )

    lines += [""]

    # Written verdict
    lines += ["### Verdict", ""]
    both_beat = all("YES" in v[3] for v in primary_verdicts)
    neither_beat = all("YES" not in v[3] for v in primary_verdicts)

    if both_beat:
        lines += [
            "**J-space (seed-vector cosine, arm1) beats the seed-anchor lexical baseline (arm3)**",
            "**on both models, by a margin larger than the 95% confidence interval.**",
            "",
            "The full J-space projection — computing cosine similarity between the inference-time",
            "hidden-state projection z = J @ h_tap and the per-disposition seed vectors — consistently",
            "outperforms a plain keyword match against the same seed-phrase vocabulary. The gain is",
            "statistically distinguishable from sampling noise at the n=350 scale.",
            "",
            "The continuous vector representation in J-space is doing real work beyond what the",
            "source vocabulary alone would explain. The J-space claim is supported.",
        ]
    elif neither_beat:
        lines += [
            "**J-space (seed-vector cosine, arm1) does NOT beat the seed-anchor lexical baseline**",
            "**(arm3) by more than the 95% confidence interval on either model.**",
            "",
            "Δ(arm1 − arm3) falls within the ±CI_half noise band on both models. This is a",
            "*negative result*, and it IS the deliverable for CE-01.",
            "",
            "**Interpretation:**",
            "The J-space vector projection (J @ h_tap → seed-vector cosine) is not adding",
            "statistically measurable signal beyond a keyword match to the same seed-phrase",
            "vocabulary at the n=350 scale used here. Either:",
            "",
            "1. The models (4B / 3B params) do not produce sufficiently differentiated",
            "   hidden states at the 3/4-depth tap layer for all 8 disposition classes.",
            "2. The 7-word seed-anchor lexicon already captures the dominant vocabulary signal,",
            "   leaving no room for the full vector representation to demonstrate uplift.",
            "3. Larger n (200 per class → ±7pp CI instead of ±14pp) may reveal a real but",
            "   small delta that is currently masked by noise.",
            "",
            "**Recommended next step (CE-06):** increase n to 200 per class to tighten CIs,",
            "or adjust seed-anchor lexicon construction to use a richer vocabulary extraction.",
        ]
    else:
        lines += [
            "**Mixed result: J-space beats the lexical baseline on one model but not the other.**",
            "",
            "See the per-model rows above. The result is inconsistent across models.",
            "The signal appears model-architecture-dependent rather than a robust property",
            "of the J-space representation at this tap depth and scale.",
            "",
            "This ambiguity is also a CE-01 deliverable: it suggests the disposition readout",
            "needs per-model calibration rather than a shared lexical/vector classifier.",
        ]

    lines += [
        "",
        "---",
        "",
        "*Generated by eval/grade_canis_eval001.py (CE-01)*",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"Report written to {out_path}")


def load_results(results_dir: pathlib.Path, model_key: str) -> list:
    path = results_dir / f"results_canis_eval001_{model_key}.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="eval")
    parser.add_argument("--models",      default="apertus,ministral")
    parser.add_argument("--out",         default="eval/canis_eval001_report.md")
    args = parser.parse_args()

    results_dir = pathlib.Path(args.results_dir)
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    model_results = {}
    for model_key in models:
        rows = load_results(results_dir, model_key)
        if not rows:
            print(f"[{model_key}] No results found — skipping", file=sys.stderr)
            continue
        model_results[model_key] = rows
        n_pos  = sum(1 for r in rows if r["split"] == "positive")
        n_idle = sum(1 for r in rows if r["split"] == "idle")
        n_neg  = sum(1 for r in rows if r["split"] == "negative")
        print(f"[{model_key}] Loaded {len(rows)} rows  (pos={n_pos}  idle={n_idle}  neg={n_neg})")

    if not model_results:
        print("No results to grade. Run run_canis_eval001.py first.", file=sys.stderr)
        sys.exit(1)

    out_path = pathlib.Path(args.out)
    generate_report(model_results, out_path)

    # Quick stdout summary
    print()
    for model_key, rows in model_results.items():
        model_label = {"apertus": "Apertus-4B", "ministral": "Ministral-3B"}.get(model_key, model_key)
        print(f"=== {model_label} ===")
        for arm in ARMS:
            m = compute_metrics(rows, arm)
            k, n, lo, hi, mid = m["overall_pos_acc"]
            print(f"  {arm} ({ARM_LABELS[arm][:35]}) : {pct(mid)}  95%CI {ci_str(lo, hi)}")
        k_i, n_i, lo_i, hi_i, mid_i = compute_metrics(rows, "arm2")["idle_acc"]
        print(f"  idle accuracy (arm2 / production): {pct(mid_i)}  95%CI {ci_str(lo_i, hi_i)}")
        print()


if __name__ == "__main__":
    main()
