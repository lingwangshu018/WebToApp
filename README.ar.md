<div dir="rtl">

# WebToApp — حوّل المواقع إلى تطبيقات

[English](README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · **العربية** · [Русский](README.ru.md) · [Español](README.es.md) · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

أدخل رابطًا، وخلال ثوانٍ تحصل على منتج نهائي يمكنك تثبيته ومشاركته واستخدامه كتطبيق.
نتيجة واحدة مُولّدة تغطي **iPhone / iPad وAndroid وWindows وmacOS وLinux**.

مفتوح المصدر · مجاني · بدون تسجيل.

---

## الميزات

- **تحليل الموقع**: يجلب الصفحة المستهدفة ويستخرج الاسم ولون السمة والأيقونة، ويحصي الإعلانات وأدوات التتبع والنوافذ المنبثقة (تقديرات للعرض فقط).
- **التحزيم متعدد المنصات**: ينشئ حِزم التثبيت لخمس منصات دفعة واحدة
  - **Android** — حزمة WebView APK حقيقية قابلة للتثبيت (موقّعة بـ v1+v2+v3). يستخدم كل تطبيق **شهادة توقيع مخصّصة خاصة به**.
  - **iOS** — ملف تعريف Web Clip بصيغة `.mobileconfig`، مع توقيع CMS اختياري باستخدام شهادة من هيئة عامة ("تثبيت بدون توقيع").
  - **Windows / macOS / Linux** — مشغّلات خفيفة بأيقونة أصلية.
- **تبديل عنوان iOS ديناميكيًا**: يشير Web Clip إلى `/a/<id>/launch`، لذا يمكنك تغيير عنوان الوجهة على الخادم دون إعادة التثبيت.
- **السجل**: يُحفظ سجل الإنشاء لكل بصمة جهاز، مع إمكانية التصدير والاستيراد إلى أجهزة أخرى.
- **التنظيف التلقائي**: تُسترجع تلقائيًا التطبيقات التي لم تُزَر خلال 30 يومًا.
- **تفريغ Cloudflare R2 الاختياري**: تمر التنزيلات عبر شبكة CDN لتوفير عرض النطاق على الخادم الأصلي.
- **واجهة متعددة اللغات**: 9 لغات مدمجة (الإنجليزية، الصينية المبسطة، اليابانية، العربية، الروسية، الإسبانية، البرتغالية، الفرنسية، الألمانية)، تتبع لغة المتصفح تلقائيًا، مع تخطيط RTL للعربية. يمكن التبديل يدويًا من الزاوية العلوية.

## التقنيات المستخدمة

- الخلفية: Python + FastAPI + Uvicorn
- الواجهة: HTML / CSS / JS خام (ملفات ثابتة يقدّمها الخادم مباشرة)
- سلسلة أدوات التحزيم: Android SDK ‏(aapt2 / d8 / apksigner / zipalign)، apktool، Pillow، openssl

## بنية المشروع

```
.
├── index.html              الصفحة الرئيسية
├── css/ js/ assets/        أصول الواجهة الثابتة
│   └── js/i18n.js          محرّك i18n خفيف
│       js/i18n.strings.js  ترجمات 9 لغات
├── server/
│   ├── main.py             تطبيق FastAPI والمسارات
│   ├── config.py           إعدادات متغيرات البيئة
│   ├── history_store.py    مخزن سجل الأجهزة (JSON)
│   └── engine/
│       ├── analyzer.py     تحليل الموقع
│       ├── distiller.py    إنشاء حِزم كل منصة (النواة)
│       ├── apk_builder.py  بناء وتوقيع Android APK
│       ├── mobileconfig_signer.py  توقيع ملف تعريف iOS
│       ├── storage.py      تفريغ Cloudflare R2
│       └── recipe.py       بيانات وصفات نموذجية
├── certs/                  مواد التوقيع (المفاتيح الخاصة لا تُرفع)
└── generated/              التطبيقات والبيانات المولّدة وقت التشغيل (لا تُرفع)
```

## البدء السريع

يتطلب Python 3.10 أو أحدث. يتطلب بناء حزمة Android APK وجود Android SDK و`apktool` (يتراجع تلقائيًا إلى حزمة PWA دون اتصال عند غيابهما).

```bash
# 1. أنشئ بيئة افتراضية وثبّت التبعيات
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. الإعداد (اختياري، لكل شيء قيم افتراضية)
cp .env.example .env
# عدّل .env حسب الحاجة

# 3. التشغيل
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

افتح http://127.0.0.1:8000.

> لا حاجة لأي متغيرات بيئة للتطوير المحلي. عند النشر العام، اضبط `PUBLIC_BASE_URL`،
> وإلا فلن تتمكن أجهزة iPhone من فتح `localhost`. راجع [`.env.example`](.env.example) للقائمة الكاملة.

## النشر

في الإنتاج، من الشائع تشغيله عبر systemd خلف وكيل عكسي Nginx:

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

لإعداد شهادة توقيع ملف تعريف iOS ("التثبيت بدون توقيع")، راجع [`certs/README.md`](certs/README.md).

## ملاحظات أمنية

- تُقرأ جميع الأسرار (R2، Cloudflare، كلمات مرور التوقيع) من متغيرات البيئة؛ ولا يحتوي المستودع على أي بيانات اعتماد حقيقية.
- **مفاتيح التوقيع الخاصة (`certs/*.keystore` و`certs/app-keys/`) وبيانات التشغيل (`generated/`) مستبعدة افتراضيًا عبر `.gitignore` — لا تقم برفعها أبدًا.**
- يستخدم كل تطبيق Android مُولّد شهادة توقيع مستقلة خاصة به، ما يمنع الإبلاغ الجماعي عن بصمة الشهادة كبرنامج ضار، ويضمن إمكانية تحديث التطبيق نفسه في مكانه.

## الترخيص

[MIT](LICENSE)

</div>
