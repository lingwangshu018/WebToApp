from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'marker not found in {path}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


replace_once('index.html',
'''                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.desktopTitle">Desktop mode</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.desktopDesc">Visit the site with a desktop browser identity. Good for dashboards, consoles and some video pages.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.desktopTitle" aria-label="Desktop mode">
                    <input id="feature-desktop-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>''',
'''                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.desktopTitle">Desktop mode</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.desktopDesc">Visit the site with a desktop browser identity. Good for dashboards, consoles and some video pages.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.desktopTitle" aria-label="Desktop mode">
                    <input id="feature-desktop-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>

                <section class="feature-card">
                  <div class="feature-copy">
                    <div class="feature-heading-row">
                      <strong data-i18n="config.edgeTitle">Microsoft Edge mode</strong>
                      <span class="feature-tag">Android</span>
                    </div>
                    <p data-i18n="config.edgeDesc">Open the generated Android app's target URL in Microsoft Edge. This uses the real Edge app instead of Android System WebView.</p>
                  </div>
                  <label class="switch" data-i18n-aria-label="config.edgeTitle" aria-label="Microsoft Edge mode">
                    <input id="feature-edge-mode" type="checkbox">
                    <span class="switch-ui"></span>
                  </label>
                </section>''')

p = Path('index.html')
text = p.read_text(encoding='utf-8')
text = text.replace('js/app.v5.js?v=20260814-html1', 'js/app.v5.js?v=20260815-edge1')
text = text.replace('js/i18n.strings.js?v=20260814-html1', 'js/i18n.strings.js?v=20260815-edge1')
p.write_text(text, encoding='utf-8')

replace_once('js/app.v5.js',
"  const desktopModeInput = document.getElementById('feature-desktop-mode');\n",
"  const desktopModeInput = document.getElementById('feature-desktop-mode');\n  const edgeModeInput = document.getElementById('feature-edge-mode');\n")

replace_once('js/app.v5.js',
"    const desktopMode = options['feature-desktop-mode'] === true || options.feature_desktop_mode === true;\n    return {\n      immersiveFullscreen,\n      desktopMode,\n    };",
"    const desktopMode = options['feature-desktop-mode'] === true || options.feature_desktop_mode === true;\n    const edgeMode = options['feature-edge-mode'] === true || options.feature_edge_mode === true || options.browser_runtime === 'edge';\n    return {\n      immersiveFullscreen,\n      desktopMode,\n      edgeMode,\n    };")

replace_once('js/app.v5.js',
"    immersiveFullscreenInput.checked = options.immersiveFullscreen;\n    desktopModeInput.checked = options.desktopMode;\n",
"    immersiveFullscreenInput.checked = options.immersiveFullscreen;\n    desktopModeInput.checked = options.desktopMode;\n    if (edgeModeInput) edgeModeInput.checked = options.edgeMode;\n")

replace_once('js/app.v5.js',
"      'feature-desktop-mode': desktopModeInput.checked,\n",
"      'feature-desktop-mode': desktopModeInput.checked,\n      'feature-edge-mode': Boolean(edgeModeInput && edgeModeInput.checked),\n")

replace_once('js/app.v5.js',
"      'feature-desktop-mode': featureOptions.desktopMode,\n",
"      'feature-desktop-mode': featureOptions.desktopMode,\n      'feature-edge-mode': featureOptions.edgeMode,\n")

replace_once('js/i18n.strings.js',
"    'config.desktopDesc': 'Visit the site with a desktop browser identity. Good for dashboards, consoles and some video pages.',\n",
"    'config.desktopDesc': 'Visit the site with a desktop browser identity. Good for dashboards, consoles and some video pages.',\n    'config.edgeTitle': 'Microsoft Edge mode',\n    'config.edgeDesc': 'Open the generated Android app in Microsoft Edge instead of Android System WebView. If Edge is unavailable, Android falls back to another browser; if that also fails, the embedded WebView is used.',\n")

replace_once('server/engine/apk_builder.py',
"        config = loadConfig();\n        webView = new WebView(this);\n",
"        config = loadConfig();\n        if (config != null && \"edge\".equals(config.browserRuntime) && launchPreferredBrowser(config.url)) {\n            finish();\n            return;\n        }\n        webView = new WebView(this);\n")

replace_once('server/engine/apk_builder.py',
"    private String sanitizeUserAgent(String ua) {\n",
'''    private boolean launchPreferredBrowser(String url) {
        if (url == null || url.trim().isEmpty()) return false;
        String target = url.trim();
        try {
            Intent edge = new Intent(Intent.ACTION_VIEW, Uri.parse(target));
            edge.addCategory(Intent.CATEGORY_BROWSABLE);
            edge.setPackage("com.microsoft.emmx");
            startActivity(edge);
            return true;
        } catch (Throwable ignored) {}
        try {
            Intent fallback = new Intent(Intent.ACTION_VIEW, Uri.parse(target));
            fallback.addCategory(Intent.CATEGORY_BROWSABLE);
            fallback.setComponent(null);
            startActivity(fallback);
            return true;
        } catch (Throwable ignored) {}
        return false;
    }

    private String sanitizeUserAgent(String ua) {
''')

replace_once('server/engine/apk_builder.py',
"            loaded.desktopMode = json.optBoolean(\"desktop_mode\", false);\n",
"            loaded.desktopMode = json.optBoolean(\"desktop_mode\", false);\n            loaded.browserRuntime = json.optString(\"browser_runtime\", \"webview\").trim().toLowerCase(Locale.US);\n")

replace_once('server/engine/apk_builder.py',
"        boolean desktopMode = false;\n",
"        boolean desktopMode = false;\n        String browserRuntime = \"webview\";\n")

replace_once('server/engine/apk_builder.py',
'''            "desktop_mode": bool(
                raw.get("feature-desktop-mode") or raw.get("feature_desktop_mode")
            ),
''',
'''            "desktop_mode": bool(
                raw.get("feature-desktop-mode") or raw.get("feature_desktop_mode")
            ),
            "browser_runtime": "edge" if bool(
                raw.get("feature-edge-mode") or raw.get("feature_edge_mode")
            ) else "webview",
''')

p = Path('server/engine/apk_builder.py')
text = p.read_text(encoding='utf-8')
text = text.replace('TEMPLATE_REVISION = "2026-06-03-adblock-1"', 'TEMPLATE_REVISION = "2026-08-15-edge-runtime-1"')
p.write_text(text, encoding='utf-8')

Path('tests/test_apk_edge_mode.py').write_text('''import json\n\nfrom server.engine.apk_builder import ApkBuilder\n\n\ndef test_config_json_defaults_to_system_webview(tmp_path):\n    builder = ApkBuilder(tmp_path)\n    payload = json.loads(builder._config_json("https://example.com", {}))\n    assert payload["browser_runtime"] == "webview"\n\n\ndef test_config_json_can_select_edge(tmp_path):\n    builder = ApkBuilder(tmp_path)\n    payload = json.loads(builder._config_json(\n        "https://example.com", {"feature-edge-mode": True}\n    ))\n    assert payload["browser_runtime"] == "edge"\n''', encoding='utf-8')
