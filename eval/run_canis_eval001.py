#!/usr/bin/env python3
"""
CANIS-EVAL-001 — batch runner (CE-01 compliant).

4 ARMS (CE-01 spec, mirrors EVAL-008):
  arm0 : ENTROPY-ONLY  (J-space zeroed — FLOOR):
         Ignores all J-space signals; entropy alone drives classification.
         High entropy → uncertain | Low entropy → confident | else → idle.
         Establishes the minimum achievable performance from the entropy signal alone.

  arm1 : J-SPACE-ONLY  (entropy gate OFF):
         Seed-vector cosine similarity; no entropy blending.
         classify_by_seed_vectors(seed_scores).

  arm2 : FULL PIPELINE (shipped config — production path):
         Seed-vector cosine + entropy blending.
         resolve_disposition_seed(seed_scores, entropy).

  arm3 : LEXICAL BASELINE (keyword match on seed anchors — adversarial control):
         Keyword match on j_tokens against words DERIVED FROM SEED_PHRASES.
         If arm3 ≈ arm2, the J-space vector projection adds nothing over a plain
         keyword match to the same anchors — the claim collapses.

2 MODELS:
  apertus   — swiss-ai/Apertus-v1.1-4B-Instruct
  ministral — Ministral-3B

FULL READOUT logged per item (argmax alone is unrecoverable):
  item_id, split, target_class, is_fp_test
  prompt, prompt_sha256
  model, answer
  tokens          : top-k j_tokens [{t, w}]
  seed_scores     : all 8 cosines {disposition: cosine_similarity}
  entropy_norm    : normalised entropy 0..1
  predicted       : arm2 output (production path, for quick access)
  arm0 … arm3     : per-arm predictions
  latency_ms      : /infer wall-clock time in milliseconds

Usage:
    python3 eval/run_canis_eval001.py \\
        [--matrix eval/canis_eval001_matrix.jsonl] \\
        [--out-dir eval/] \\
        [--server http://localhost:8000] \\
        [--models apertus,ministral] \\
        [--max-tokens 64] \\
        [--temperature 0.7] \\
        [--timeout 120] \\
        [--resume]

The --resume flag skips already-recorded item_ids in the output file.
Set --models apertus or --models ministral to run a single model.
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

_REPO_ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "disposition-lens"))

from disposition import (
    classify_by_seed_vectors,
    resolve_disposition_seed,
    ENTROPY_HIGH,
    ENTROPY_LOW,
    WEIGHT_FLOOR,
    _normalise_token,
    _token_matches,
    DISPOSITIONS,
)

# ---------------------------------------------------------------------------
# CE-01 arm definitions
# ---------------------------------------------------------------------------

INFER_URL_TEMPLATE = "{server}/infer"
DEFAULT_MODELS = ["apertus", "ministral"]

# Arm 3 — LEXICAL BASELINE.
# Words extracted from SEED_PHRASES in disposition-lens/jlens.py.
# Purpose: adversarial control to test whether vector projection (arm1/arm2)
# adds anything over a keyword match to the SAME anchor words.
# If arm3 ≈ arm2 on pooled positive accuracy, the J-space claim collapses.
SEED_ANCHOR_LEXICON: dict = {
    "confident":  {"confirm", "definitely", "certainly", "absolutely", "correct", "indeed"},
    "uncertain":  {"sure", "possible", "maybe", "perhaps", "uncertain", "unclear", "depends"},
    "curious":    {"wonder", "interesting", "explain", "reason", "intriguing"},
    "concern":    {"warning", "dangerous", "risk", "danger", "harm", "alert", "hazard", "safety"},
    "reluctant":  {"cannot", "sorry", "unable", "decline", "unfortunately", "comply"},
    "warm":       {"wonderful", "glad", "excellent", "delighted", "fantastic", "pleased"},
    "mischief":   {"loophole", "technically", "rephrase", "bypass", "notice", "workaround"},
}


def arm0_entropy_only(entropy: float) -> str:
    """FLOOR: classify from entropy alone, J-space zeroed out."""
    if entropy >= ENTROPY_HIGH:
        return "uncertain"
    if entropy <= ENTROPY_LOW:
        return "confident"
    return "idle"


def arm3_seed_anchor_lexicon(tokens: list) -> str:
    """
    LEXICAL BASELINE: keyword match on seed-anchor words derived from SEED_PHRASES.

    Uses the same weight-gated vote as the production lexicon path but against
    SEED_ANCHOR_LEXICON (words from the seed phrases) rather than the hand-curated
    LEXICON. This tests whether the vector representation in J-space is doing more
    than a simple keyword lookup to the same source vocabulary.
    """
    scores: dict = defaultdict(float)
    for tok in tokens:
        t_norm = _normalise_token(tok.get("t", ""))
        w = float(tok.get("w", 0.0))
        if not t_norm or w < WEIGHT_FLOOR:
            continue
        for disp, keywords in SEED_ANCHOR_LEXICON.items():
            if any(_token_matches(t_norm, kw) for kw in keywords):
                scores[disp] += w
                break
    if not scores:
        return "idle"
    return max(scores, key=lambda d: scores[d])


def _ensure_all_cosines(seed_scores: dict) -> dict:
    """
    Return seed_scores with all 8 DISPOSITIONS present.
    Server only returns the 7 elicitable classes; idle has no seed vector → 0.0.
    """
    full = {d: 0.0 for d in DISPOSITIONS}
    full.update(seed_scores)
    return full


def apply_four_arms_ce01(tokens: list, seed_scores: dict, entropy: float) -> dict:
    """CE-01 4-arm classification."""
    arm2 = (
        resolve_disposition_seed(seed_scores, entropy)
        if seed_scores
        else arm0_entropy_only(entropy)
    )
    return {
        "arm0": arm0_entropy_only(entropy),
        "arm1": classify_by_seed_vectors(seed_scores) if seed_scores else "idle",
        "arm2": arm2,
        "arm3": arm3_seed_anchor_lexicon(tokens),
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def call_infer(
    server: str,
    prompt: str,
    model: str,
    max_tokens: int,
    temperature: float,
    timeout: int,
    return_h_tap: bool = False,
) -> tuple:
    """POST /infer and return (parsed_json_or_None, latency_ms)."""
    url = INFER_URL_TEMPLATE.format(server=server)
    payload = json.dumps({
        "prompt": prompt,
        "model": model,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "search_enabled": False,
        "return_h_tap": return_h_tap,
    }).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    t0 = time.monotonic()
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
                latency_ms = round((time.monotonic() - t0) * 1000, 1)
                return resp, latency_ms
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:200]
            print(f"  [HTTP {exc.code}] {body}", file=sys.stderr)
            return None, round((time.monotonic() - t0) * 1000, 1)
        except Exception as exc:
            if attempt == 0:
                print(f"  [retry] {exc}", file=sys.stderr)
                time.sleep(5)
            else:
                print(f"  [error] {exc}", file=sys.stderr)
                return None, round((time.monotonic() - t0) * 1000, 1)
    return None, 0.0


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------

def load_done(out_path: pathlib.Path) -> set:
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                try:
                    done.add(json.loads(line)["item_id"])
                except Exception:
                    pass
    return done


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix",      default="eval/canis_eval001_matrix.jsonl")
    parser.add_argument("--out-dir",     default="eval")
    parser.add_argument("--server",      default="http://localhost:8000")
    parser.add_argument("--models",      default=",".join(DEFAULT_MODELS))
    parser.add_argument("--max-tokens",  type=int,   default=64)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--timeout",     type=int,   default=120)
    parser.add_argument("--h-tap",       action="store_true",
                        help="also persist the raw tap-layer hidden state to "
                             "h_tap_canis_eval001_<model>.jsonl (~35MB/model). "
                             "Required to probe whether a disposition is "
                             "represented but not recoverable through the "
                             "seed-vector projection.")
    parser.add_argument("--resume",      action="store_true",
                        help="Skip item_ids already in the output file")
    args = parser.parse_args()

    matrix_path = pathlib.Path(args.matrix)
    if not matrix_path.exists():
        print(f"Matrix file not found: {matrix_path}", file=sys.stderr)
        print("Run: python3 eval/gen_canis_eval001.py first", file=sys.stderr)
        sys.exit(1)

    matrix = [
        json.loads(line)
        for line in matrix_path.read_text().splitlines()
        if line.strip()
    ]
    print(f"Loaded {len(matrix)} items from {matrix_path}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for model_key in models:
        out_path = out_dir / f"results_canis_eval001_{model_key}.jsonl"
        done = load_done(out_path) if args.resume else set()
        if done:
            print(f"[{model_key}] Resuming — {len(done)} items already recorded")

        n_ok = n_err = 0
        htap_path = out_dir / f"h_tap_canis_eval001_{model_key}.jsonl"
        fhtap = open(htap_path, "a" if args.resume else "w") if args.h_tap else None
        with open(out_path, "a" if args.resume else "w") as fout:
            for i, item in enumerate(matrix):
                if item["item_id"] in done:
                    continue

                resp, latency_ms = call_infer(
                    args.server,
                    item["prompt"],
                    model_key,
                    args.max_tokens,
                    args.temperature,
                    args.timeout,
                    return_h_tap=args.h_tap,
                )

                if resp is None:
                    print(
                        f"  [{model_key}] ERROR {item['item_id']} — skipping",
                        file=sys.stderr,
                    )
                    n_err += 1
                    continue

                tokens      = resp.get("tokens", [])
                seed_scores = _ensure_all_cosines(resp.get("seed_scores", {}))
                entropy     = float(resp.get("entropy", 0.5))
                arms        = apply_four_arms_ce01(tokens, seed_scores, entropy)

                # h_tap goes to a sidecar, not the results row: it is ~3k floats
                # per item and would make the results jsonl unreadable. Appended
                # incrementally so --resume works the same way as the main file.
                if args.h_tap and fhtap is not None and resp.get("h_tap"):
                    fhtap.write(json.dumps({
                        "item_id":       item["item_id"],
                        "model":         model_key,
                        "tap_layer_idx": resp.get("tap_layer_idx"),
                        "h_tap":         resp["h_tap"],
                    }) + "\n")
                    fhtap.flush()

                row = {
                    # --- item identity ---
                    "item_id":       item["item_id"],
                    "split":         item["split"],
                    "target_class":  item["target_class"],
                    "is_fp_test":    item["is_fp_test"],
                    "prompt":        item["prompt"],
                    "prompt_sha256": prompt_sha256(item["prompt"]),
                    # --- inference ---
                    "model":         model_key,
                    "answer":        resp.get("answer", ""),
                    # --- full signal readout (argmax alone is unrecoverable) ---
                    "tokens":        tokens,
                    "seed_scores":   seed_scores,
                    "entropy_norm":  entropy,
                    # --- arm predictions ---
                    "predicted":     arms["arm2"],   # production path, quick access
                    "arm0":          arms["arm0"],
                    "arm1":          arms["arm1"],
                    "arm2":          arms["arm2"],
                    "arm3":          arms["arm3"],
                    # --- timing ---
                    "latency_ms":    latency_ms,
                }
                fout.write(json.dumps(row) + "\n")
                fout.flush()
                n_ok += 1

                if (i + 1) % 50 == 0:
                    pct = round((i + 1) / len(matrix) * 100)
                    print(
                        f"  [{model_key}] {i + 1}/{len(matrix)} ({pct}%)"
                        f"  ok={n_ok}  err={n_err}"
                    )

        if fhtap is not None:
            fhtap.close()
            print(f"[{model_key}] h_tap sidecar → {htap_path}")

        print(f"[{model_key}] Done — ok={n_ok}  err={n_err}  → {out_path}")


if __name__ == "__main__":
    main()
