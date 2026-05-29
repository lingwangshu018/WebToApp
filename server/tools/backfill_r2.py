"""
One-shot backfill: upload existing ``generated/<app_id>/downloads/`` artifacts
to Cloudflare R2 and stamp ``downloads_cdn`` into each ``recipe.json``.

Usage (run from project root):

    R2_ACCOUNT_ID=... \
    R2_ACCESS_KEY_ID=... \
    R2_SECRET_ACCESS_KEY=... \
    R2_BUCKET=... \
    R2_PUBLIC_BASE_URL=https://files.example.com \
    python -m server.tools.backfill_r2

Flags:
    --dry-run     Only list what would be uploaded; no network calls.
    --force       Re-upload even if the recipe already lists CDN URLs.
    --app <id>    Limit to a single app id (repeatable).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

from server import config
from server.engine.storage import r2_storage


def _iter_app_dirs(apps_root: Path, only: Iterable[str]) -> Iterable[Path]:
    only_set = {item for item in only if item}
    for recipe_path in sorted(apps_root.glob("*/recipe.json")):
        app_dir = recipe_path.parent
        if only_set and app_dir.name not in only_set:
            continue
        yield app_dir


def _load_recipe(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save_recipe(path: Path, recipe: dict) -> None:
    path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill existing app downloads to Cloudflare R2.")
    parser.add_argument("--dry-run", action="store_true", help="List planned uploads without touching R2.")
    parser.add_argument("--force", action="store_true", help="Re-upload even if recipe already has downloads_cdn.")
    parser.add_argument("--app", action="append", default=[], help="Limit to specific app_id (repeatable).")
    args = parser.parse_args(argv)

    if not config.r2_configured():
        print("[backfill] R2 not configured. Set R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / "
              "R2_SECRET_ACCESS_KEY / R2_BUCKET / R2_PUBLIC_BASE_URL and rerun.")
        return 2

    root = Path(__file__).resolve().parents[2]
    apps_root = root / "generated"
    if not apps_root.exists():
        print(f"[backfill] No generated/ directory at {apps_root}")
        return 0

    total = 0
    uploaded = 0
    skipped = 0
    for app_dir in _iter_app_dirs(apps_root, args.app):
        total += 1
        recipe_path = app_dir / "recipe.json"
        recipe = _load_recipe(recipe_path)
        downloads_dir = app_dir / "downloads"
        existing_cdn = recipe.get("downloads_cdn") or {}
        if existing_cdn and not args.force:
            skipped += 1
            print(f"[skip ] {app_dir.name}: already has {len(existing_cdn)} CDN URLs")
            continue
        if not downloads_dir.exists():
            skipped += 1
            print(f"[skip ] {app_dir.name}: no downloads/ dir")
            continue
        files = sorted(p.name for p in downloads_dir.iterdir() if p.is_file())
        if not files:
            skipped += 1
            print(f"[skip ] {app_dir.name}: downloads/ empty")
            continue
        if args.dry_run:
            print(f"[plan ] {app_dir.name}: would upload {len(files)} files: {', '.join(files)}")
            continue
        try:
            urls = r2_storage.upload_app_downloads(app_dir.name, downloads_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {app_dir.name}: upload failed: {exc}")
            continue
        if not urls:
            skipped += 1
            print(f"[skip ] {app_dir.name}: nothing uploaded")
            continue
        merged = dict(existing_cdn)
        merged.update(urls)
        recipe["downloads_cdn"] = merged
        _save_recipe(recipe_path, recipe)
        uploaded += 1
        print(f"[ok   ] {app_dir.name}: uploaded {len(urls)} files")

    print(
        f"\nDone. apps scanned={total}, uploaded={uploaded}, skipped={skipped}"
        f"{', dry-run' if args.dry_run else ''}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
