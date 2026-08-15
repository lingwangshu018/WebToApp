"""Aggregate Digital Asset Links for TWA apps hosted by this WebToApp instance.

WebToApp serves the project root through its catch-all StaticFiles mount.  By
materializing ``.well-known/assetlinks.json`` at the root, uploaded HTML apps
that are hosted under ``/a/<id>/site/...`` can verify their TWA association
without the user manually copying a file into another web host.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

_LOCK = threading.RLock()
_HOSTED_SITE_RE = re.compile(r"^/a/(?P<app_id>[A-Za-z0-9_-]+)/site(?:/|$)")


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _generated_root() -> Path:
    return _root() / "generated"


def registry_path() -> Path:
    return _root() / ".well-known" / "assetlinks.json"


def is_hosted_site_url(url: str, app_id: str | None = None) -> bool:
    """Return True for the HTML-app URLs served by WebToApp itself."""
    try:
        parsed = urlparse(str(url or ""))
    except Exception:
        return False
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return False
    match = _HOSTED_SITE_RE.match(parsed.path or "/")
    if not match:
        return False
    return app_id is None or match.group("app_id") == str(app_id)


def _valid_statement(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    target = value.get("target")
    if not isinstance(target, dict) or target.get("namespace") != "android_app":
        return None
    package_name = str(target.get("package_name") or "").strip()
    fingerprints = target.get("sha256_cert_fingerprints")
    if not package_name or not isinstance(fingerprints, list):
        return None
    cleaned = [str(item).strip() for item in fingerprints if str(item).strip()]
    if not cleaned:
        return None
    return {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": package_name,
            "sha256_cert_fingerprints": cleaned,
        },
    }


def _iter_generated_statements() -> Iterable[dict]:
    generated = _generated_root()
    if not generated.is_dir():
        return
    for assetlinks in generated.glob("*/downloads/assetlinks.json"):
        app_id = assetlinks.parents[1].name
        recipe_path = assetlinks.parents[1] / "recipe.json"
        # Existing completed builds are only auto-published when the target is
        # one of this server's hosted HTML sites. External origins still get
        # their per-app downloadable assetlinks.json but must publish it there.
        if recipe_path.exists():
            try:
                recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not is_hosted_site_url(recipe.get("url"), app_id):
                continue
        try:
            payload = json.loads(assetlinks.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, list):
            continue
        for item in payload:
            statement = _valid_statement(item)
            if statement:
                yield statement


def rebuild_registry(extra_statement: dict | None = None) -> Path | None:
    """Rebuild the root Digital Asset Links file from live generated apps.

    ``extra_statement`` is used by the TWA builder before recipe.json has been
    persisted. This keeps the just-built app in the registry on its first
    successful build while still letting later rebuilds prune removed apps.
    """
    with _LOCK:
        statements = list(_iter_generated_statements() or [])
        extra = _valid_statement(extra_statement) if extra_statement else None
        if extra:
            statements.append(extra)

        # One package should have one current statement. Rebuilds replace the
        # previous certificate association deterministically.
        by_package: dict[str, dict] = {}
        for statement in statements:
            package_name = statement["target"]["package_name"]
            by_package[package_name] = statement
        payload = [by_package[key] for key in sorted(by_package)]

        path = registry_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
            return path
        except OSError as exc:
            # A read-only deployment should not make APK generation fail. The
            # per-app assetlinks.json is still produced and can be published by
            # the site owner manually.
            print(f"[AssetLinksRegistry] unable to publish root assetlinks.json: {exc}")
            return None
