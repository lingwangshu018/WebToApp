"""
Lightweight JSON-backed history store for device-linked build history.
"""

import base64
import json
import threading
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(raw: Optional[str]) -> Optional[datetime]:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class HistoryStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self._state = None
        self._dirty = False
        self._pending_visits = defaultdict(lambda: {"total": 0, "landing": 0, "install": 0, "pwa": 0, "launch": 0, "downloads": defaultdict(int), "last_visited_at": None})
        self._pending_limit = 64
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_state(self._default_state())
        self._state = self._read_state()

    def _default_state(self) -> dict:
        return {
            "devices": {},
            "apps": {},
            "visits": {},
        }

    def _read_state(self) -> dict:
        if not self.path.exists():
            return self._default_state()
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return self._default_state()

    def _write_state(self, state: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        tmp.replace(self.path)

    def _get_state_locked(self) -> dict:
        if self._state is None:
            self._state = self._read_state()
        return self._state

    def _mark_dirty_locked(self) -> None:
        self._dirty = True

    def _flush_locked(self) -> None:
        state = self._get_state_locked()
        if self._pending_visits:
            visits = state.setdefault("visits", {})
            for app_id, delta in list(self._pending_visits.items()):
                stats = visits.setdefault(app_id, self._visit_entry())
                stats["total"] = int(stats.get("total", 0)) + int(delta.get("total", 0))
                for key in ("landing", "install", "pwa", "launch"):
                    stats[key] = int(stats.get(key, 0)) + int(delta.get(key, 0))
                downloads = stats.setdefault("downloads", {})
                for platform, count in (delta.get("downloads") or {}).items():
                    downloads[platform] = int(downloads.get(platform, 0)) + int(count)
                if delta.get("last_visited_at"):
                    stats["last_visited_at"] = delta["last_visited_at"]
            self._pending_visits.clear()
            self._dirty = True
        if self._dirty:
            self._write_state(state)
            self._dirty = False

    def flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _visit_entry(self) -> dict:
        return {
            "total": 0,
            "landing": 0,
            "install": 0,
            "pwa": 0,
            "launch": 0,
            "downloads": {},
            "last_visited_at": None,
        }

    def _merge_visit_stats(self, existing: dict, imported: dict) -> dict:
        merged = self._visit_entry()
        merged["total"] = max(int(existing.get("total", 0)), int(imported.get("total", 0)))
        for key in ("landing", "install", "pwa", "launch"):
            merged[key] = max(int(existing.get(key, 0)), int(imported.get(key, 0)))
        existing_downloads = existing.get("downloads") or {}
        imported_downloads = imported.get("downloads") or {}
        downloads = {}
        for key in set(existing_downloads.keys()) | set(imported_downloads.keys()):
            downloads[key] = max(int(existing_downloads.get(key, 0)), int(imported_downloads.get(key, 0)))
        merged["downloads"] = downloads
        merged["last_visited_at"] = max(existing.get("last_visited_at") or "", imported.get("last_visited_at") or "") or None
        return merged

    def _snapshot_from_recipe(self, recipe: dict, public_path: str, runtime_url: Optional[str]) -> dict:
        safe_recipe = deepcopy(recipe)
        safe_recipe.pop("_custom_icon_data_url", None)
        # edit_token is a secret that gates URL hot-swaps; it must never travel
        # in history snapshots (served via /api/history and export/import).
        safe_recipe.pop("edit_token", None)
        return {
            "app_id": recipe.get("id"),
            "name": recipe.get("name") or recipe.get("id"),
            "target_url": recipe.get("url") or "",
            "public_path": public_path,
            "runtime_url": runtime_url or recipe.get("url") or "",
            "color": recipe.get("color") or "#7c3aed",
            "display": recipe.get("display") or "fullscreen",
            "orientation": recipe.get("orientation") or "any",
            "android_version_code": recipe.get("android_version_code"),
            "android_version_name": recipe.get("android_version_name"),
            "android_package_prefix": recipe.get("android_package_prefix"),
            "custom_icon_uploaded": bool(recipe.get("custom_icon_uploaded")),
            "recipe": safe_recipe,
        }

    def record_build(self, device_fingerprint: Optional[str], recipe: dict, public_path: str, runtime_url: Optional[str]) -> None:
        app_id = str(recipe.get("id") or "").strip()
        if not app_id:
            return
        now = _utc_now()
        with self._lock:
            state = self._get_state_locked()
            previous = state["apps"].get(app_id, {})
            snapshot = self._snapshot_from_recipe(recipe, public_path, runtime_url)
            snapshot["created_at"] = previous.get("created_at") or now
            snapshot["updated_at"] = now
            state["apps"][app_id] = snapshot
            state["visits"].setdefault(app_id, self._visit_entry())
            if device_fingerprint:
                self._attach_app_locked(state, device_fingerprint, app_id, now)
            self._mark_dirty_locked()
            self._flush_locked()

    def _attach_app_locked(self, state: dict, device_fingerprint: str, app_id: str, now: str) -> None:
        device = state["devices"].setdefault(
            device_fingerprint,
            {"app_ids": [], "created_at": now, "updated_at": now},
        )
        ordered = [value for value in device.get("app_ids", []) if value != app_id]
        ordered.insert(0, app_id)
        device["app_ids"] = ordered
        device["updated_at"] = now

    def attach_app(self, device_fingerprint: Optional[str], app_id: str) -> None:
        if not device_fingerprint or not app_id:
            return
        now = _utc_now()
        with self._lock:
            state = self._get_state_locked()
            self._attach_app_locked(state, device_fingerprint, app_id, now)
            self._mark_dirty_locked()
            self._flush_locked()

    def update_recipe(self, recipe: dict, public_path: Optional[str] = None, runtime_url: Optional[str] = None) -> None:
        app_id = str(recipe.get("id") or "").strip()
        if not app_id:
            return
        now = _utc_now()
        with self._lock:
            state = self._get_state_locked()
            previous = state["apps"].get(app_id, {})
            snapshot = self._snapshot_from_recipe(
                recipe,
                public_path or previous.get("public_path") or f"/a/{app_id}",
                runtime_url or previous.get("runtime_url"),
            )
            snapshot["created_at"] = previous.get("created_at") or now
            snapshot["updated_at"] = now
            state["apps"][app_id] = snapshot
            state["visits"].setdefault(app_id, self._visit_entry())
            self._mark_dirty_locked()
            self._flush_locked()

    def import_snapshot(
        self,
        device_fingerprint: Optional[str],
        snapshot: dict,
        recipe: dict,
        public_path: Optional[str] = None,
        runtime_url: Optional[str] = None,
    ) -> None:
        app_id = str(recipe.get("id") or snapshot.get("app_id") or "").strip()
        if not app_id:
            return
        now = _utc_now()
        imported_visit_breakdown = snapshot.get("visit_breakdown") or {}
        imported_downloads = snapshot.get("download_breakdown") or {}
        imported_visits = {
            "total": int(snapshot.get("total_activity_count", snapshot.get("visit_count", 0)) or 0),
            "landing": int(imported_visit_breakdown.get("landing", 0) or 0),
            "install": int(imported_visit_breakdown.get("install", 0) or 0),
            "pwa": int(imported_visit_breakdown.get("pwa", 0) or 0),
            "launch": int(imported_visit_breakdown.get("launch", 0) or 0),
            "downloads": {key: int(value or 0) for key, value in imported_downloads.items()},
            "last_visited_at": snapshot.get("last_visited_at"),
        }
        with self._lock:
            state = self._get_state_locked()
            previous = state["apps"].get(app_id, {})
            merged_snapshot = self._snapshot_from_recipe(
                recipe,
                public_path or snapshot.get("public_path") or f"/a/{app_id}",
                runtime_url or snapshot.get("runtime_url") or recipe.get("url"),
            )
            merged_snapshot["created_at"] = previous.get("created_at") or snapshot.get("created_at") or now
            merged_snapshot["updated_at"] = max(previous.get("updated_at") or "", snapshot.get("updated_at") or "", now)
            state["apps"][app_id] = merged_snapshot
            current_visits = state["visits"].get(app_id) or self._visit_entry()
            state["visits"][app_id] = self._merge_visit_stats(current_visits, imported_visits)
            if device_fingerprint:
                self._attach_app_locked(state, device_fingerprint, app_id, now)
            self._mark_dirty_locked()
            self._flush_locked()

    def record_visit(self, app_id: str, channel: str) -> None:
        if not app_id:
            return
        now = _utc_now()
        channel_name = str(channel or "").strip().lower()
        with self._lock:
            delta = self._pending_visits[app_id]
            delta["total"] = int(delta.get("total", 0)) + 1
            if channel_name in {"landing", "install", "pwa", "launch"}:
                delta[channel_name] = int(delta.get(channel_name, 0)) + 1
            elif channel_name.startswith("download:"):
                platform = channel_name.split(":", 1)[1] or "unknown"
                downloads = delta["downloads"]
                downloads[platform] = int(downloads.get(platform, 0)) + 1
            delta["last_visited_at"] = now
            if sum(int(item.get("total", 0)) for item in self._pending_visits.values()) >= self._pending_limit:
                self._flush_locked()

    def list_history(self, device_fingerprint: Optional[str], apps_dir: Path) -> List[dict]:
        if not device_fingerprint:
            return []
        with self._lock:
            self._flush_locked()
            state = self._get_state_locked()
            device = state["devices"].get(device_fingerprint) or {}
            app_ids = device.get("app_ids", [])
            items = []
            for app_id in app_ids:
                snapshot = deepcopy(state["apps"].get(app_id) or {})
                if not snapshot:
                    continue
                stats = deepcopy(state["visits"].get(app_id) or self._visit_entry())
                available = (apps_dir / app_id / "recipe.json").exists()
                snapshot["available"] = available
                snapshot["icon_url"] = f"/a/{app_id}/icon.png" if (apps_dir / app_id / "icon.png").exists() else None
                snapshot["visit_count"] = int(stats.get("landing", 0))
                snapshot["total_activity_count"] = int(stats.get("total", 0))
                snapshot["visit_breakdown"] = {
                    "landing": int(stats.get("landing", 0)),
                    "install": int(stats.get("install", 0)),
                    "pwa": int(stats.get("pwa", 0)),
                    "launch": int(stats.get("launch", 0)),
                }
                snapshot["download_breakdown"] = deepcopy(stats.get("downloads") or {})
                snapshot["download_count"] = int(sum((stats.get("downloads") or {}).values()))
                snapshot["last_visited_at"] = stats.get("last_visited_at")
                items.append(snapshot)
            items.sort(key=lambda entry: entry.get("updated_at") or "", reverse=True)
            return items

    def export_history(self, device_fingerprint: Optional[str], apps_dir: Path) -> dict:
        items = self.list_history(device_fingerprint, apps_dir)
        export_items = []
        for item in items:
            app_id = item.get("app_id")
            icon_path = apps_dir / str(app_id) / "icon.png"
            icon_data_url = None
            if icon_path.exists():
                icon_data_url = "data:image/png;base64," + base64.b64encode(icon_path.read_bytes()).decode("ascii")
            export_items.append(
                {
                    "app_id": app_id,
                    "snapshot": item,
                    "recipe": deepcopy(item.get("recipe") or {}),
                    "icon_data_url": icon_data_url,
                }
            )
        return {
            "version": 1,
            "exported_at": _utc_now(),
            "items": export_items,
        }

    def count_recent_builds(self, device_fingerprint: Optional[str], since_iso: str) -> int:
        """Count distinct apps attached to `device_fingerprint` whose
        `created_at` >= `since_iso`. Repeated builds of the same URL share an
        `app_id` and one `created_at`, so they intentionally don't double-count.
        """
        since = _parse_utc(since_iso)
        if since is None or not device_fingerprint:
            return 0
        with self._lock:
            self._flush_locked()
            state = self._get_state_locked()
            device = state.get("devices", {}).get(device_fingerprint)
            if not device:
                return 0
            count = 0
            for app_id in device.get("app_ids", []):
                snapshot = state.get("apps", {}).get(app_id) or {}
                created = _parse_utc(snapshot.get("created_at"))
                if created and created >= since:
                    count += 1
            return count

    def remove_from_device(self, device_fingerprint: Optional[str], app_id: str) -> bool:
        if not device_fingerprint or not app_id:
            return False
        removed = False
        with self._lock:
            self._flush_locked()
            state = self._get_state_locked()
            device = state.get("devices", {}).get(device_fingerprint)
            if not device:
                return False
            previous = list(device.get("app_ids", []))
            device["app_ids"] = [value for value in previous if value != app_id]
            removed = len(previous) != len(device["app_ids"])
            if not device["app_ids"]:
                state["devices"].pop(device_fingerprint, None)
            else:
                device["updated_at"] = _utc_now()
            self._mark_dirty_locked()
            self._flush_locked()
        return removed

    def list_expired_apps(self, cutoff_iso: str) -> List[dict]:
        cutoff = _parse_utc(cutoff_iso)
        if cutoff is None:
            return []
        with self._lock:
            self._flush_locked()
            state = self._get_state_locked()
            expired = []
            for app_id, snapshot in (state.get("apps") or {}).items():
                stats = state.get("visits", {}).get(app_id) or self._visit_entry()
                last_active_at = (
                    stats.get("last_visited_at")
                    or snapshot.get("updated_at")
                    or snapshot.get("created_at")
                )
                last_active_dt = _parse_utc(last_active_at)
                if last_active_dt is None or last_active_dt >= cutoff:
                    continue
                expired.append(
                    {
                        "app_id": app_id,
                        "name": snapshot.get("name") or app_id,
                        "last_active_at": last_active_at,
                    }
                )
            expired.sort(key=lambda item: item.get("last_active_at") or "")
            return expired

    def purge_apps(self, app_ids: List[str]) -> int:
        purge_ids = {str(app_id or "").strip() for app_id in app_ids if str(app_id or "").strip()}
        if not purge_ids:
            return 0
        removed = 0
        now = _utc_now()
        with self._lock:
            self._flush_locked()
            state = self._get_state_locked()
            apps = state.setdefault("apps", {})
            visits = state.setdefault("visits", {})
            devices = state.setdefault("devices", {})
            for app_id in purge_ids:
                if app_id in apps or app_id in visits:
                    removed += 1
                apps.pop(app_id, None)
                visits.pop(app_id, None)
                self._pending_visits.pop(app_id, None)
            for device_id, device in list(devices.items()):
                previous = list(device.get("app_ids", []))
                filtered = [value for value in previous if value not in purge_ids]
                if len(filtered) == len(previous):
                    continue
                if filtered:
                    device["app_ids"] = filtered
                    device["updated_at"] = now
                else:
                    devices.pop(device_id, None)
            self._mark_dirty_locked()
            self._flush_locked()
        return removed
