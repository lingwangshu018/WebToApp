"""Trusted Web Activity builder used by the optional Android TWA runtime.

The normal WebToApp Android path is a tiny android.webkit.WebView shell.  TWA
mode is deliberately kept separate: it uses Google's Bubblewrap CLI to build a
real Trusted Web Activity and reuses WebToApp's per-app signing key so Digital
Asset Links stay stable across rebuilds.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from server.engine.apk_builder import ApkBuilder


class TwaBuilder:
    """Build a signed, sticky-immersive TWA APK and its assetlinks.json."""

    def __init__(self):
        self.apk_builder = ApkBuilder()
        self.root = Path(__file__).resolve().parents[2]
        self.tools_dir = self.root / "server" / "engine" / "_android_tools"

    def _bubblewrap_command(self):
        direct = shutil.which("bubblewrap")
        if direct:
            return [direct]
        local = self.tools_dir / "bubblewrap" / "node_modules" / ".bin" / "bubblewrap"
        if local.exists():
            return [str(local)]
        return None

    @property
    def can_build(self):
        return bool(
            self._bubblewrap_command()
            and self.apk_builder.sdk
            and shutil.which("java")
            and shutil.which("keytool")
        )

    @staticmethod
    def _start_url(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if parsed.fragment:
            path += "#" + parsed.fragment
        return path

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            raise ValueError("TWA requires an absolute HTTPS URL")
        return f"https://{parsed.netloc}"

    @staticmethod
    def _launcher_name(name: str) -> str:
        value = str(name or "App").strip() or "App"
        return value[:12]

    def _manifest(self, *, url, name, pkg, color, version_code, version_name,
                  keystore, alias, icon_url):
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or not parsed.netloc:
            raise ValueError("TWA requires an absolute HTTPS URL")
        color = str(color or "#000000")
        return {
            "packageId": pkg,
            "host": parsed.netloc,
            "name": str(name or "App"),
            "launcherName": self._launcher_name(name),
            "display": "fullscreen-sticky",
            "themeColor": color,
            "themeColorDark": color,
            "navigationColor": color,
            "navigationColorDark": color,
            "navigationDividerColor": color,
            "navigationDividerColorDark": color,
            "backgroundColor": color,
            "enableNotifications": False,
            "startUrl": self._start_url(url),
            "iconUrl": icon_url,
            "maskableIconUrl": icon_url,
            "splashScreenFadeOutDuration": 200,
            "signingKey": {"path": str(keystore), "alias": alias},
            "appVersionCode": max(1, int(version_code or 1)),
            "appVersion": str(version_name or "1.0"),
            "shortcuts": [],
            "generatorApp": "WebToApp",
            "fallbackType": "customtabs",
            "features": {},
            "alphaDependencies": {"enabled": False},
            "enableSiteSettingsShortcut": True,
            "isChromeOSOnly": False,
            "isMetaQuest": False,
            "minSdkVersion": 21,
            "orientation": "any",
            "fingerprints": [],
            "additionalTrustedOrigins": [],
            "retainedBundles": [],
            "displayOverride": [],
        }

    @staticmethod
    def _certificate_fingerprint(keystore: Path, password: str, alias: str) -> str:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cert = Path(tmp_dir) / "cert.der"
            subprocess.run(
                [
                    "keytool", "-exportcert",
                    "-keystore", str(keystore),
                    "-storepass", password,
                    "-alias", alias,
                    "-file", str(cert),
                ],
                check=True,
                capture_output=True,
            )
            digest = hashlib.sha256(cert.read_bytes()).hexdigest().upper()
        return ":".join(digest[i:i + 2] for i in range(0, len(digest), 2))

    @staticmethod
    def assetlinks_json(pkg: str, fingerprint: str) -> str:
        payload = [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": pkg,
                    "sha256_cert_fingerprints": [fingerprint],
                },
            }
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def build(self, output, *, url, name, pkg, color, version_code=1,
              version_name="1.0", app_id=None, icon_url=None,
              assetlinks_output=None):
        """Build a real TWA APK.

        Returns metadata on success and ``None`` when Bubblewrap/Android tools
        are unavailable or the build fails.  A caller can then fall back to a
        different runtime without pretending the result is a TWA.
        """
        if not self.can_build:
            return None
        try:
            self._origin(url)
            keystore, password, alias = self.apk_builder._ensure_app_keystore(app_id or pkg)
            fingerprint = self._certificate_fingerprint(keystore, password, alias)
            icon_url = str(icon_url or "").strip()
            if not icon_url:
                parsed = urlparse(url)
                icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            if assetlinks_output is None:
                assetlinks_output = output.parent / "assetlinks.json"
            assetlinks_output = Path(assetlinks_output)

            with tempfile.TemporaryDirectory(prefix="webtoapp-twa-") as tmp_dir:
                work = Path(tmp_dir)
                manifest = self._manifest(
                    url=url,
                    name=name,
                    pkg=pkg,
                    color=color,
                    version_code=version_code,
                    version_name=version_name,
                    keystore=keystore,
                    alias=alias,
                    icon_url=icon_url,
                )
                (work / "twa-manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                command = self._bubblewrap_command()
                env = os.environ.copy()
                env["BUBBLEWRAP_KEYSTORE_PASSWORD"] = password
                env["BUBBLEWRAP_KEY_PASSWORD"] = password
                if self.apk_builder.sdk:
                    env["ANDROID_HOME"] = self.apk_builder.sdk
                    env["ANDROID_SDK_ROOT"] = self.apk_builder.sdk

                subprocess.run(
                    command + ["update", "--skipVersionUpgrade", f"--manifest={work}"],
                    cwd=work,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    command + [
                        "build",
                        "--skipPwaValidation",
                        f"--manifest={work}",
                        f"--signingKeyPath={keystore}",
                        f"--signingKeyAlias={alias}",
                    ],
                    cwd=work,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                signed = work / "app-release-signed.apk"
                if not signed.exists():
                    raise RuntimeError("Bubblewrap did not produce app-release-signed.apk")
                shutil.copy2(signed, output)

            assetlinks_output.write_text(
                self.assetlinks_json(pkg, fingerprint),
                encoding="utf-8",
            )
            return {
                "apk": True,
                "fallback": False,
                "runtime": "twa_immersive",
                "twa_verified_origin": self._origin(url),
                "assetlinks_file": assetlinks_output.name,
                "package_name": pkg,
                "sha256_cert_fingerprint": fingerprint,
            }
        except Exception as exc:
            print(f"[TwaBuilder] build failed: {exc}")
            return None
