import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import server.history_store as history_module
import server.task_store as task_module
from server.history_store import HistoryStore, _parse_utc
from server.task_store import TaskStore


def _task(task_id, status="pending", finished_at=None, **overrides):
    value = {
        "task_id": task_id,
        "app_id": "app-" + task_id,
        "status": status,
        "stage": "queued",
        "stage_detail": {"percent": 1},
        "payload": {"url": "https://example.com"},
        "result": None,
        "error": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "finished_at": finished_at,
    }
    value.update(overrides)
    return value


def _recipe(app_id="app1", **overrides):
    value = {
        "id": app_id,
        "name": "App " + app_id,
        "url": "https://example.com/" + app_id,
        "color": "#123456",
    }
    value.update(overrides)
    return value


def test_task_store_crud_conversion_stats_and_resumable_order(tmp_path):
    store = TaskStore(tmp_path / "nested" / "tasks.sqlite3")
    assert store.get("missing") is None

    store.upsert(_task("b", created_at="2024-01-02T00:00:00Z"))
    store.upsert(_task("a", status="running", created_at="2024-01-01T00:00:00Z"))
    store.upsert(
        _task(
            "done",
            status="done",
            finished_at=50.0,
            result={"ok": True},
            stage_detail={},
            payload={},
            error="finished",
        )
    )

    loaded = store.get("done")
    assert loaded == {
        "task_id": "done",
        "app_id": "app-done",
        "status": "done",
        "stage": "queued",
        "stage_detail": {},
        "payload": {},
        "result": {"ok": True},
        "error": "finished",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "finished_at": 50.0,
    }
    assert [item["task_id"] for item in store.list_resumable()] == ["a", "b"]
    assert store.stats() == {"total": 3, "active": 2, "path": str(tmp_path / "nested" / "tasks.sqlite3")}

    store.delete("b")
    store.delete("does-not-exist")
    assert store.get("b") is None

    row = {
        "task_id": "broken",
        "app_id": None,
        "status": None,
        "stage": None,
        "stage_detail_json": None,
        "payload_json": "not-json",
        "result_json": "not-json",
        "error": None,
        "created_at": None,
        "updated_at": None,
        "finished_at": None,
    }
    converted = store._row_to_task(row)
    assert converted["stage_detail"] == {}
    assert converted["payload"] == {}
    assert converted["result"] is None


def test_task_store_prune_ttl_capacity_and_none_guard(tmp_path, monkeypatch):
    store = TaskStore(tmp_path / "tasks.sqlite3")
    monkeypatch.setattr(task_module.time, "time", lambda: 100.0)
    store.upsert(_task("expired", status="done", finished_at=10.0))
    store.upsert(_task("keep-old", status="done", finished_at=91.0))
    store.upsert(_task("keep-new", status="done", finished_at=99.0))
    store.upsert(_task("active", status="running", finished_at=None))

    assert store.prune(ttl_seconds=20.0, max_finished=1) == 2
    assert store.get("expired") is None
    assert store.get("keep-old") is None
    assert store.get("keep-new") is not None
    assert store.get("active") is not None
    assert store.prune(ttl_seconds=20.0, max_finished=10) == 0

    class _RowsOnlyConnection:
        def execute(self, statement, params=()):
            assert statement.startswith("SELECT")
            return self

        def fetchall(self):
            return [{"task_id": "impossible", "finished_at": None}]

    real_connection = store._conn
    store._conn = _RowsOnlyConnection()
    try:
        assert store.prune(ttl_seconds=1, max_finished=1) == 0
    finally:
        store._conn = real_connection


