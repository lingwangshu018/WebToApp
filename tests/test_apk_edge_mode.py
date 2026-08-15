import json

from server.engine.apk_builder import ACTIVITY_JAVA, ApkBuilder


def test_config_json_defaults_to_system_webview(tmp_path):
    builder = ApkBuilder()
    payload = json.loads(builder._config_json("https://example.com", {}))
    assert payload["browser_runtime"] == "webview"


def test_config_json_can_select_edge(tmp_path):
    builder = ApkBuilder()
    payload = json.loads(builder._config_json(
        "https://example.com", {"feature-edge-mode": True}
    ))
    assert payload["browser_runtime"] == "edge_custom_tab"


def test_edge_mode_uses_custom_tab_with_session_sharing_hints():
    assert "com.microsoft.emmx" in ACTIVITY_JAVA
    assert "android.support.customtabs.extra.SESSION" in ACTIVITY_JAVA
    assert "android.support.customtabs.extra.ENABLE_URLBAR_HIDING" in ACTIVITY_JAVA
    assert "edge_custom_tab" in ACTIVITY_JAVA
