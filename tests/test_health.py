import unittest

from fastapi.testclient import TestClient

from server import main


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_healthz(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_readyz(self):
        resp = self.client.get("/readyz")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("apps_writable"))

    def test_metrics(self):
        resp = self.client.get("/api/metrics")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("distill", body)
        self.assertIn("caches", body)
        self.assertIn("features", body)
        self.assertIn("analyze", body)
        self.assertIn("history", body)


if __name__ == "__main__":
    unittest.main()
