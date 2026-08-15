from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'marker not found in {path}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# Frontend wording: this is specifically a shared Edge session, not an embedded Edge engine.
replace_once(
    'index.html',
    '<strong data-i18n="config.edgeTitle">Microsoft Edge mode</strong>',
    '<strong data-i18n="config.edgeTitle">Microsoft Edge shared session</strong>',
)
replace_once(
    'index.html',
    "<p data-i18n=\"config.edgeDesc\">Open the generated Android app's target URL in Microsoft Edge. This uses the real Edge app instead of Android System WebView.</p>",
    '<p data-i18n="config.edgeDesc">Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling; true zero-UI fullscreen still requires a verified TWA site.</p>',
)

# English fallback strings.
replace_once(
    'js/i18n.strings.js',
    "    'config.edgeTitle': 'Microsoft Edge mode',\n    'config.edgeDesc': 'Open the generated Android app in Microsoft Edge instead of Android System WebView. If Edge is unavailable, Android falls back to another browser; if that also fails, the embedded WebView is used.',\n",
    "    'config.edgeTitle': 'Microsoft Edge shared session',\n    'config.edgeDesc': 'Open the site in an Edge Custom Tab so Edge cookies and browser-bound login state are reused. The toolbar can collapse while scrolling. True zero-UI fullscreen requires a verified Trusted Web Activity site.',\n",
)

# APK runtime: Edge Custom Tab first; preserve older `edge` config values for compatibility.
replace_once(
    'server/engine/apk_builder.py',
    '''        if (config != null && "edge".equals(config.browserRuntime) && launchPreferredBrowser(config.url)) {
            finish();
            return;
        }
''',
    '''        if (config != null
                && ("edge".equals(config.browserRuntime) || "edge_custom_tab".equals(config.browserRuntime))
                && launchEdgeSharedSession(config.url)) {
            finish();
            return;
        }
''',
)

old_method = '''    private boolean launchPreferredBrowser(String url) {
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
'''
new_method = '''    private boolean launchEdgeSharedSession(String url) {
        if (url == null || url.trim().isEmpty()) return false;
        String target = url.trim();

        // Prefer a Microsoft Edge Custom Tab. Custom Tabs are browser-owned,
        // so the page reuses the Edge profile's cookies/session state instead
        // of creating a separate android.webkit.WebView identity. Asking the
        // browser to hide the URL bar allows the toolbar to collapse on scroll.
        try {
            Intent customTab = new Intent(Intent.ACTION_VIEW, Uri.parse(target));
            customTab.addCategory(Intent.CATEGORY_BROWSABLE);
            customTab.setPackage("com.microsoft.emmx");
            android.os.Bundle extras = new android.os.Bundle();
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR2) {
                extras.putBinder("android.support.customtabs.extra.SESSION", null);
            }
            customTab.putExtras(extras);
            customTab.putExtra("android.support.customtabs.extra.ENABLE_URLBAR_HIDING", true);
            customTab.putExtra("android.support.customtabs.extra.EXTRA_ENABLE_INSTANT_APPS", true);
            customTab.putExtra("android.support.customtabs.extra.SHARE_MENU_ITEM", false);
            startActivity(customTab);
            return true;
        } catch (Throwable ignored) {}

        // Edge may be installed but reject/disable Custom Tabs on a device.
        // Fall back to a normal Edge tab before giving Android another browser.
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
'''
replace_once('server/engine/apk_builder.py', old_method, new_method)

replace_once(
    'server/engine/apk_builder.py',
    '''            "browser_runtime": "edge" if bool(
                raw.get("feature-edge-mode") or raw.get("feature_edge_mode")
            ) else "webview",
''',
    '''            "browser_runtime": "edge_custom_tab" if bool(
                raw.get("feature-edge-mode") or raw.get("feature_edge_mode")
            ) else "webview",
''',
)

p = Path('server/engine/apk_builder.py')
text = p.read_text(encoding='utf-8')
text = text.replace('TEMPLATE_REVISION = "2026-08-15-edge-runtime-1"', 'TEMPLATE_REVISION = "2026-08-15-edge-shared-session-2"')
p.write_text(text, encoding='utf-8')

# Expand regression tests to lock down the runtime selection and Custom Tabs path.
p = Path('tests/test_apk_edge_mode.py')
text = p.read_text(encoding='utf-8')
text = text.replace('assert payload["browser_runtime"] == "edge"', 'assert payload["browser_runtime"] == "edge_custom_tab"')
if 'ACTIVITY_JAVA' not in text:
    text = text.replace(
        'from server.engine.apk_builder import ApkBuilder\n',
        'from server.engine.apk_builder import ACTIVITY_JAVA, ApkBuilder\n',
    )
    text += '''\n\ndef test_edge_mode_uses_custom_tab_with_session_sharing_hints():\n    assert \"com.microsoft.emmx\" in ACTIVITY_JAVA\n    assert \"android.support.customtabs.extra.SESSION\" in ACTIVITY_JAVA\n    assert \"android.support.customtabs.extra.ENABLE_URLBAR_HIDING\" in ACTIVITY_JAVA\n    assert \"edge_custom_tab\" in ACTIVITY_JAVA\n'''
p.write_text(text, encoding='utf-8')

# Cache-bust changed frontend strings.
p = Path('index.html')
text = p.read_text(encoding='utf-8')
text = text.replace('js/i18n.strings.js?v=20260815-edge1', 'js/i18n.strings.js?v=20260815-edge2')
p.write_text(text, encoding='utf-8')
