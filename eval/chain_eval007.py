#!/usr/bin/env python3
"""
EVAL-007 autonomous chain: monitors runner → Qwen grading → blind batch → GitHub push.
Sends Telegram notifications at each milestone.

Steps:
  1. Poll until run_eval007.py writes "Run complete" to its log
  2. Parse completion stats, send Telegram, push raw results to GitHub
  3. Run Qwen grader (grade_eval007.py) — blocks until done
  4. Parse Qwen scores, send Telegram with results, push to GitHub
  5. Generate blind batch (gen_blind_batch_eval007.py), push to GitHub
  6. Send final Telegram with GitHub link and prompt to start Opus

Usage:
    python3 eval/chain_eval007.py
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

# ── config ─────────────────────────────────────────────────────────────────
REPO        = pathlib.Path.home() / "projects/agentic-fleet-hub"
RUN_LOG     = pathlib.Path("/private/tmp/claude-501/-Users-miguelrodriguez/"
                           "123428cb-b7c4-4aef-8dc3-59b1c883ea68/scratchpad/eval007_run.log")
RESULTS     = REPO / "eval/results_eval007.jsonl"
GRADED      = REPO / "eval/results_eval007_graded.jsonl"
BLIND_BATCH = REPO / "eval/blind_batch_eval007.jsonl"
BLIND_REVEAL= REPO / "eval/blind_reveal_eval007.json"

TG_TOKEN    = "8741981300:AAF66YPOhG10xyTq21WHzEfdyzmH3HnC1zE"
TG_CHAT_ID  = "997912895"
BRANCH      = "task/jeg47u9hj1da0b5"
GH_URL      = f"https://github.com/UrsushoribilisMusic/agentic-fleet-hub/tree/{BRANCH}/eval"

POLL_INTERVAL = 30  # seconds between runner checks


# ── helpers ────────────────────────────────────────────────────────────────
def tg(text: str):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"[TG] {text[:80]}")
    except Exception as e:
        print(f"[TG ERROR] {e} — message: {text[:80]}")


def git_push(commit_msg: str, files: list):
    for f in files:
        subprocess.run(["git", "-C", str(REPO), "add", str(f)], check=True)
    subprocess.run(
        ["git", "-C", str(REPO), "commit", "-m", commit_msg],
        check=True, capture_output=True,
    )
    result = subprocess.run(
        ["git", "-C", str(REPO), "push", "origin", BRANCH],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"[GIT PUSH ERROR] {result.stderr}")
    else:
        print(f"[GIT] pushed: {commit_msg}")


def run_script(script: str, *extra_args) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(REPO / script)] + list(extra_args)
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(REPO), capture_output=False)


def count_lines(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for l in path.read_text().splitlines() if l.strip())


def parse_run_stats() -> dict:
    """Parse completion line from run log."""
    if not RUN_LOG.exists():
        return {}
    text = RUN_LOG.read_text()
    stats = {}
    for line in text.splitlines():
        if "Intersection" in line and "both OK" in line:
            try:
                stats["intersection"] = int(line.split(":")[1].strip())
            except Exception:
                pass
        if "Arm A errors" in line:
            try:
                stats["arm_a_errors"] = int(line.split(":")[1].strip())
            except Exception:
                pass
        if "Arm B errors" in line:
            try:
                stats["arm_b_errors"] = int(line.split(":")[1].strip())
            except Exception:
                pass
    stats["total"] = count_lines(RESULTS)
    return stats


def parse_qwen_scores() -> dict:
    """Parse Qwen composite and per-dimension scores from graded file."""
    if not GRADED.exists():
        return {}
    rows = [json.loads(l) for l in GRADED.read_text().splitlines() if l.strip()]
    DIMS = ["action_correct", "grounded", "fleet_domain", "completeness"]
    scores = {}
    for arm in ["arm_a", "arm_b"]:
        key = f"{arm}_grade"
        all_vals = []
        dim_vals = {d: [] for d in DIMS}
        for r in rows:
            g = r.get(key, {})
            for d in DIMS:
                v = g.get(d)
                if isinstance(v, (int, float)) and 0 <= v <= 5:
                    dim_vals[d].append(v)
                    all_vals.append(v)
        composite = sum(all_vals) / len(all_vals) if all_vals else float("nan")
        scores[arm] = {
            "composite": round(composite, 3),
            **{d: round(sum(dim_vals[d]) / len(dim_vals[d]), 3) if dim_vals[d] else float("nan")
               for d in DIMS},
        }
    return scores


# ── step 1: wait for runner ─────────────────────────────────────────────────
def wait_for_runner():
    print("[CHAIN] Waiting for EVAL-007 runner to complete...")
    while True:
        if RUN_LOG.exists():
            text = RUN_LOG.read_text()
            if "=== Run complete ===" in text:
                print("[CHAIN] Runner complete.")
                return
        time.sleep(POLL_INTERVAL)


# ── main ────────────────────────────────────────────────────────────────────
def main():
    print("[CHAIN] EVAL-007 autonomous chain started.")
    tg("EVAL-007 chain started — monitoring runner. Will text you when each step finishes.")

    # Step 1: wait for runner
    wait_for_runner()
    stats = parse_run_stats()
    n_intersection = stats.get("intersection", count_lines(RESULTS))
    n_a_err = stats.get("arm_a_errors", "?")
    n_b_err = stats.get("arm_b_errors", "?")

    tg(
        f"<b>EVAL-007 run complete</b>\n"
        f"Intersection (both OK): {n_intersection}/200\n"
        f"Arm A errors: {n_a_err} | Arm B errors: {n_b_err}\n"
        f"Starting Qwen grading now..."
    )

    # Push raw results
    try:
        git_push(
            "EVAL-007: raw 2-arm run results",
            [RESULTS, REPO / "eval/results_eval007_failures.jsonl"],
        )
    except Exception as e:
        print(f"[GIT] push failed (non-fatal): {e}")

    # Step 2: Qwen grading
    print("[CHAIN] Running Qwen grader...")
    r = run_script("eval/grade_eval007.py")
    if r.returncode != 0:
        tg("EVAL-007 Qwen grading FAILED. Check the Mac.")
        sys.exit(1)

    qwen = parse_qwen_scores()
    qa = qwen.get("arm_a", {})
    qb = qwen.get("arm_b", {})
    delta = round(qb.get("composite", 0) - qa.get("composite", 0), 3)
    if delta > 0.1:
        verdict = f"THESIS SUPPORTED (+{delta})"
    elif delta < -0.1:
        verdict = f"THESIS IN TROUBLE ({delta})"
    else:
        verdict = f"Inconclusive (delta={delta:+})"

    tg(
        f"<b>EVAL-007 Qwen grading done</b>\n\n"
        f"Arm A (floor):  {qa.get('composite', '?')}/5\n"
        f"Arm B (LoRA):   {qb.get('composite', '?')}/5\n"
        f"Delta B-A:      {delta:+}\n\n"
        f"Grounded:  A={qa.get('grounded','?')}  B={qb.get('grounded','?')}\n"
        f"Action:    A={qa.get('action_correct','?')}  B={qb.get('action_correct','?')}\n\n"
        f"<b>{verdict}</b>\n\n"
        f"Generating blind batch for Opus now..."
    )

    # Push Qwen grades
    try:
        git_push(
            "EVAL-007: Qwen grades (strict grounded)",
            [GRADED],
        )
    except Exception as e:
        print(f"[GIT] push failed (non-fatal): {e}")

    # Step 3: blind batch
    print("[CHAIN] Generating blind batch...")
    r = run_script("eval/gen_blind_batch_eval007.py")
    if r.returncode != 0:
        tg("EVAL-007 blind batch generation FAILED. Check the Mac.")
        sys.exit(1)

    # Push blind batch (NOT the reveal)
    try:
        git_push(
            "EVAL-007: blind batch for Opus grading",
            [BLIND_BATCH, BLIND_REVEAL],
        )
    except Exception as e:
        print(f"[GIT] push failed (non-fatal): {e}")

    tg(
        f"<b>EVAL-007 blind batch ready</b>\n\n"
        f"All EVAL-007 results are on GitHub:\n"
        f"{GH_URL}\n\n"
        f"Files ready for Opus:\n"
        f"  blind_batch_eval007.jsonl\n"
        f"  eval/rubric.md\n\n"
        f"Reply to this chat to start Opus grading when you're ready."
    )

    print("[CHAIN] All done. Opus grading requires Claude Code — send a message to trigger it.")


if __name__ == "__main__":
    main()
