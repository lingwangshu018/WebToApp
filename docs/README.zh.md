<div align="center">

<img src="../assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**几秒钟把任意网站变成可安装的应用。**

输入一个链接，输出覆盖 **iPhone / iPad · Android · Windows · macOS · Linux** 的成品。

[![在线演示](https://img.shields.io/badge/在线演示-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![许可证: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](../LICENSE)
[![平台](https://img.shields.io/badge/平台-5-736357?style=for-the-badge)](#功能)

[English](../README.md) · **简体中文** · [日本語](README.ja.md) · [العربية](README.ar.md) · [Русский](README.ru.md) · [Español](README.es.md) · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="../assets/screenshot-1.png" alt="WebToApp 截图" width="420">
  <img src="../assets/screenshot-2.png" alt="WebToApp 截图" width="420">
  <br>
  <img src="../assets/screenshot-3.png" alt="WebToApp 截图" width="420">
  <img src="../assets/screenshot-4.png" alt="WebToApp 截图" width="420">
</div>

---

输入一个网址，几秒钟后得到一个可以安装、可以分享、可以像应用一样使用的成品。
一套生成结果同时覆盖 **iPhone / iPad、Android、Windows、macOS、Linux**。

开源 · 免费 · 无需登录。在线体验：**[shiaho.sbs](https://shiaho.sbs)**。

---

## 功能

- **站点分析**：抓取目标页面，提取名称、主题色、图标，并统计广告/追踪器/弹窗（展示用估算）。
- **多平台打包**：一次生成五端安装包
  - **Android** — 真实可安装的 WebView APK（v1+v2+v3 签名）。每个应用使用**独立签名证书**。
  - **iOS** — `.mobileconfig` Web Clip 描述文件，支持用公共 CA 证书做 CMS 签名（“免签”）。
  - **Windows / macOS / Linux** — 带原生图标的轻量启动器。
- **iOS 动态换链**：Web Clip 指向 `/a/<id>/launch`，后台改 URL 无需重装。
- **历史记录**：按设备指纹保存生成历史，支持导出 / 导入到其它设备。
- **自动清理**：连续 30 天无访问的应用会被自动回收。
- **可选 Cloudflare R2 卸载**：下载走 CDN，源站省带宽。
- **多语言界面**：内置 9 种语言（英语、简体中文、日语、阿拉伯语、俄语、西班牙语、葡萄牙语、法语、德语），界面默认英语，右上角可手动切换，阿拉伯语支持 RTL 布局。

## 技术栈

- 后端：Python + FastAPI + Uvicorn
- 前端：原生 HTML / CSS / JS（静态文件，由后端直接托管）
- 打包工具链：Android SDK（aapt2 / d8 / apksigner / zipalign）、apktool、Pillow、openssl

## 目录结构

```
.
├── index.html              首页
├── css/ js/ assets/        前端静态资源
│   └── js/i18n.js          轻量 i18n 运行时
│       js/i18n.strings.js  9 种语言翻译资源
├── server/
│   ├── main.py             FastAPI 应用与路由
│   ├── config.py           环境变量配置
│   ├── history_store.py    设备历史存储（JSON）
│   └── engine/
│       ├── analyzer.py     站点分析
│       ├── distiller.py    生成各平台包（核心）
│       ├── apk_builder.py  Android APK 构建与签名
│       ├── mobileconfig_signer.py  iOS 描述文件签名
│       ├── storage.py      Cloudflare R2 卸载
│       └── recipe.py       示例配方数据
├── certs/                  签名材料（私钥不入库）
└── generated/              运行时生成的应用与数据（不入库）
```

## 快速开始

需要 Python 3.10+。Android APK 构建需要 Android SDK 与 `apktool`（缺失时会自动回退为 PWA 离线包）。

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. 配置（可选，全部有默认值）
cp .env.example .env
# 按需编辑 .env

# 3. 启动
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000 即可。

> 本地调试无需配置任何环境变量。部署到公网时请设置 `PUBLIC_BASE_URL`，
> 否则 iPhone 无法打开 `localhost`。完整变量见 [`.env.example`](../.env.example)。

## 部署

> 完整的生产部署教程（systemd、Nginx、HTTPS、Android/iOS、R2），见 **[DEPLOY.zh.md](DEPLOY.zh.md)**。

生产环境用 systemd 托管，前置 Nginx 反代是常见做法：

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

iOS 描述文件签名（“免签”）的证书配置见 [`certs/README.md`](../certs/README.md)。

## 安全说明

- 所有密钥（R2、Cloudflare、签名口令）均从环境变量读取，仓库内不含任何真实凭证。
- **签名私钥（`certs/*.keystore`、`certs/app-keys/`）和运行时数据（`generated/`）默认被 `.gitignore` 排除，切勿提交。**
- 每个生成的 Android 应用使用各自独立的签名证书，避免证书指纹被批量误杀，并保证同一应用可被覆盖更新。

## 许可证

[MIT](../LICENSE)
