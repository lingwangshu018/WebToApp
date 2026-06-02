<div align="center">

<img src="../assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**Convierte cualquier sitio web en una app instalable, en segundos.**

Un enlace de entrada, productos terminados para **iPhone / iPad · Android · Windows · macOS · Linux**.

[![Demo](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](../LICENSE)
[![Plataformas](https://img.shields.io/badge/Plataformas-5-736357?style=for-the-badge)](#features)

[English](../README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [العربية](README.ar.md) · [Русский](README.ru.md) · **Español** · [Português](README.pt.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="../assets/screenshot-1.png" alt="WebToApp" width="420">
  <img src="../assets/screenshot-2.png" alt="WebToApp" width="420">
  <br>
  <img src="../assets/screenshot-3.png" alt="WebToApp" width="420">
  <img src="../assets/screenshot-4.png" alt="WebToApp" width="420">
</div>

---

Introduce una URL y, en segundos, obtén un producto terminado que puedes instalar, compartir y usar como una app.
Un único resultado generado abarca **iPhone / iPad, Android, Windows, macOS y Linux**, y cada uno ocupa solo unos pocos KB, por lo que se descarga e instala casi al instante.

Código abierto · Gratis · Sin registro. Pruébalo en vivo en **[shiaho.sbs](https://shiaho.sbs)**.

---

## Funciones

- **Análisis del sitio**: obtiene la página de destino y extrae el nombre, el color del tema y el icono, y cuenta anuncios / rastreadores / ventanas emergentes (estimaciones solo para mostrar).
- **Empaquetado multiplataforma**: crea instaladores para cinco plataformas a la vez
  - **Android** — un APK WebView real e instalable (firmado con v1+v2+v3). Cada app usa su **propio certificado de firma dedicado**.
  - **iOS** — un perfil Web Clip `.mobileconfig`, con firma CMS opcional usando un certificado de una CA pública (instalación "sin firma").
  - **Windows / macOS / Linux** — lanzadores ligeros con un icono nativo.
- **Cambio dinámico de URL en iOS**: el Web Clip apunta a `/a/<id>/launch`, así que puedes cambiar la URL de destino en el servidor sin reinstalar.
- **Historial**: el historial de compilaciones se guarda por huella del dispositivo, con exportación / importación a otros dispositivos.
- **Limpieza automática**: las apps sin visitas durante 30 días se recuperan automáticamente.
- **Descarga opcional vía Cloudflare R2**: las descargas pasan por la CDN, ahorrando ancho de banda del origen.
- **Interfaz multilingüe**: 9 idiomas integrados (inglés, chino simplificado, japonés, árabe, ruso, español, portugués, francés, alemán), que sigue automáticamente el idioma del navegador, con diseño RTL para el árabe. Cámbialo manualmente desde la esquina superior derecha.

## Tamaño de la app

Cada paquete es solo un punto de entrada ligero a tu sitio — no empaqueta contenido del sitio, por lo que los artefactos se miden en **kilobytes, no megabytes**. Por debajo usa la cubierta ligera nativa de cada plataforma: un APK WebView de Android, un perfil Web Clip de iOS y lanzadores `.app` / `.bat` / `.desktop` que abren el navegador del sistema en modo app en escritorio.

Medido en una compilación real (las cifras son representativas; apenas varían según el sitio):

| Plataforma | Paquete | Tamaño típico | Contenido |
| --- | --- | --- | --- |
| Android | `android.apk` | **~21 KB** | Un APK WebView real e instalable (firmado v1+v2+v3) |
| iOS / iPadOS | `ios.mobileconfig` | **~4 KB** | Un perfil de configuración Web Clip |
| macOS | `macos.zip` | **~1,4 KB** | Un paquete `.app` (script lanzador + icono) |
| Windows | `windows.zip` | **~1,2 KB** | Un lanzador `.bat` + ayudante de acceso directo + icono |
| Linux | `linux.tar.gz` | **~0,7 KB** | Una entrada `.desktop` + script de instalación + icono |

## Tecnologías

- Backend: Python + FastAPI + Uvicorn
- Frontend: HTML / CSS / JS puro (archivos estáticos servidos directamente por el backend)
- Cadena de empaquetado: Android SDK (aapt2 / d8 / apksigner / zipalign), apktool, Pillow, openssl

## Estructura del proyecto

```
.
├── index.html              Página de inicio
├── css/ js/ assets/        Recursos estáticos del frontend
│   └── js/i18n.js          Runtime i18n ligero
│       js/i18n.strings.js  Traducciones para 9 idiomas
├── server/
│   ├── main.py             Aplicación FastAPI y rutas
│   ├── config.py           Configuración por variables de entorno
│   ├── history_store.py    Almacén de historial por dispositivo (JSON)
│   └── engine/
│       ├── analyzer.py     Análisis del sitio
│       ├── distiller.py    Genera los paquetes por plataforma (núcleo)
│       ├── apk_builder.py  Compilación y firma del APK de Android
│       ├── mobileconfig_signer.py  Firma del perfil de iOS
│       ├── storage.py      Descarga vía Cloudflare R2
│       └── recipe.py       Datos de recetas de ejemplo
├── certs/                  Material de firma (las claves privadas no se suben)
└── generated/              Apps y datos generados en tiempo de ejecución (no se suben)
```

## Inicio rápido

Requiere Python 3.10+. Compilar un APK de Android requiere el Android SDK y `apktool` (si faltan, recurre automáticamente a un paquete PWA sin conexión).

```bash
# 1. Crea un entorno virtual e instala las dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. Configuración (opcional, todo tiene valores por defecto)
cp .env.example .env
# Edita .env según necesites

# 3. Ejecutar
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000.

> No se necesitan variables de entorno para el desarrollo local. Al desplegar públicamente, define `PUBLIC_BASE_URL`,
> de lo contrario los iPhone no podrán abrir `localhost`. Consulta [`.env.example`](../.env.example) para la lista completa.

## Despliegue

> Para una guía completa de despliegue en producción (systemd, Nginx, HTTPS, Android/iOS, R2), consulta **[DEPLOY.es.md](DEPLOY.es.md)**.

En producción es habitual ejecutarlo con systemd, detrás de un proxy inverso Nginx:

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

Para la firma del perfil de iOS (instalación "sin firma"), consulta la configuración del certificado en [`certs/README.md`](../certs/README.md).

## Notas de seguridad

- Todos los secretos (R2, Cloudflare, contraseñas de firma) se leen de variables de entorno; el repositorio no contiene credenciales reales.
- **Las claves privadas de firma (`certs/*.keystore`, `certs/app-keys/`) y los datos de tiempo de ejecución (`generated/`) están excluidos por `.gitignore` de forma predeterminada; nunca los subas.**
- Cada app de Android generada usa su propio certificado de firma independiente, lo que evita que la huella del certificado sea marcada en masa y garantiza que la misma app pueda actualizarse in situ.

## Licencia

[MIT](../LICENSE)
