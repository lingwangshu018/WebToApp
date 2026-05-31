<div align="center">

<img src="assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**Превратите любой сайт в устанавливаемое приложение за секунды.**

Одна ссылка на входе — готовые продукты для **iPhone / iPad · Android · Windows · macOS · Linux**.

[![Демо](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![Лицензия: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](LICENSE)
[![Платформы](https://img.shields.io/badge/Platforms-5-736357?style=for-the-badge)](#features)

[English](README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [العربية](README.ar.md) · **Русский** · [Español](README.es.md) · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="assets/screenshot-1.png" alt="WebToApp" width="420">
  <img src="assets/screenshot-2.png" alt="WebToApp" width="420">
  <br>
  <img src="assets/screenshot-3.png" alt="WebToApp" width="420">
  <img src="assets/screenshot-4.png" alt="WebToApp" width="420">
</div>

---

Введите URL и через несколько секунд получите готовый продукт, который можно установить, отправить и использовать как приложение.
Один результат генерации сразу охватывает **iPhone / iPad, Android, Windows, macOS и Linux**.

Открытый код · Бесплатно · Без регистрации. Демо: **[shiaho.sbs](https://shiaho.sbs)**.

---

## Возможности

- **Анализ сайта**: загружает целевую страницу и извлекает название, цвет темы и значок, а также подсчитывает рекламу / трекеры / всплывающие окна (оценки только для отображения).
- **Сборка под несколько платформ**: создаёт установщики для пяти платформ за один раз
  - **Android** — настоящий устанавливаемый WebView APK (подпись v1+v2+v3). Каждое приложение использует **собственный отдельный сертификат подписи**.
  - **iOS** — профиль Web Clip в формате `.mobileconfig`, с опциональной CMS-подписью сертификатом публичного УЦ («установка без подписи»).
  - **Windows / macOS / Linux** — лёгкие лаунчеры с нативным значком.
- **Динамическая смена URL для iOS**: Web Clip указывает на `/a/<id>/launch`, поэтому целевой URL можно изменить на сервере без переустановки.
- **История**: история сборок сохраняется по отпечатку устройства, с экспортом / импортом на другие устройства.
- **Автоочистка**: приложения без посещений в течение 30 дней автоматически удаляются.
- **Опциональная разгрузка через Cloudflare R2**: загрузки идут через CDN, экономя трафик источника.
- **Многоязычный интерфейс**: 9 встроенных языков (английский, упрощённый китайский, японский, арабский, русский, испанский, португальский, французский, немецкий), автоматически следует языку браузера, с RTL-вёрсткой для арабского. Переключение вручную в правом верхнем углу.

## Технологии

- Бэкенд: Python + FastAPI + Uvicorn
- Фронтенд: чистый HTML / CSS / JS (статические файлы, отдаваемые бэкендом напрямую)
- Инструменты сборки: Android SDK (aapt2 / d8 / apksigner / zipalign), apktool, Pillow, openssl

## Структура проекта

```
.
├── index.html              Главная страница
├── css/ js/ assets/        Статические ресурсы фронтенда
│   └── js/i18n.js          Лёгкий runtime i18n
│       js/i18n.strings.js  Переводы на 9 языков
├── server/
│   ├── main.py             Приложение FastAPI и маршруты
│   ├── config.py           Настройка через переменные окружения
│   ├── history_store.py    Хранилище истории по устройствам (JSON)
│   └── engine/
│       ├── analyzer.py     Анализ сайта
│       ├── distiller.py    Генерация пакетов под платформы (ядро)
│       ├── apk_builder.py  Сборка и подпись Android APK
│       ├── mobileconfig_signer.py  Подпись профиля iOS
│       ├── storage.py      Разгрузка через Cloudflare R2
│       └── recipe.py       Примеры данных рецептов
├── certs/                  Материалы подписи (приватные ключи не коммитятся)
└── generated/              Приложения и данные, созданные во время работы (не коммитятся)
```

## Быстрый старт

Требуется Python 3.10+. Для сборки Android APK нужны Android SDK и `apktool` (при их отсутствии происходит автоматический откат к офлайн-пакету PWA).

```bash
# 1. Создайте виртуальное окружение и установите зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. Настройка (необязательно, у всего есть значения по умолчанию)
cp .env.example .env
# Отредактируйте .env при необходимости

# 3. Запуск
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Откройте http://127.0.0.1:8000.

> Для локальной разработки переменные окружения не нужны. При публичном развёртывании задайте `PUBLIC_BASE_URL`,
> иначе iPhone не сможет открыть `localhost`. Полный список см. в [`.env.example`](.env.example).

## Развёртывание

> Полное руководство по продакшен-развёртыванию (systemd, Nginx, HTTPS, Android/iOS, R2) — в **[DEPLOY.ru.md](DEPLOY.ru.md)**.

В продакшене обычно запускают через systemd за обратным прокси Nginx:

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

Настройку сертификата для подписи профиля iOS («установка без подписи») см. в [`certs/README.md`](certs/README.md).

## Замечания по безопасности

- Все секреты (R2, Cloudflare, пароли подписи) читаются из переменных окружения; в репозитории нет реальных учётных данных.
- **Приватные ключи подписи (`certs/*.keystore`, `certs/app-keys/`) и runtime-данные (`generated/`) по умолчанию исключены через `.gitignore` — никогда не коммитьте их.**
- Каждое сгенерированное Android-приложение использует собственный независимый сертификат подписи, что предотвращает массовую блокировку по отпечатку сертификата и гарантирует возможность обновления того же приложения «на месте».

## Лицензия

[MIT](LICENSE)