def test_history_path_variants_time_parsing_and_no_legacy(tmp_path):
    assert _parse_utc(None) is None
    assert _parse_utc("  ") is None
    assert _parse_utc("not-a-date") is None
    assert _parse_utc("2024-01-01T00:00:00Z").isoformat().endswith("+00:00")

    json_store = HistoryStore(tmp_path / "one.json")
    assert json_store.db_path == tmp_path / "one.sqlite3"
    assert json_store.json_legacy_path == tmp_path / "one.json"

    suffix_store = HistoryStore(tmp_path / "two.db")
    assert suffix_store.db_path == tmp_path / "two.db"
    assert suffix_store.json_legacy_path == tmp_path / "two.json"

    bare_store = HistoryStore(tmp_path / "three")
    assert bare_store.db_path == tmp_path / "three.sqlite3"
    assert bare_store.json_legacy_path == tmp_path / "three.json"

    special_store = HistoryStore(tmp_path / "_history")
    assert special_store.json_legacy_path == tmp_path / "_history.json"
    before = special_store._conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
    special_store._migrate_json_if_needed()
    assert special_store._conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0] == before


def test_history_migrates_full_legacy_state_and_removes_when_backup_exists(tmp_path):
    legacy = tmp_path / "history.json"
    backup = legacy.with_suffix(".json.bak")
    backup.write_text("old backup")
    legacy.write_text(
        json.dumps(
            {
                "apps": {
                    "full": {
                        "name": "Full",
                        "target_url": "https://full.example",
                        "public_path": "/custom/full",
                        "runtime_url": "https://runtime.example",
                        "color": "#abcdef",
                        "recipe": {"id": "full"},
                        "created_at": "2020-01-01T00:00:00Z",
                        "updated_at": "2021-01-01T00:00:00Z",
                    },
                    "defaults": {"created_at": "2020-02-01T00:00:00Z"},
                },
                "devices": {
                    "device": {
                        "app_ids": ["full", "defaults"],
                        "created_at": "2020-01-01T00:00:00Z",
                        "updated_at": "2021-01-01T00:00:00Z",
                    },
                    "empty": {},
                },
                "visits": {
                    "full": {
                        "total": 5,
                        "landing": 1,
                        "install": 2,
                        "pwa": 3,
                        "launch": 4,
                        "downloads": {"android": 2},
                        "last_visited_at": "2022-01-01T00:00:00Z",
                    },
                    "defaults": {},
                },
            }
        )
    )

    store = HistoryStore(legacy)
    assert not legacy.exists()
    assert backup.read_text() == "old backup"
    items = store.list_history("device", tmp_path)
    assert [item["app_id"] for item in items] == ["full", "defaults"]
    assert items[0]["visit_count"] == 5
    assert items[0]["download_breakdown"] == {"android": 2}
    defaults = items[1]
    assert defaults["name"] == "defaults"
    assert defaults["target_url"] == ""
    assert defaults["public_path"] == "/a/defaults"
    assert defaults["runtime_url"] == ""
    assert defaults["color"] == "#7c3aed"
    assert store._get_device_app_ids_locked("empty") == []


def test_history_malformed_legacy_is_backed_up_and_path_failures_are_tolerated(tmp_path):
    legacy = tmp_path / "broken.json"
    legacy.write_text("not-json")
    store = HistoryStore(legacy)
    assert legacy.with_suffix(".json.bak").exists()
    assert store.stats()["apps"] == 0

    store._conn.execute("DELETE FROM meta WHERE key = 'migrated_from_json'")
    fake_legacy = MagicMock()
    fake_legacy.exists.return_value = True
    fake_legacy.read_text.side_effect = OSError("unreadable")
    fake_backup = MagicMock()
    fake_backup.exists.return_value = False
    fake_legacy.with_suffix.return_value = fake_backup
    fake_legacy.replace.side_effect = OSError("cannot replace")
    fake_legacy.unlink.side_effect = OSError("cannot unlink")
    store.json_legacy_path = fake_legacy
    store._migrate_json_if_needed()
    assert fake_legacy.unlink.call_count == 1


