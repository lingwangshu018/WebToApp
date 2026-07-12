import tempfile
import unittest
from pathlib import Path

from server.task_store import TaskStore


class TaskStoreTests(unittest.TestCase):
    def test_upsert_get_resume_and_prune(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TaskStore(Path(tmp) / "tasks.sqlite3")
            task = {
                "task_id": "t1",
                "app_id": "a1",
                "status": "pending",
                "stage": "queued",
                "stage_detail": {},
                "payload": {"url": "https://example.com"},
                "result": None,
                "error": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "finished_at": None,
            }
            store.upsert(task)
            loaded = store.get("t1")
            self.assertEqual(loaded["payload"]["url"], "https://example.com")
            self.assertEqual(len(store.list_resumable()), 1)
            task["status"] = "done"
            task["finished_at"] = 1
            store.upsert(task)
            self.assertEqual(len(store.list_resumable()), 0)
            removed = store.prune(ttl_seconds=0, max_finished=0)
            self.assertGreaterEqual(removed, 1)
            self.assertIsNone(store.get("t1"))


if __name__ == "__main__":
    unittest.main()
