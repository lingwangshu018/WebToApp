from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'marker not found in {path}: {old[:160]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Distiller imports the dedicated real-TWA builder.
replace_once(
    'server/engine/distiller.py',
    'from server.engine.apk_builder import ApkBuilder\n',
    'from server.engine.apk_builder import ApkBuilder\nfrom server.engine.twa_builder import TwaBuilder\n',
)

# Give the Android builder access to the public WebToApp origin so Bubblewrap can
# fetch the generated high-resolution icon instead of relying on a site favicon.
replace_once(
    'server/engine/distiller.py',
    '            meta = self._build_android(dl, recipe, icon_png, direct_url)\n',
    '            meta = self._build_android(dl, recipe, icon_png, direct_url, base_url=base_url)\n',
)

old_android = '''    def _build_android(self, dl: Path, r: dict, icon_png, shell_url: str):
        builder = ApkBuilder()
        prefix = r.get("android_package_prefix") or config.android_package_prefix()
        pkg = f"{prefix}.a{r['id']}"
        apk_path = dl / "android.apk"
        zip_path = dl / "android.zip"

        if builder.build_apk(
            str(apk_path),
            shell_url,
            r['name'],
            pkg,
            icon_png,
            version_code=r.get("android_version_code", 1),
            version_name=r.get("android_version_name", "1.0"),
            feature_options=r.get("options") or {},
            app_id=r['id'],
        ):
            if zip_path.exists():
                zip_path.unlink()
            return {"apk": True, "fallback": False}

        builder.build_fallback(str(zip_path), shell_url, r['name'], icon_png, r['color'])
        return {"apk": False, "fallback": True}
'''
new_android = '''    def _build_android(self, dl: Path, r: dict, icon_png, shell_url: str, base_url: Optional[str] = None):
        options = dict(r.get("options") or {})
        prefix = r.get("android_package_prefix") or config.android_package_prefix()
        pkg = f"{prefix}.a{r['id']}"
        apk_path = dl / "android.apk"
        zip_path = dl / "android.zip"

        if options.get("feature-twa-mode"):
            icon_url = None
            if base_url and icon_png:
                icon_url = f"{str(base_url).rstrip('/')}/a/{r['id']}/icon.png"
            twa = TwaBuilder()
            twa_meta = twa.build(
                str(apk_path),
                url=shell_url,
                name=r['name'],
                pkg=pkg,
                color=r.get('color') or '#000000',
                version_code=r.get("android_version_code", 1),
                version_name=r.get("android_version_name", "1.0"),
                app_id=r['id'],
                icon_url=icon_url,
                assetlinks_output=dl / "assetlinks.json",
            )
            if twa_meta:
                if zip_path.exists():
                    zip_path.unlink()
                return twa_meta

            # TWA tooling may be unavailable on a lightweight deployment. Do not
            # silently pretend a WebView is a TWA: produce the safest browser-
            # identity-preserving fallback, an Edge shared-session APK, and mark
            # that fallback explicitly in recipe metadata.
            options["feature-twa-mode"] = False
            options["feature-edge-mode"] = True
            builder = ApkBuilder()
            if builder.build_apk(
                str(apk_path), shell_url, r['name'], pkg, icon_png,
                version_code=r.get("android_version_code", 1),
                version_name=r.get("android_version_name", "1.0"),
                feature_options=options,
                app_id=r['id'],
            ):
                if zip_path.exists():
                    zip_path.unlink()
                return {
                    "apk": True,
                    "fallback": True,
                    "runtime": "edge_custom_tab",
                    "requested_runtime": "twa_immersive",
                    "fallback_reason": "twa_builder_unavailable_or_failed",
                }
        else:
            builder = ApkBuilder()
            if builder.build_apk(
                str(apk_path),
                shell_url,
                r['name'],
                pkg,
                icon_png,
                version_code=r.get("android_version_code", 1),
                version_name=r.get("android_version_name", "1.0"),
                feature_options=options,
                app_id=r['id'],
            ):
                if zip_path.exists():
                    zip_path.unlink()
                return {
                    "apk": True,
                    "fallback": False,
                    "runtime": "edge_custom_tab" if options.get("feature-edge-mode") else "webview",
                }

        builder = ApkBuilder()
        builder.build_fallback(str(zip_path), shell_url, r['name'], icon_png, r['color'])
        return {"apk": False, "fallback": True, "runtime": "pwa_package"}
'''
replace_once('server/engine/distiller.py', old_android, new_android)

