# WebToApp — Turn websites into apps

**English** · [简体中文](README.zh.md) · [日本語](README.ja.md) · [العربية](README.ar.md) · [Русский](README.ru.md) · [Español](README.es.md) · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Enter a URL and, seconds later, get a finished product you can install, share and use like an app.
A single generated result covers **iPhone / iPad, Android, Windows, macOS and Linux**.

Open source · Free · No sign-up.

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

## Security notes

- All secrets (R2, Cloudflare, signing passwords) are read from environment variables; the repository contains no real credentials.
- **Signing private keys (`certs/*.keystore`, `certs/app-keys/`) and runtime data (`generated/`) are excluded by `.gitignore` by default — never commit them.**
- Each generated Android app uses its own independent signing certificate, which avoids the certificate fingerprint being flagged en masse and ensures the same app can be updated in place.

## License

[MIT](LICENSE)
