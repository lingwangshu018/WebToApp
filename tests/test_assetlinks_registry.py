import json

from server.engine import assetlinks_registry as registry


def _statement(package, fingerprint):
    return {
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": package,
            "sha256_cert_fingerprints": [fingerprint],
        },
    }


def test_hosted_site_url_detection():
    assert registry.is_hosted_site_url(
        "https://apps.example/a/abc12345/site/index.html", "abc12345"
    )
    assert not registry.is_hosted_site_url(
        "https://apps.example/a/other/site/index.html", "abc12345"
    )
    assert not registry.is_hosted_site_url("https://third-party.example/app", "abc12345")
    assert not registry.is_hosted_site_url("http://apps.example/a/abc12345/site/index.html", "abc12345")


def test_rebuild_registry_aggregates_live_hosted_twa_apps(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "_root", lambda: tmp_path)

    hosted = tmp_path / "generated" / "aaa11111"
    hosted_downloads = hosted / "downloads"
    hosted_downloads.mkdir(parents=True)
    (hosted / "recipe.json").write_text(
        json.dumps({"url": "https://apps.example/a/aaa11111/site/index.html"}),
        encoding="utf-8",
    )
    (hosted_downloads / "assetlinks.json").write_text(
        json.dumps([_statement("com.example.one", "AA:11")]),
        encoding="utf-8",
    )

    external = tmp_path / "generated" / "bbb22222"
    external_downloads = external / "downloads"
    external_downloads.mkdir(parents=True)
    (external / "recipe.json").write_text(
        json.dumps({"url": "https://third-party.example/app"}),
        encoding="utf-8",
    )
    (external_downloads / "assetlinks.json").write_text(
        json.dumps([_statement("com.example.external", "BB:22")]),
        encoding="utf-8",
    )

    path = registry.rebuild_registry(_statement("com.example.two", "CC:33"))
    assert path == tmp_path / ".well-known" / "assetlinks.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    packages = [item["target"]["package_name"] for item in payload]
    assert packages == ["com.example.one", "com.example.two"]
    assert "com.example.external" not in packages


def test_rebuild_registry_replaces_duplicate_package(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "_root", lambda: tmp_path)
    path = registry.rebuild_registry(_statement("com.example.phone", "NEW:FF"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload[0]["target"]["package_name"] == "com.example.phone"
    assert payload[0]["target"]["sha256_cert_fingerprints"] == ["NEW:FF"]
