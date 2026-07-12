#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.engine.distiller import Distiller


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate download page.html for existing apps")
    parser.add_argument("--apps-dir", default=str(ROOT / "generated"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--app-id", action="append", default=[])
    args = parser.parse_args()
    apps_dir = Path(args.apps_dir)
    distiller = Distiller()
    paths = []
    if args.app_id:
        paths = [apps_dir / app_id / "recipe.json" for app_id in args.app_id]
    else:
        paths = sorted(apps_dir.glob("*/recipe.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if args.limit and args.limit > 0:
        paths = paths[: args.limit]
    ok = 0
    failed = 0
    for recipe_path in paths:
        if not recipe_path.exists():
            failed += 1
            continue
        app_dir = recipe_path.parent
        try:
            recipe = json.loads(recipe_path.read_text())
            distiller._write_download_page(app_dir, recipe)
            ok += 1
            print(f"ok {app_dir.name}")
        except Exception as exc:
            failed += 1
            print(f"fail {app_dir.name}: {exc}", file=sys.stderr)
    print(f"done ok={ok} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