def test_history_record_update_attach_visits_list_and_export(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    apps_dir = tmp_path / "apps"

    store.record_build("device", {"name": "missing id"}, "/x", None)
    store.attach_app(None, "x")
    store.attach_app("device", "")
    store.record_visit("", "landing")
    assert store.list_history(None, apps_dir) == []

    recipe = _recipe("app1", _custom_icon_data_url="secret", edit_token="token")
    store.record_build("device", recipe, "/a/app1", None)
    first_created = store._conn.execute("SELECT created_at FROM apps WHERE app_id='app1'").fetchone()[0]
    store.record_build(None, _recipe("app1", name="Renamed"), "/renamed", "https://runtime.example")
    assert store._conn.execute("SELECT created_at FROM apps WHERE app_id='app1'").fetchone()[0] == first_created

    store.attach_app("device", "app1")
    store.attach_app("device", "app1")
    store.record_build("device", _recipe("app2", name=""), "/a/app2", "")
    store._set_device_app_ids_locked("device", ["ghost", "app2", "app1"])

    store.record_visit("app1", "landing")
    store.record_visit("app1", "download:android")
    store.record_visit("app1", "download:")
    store.record_visit("app1", "unclassified")
    store.flush()
    store.record_visit("app1", "install")
    store.record_visit("app1", "pwa")
    store.record_visit("app1", "launch")
    store.flush()
    store.flush()

    icon = apps_dir / "app1" / "icon.png"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(b"png")
    items = store.list_history("device", apps_dir)
    assert [item["app_id"] for item in items] == ["app2", "app1"]
    app1 = items[1]
    assert app1["visit_count"] == 7
    assert app1["visit_breakdown"] == {"landing": 1, "install": 1, "pwa": 1, "launch": 1}
    assert app1["download_count"] == 2
    assert app1["download_breakdown"] == {"android": 1, "unknown": 1}
    assert app1["icon_url"] == "/a/app1/icon.png"
    assert items[0]["icon_url"] is None
    assert "_custom_icon_data_url" not in app1["recipe"]
    assert "edit_token" not in app1["recipe"]

    exported = store.export_history("device", apps_dir)
    assert exported["version"] == 1
    by_id = {item["app_id"]: item for item in exported["items"]}
    assert by_id["app1"]["icon_data_url"] == "data:image/png;base64,cG5n"
    assert by_id["app2"]["icon_data_url"] is None
    by_id["app1"]["recipe"]["name"] = "mutated"
    assert app1["recipe"]["name"] != "mutated"


def test_history_visit_auto_flush_row_decoding_and_device_json_errors(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    store._pending_limit = 2
    store.record_visit("orphan", "landing")
    assert store._conn.execute("SELECT * FROM visits WHERE app_id='orphan'").fetchone() is None
    store.record_visit("orphan", "landing")
    assert store._conn.execute("SELECT total FROM visits WHERE app_id='orphan'").fetchone()[0] == 2

    store._conn.execute(
        "INSERT INTO devices(device_id, app_ids_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("broken", "not-json", "now", "now"),
    )
    assert store._get_device_app_ids_locked("missing") == []
    assert store._get_device_app_ids_locked("broken") == []
    store._set_device_app_ids_locked("broken", ["", None, "ok"], "later")
    assert store._get_device_app_ids_locked("broken") == ["ok"]
    store._set_device_app_ids_locked("broken", [], "latest")
    assert store._get_device_app_ids_locked("broken") == []

    app_row = {
        "app_id": "bad",
        "name": "",
        "target_url": "https://target.example",
        "public_path": "",
        "runtime_url": "",
        "color": "",
        "recipe_json": "not-json",
        "created_at": None,
        "updated_at": None,
    }
    snapshot = store._app_row_to_snapshot(app_row)
    assert snapshot["recipe"] == {}
    assert snapshot["name"] == "bad"
    assert snapshot["public_path"] == "/a/bad"
    assert snapshot["runtime_url"] == "https://target.example"
    assert snapshot["color"] == "#7c3aed"

    assert store._visit_row_to_stats(None) == store._visit_entry()
    visit_row = {
        "total": None,
        "landing": None,
        "install": None,
        "pwa": None,
        "launch": None,
        "downloads_json": "not-json",
        "last_visited_at": None,
    }
    assert store._visit_row_to_stats(visit_row)["downloads"] == {}


def test_history_update_recipe_new_existing_and_runtime_choices(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    store.update_recipe({})
    store.update_recipe(_recipe("new"), public_path="/public/new", runtime_url="https://run.example")
    original_created = store._conn.execute("SELECT created_at FROM apps WHERE app_id='new'").fetchone()[0]
    store.update_recipe(_recipe("new", name="Updated"))
    row = store._conn.execute("SELECT * FROM apps WHERE app_id='new'").fetchone()
    assert row["created_at"] == original_created
    assert row["public_path"] == "/public/new"
    assert row["runtime_url"] == "https://run.example"
    store.update_recipe(_recipe("new"), public_path="/replacement", runtime_url="")
    row = store._conn.execute("SELECT * FROM apps WHERE app_id='new'").fetchone()
    assert row["public_path"] == "/replacement"
    assert row["runtime_url"] == ""
    store.update_recipe(_recipe("defaulted", name="", color=""))
    row = store._conn.execute("SELECT * FROM apps WHERE app_id='defaulted'").fetchone()
    assert row["name"] == "defaulted"
    assert row["public_path"] == "/a/defaulted"
    assert row["color"] == "#7c3aed"


def test_history_import_snapshot_merges_and_uses_fallbacks(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    store.import_snapshot("device", {}, {}, None, None)
    snapshot = {
        "app_id": "imported",
        "name": "Snapshot Name",
        "target_url": "https://snapshot.example",
        "public_path": "/snapshot/path",
        "runtime_url": "https://snapshot-runtime.example",
        "color": "#fedcba",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2021-01-01T00:00:00Z",
        "total_activity_count": 9,
        "visit_count": 2,
        "visit_breakdown": {"landing": 3, "install": 2, "pwa": 1, "launch": 4},
        "download_breakdown": {"android": 5},
        "last_visited_at": "2022-01-01T00:00:00Z",
    }
    recipe = _recipe("imported", _custom_icon_data_url="secret", edit_token="secret")
    store.import_snapshot("device", snapshot, recipe)
    item = store.list_history("device", tmp_path)[0]
    assert item["name"] == "Snapshot Name"
    assert item["visit_count"] == 9
    assert item["visit_breakdown"]["launch"] == 4
    assert item["download_breakdown"] == {"android": 5}
    assert "edit_token" not in item["recipe"]

    lower_and_new = {
        "visit_count": 4,
        "visit_breakdown": {"landing": 1, "install": 8},
        "download_breakdown": {"android": 2, "ios": 7},
        "last_visited_at": "2020-01-01T00:00:00Z",
    }
    store.import_snapshot(None, lower_and_new, _recipe("imported", name="Recipe Name"), "/explicit", "")
    row = store._conn.execute("SELECT * FROM apps WHERE app_id='imported'").fetchone()
    stats = store._visit_row_to_stats(store._conn.execute("SELECT * FROM visits WHERE app_id='imported'").fetchone())
    # The explicit arguments win at storage time even over the existing row.
    # (_app_row_to_snapshot applies a display fallback to target_url, so the
    # raw row is the right place to assert storage semantics.)
    assert row["public_path"] == "/explicit"
    assert row["runtime_url"] == ""
    assert stats["total"] == 9
    assert stats["install"] == 8
    assert stats["downloads"] == {"android": 5, "ios": 7}
    assert stats["last_visited_at"] == "2022-01-01T00:00:00Z"

    store.import_snapshot(None, {}, _recipe("imported", name=""))
    row = store._conn.execute("SELECT * FROM apps WHERE app_id='imported'").fetchone()
    # Empty name in both snapshot and recipe falls back to the existing row
    # name, which the previous import set to "Recipe Name".
    assert row["name"] == "Recipe Name"
    assert row["target_url"].startswith("https://example.com")
    assert row["public_path"] == "/explicit"
    assert row["runtime_url"].startswith("https://example.com")

    store.import_snapshot(
        None,
        {"app_id": "snapshot-only", "visit_count": 1},
        {"name": "No recipe id", "url": "https://only.example"},
    )
    assert store._conn.execute("SELECT 1 FROM apps WHERE app_id='snapshot-only'").fetchone()


def test_history_counts_removal_expiry_purge_and_stats(tmp_path):
    store = HistoryStore(tmp_path / "history.sqlite3")
    apps_dir = tmp_path / "apps"
    for app_id in ("old", "new", "bad", "visited-old"):
        store.record_build("device", _recipe(app_id), f"/a/{app_id}", None)
    store._set_device_app_ids_locked("device", ["ghost", "bad", "new", "old", "visited-old"])
    store._conn.execute("UPDATE apps SET created_at=?, updated_at=? WHERE app_id='old'", ("2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"))
    store._conn.execute("UPDATE apps SET created_at=?, updated_at=? WHERE app_id='new'", ("2030-01-01T00:00:00Z", "2030-01-02T00:00:00Z"))
    store._conn.execute("UPDATE apps SET created_at=?, updated_at=? WHERE app_id='bad'", ("invalid", "invalid"))
    store._conn.execute("UPDATE apps SET created_at=?, updated_at=? WHERE app_id='visited-old'", ("2030-01-01T00:00:00Z", "2030-01-02T00:00:00Z"))
    store._conn.execute(
        "INSERT INTO visits(app_id, total, landing, install, pwa, launch, downloads_json, last_visited_at) VALUES (?,0,0,0,0,0,'{}',?)",
        ("visited-old", "2019-01-01T00:00:00Z"),
    )

    assert store.count_recent_builds(None, "2024-01-01T00:00:00Z") == 0
    assert store.count_recent_builds("device", "invalid") == 0
    assert store.count_recent_builds("device", "2024-01-01T00:00:00Z") == 2
    assert store.list_expired_apps("invalid") == []
    expired = store.list_expired_apps("2024-01-01T00:00:00Z")
    assert [item["app_id"] for item in expired] == ["visited-old", "old"]

    assert store.remove_from_device(None, "old") is False
    assert store.remove_from_device("device", "") is False
    assert store.remove_from_device("device", "absent") is False
    assert store.remove_from_device("device", "old") is True
    assert store.remove_from_device("device", "old") is False

    store.record_visit("pending-only", "landing")
    store._conn.execute(
        "INSERT INTO visits(app_id,total,landing,install,pwa,launch,downloads_json,last_visited_at) VALUES ('visit-only',1,0,0,0,0,'{}',NULL)"
    )
    store._conn.execute(
        "INSERT INTO devices(device_id,app_ids_json,created_at,updated_at) VALUES ('unchanged','[\"new\"]','x','x')"
    )
    store._conn.execute(
        "INSERT INTO devices(device_id,app_ids_json,created_at,updated_at) VALUES ('invalid-json','oops','x','x')"
    )
    assert store.purge_apps(["", None]) == 0
    assert store.purge_apps(["old", "visit-only", "pending-only", "missing"]) == 3
    assert "pending-only" not in store._pending_visits
    assert store._get_device_app_ids_locked("unchanged") == ["new"]
    assert store._get_device_app_ids_locked("invalid-json") == []
    assert store.purge_apps(["missing"]) == 0
    stats = store.stats()
    assert stats["backend"] == "sqlite"
    assert stats["db_path"] == str(tmp_path / "history.sqlite3")
    assert stats["apps"] == 3
    assert stats["devices"] >= 1

    assert store.export_history(None, apps_dir)["items"] == []
