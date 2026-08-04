import unittest
import math
import numpy as np
import torch

from server import app, compute_step_entropy
from fastapi.testclient import TestClient
from jlens import project_jlens, CALIB_PROMPTS, N_CALIB_PROMPTS


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


if __name__ == "__main__":
    unittest.main()
