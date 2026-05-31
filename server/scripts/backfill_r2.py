"""
One-off backfill: upload existing apps' download artifacts to Cloudflare R2
and record the public URLs in each app's recipe.json (``downloads_cdn``).

After this runs, the /a/{id}/download/{platform} endpoint will 302-redirect
old apps to the R2 CDN just like freshly-built ones.

Idempotent: re-running re-uploads (overwrites) and refreshes the URL map.
Pass --dry-run to preview without uploading or writing.

Run on the server, where the R2_* env vars are loaded and generated/ lives:

    set -a; . /www/wwwroot/web-to-app-7/webtoapp.env; set +a
    venv/bin/python -m server.scripts.backfill_r2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from server import config
from server.engine.storage import r2_storage

APPS_DIR = Path(__file__).resolve().parents[2] / "generated"


def iter_app_dirs():
    if not APPS_DIR.exists():
        return
    for recipe_path in sorted(APPS_DIR.glob("*/recipe.json")):
        yield recipe_path.parent, recipe_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill existing app downloads to R2.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; no upload/write.")
    args = parser.parse_args()

    if not config.r2_configured():
        print("ERROR: R2 is not configured (R2_* env vars missing). Aborting.", file=sys.stderr)
        print("Hint: set -a; . /www/wwwroot/web-to-app-7/webtoapp.env; set +a", file=sys.stderr)
        return 1

    print(f"R2 bucket   : {config.r2_bucket()}")
    print(f"Public base : {config.r2_public_base_url()}")
    print(f"Apps dir    : {APPS_DIR}")
    print(f"Mode        : {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("-" * 60)

    total_apps = 0
    uploaded_apps = 0
    skipped_apps = 0
    total_files = 0
    errors = 0

    for app_dir, recipe_path in iter_app_dirs():
        app_id = app_dir.name
        total_apps += 1
        downloads_dir = app_dir / "downloads"

        files = sorted(p.name for p in downloads_dir.iterdir() if p.is_file()) if downloads_dir.exists() else []
        if not files:
            print(f"[skip] {app_id}: no download files")
            skipped_apps += 1
            continue

        try:
            recipe = json.loads(recipe_path.read_text())
        except Exception as exc:
            print(f"[ERR ] {app_id}: cannot read recipe.json ({exc})")
            errors += 1
            continue

        if args.dry_run:
            print(f"[plan] {app_id}: would upload {len(files)} file(s): {', '.join(files)}")
            total_files += len(files)
            continue

        try:
            urls = r2_storage.upload_app_downloads(app_id, downloads_dir)
        except Exception as exc:
            print(f"[ERR ] {app_id}: upload failed ({exc})")
            errors += 1
            continue

        if not urls:
            print(f"[skip] {app_id}: nothing uploaded")
            skipped_apps += 1
            continue

        # Merge into any existing map so we never drop previously-known URLs.
        existing = recipe.get("downloads_cdn") or {}
        existing.update(urls)
        recipe["downloads_cdn"] = existing
        recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2))

        uploaded_apps += 1
        total_files += len(urls)
        print(f"[ok  ] {app_id}: {len(urls)} file(s) -> R2 ({', '.join(sorted(urls))})")

    print("-" * 60)
    print(f"Apps scanned : {total_apps}")
    print(f"Apps updated : {uploaded_apps}")
    print(f"Apps skipped : {skipped_apps}")
    print(f"Files done   : {total_files}")
    print(f"Errors       : {errors}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
