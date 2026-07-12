import time
import unittest

from server.engine.cache import TTLCache


class TTLCacheTests(unittest.TestCase):
    def test_set_get_and_ttl(self):
        cache = TTLCache(max_size=2, ttl_seconds=0.05)
        cache.set("a", b"1")
        self.assertEqual(cache.get("a"), b"1")
        time.sleep(0.08)
        self.assertIsNone(cache.get("a"))

    def test_evicts_oldest(self):
        cache = TTLCache(max_size=2, ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)


if __name__ == "__main__":
    unittest.main()
