"""
Unit tests for jlens.py — pure numpy/math, no model loading required.
Run with any Python that has numpy and pytest.
"""
import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from jlens import project_jlens, CALIB_PROMPTS, N_CALIB_PROMPTS, TOP_K


class DummyTokenizer:
    def decode(self, ids):
        return f"tok{ids[0]}"


def make_random_jlens(vocab_size=100, hidden_size=16, seed=42):
    rng = np.random.default_rng(seed)
    J = rng.standard_normal((vocab_size, hidden_size)).astype(np.float32)
    h = rng.standard_normal(hidden_size).astype(np.float32)
    return J, h


class TestProjectJlens(unittest.TestCase):
    def test_returns_list_of_dicts(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=3)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 3)
        for item in result:
            self.assertIn("t", item)
            self.assertIn("w", item)
            self.assertIsInstance(item["t"], str)
            self.assertIsInstance(item["w"], float)

    def test_weights_in_0_1(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=5)
        for item in result:
            self.assertTrue(0.0 <= item["w"] <= 1.0, f"weight out of range: {item}")

    def test_highest_weight_is_1(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=5)
        if result:
            self.assertAlmostEqual(max(i["w"] for i in result), 1.0, places=2)

    def test_weights_sorted_descending(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=5)
        weights = [item["w"] for item in result]
        self.assertEqual(weights, sorted(weights, reverse=True))

    def test_top_k_respected(self):
        J, h = make_random_jlens(vocab_size=50)
        tok = DummyTokenizer()
        for k in [1, 3, 5]:
            result = project_jlens(J, h, tok, top_k=k)
            self.assertLessEqual(len(result), k)

    def test_deterministic(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        r1 = project_jlens(J, h, tok, top_k=3)
        r2 = project_jlens(J, h, tok, top_k=3)
        self.assertEqual(r1, r2)

    def test_numerical_stability_large_values(self):
        J = np.ones((100, 16), dtype=np.float32) * 1e6
        h = np.ones(16, dtype=np.float32)
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=3)
        for item in result:
            self.assertFalse(np.isnan(item["w"]))
            self.assertTrue(0.0 <= item["w"] <= 1.0)

    def test_all_zero_h_does_not_crash(self):
        J, _ = make_random_jlens()
        h = np.zeros(16, dtype=np.float32)
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=3)
        self.assertIsInstance(result, list)

    def test_single_top_k(self):
        J, h = make_random_jlens()
        tok = DummyTokenizer()
        result = project_jlens(J, h, tok, top_k=1)
        self.assertLessEqual(len(result), 1)
        if result:
            self.assertAlmostEqual(result[0]["w"], 1.0, places=2)


class TestCalibrationPrompts(unittest.TestCase):
    def test_correct_count(self):
        self.assertEqual(len(CALIB_PROMPTS), N_CALIB_PROMPTS)

    def test_all_nonempty(self):
        for p in CALIB_PROMPTS:
            self.assertTrue(p.strip(), f"Empty calibration prompt: {p!r}")

    def test_all_strings(self):
        for p in CALIB_PROMPTS:
            self.assertIsInstance(p, str)

    def test_no_duplicates(self):
        self.assertEqual(len(CALIB_PROMPTS), len(set(CALIB_PROMPTS)))


class TestProjectJlensMatchesSpec(unittest.TestCase):
    """Verify the output shape matches the signal contract spec."""

    def test_signal_contract_shape(self):
        """tokens[] should be [{t: str, w: float in 0..1}, ...]"""
        J, h = make_random_jlens(vocab_size=200, hidden_size=32)
        tok = DummyTokenizer()
        tokens = project_jlens(J, h, tok, top_k=TOP_K)

        self.assertIsInstance(tokens, list)
        self.assertLessEqual(len(tokens), TOP_K)
        for entry in tokens:
            self.assertIsInstance(entry["t"], str)
            w = entry["w"]
            self.assertIsInstance(w, float)
            self.assertGreaterEqual(w, 0.0)
            self.assertLessEqual(w, 1.0)


if __name__ == "__main__":
    unittest.main()
