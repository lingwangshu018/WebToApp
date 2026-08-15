from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'marker not found in {path}: {old[:160]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

replace_once(
    'server/main.py',
    '    "ios": ("ios.mobileconfig", "application/x-apple-aspen-config"),\n',
    '    "ios": ("ios.mobileconfig", "application/x-apple-aspen-config"),\n    "assetlinks": ("assetlinks.json", "application/json"),\n',
)

replace_once(
    'server/engine/distiller.py',
    '''        platform_rows = [
            ("iPhone / iPad", "apple", f"{base}/download/ios", "platIosDetail", "actionInstall", ""),
            ("Android", "android", f"{base}/download/android", android_detail_key, "actionDownload", android_badge),
            ("macOS", "apple", f"{base}/download/macos", "platMacDetail", "actionDownload", ""),
            ("Windows", "windows", f"{base}/download/windows", "platWinDetail", "actionDownload", ""),
            ("Linux", "linux", f"{base}/download/linux", "platLinuxDetail", "actionDownload", ""),
        ]
''',
    '''        platform_rows = [
            ("iPhone / iPad", "apple", f"{base}/download/ios", "platIosDetail", "actionInstall", ""),
            ("Android", "android", f"{base}/download/android", android_detail_key, "actionDownload", android_badge),
            ("macOS", "apple", f"{base}/download/macos", "platMacDetail", "actionDownload", ""),
            ("Windows", "windows", f"{base}/download/windows", "platWinDetail", "actionDownload", ""),
            ("Linux", "linux", f"{base}/download/linux", "platLinuxDetail", "actionDownload", ""),
        ]
        if (app_dir / "downloads" / "assetlinks.json").exists():
            platform_rows.insert(
                2,
                ("TWA assetlinks.json", "android", f"{base}/download/assetlinks", "platTwaAssetlinksDetail", "actionDownload", ""),
            )
''',
)

# Add fallback translations for the verification file shown only on TWA builds.
replace_once(
    'server/engine/distiller.py',
    '                "platAndroidZipDetail": ".zip · lightweight PWA package",\n',
    '                "platAndroidZipDetail": ".zip · lightweight PWA package",\n                "platTwaAssetlinksDetail": "Deploy this file as /.well-known/assetlinks.json on the wrapped site to verify fullscreen TWA ownership",\n',
)
replace_once(
    'server/engine/distiller.py',
    '                "platAndroidZipDetail": ".zip · 轻量 PWA 包",\n',
    '                "platAndroidZipDetail": ".zip · 轻量 PWA 包",\n                "platTwaAssetlinksDetail": "把此文件部署到目标站点的 /.well-known/assetlinks.json，用于验证 TWA 全屏权限",\n',
)

# Deployment docs: explain the selectable runtime and optional TWA dependency.
p = Path('docs/DEPLOY.zh.md')
text = p.read_text(encoding='utf-8')
needle = '**没有 SDK 时**，跳过 APK 生成，安卓用户改为获得可安装的 PWA 包——其余功能照常工作。\n'
addition = '''**没有 SDK 时**，跳过 APK 生成，安卓用户改为获得可安装的 PWA 包——其余功能照常工作。

### Android 运行模式

生成器现在可以为每个应用单独选择 Android 运行方式：

- **System WebView**：默认模式，继续使用系统 `android.webkit.WebView`。
- **Microsoft Edge shared session**：通过 Edge Custom Tab 打开，优先复用 Edge 的 Cookie / 登录状态。
- **TWA immersive fullscreen**：使用 Bubblewrap 生成真正的 Trusted Web Activity，并请求 `fullscreen-sticky` 沉浸模式。

TWA 模式额外需要 **Node.js + npm**。再次运行 `server/scripts/install_android_sdk.sh` 时，如果系统存在 `npm`，脚本会把固定版本的 Bubblewrap 安装到 WebToApp 自己的 `_android_tools` 目录；`/api/metrics` 中的 `features.android_twa` 可用来确认服务器是否具备真实 TWA 构建能力。

TWA 构建成功后，下载目录会多出 `assetlinks.json`，下载页也会显示它。把这个文件部署到目标站点的：

```text
/.well-known/assetlinks.json
```

文件中的包名和 SHA-256 证书指纹由 WebToApp 按当前应用的稳定签名自动生成。站点未完成 Digital Asset Links 验证时，浏览器会按 TWA 机制退回带浏览器 UI 的 Custom Tab；因此不要把“APK 已生成”误认为“站点已验证”。
'''
if needle not in text:
    raise SystemExit('deploy doc marker missing')
p.write_text(text.replace(needle, addition, 1), encoding='utf-8')

Path('tests/test_twa_assetlinks_download.py').write_text('''from server.main import DOWNLOAD_TYPES\n\n\ndef test_assetlinks_is_downloadable_from_app_page():\n    assert DOWNLOAD_TYPES[\"assetlinks\"] == (\"assetlinks.json\", \"application/json\")\n''', encoding='utf-8')
