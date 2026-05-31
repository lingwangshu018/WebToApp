<div align="center">

<img src="assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**ウェブサイトを数秒でインストール可能なアプリに。**

リンクを 1 つ入力すると、**iPhone / iPad · Android · Windows · macOS · Linux** 向けの完成品が手に入ります。

[![ライブデモ](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![ライセンス: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](LICENSE)
[![プラットフォーム](https://img.shields.io/badge/Platforms-5-736357?style=for-the-badge)](#features)

[English](README.md) · [简体中文](README.zh.md) · **日本語** · [العربية](README.ar.md) · [Русский](README.ru.md) · [Español](README.es.md) · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="assets/screenshot-1.png" alt="WebToApp スクリーンショット" width="860">
  <br><br>
  <img src="assets/screenshot-2.png" alt="WebToApp スクリーンショット" width="430">
  <img src="assets/screenshot-3.png" alt="WebToApp スクリーンショット" width="430">
  <br>
  <img src="assets/screenshot-4.png" alt="WebToApp スクリーンショット" width="860">
</div>

---

URL を入力すると、数秒後にインストール・共有でき、アプリのように使える完成品が手に入ります。
1 回の生成結果で **iPhone / iPad、Android、Windows、macOS、Linux** をまとめてカバーします。

オープンソース · 無料 · 登録不要。ライブデモ：**[shiaho.sbs](https://shiaho.sbs)**。

---

## 機能

- **サイト分析**：対象ページを取得し、名前・テーマカラー・アイコンを抽出し、広告／トラッカー／ポップアップを集計します（表示用の概算値）。
- **マルチプラットフォーム・パッケージング**：5 つのプラットフォーム向けインストーラーを一度に生成
  - **Android** — 実際にインストール可能な WebView APK（v1+v2+v3 署名）。各アプリは**専用の署名証明書**を使用します。
  - **iOS** — `.mobileconfig` Web Clip プロファイル。公的 CA 証明書による CMS 署名にも対応（「署名不要」インストール）。
  - **Windows / macOS / Linux** — ネイティブアイコン付きの軽量ランチャー。
- **iOS の動的 URL 切り替え**：Web Clip は `/a/<id>/launch` を指すため、サーバー側で対象 URL を変更すれば再インストール不要です。
- **履歴**：デバイスフィンガープリントごとにビルド履歴を保存し、他のデバイスへエクスポート／インポートできます。
- **自動クリーンアップ**：30 日間アクセスのないアプリは自動的に回収されます。
- **任意の Cloudflare R2 オフロード**：ダウンロードを CDN 経由にして、オリジンの帯域を節約します。
- **多言語 UI**：9 言語を内蔵（英語、簡体字中国語、日本語、アラビア語、ロシア語、スペイン語、ポルトガル語、フランス語、ドイツ語）。ブラウザの言語に自動追従し、アラビア語は RTL レイアウトに対応。右上から手動で切り替えできます。

## 技術スタック

- バックエンド：Python + FastAPI + Uvicorn
- フロントエンド：素の HTML / CSS / JS（静的ファイルをバックエンドが直接配信）
- パッケージングツールチェーン：Android SDK（aapt2 / d8 / apksigner / zipalign）、apktool、Pillow、openssl

## ディレクトリ構成

```
.
├── index.html              トップページ
├── css/ js/ assets/        フロントエンドの静的アセット
│   └── js/i18n.js          軽量 i18n ランタイム
│       js/i18n.strings.js  9 言語の翻訳リソース
├── server/
│   ├── main.py             FastAPI アプリとルーティング
│   ├── config.py           環境変数の設定
│   ├── history_store.py    デバイス履歴ストア（JSON）
│   └── engine/
│       ├── analyzer.py     サイト分析
│       ├── distiller.py    各プラットフォーム用パッケージの生成（コア）
│       ├── apk_builder.py  Android APK のビルドと署名
│       ├── mobileconfig_signer.py  iOS プロファイル署名
│       ├── storage.py      Cloudflare R2 オフロード
│       └── recipe.py       サンプルレシピデータ
├── certs/                  署名素材（秘密鍵はコミットしない）
└── generated/              実行時に生成されるアプリとデータ（コミットしない）
```

## クイックスタート

Python 3.10 以上が必要です。Android APK のビルドには Android SDK と `apktool` が必要です（未導入の場合は PWA オフラインパッケージに自動フォールバックします）。

```bash
# 1. 仮想環境を作成し依存関係をインストール
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. 設定（任意。すべてデフォルト値あり）
cp .env.example .env
# 必要に応じて .env を編集

# 3. 起動
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

http://127.0.0.1:8000 を開きます。

> ローカル開発では環境変数は不要です。公開デプロイ時は `PUBLIC_BASE_URL` を設定してください。
> 設定しないと iPhone から `localhost` を開けません。全変数は [`.env.example`](.env.example) を参照してください。

## デプロイ

本番環境では、Nginx リバースプロキシの背後で systemd により管理するのが一般的です。

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

iOS プロファイル署名（「署名不要」インストール）の証明書設定は [`certs/README.md`](certs/README.md) を参照してください。

## セキュリティに関する注意

- すべての秘密情報（R2、Cloudflare、署名パスワード）は環境変数から読み込まれ、リポジトリには実際の認証情報は含まれません。
- **署名用の秘密鍵（`certs/*.keystore`、`certs/app-keys/`）と実行時データ（`generated/`）はデフォルトで `.gitignore` により除外されています。決してコミットしないでください。**
- 生成される各 Android アプリは独立した署名証明書を使用するため、証明書のフィンガープリントが一括で誤検知されるのを防ぎ、同じアプリを上書き更新できることを保証します。

## ライセンス

[MIT](LICENSE)
