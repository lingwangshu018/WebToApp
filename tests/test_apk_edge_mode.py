import json

from server.engine.apk_builder import ApkBuilder


def test_config_json_defaults_to_system_webview(tmp_path):
    builder = ApkBuilder()
    payload = json.loads(builder._config_json("https://example.com", {}))
    assert payload["browser_runtime"] == "webview"


def test_config_json_can_select_edge(tmp_path):
    builder = ApkBuilder()
    payload = json.loads(builder._config_json(
        "https://example.com", {"feature-edge-mode": True}
    ))
    assert payload["browser_runtime"] == "edge"
