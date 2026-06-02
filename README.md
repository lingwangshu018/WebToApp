<div align="center">

<img src="assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**Turn any website into an installable app — in seconds.**

One link in, finished products out for **iPhone / iPad · Android · Windows · macOS · Linux**.

[![Live Demo](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![License: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](LICENSE)
[![Platforms](https://img.shields.io/badge/Platforms-5-736357?style=for-the-badge)](#features)

**English** · [简体中文](docs/README.zh.md) · [日本語](docs/README.ja.md) · [العربية](docs/README.ar.md) · [Русский](docs/README.ru.md) · [Español](docs/README.es.md) · [Português](docs/README.pt.md) · [Français](docs/README.fr.md) · [Deutsch](docs/README.de.md)

</div>

---

<div align="center">
  <img src="assets/screenshot-1.png" alt="WebToApp screenshot" width="420">
  <img src="assets/screenshot-2.png" alt="WebToApp screenshot" width="420">
  <br>
  <img src="assets/screenshot-3.png" alt="WebToApp screenshot" width="420">
  <img src="assets/screenshot-4.png" alt="WebToApp screenshot" width="420">
</div>

---

Enter a URL and, seconds later, get a finished product you can install, share and use like an app.
A single generated result covers **iPhone / iPad, Android, Windows, macOS and Linux**, and each one is only a few KB — so it downloads and installs almost instantly.

Open source · Free · No sign-up. Try it live at **[shiaho.sbs](https://shiaho.sbs)**.

---

## Features

- **Site analysis**: fetches the target page and extracts the name, theme color and icon, and counts ads / trackers / popups (display-only estimates).
- **Multi-platform packaging**: builds installers for five platforms at once
  - **Android** — a real, installable WebView APK (v1+v2+v3 signed). Each app uses its **own dedicated signing certificate**.
  - **iOS** — a `.mobileconfig` Web Clip profile, with optional CMS signing using a public-CA certificate ("signature-free" install).
  - **Windows / macOS / Linux** — lightweight launchers with a native icon.
- **iOS dynamic URL swap**: the Web Clip points at `/a/<id>/launch`, so you can change the target URL on the server without reinstalling.
- **History**: build history is saved per device fingerprint, with export / import to other devices.
- **Auto cleanup**: apps with no visits for 30 days are automatically reclaimed.
- **Optional Cloudflare R2 offload**: downloads go through the CDN, saving origin bandwidth.
- **Multilingual UI**: 9 built-in languages (English, Simplified Chinese, Japanese, Arabic, Russian, Spanish, Portuguese, French, German). The UI defaults to English and can be switched manually from the top-right corner, with RTL layout for Arabic.

## App size

Each package is just a thin entry point to your site — it bundles no site content, so the artifacts are measured in **kilobytes, not megabytes**. Under the hood it uses each platform's native lightweight shell: an Android WebView APK, an iOS Web Clip profile, and `.app` / `.bat` / `.desktop` launchers that open the system browser in app mode on desktop.

Measured on a real build (figures are representative; they barely vary by site):

| Platform | Package | Typical size | What's inside |
| --- | --- | --- | --- |
| Android | `android.apk` | **~21 KB** | A real, installable WebView APK (v1+v2+v3 signed) |
| iOS / iPadOS | `ios.mobileconfig` | **~4 KB** | A Web Clip configuration profile |
| macOS | `macos.zip` | **~1.4 KB** | A `.app` bundle (launcher script + icon) |
| Windows | `windows.zip` | **~1.2 KB** | A `.bat` launcher + desktop-shortcut helper + icon |
| Linux | `linux.tar.gz` | **~0.7 KB** | A `.desktop` entry + install script + icon |

## Tech stack

- Backend: Python + FastAPI + Uvicorn
- Frontend: plain HTML / CSS / JS (static files served directly by the backend)
- Packaging toolchain: Android SDK (aapt2 / d8 / apksigner / zipalign), apktool, Pillow, openssl

## Project structure

```
.
├── index.html              Homepage
├── css/ js/ assets/        Frontend static assets
│   └── js/i18n.js          Lightweight i18n runtime
│       js/i18n.strings.js  Translations for 9 languages
├── server/
│   ├── main.py             FastAPI app and routes
│   ├── config.py           Environment-variable configuration
│   ├── history_store.py    Per-device history store (JSON)
│   └── engine/
│       ├── analyzer.py     Site analysis
│       ├── distiller.py    Generates the per-platform packages (core)
│       ├── apk_builder.py  Android APK build and signing
│       ├── mobileconfig_signer.py  iOS profile signing
│       ├── storage.py      Cloudflare R2 offload
│       └── recipe.py       Sample recipe data
├── certs/                  Signing material (private keys are not committed)
└── generated/              Runtime-generated apps and data (not committed)
```

## Quick start

Requires Python 3.10+. Building an Android APK requires the Android SDK and `apktool` (it falls back to a PWA offline package when they are missing).

```bash
# 1. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. Configure (optional, everything has defaults)
cp .env.example .env
# Edit .env as needed

# 3. Run
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

> No environment variables are needed for local development. When deploying publicly, set `PUBLIC_BASE_URL`,
> otherwise iPhones cannot open `localhost`. See [`.env.example`](.env.example) for the full list.

## Deployment

> For a complete step-by-step production guide (systemd, Nginx, HTTPS, Android/iOS, R2), see **[docs/DEPLOY.md](docs/DEPLOY.md)**.

In production it is common to run it under systemd, behind an Nginx reverse proxy:

```ini
# /etc/systemd/system/webtoapp.service
[Unit]
Description=WebToApp
After=network.target

[Service]
WorkingDirectory=/path/to/web-to-app
Environment=PUBLIC_BASE_URL=https://your-domain.com
ExecStart=/path/to/web-to-app/venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

For iOS profile signing ("signature-free" install), see the certificate setup in [`certs/README.md`](certs/README.md).

## How Cloudflare R2 offload works

Generated installers (APK / ZIP / `.mobileconfig`) can be large, and serving every download from the origin burns its bandwidth. When R2 is configured:

1. **After each build**, every file in `generated/<app_id>/downloads/` is mirrored to R2 under the key `<app_id>/downloads/<filename>` (`server/engine/storage.py`), and the resulting public URLs are written into the app's `recipe.json` as a `downloads_cdn` map.
2. **On download**, `GET /a/<id>/download/<platform>` prefers the CDN URL in `downloads_cdn` and returns a **302 redirect** to R2; if absent, it falls back to streaming the local file. The origin therefore spends CPU during builds, not bandwidth on every share or QR scan.
3. **On cleanup**, an app's objects under `<app_id>/` are removed from R2 alongside its local data.

If any `R2_*` variable is unset the feature is a no-op and downloads are served locally — nothing breaks. Existing apps built before R2 was enabled can be migrated with `python -m server.scripts.backfill_r2`. Full setup steps (bucket, API token, public access, custom domain, backfill) are in [docs/DEPLOY.md §11](docs/DEPLOY.md#11-cloudflare-r2-offload-optional).

## Security notes

- All secrets (R2, Cloudflare, signing passwords) are read from environment variables; the repository contains no real credentials.
- **Signing private keys (`certs/*.keystore`, `certs/app-keys/`) and runtime data (`generated/`) are excluded by `.gitignore` by default — never commit them.**
- Each generated Android app uses its own independent signing certificate, which avoids the certificate fingerprint being flagged en masse and ensures the same app can be updated in place.

## License

[MIT](LICENSE)
