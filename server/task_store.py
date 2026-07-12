import json
import sqlite3
import threading
import time
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional


class TaskStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    app_id TEXT,
                    status TEXT,
                    stage TEXT,
                    stage_detail_json TEXT,
                    payload_json TEXT,
                    result_json TEXT,
                    error TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    finished_at REAL
                )
                """
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_finished_at ON tasks(finished_at)")

    def upsert(self, task: dict) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO tasks(
                    task_id, app_id, status, stage, stage_detail_json, payload_json,
                    result_json, error, created_at, updated_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.get("task_id"),
                    task.get("app_id"),
                    task.get("status"),
                    task.get("stage"),
                    json.dumps(task.get("stage_detail") or {}, ensure_ascii=False),
                    json.dumps(task.get("payload") or {}, ensure_ascii=False),
                    json.dumps(task.get("result"), ensure_ascii=False) if task.get("result") is not None else None,
                    task.get("error"),
                    task.get("created_at"),
                    task.get("updated_at"),
                    task.get("finished_at"),
                ),
            )

    def get(self, task_id: str) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return self._row_to_task(row)

    def list_resumable(self) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM tasks WHERE status IN ('pending', 'running') ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_task(row) for row in rows]

    def delete(self, task_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))

    def prune(self, ttl_seconds: float, max_finished: int) -> int:
        now = time.time()
        removed = 0
        with self._lock:
            rows = self._conn.execute(
                "SELECT task_id, finished_at FROM tasks WHERE finished_at IS NOT NULL"
            ).fetchall()
            finished = []
            for row in rows:
                finished_at = row["finished_at"]
                if finished_at is None:
                    continue
                if now - float(finished_at) > ttl_seconds:
                    self._conn.execute("DELETE FROM tasks WHERE task_id = ?", (row["task_id"],))
                    removed += 1
                else:
                    finished.append((float(finished_at), row["task_id"]))
            if len(finished) > max_finished:
                finished.sort()
                for _finished_at, task_id in finished[: len(finished) - max_finished]:
                    self._conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                    removed += 1
        return removed

    def stats(self) -> dict:
        with self._lock:
            total = self._conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
            pending = self._conn.execute(
                "SELECT COUNT(*) AS c FROM tasks WHERE status IN ('pending', 'running')"
            ).fetchone()["c"]
            return {"total": total, "active": pending, "path": str(self.path)}

    def _row_to_task(self, row) -> dict:
        def _loads(raw, default):
            if raw is None:
                return deepcopy(default)
            try:
                return json.loads(raw)
            except Exception:
                return deepcopy(default)

        return {
            "task_id": row["task_id"],
            "app_id": row["app_id"],
            "status": row["status"],
            "stage": row["stage"],
            "stage_detail": _loads(row["stage_detail_json"], {}),
            "payload": _loads(row["payload_json"], {}),
            "result": _loads(row["result_json"], None) if row["result_json"] is not None else None,
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "finished_at": row["finished_at"],
        }
