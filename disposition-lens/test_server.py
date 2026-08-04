import unittest
import math
import torch

from server import app, compute_step_entropy
from fastapi.testclient import TestClient

class TestDispositionLensServer(unittest.TestCase):
    def test_entropy_computation(self):
        # High entropy (uniform distribution)
        vocab_size = 1000
        uniform_logits = torch.zeros(1, vocab_size)
        entropy_high = compute_step_entropy(uniform_logits)
        self.assertAlmostEqual(entropy_high, 1.0, places=2)
        
        # Low entropy (one-hot distribution)
        one_hot_logits = torch.full((1, vocab_size), -100.0)
        one_hot_logits[0, 42] = 100.0
        entropy_low = compute_step_entropy(one_hot_logits)
        self.assertAlmostEqual(entropy_low, 0.0, places=2)
        
        # Bounded between 0 and 1
        self.assertTrue(0.0 <= entropy_high <= 1.0)
        self.assertTrue(0.0 <= entropy_low <= 1.0)

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "disposition-lens-infer")

if __name__ == "__main__":
    unittest.main()
