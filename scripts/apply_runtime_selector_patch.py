from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'marker not found in {path}: {old[:140]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# UI: add TWA as a first-class selectable Android runtime.
replace_once('index.html', '''                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.edgeTitle">Microsoft Edge shared session</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.edgeDesc">Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling; true zero-UI fullscreen still requires a verified TWA site.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.edgeTitle" aria-label="Microsoft Edge mode">
                    <input id="feature-edge-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>''', '''                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.edgeTitle">Microsoft Edge shared session</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.edgeDesc">Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.edgeTitle" aria-label="Microsoft Edge shared session">
                    <input id="feature-edge-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>

                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.twaTitle">TWA immersive fullscreen</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.twaDesc">Build this site as a verified Trusted Web Activity with sticky immersive fullscreen. The site must publish the generated Digital Asset Links file; otherwise the browser falls back to a Custom Tab.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.twaTitle" aria-label="TWA immersive fullscreen">
                    <input id="feature-twa-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>''')

# Frontend config + mutual exclusion.
replace_once('js/app.v5.js', "  const edgeModeInput = document.getElementById('feature-edge-mode');\n", "  const edgeModeInput = document.getElementById('feature-edge-mode');\n  const twaModeInput = document.getElementById('feature-twa-mode');\n")
replace_once('js/app.v5.js', '''    const edgeMode = options['feature-edge-mode'] === true || options.feature_edge_mode === true || options.browser_runtime === 'edge';
    return {
      immersiveFullscreen,
      desktopMode,
      edgeMode,
    };''', '''    const twaMode = options['feature-twa-mode'] === true || options.feature_twa_mode === true || options.browser_runtime === 'twa_immersive';
    const edgeMode = !twaMode && (options['feature-edge-mode'] === true || options.feature_edge_mode === true || options.browser_runtime === 'edge' || options.browser_runtime === 'edge_custom_tab');
    return {
      immersiveFullscreen,
      desktopMode,
      edgeMode,
      twaMode,
    };''')
replace_once('js/app.v5.js', '''    if (edgeModeInput) edgeModeInput.checked = options.edgeMode;
  }

  function collectFeatureOptions() {''', '''    if (edgeModeInput) edgeModeInput.checked = options.edgeMode;
    if (twaModeInput) twaModeInput.checked = options.twaMode;
  }

  if (edgeModeInput && twaModeInput) {
    edgeModeInput.addEventListener('change', () => {
      if (edgeModeInput.checked) twaModeInput.checked = false;
    });
    twaModeInput.addEventListener('change', () => {
      if (twaModeInput.checked) edgeModeInput.checked = false;
    });
  }

  function collectFeatureOptions() {''')
replace_once('js/app.v5.js', '''      'feature-edge-mode': Boolean(edgeModeInput && edgeModeInput.checked),
    });
    return {
      'feature-immersive-fullscreen': featureOptions.immersiveFullscreen,
      'feature-desktop-mode': featureOptions.desktopMode,
      'feature-edge-mode': featureOptions.edgeMode,
    };''', '''      'feature-edge-mode': Boolean(edgeModeInput && edgeModeInput.checked),
      'feature-twa-mode': Boolean(twaModeInput && twaModeInput.checked),
    });
    return {
      'feature-immersive-fullscreen': featureOptions.immersiveFullscreen,
      'feature-desktop-mode': featureOptions.desktopMode,
      'feature-edge-mode': featureOptions.edgeMode,
      'feature-twa-mode': featureOptions.twaMode,
    };''')

# English fallback strings.
replace_once('js/i18n.strings.js', "    'config.edgeDesc': 'Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling. True zero-UI fullscreen requires a verified Trusted Web Activity site.',\n", "    'config.edgeDesc': 'Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling.',\n    'config.twaTitle': 'TWA immersive fullscreen',\n    'config.twaDesc': 'Build this site as a verified Trusted Web Activity with sticky immersive fullscreen. The site must publish the generated Digital Asset Links file; otherwise the browser falls back to a Custom Tab.',\n")

# The real recipe pipeline previously dropped Edge mode entirely. Preserve both runtime flags.
replace_once('server/engine/distiller.py', '''            "feature-desktop-mode": bool(
                raw.get("feature-desktop-mode") or raw.get("feature_desktop_mode")
            ),
        }''', '''            "feature-desktop-mode": bool(
                raw.get("feature-desktop-mode") or raw.get("feature_desktop_mode")
            ),
            "feature-edge-mode": bool(
                raw.get("feature-edge-mode") or raw.get("feature_edge_mode")
            ) and not bool(raw.get("feature-twa-mode") or raw.get("feature_twa_mode")),
            "feature-twa-mode": bool(
                raw.get("feature-twa-mode") or raw.get("feature_twa_mode")
            ),
        }''')

# APK config recognizes the new runtime. TWA build routing is added separately; keep serialization correct now.
replace_once('server/engine/apk_builder.py', '''            "browser_runtime": "edge_custom_tab" if bool(
                raw.get("feature-edge-mode") or raw.get("feature_edge_mode")
            ) else "webview",
''', '''            "browser_runtime": (
                "twa_immersive" if bool(raw.get("feature-twa-mode") or raw.get("feature_twa_mode"))
                else "edge_custom_tab" if bool(raw.get("feature-edge-mode") or raw.get("feature_edge_mode"))
                else "webview"
            ),
''')

# Cache-bust frontend assets.
p = Path('index.html')
text = p.read_text(encoding='utf-8')
text = text.replace('js/app.v5.js?v=20260815-edge1', 'js/app.v5.js?v=20260815-runtime2')
text = text.replace('js/i18n.strings.js?v=20260815-edge2', 'js/i18n.strings.js?v=20260815-runtime2')
p.write_text(text, encoding='utf-8')

# Tests cover the real recipe pipeline and mutual runtime serialization.
Path('tests/test_android_runtime_modes.py').write_text('''import json\n\nfrom server.engine.apk_builder import ApkBuilder\nfrom server.engine.distiller import Distiller\n\n\ndef test_distiller_preserves_edge_runtime_flag():\n    options = Distiller()._feature_options({\"feature-edge-mode\": True})\n    assert options[\"feature-edge-mode\"] is True\n    assert options[\"feature-twa-mode\"] is False\n\n\ndef test_twa_wins_if_both_runtime_flags_are_present():\n    options = Distiller()._feature_options({\"feature-edge-mode\": True, \"feature-twa-mode\": True})\n    assert options[\"feature-edge-mode\"] is False\n    assert options[\"feature-twa-mode\"] is True\n\n\ndef test_apk_config_serializes_all_runtime_modes():\n    builder = ApkBuilder()\n    webview = json.loads(builder._config_json(\"https://example.com\", {}))\n    edge = json.loads(builder._config_json(\"https://example.com\", {\"feature-edge-mode\": True}))\n    twa = json.loads(builder._config_json(\"https://example.com\", {\"feature-twa-mode\": True}))\n    assert webview[\"browser_runtime\"] == \"webview\"\n    assert edge[\"browser_runtime\"] == \"edge_custom_tab\"\n    assert twa[\"browser_runtime\"] == \"twa_immersive\"\n''', encoding='utf-8')
