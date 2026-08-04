import unittest
import math
import numpy as np
import torch

from server import app, compute_step_entropy
from fastapi.testclient import TestClient
from jlens import project_jlens, CALIB_PROMPTS, N_CALIB_PROMPTS, normalise_entropy, compute_raw_entropy
from disposition import classify_disposition, DISPOSITIONS, LEXICON


class TestComputeStepEntropy(unittest.TestCase):
    def test_uniform_logits_give_max_entropy(self):
        vocab_size = 1000
        uniform_logits = torch.zeros(1, vocab_size)
        entropy_high = compute_step_entropy(uniform_logits)
        self.assertAlmostEqual(entropy_high, 1.0, places=2)

    def test_one_hot_logits_give_zero_entropy(self):
        vocab_size = 1000
        one_hot_logits = torch.full((1, vocab_size), -100.0)
        one_hot_logits[0, 42] = 100.0
        entropy_low = compute_step_entropy(one_hot_logits)
        self.assertAlmostEqual(entropy_low, 0.0, places=2)

    def test_entropy_bounded_0_1(self):
        for _ in range(5):
            logits = torch.randn(1, 500)
            e = compute_step_entropy(logits)
            self.assertTrue(0.0 <= e <= 1.0, f"entropy {e} out of [0,1]")


class TestHealthEndpoint(unittest.TestCase):
    def test_health_returns_ok(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "disposition-lens-infer")


class TestProjectJlens(unittest.TestCase):
    """Unit tests for J-lens projection — no model needed."""

    def _make_jlens(self, vocab_size=100, hidden_size=16):
        """Random J-lens matrix and h_mid for testing."""
        rng = np.random.default_rng(42)
        J = rng.standard_normal((vocab_size, hidden_size)).astype(np.float32)
        h = rng.standard_normal(hidden_size).astype(np.float32)
        return J, h

    def _dummy_tokenizer(self):
        class DummyTokenizer:
            def decode(self, ids):
                return f"tok{ids[0]}"
        return DummyTokenizer()

    def test_returns_list_of_dicts(self):
        J, h = self._make_jlens()
        tok = self._dummy_tokenizer()
        result = project_jlens(J, h, tok, top_k=3)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 3)
        for item in result:
            self.assertIn("t", item)
            self.assertIn("w", item)

    def test_weights_normalised_0_to_1(self):
        J, h = self._make_jlens()
        tok = self._dummy_tokenizer()
        result = project_jlens(J, h, tok, top_k=5)
        weights = [item["w"] for item in result]
        self.assertTrue(all(0.0 <= w <= 1.0 for w in weights), f"weights out of range: {weights}")
        # Highest-weight token should have w=1.0
        if weights:
            self.assertAlmostEqual(max(weights), 1.0, places=2)

    def test_sorted_descending(self):
        J, h = self._make_jlens()
        tok = self._dummy_tokenizer()
        result = project_jlens(J, h, tok, top_k=5)
        weights = [item["w"] for item in result]
        self.assertEqual(weights, sorted(weights, reverse=True))

    def test_top_k_respected(self):
        J, h = self._make_jlens(vocab_size=50)
        tok = self._dummy_tokenizer()
        for k in [1, 3, 5]:
            result = project_jlens(J, h, tok, top_k=k)
            self.assertLessEqual(len(result), k)

    def test_deterministic(self):
        J, h = self._make_jlens()
        tok = self._dummy_tokenizer()
        r1 = project_jlens(J, h, tok, top_k=3)
        r2 = project_jlens(J, h, tok, top_k=3)
        self.assertEqual(r1, r2)

    def test_large_constant_j_gives_valid_output(self):
        # J with very large values — checks numerical stability
        J = np.ones((100, 16), dtype=np.float32) * 1e6
        h = np.ones(16, dtype=np.float32)
        tok = self._dummy_tokenizer()
        result = project_jlens(J, h, tok, top_k=3)
        weights = [item["w"] for item in result]
        self.assertTrue(all(0.0 <= w <= 1.0 for w in weights))


class TestCalibrationPrompts(unittest.TestCase):
    def test_correct_count(self):
        self.assertEqual(len(CALIB_PROMPTS), N_CALIB_PROMPTS)

    def test_all_nonempty(self):
        for p in CALIB_PROMPTS:
            self.assertTrue(p.strip(), f"Empty calibration prompt: {p!r}")


# ---------------------------------------------------------------------------
# DL-3: disposition classifier tests
# ---------------------------------------------------------------------------