# Metrics should expose whether real TWA builds are available on this server.
replace_once(
    'server/main.py',
    '''    apk_builder_ready = False
    try:
        from server.engine.apk_builder import ApkBuilder
        apk_builder_ready = bool(ApkBuilder().can_build_apk)
    except Exception:
        apk_builder_ready = False
''',
    '''    apk_builder_ready = False
    twa_builder_ready = False
    try:
        from server.engine.apk_builder import ApkBuilder
        apk_builder_ready = bool(ApkBuilder().can_build_apk)
    except Exception:
        apk_builder_ready = False
    try:
        from server.engine.twa_builder import TwaBuilder
        twa_builder_ready = bool(TwaBuilder().can_build)
    except Exception:
        twa_builder_ready = False
''',
)
replace_once(
    'server/main.py',
    '            "android_apk": apk_builder_ready,\n',
    '            "android_apk": apk_builder_ready,\n            "android_twa": twa_builder_ready,\n',
)

# Extend the Android SDK helper with a local (non-system-global) Bubblewrap install.
p = Path('server/scripts/install_android_sdk.sh')
text = p.read_text(encoding='utf-8')
text = text.replace(
    'APKTOOL_VERSION="${APKTOOL_VERSION:-2.11.1}"\n',
    'APKTOOL_VERSION="${APKTOOL_VERSION:-2.11.1}"\nBUBBLEWRAP_VERSION="${BUBBLEWRAP_VERSION:-1.24.1}"\n',
    1,
)
text = text.replace(
    'need_cmd keytool\n',
    '''need_cmd keytool

# TWA mode additionally needs Node/npm. Keep ordinary WebView APK builds usable
# when Node is absent; the server will report android_twa=false and gracefully
# fall back to Edge shared-session mode for TWA requests.
HAS_NPM=0
if command -v npm >/dev/null 2>&1; then
  HAS_NPM=1
fi
''',
    1,
)
text = text.replace(
    'chmod +x /usr/local/bin/apktool\n\nexport PATH=',
    '''chmod +x /usr/local/bin/apktool

if [ "$HAS_NPM" = "1" ]; then
  BUBBLEWRAP_DIR="$TOOLS_DIR/bubblewrap"
  mkdir -p "$BUBBLEWRAP_DIR"
  if [ ! -x "$BUBBLEWRAP_DIR/node_modules/.bin/bubblewrap" ]; then
    npm install --prefix "$BUBBLEWRAP_DIR" "@bubblewrap/cli@${BUBBLEWRAP_VERSION}"
  fi
  cat > /usr/local/bin/bubblewrap << EOF3
#!/bin/sh
exec "$BUBBLEWRAP_DIR/node_modules/.bin/bubblewrap" "\\$@"
EOF3
  chmod +x /usr/local/bin/bubblewrap
fi

export PATH=''',
    1,
)
text = text.replace(
    'echo "apktool=$(apktool --version 2>/dev/null || true)"\necho "done"\n',
    'echo "apktool=$(apktool --version 2>/dev/null || true)"\necho "bubblewrap=$(command -v bubblewrap 2>/dev/null || echo unavailable)"\necho "done"\n',
    1,
)
p.write_text(text, encoding='utf-8')

# Real builder tests do not execute Bubblewrap; they validate deterministic
# manifest/DAL generation and Distiller routing via mocks.
Path('tests/test_twa_builder.py').write_text(r'''import json
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
''', encoding='utf-8')
