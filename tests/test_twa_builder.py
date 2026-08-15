import json
from pathlib import Path
from unittest.mock import patch

from server.engine.twa_builder import TwaBuilder
from server.engine.distiller import Distiller


def test_twa_manifest_requests_sticky_fullscreen(tmp_path):
    builder = TwaBuilder()
    data = builder._manifest(
        url="https://example.com/chat?a=1",
        name="Example Phone",
        pkg="com.example.phone",
        color="#123456",
        version_code=7,
        version_name="1.2.3",
        keystore=tmp_path / "app.keystore",
        alias="appkey",
        icon_url="https://example.com/icon.png",
    )
    assert data["display"] == "fullscreen-sticky"
    assert data["fallbackType"] == "customtabs"
    assert data["host"] == "example.com"
    assert data["startUrl"] == "/chat?a=1"
    assert data["packageId"] == "com.example.phone"


def test_assetlinks_targets_generated_package_and_fingerprint():
    raw = TwaBuilder.assetlinks_json("com.example.phone", "AA:BB")
    data = json.loads(raw)
    assert data[0]["relation"] == ["delegate_permission/common.handle_all_urls"]
    assert data[0]["target"]["package_name"] == "com.example.phone"
    assert data[0]["target"]["sha256_cert_fingerprints"] == ["AA:BB"]


def test_distiller_routes_twa_mode_to_twa_builder(tmp_path):
    distiller = Distiller()
    recipe = {
        "id": "abc12345",
        "name": "Phone",
        "color": "#123456",
        "android_package_prefix": "com.example",
        "android_version_code": 1,
        "android_version_name": "1.0",
        "options": {"feature-twa-mode": True, "feature-edge-mode": False},
    }
    expected = {"apk": True, "fallback": False, "runtime": "twa_immersive"}
    with patch("server.engine.distiller.TwaBuilder.build", return_value=expected) as build:
        result = distiller._build_android(
            tmp_path,
            recipe,
            b"png",
            "https://example.com/app",
            base_url="https://builder.example",
        )
    assert result == expected
    kwargs = build.call_args.kwargs
    assert kwargs["icon_url"] == "https://builder.example/a/abc12345/icon.png"
    assert Path(kwargs["assetlinks_output"]).name == "assetlinks.json"
