import json

from server.engine.apk_builder import ApkBuilder
from server.engine.distiller import Distiller


def test_distiller_preserves_edge_runtime_flag():
    options = Distiller()._feature_options({"feature-edge-mode": True})
    assert options["feature-edge-mode"] is True
    assert options["feature-twa-mode"] is False


def test_twa_wins_if_both_runtime_flags_are_present():
    options = Distiller()._feature_options({"feature-edge-mode": True, "feature-twa-mode": True})
    assert options["feature-edge-mode"] is False
    assert options["feature-twa-mode"] is True


def test_apk_config_serializes_all_runtime_modes():
    builder = ApkBuilder()
    webview = json.loads(builder._config_json("https://example.com", {}))
    edge = json.loads(builder._config_json("https://example.com", {"feature-edge-mode": True}))
    twa = json.loads(builder._config_json("https://example.com", {"feature-twa-mode": True}))
    assert webview["browser_runtime"] == "webview"
    assert edge["browser_runtime"] == "edge_custom_tab"
    assert twa["browser_runtime"] == "twa_immersive"