class TestClassifyDisposition(unittest.TestCase):
    def _tok(self, t, w):
        return {"t": t, "w": w}

    def test_idle_when_no_tokens(self):
        self.assertEqual(classify_disposition([]), "idle")

    def test_idle_when_no_keyword_match(self):
        tokens = [self._tok("the", 0.8), self._tok("and", 0.5)]
        self.assertEqual(classify_disposition(tokens), "idle")

    def test_concern_keywords(self):
        for kw in ("danger", "warning", "alert", "unsafe", "risk"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "concern")

    def test_reluctant_keywords(self):
        for kw in ("cannot", "sorry", "unable", "decline"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "reluctant")

    def test_uncertain_keywords(self):
        for kw in ("maybe", "unsure", "perhaps", "possibly"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "uncertain")

    def test_warm_keywords(self):
        for kw in ("great", "done", "wonderful", "glad"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "warm")

    def test_confident_keywords(self):
        for kw in ("certain", "yes", "definitely", "absolutely"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "confident")

    def test_curious_keywords(self):
        for kw in ("why", "how", "interesting", "explain"):
            with self.subTest(kw=kw):
                self.assertEqual(classify_disposition([self._tok(kw, 1.0)]), "curious")

    def test_prefix_match_certainly_gives_confident(self):
        # "certainly" starts with "certain" → confident
        self.assertEqual(classify_disposition([self._tok("certainly", 0.9)]), "confident")

    def test_prefix_match_warning_gives_concern(self):
        self.assertEqual(classify_disposition([self._tok("warning", 0.7)]), "concern")

    def test_weighted_vote_highest_wins(self):
        # uncertain token weight 0.8, warm token weight 0.3 → uncertain wins
        tokens = [self._tok("maybe", 0.8), self._tok("great", 0.3)]
        self.assertEqual(classify_disposition(tokens), "uncertain")

    def test_weighted_vote_sum_across_same_disposition(self):
        # two concern tokens: 0.4 + 0.5 = 0.9 vs single warm: 0.8 → concern wins
        tokens = [self._tok("danger", 0.4), self._tok("warning", 0.5), self._tok("great", 0.8)]
        self.assertEqual(classify_disposition(tokens), "concern")

    def test_returns_valid_disposition(self):
        tokens = [self._tok("yes", 0.9), self._tok("done", 0.5)]
        result = classify_disposition(tokens)
        self.assertIn(result, DISPOSITIONS)

    def test_bpe_prefix_stripped(self):
        # BPE tokenizers often prefix with ▁ (sentencepiece) or Ġ (GPT-2 style)
        self.assertEqual(classify_disposition([self._tok("▁maybe", 1.0)]), "uncertain")
        self.assertEqual(classify_disposition([self._tok("Ġdanger", 1.0)]), "concern")

    def test_case_insensitive(self):
        self.assertEqual(classify_disposition([self._tok("CANNOT", 1.0)]), "reluctant")
        self.assertEqual(classify_disposition([self._tok("Maybe", 1.0)]), "uncertain")

    def test_all_7_dispositions_reachable(self):
        trigger_map = {
            "concern":   "danger",
            "reluctant": "cannot",
            "uncertain": "maybe",
            "warm":      "great",
            "confident": "yes",
            "curious":   "why",
        }
        for disp, kw in trigger_map.items():
            with self.subTest(disp=disp):
                result = classify_disposition([self._tok(kw, 1.0)])
                self.assertEqual(result, disp)
        # idle via empty list
        self.assertEqual(classify_disposition([]), "idle")


# ---------------------------------------------------------------------------
# DL-3: entropy normalisation tests
# ---------------------------------------------------------------------------

class TestNormaliseEntropy(unittest.TestCase):
    def test_at_min_gives_zero(self):
        stats = {"min": 2.0, "max": 8.0}
        self.assertAlmostEqual(normalise_entropy(2.0, stats), 0.0)

    def test_at_max_gives_one(self):
        stats = {"min": 2.0, "max": 8.0}
        self.assertAlmostEqual(normalise_entropy(8.0, stats), 1.0)

    def test_midpoint(self):
        stats = {"min": 0.0, "max": 10.0}
        self.assertAlmostEqual(normalise_entropy(5.0, stats), 0.5)

    def test_clamped_below_zero(self):
        stats = {"min": 3.0, "max": 7.0}
        self.assertEqual(normalise_entropy(1.0, stats), 0.0)  # below calibration min

    def test_clamped_above_one(self):
        stats = {"min": 3.0, "max": 7.0}
        self.assertEqual(normalise_entropy(10.0, stats), 1.0)  # above calibration max

    def test_degenerate_min_equals_max_returns_half(self):
        stats = {"min": 5.0, "max": 5.0}
        self.assertAlmostEqual(normalise_entropy(5.0, stats), 0.5)


class TestComputeRawEntropy(unittest.TestCase):
    def test_uniform_returns_log_vocab(self):
        vocab_size = 1000
        logits = np.zeros(vocab_size, dtype=np.float32)
        raw = compute_raw_entropy(logits)
        self.assertAlmostEqual(raw, math.log(vocab_size), places=2)

    def test_one_hot_returns_zero(self):
        vocab_size = 1000
        logits = np.full(vocab_size, -100.0, dtype=np.float32)
        logits[42] = 100.0
        raw = compute_raw_entropy(logits)
        self.assertAlmostEqual(raw, 0.0, places=2)

    def test_non_negative(self):
        for _ in range(5):
            logits = np.random.randn(500).astype(np.float32)
            self.assertGreaterEqual(compute_raw_entropy(logits), 0.0)


class TestComputeStepEntropyWithStats(unittest.TestCase):
    """compute_step_entropy with calibration stats uses min-max normalisation."""

    def test_with_stats_clamps_to_01(self):
        stats = {"min": 2.0, "max": 8.0}
        # Uniform logits → raw ≈ log(1000) ≈ 6.9, within [2, 8] → ~0.82
        vocab_size = 1000
        uniform_logits = torch.zeros(1, vocab_size)
        e = compute_step_entropy(uniform_logits, stats=stats)
        self.assertTrue(0.0 <= e <= 1.0, f"entropy {e} out of [0,1]")

    def test_without_stats_still_bounded(self):
        vocab_size = 500
        for _ in range(5):
            logits = torch.randn(1, vocab_size)
            e = compute_step_entropy(logits)  # no stats → log-vocab fallback
            self.assertTrue(0.0 <= e <= 1.0, f"entropy {e} out of [0,1]")


if __name__ == "__main__":
    unittest.main()
