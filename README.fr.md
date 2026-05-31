<div align="center">

<img src="assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**Transformez n'importe quel site web en application installable, en quelques secondes.**

Un lien en entrée, des produits finis pour **iPhone / iPad · Android · Windows · macOS · Linux**.

[![Démo](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![Licence : MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](LICENSE)
[![Plateformes](https://img.shields.io/badge/Plateformes-5-736357?style=for-the-badge)](#features)

[English](README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [العربية](README.ar.md) · [Русский](README.ru.md) · [Español](README.es.md) · [Português](README.pt.md) · **Français** · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="assets/screenshot-1.png" alt="WebToApp" width="860">
  <br><br>
  <img src="assets/screenshot-2.png" alt="WebToApp" width="430">
  <img src="assets/screenshot-3.png" alt="WebToApp" width="430">
</div>

---

Saisissez une URL et, quelques secondes plus tard, obtenez un produit fini que vous pouvez installer, partager et utiliser comme une application.
Un seul résultat généré couvre **iPhone / iPad, Android, Windows, macOS et Linux**.

Open source · Gratuit · Sans inscription. Essayez-le en direct sur **[shiaho.sbs](https://shiaho.sbs)**.

---

## Fonctionnalités

- **Analyse du site** : récupère la page cible et en extrait le nom, la couleur du thème et l'icône, puis compte les publicités / traceurs / fenêtres pop-up (estimations à titre indicatif).
- **Empaquetage multiplateforme** : crée des installateurs pour cinq plateformes en une fois
  - **Android** — un véritable APK WebView installable (signé v1+v2+v3). Chaque application utilise son **propre certificat de signature dédié**.
  - **iOS** — un profil Web Clip `.mobileconfig`, avec signature CMS optionnelle à l'aide d'un certificat d'une AC publique (installation « sans signature »).
  - **Windows / macOS / Linux** — des lanceurs légers avec une icône native.
- **Changement d'URL dynamique sur iOS** : le Web Clip pointe vers `/a/<id>/launch`, vous pouvez donc changer l'URL cible côté serveur sans réinstaller.
- **Historique** : l'historique des builds est enregistré par empreinte d'appareil, avec export / import vers d'autres appareils.
- **Nettoyage automatique** : les applications sans visite pendant 30 jours sont automatiquement récupérées.
- **Déchargement Cloudflare R2 optionnel** : les téléchargements passent par le CDN, économisant la bande passante de l'origine.
- **Interface multilingue** : 9 langues intégrées (anglais, chinois simplifié, japonais, arabe, russe, espagnol, portugais, français, allemand), qui suit automatiquement la langue du navigateur, avec une mise en page RTL pour l'arabe. Changez-la manuellement dans le coin supérieur droit.

## Pile technique

- Backend : Python + FastAPI + Uvicorn
- Frontend : HTML / CSS / JS pur (fichiers statiques servis directement par le backend)
- Chaîne d'empaquetage : Android SDK (aapt2 / d8 / apksigner / zipalign), apktool, Pillow, openssl

## Structure du projet

```
.
├── index.html              Page d'accueil
├── css/ js/ assets/        Ressources statiques du frontend
│   └── js/i18n.js          Runtime i18n léger
│       js/i18n.strings.js  Traductions pour 9 langues
├── server/
│   ├── main.py             Application FastAPI et routes
│   ├── config.py           Configuration par variables d'environnement
│   ├── history_store.py    Stockage de l'historique par appareil (JSON)
│   └── engine/
│       ├── analyzer.py     Analyse du site
│       ├── distiller.py    Génère les paquets par plateforme (cœur)
│       ├── apk_builder.py  Compilation et signature de l'APK Android
│       ├── mobileconfig_signer.py  Signature du profil iOS
│       ├── storage.py      Déchargement Cloudflare R2
│       └── recipe.py       Données d'exemples de recettes
├── certs/                  Matériel de signature (les clés privées ne sont pas versionnées)
└── generated/              Applications et données générées à l'exécution (non versionnées)
```

## Démarrage rapide

Nécessite Python 3.10+. La compilation d'un APK Android nécessite le SDK Android et `apktool` (repli automatique vers un paquet PWA hors ligne en cas d'absence).

```bash
# 1. Créez un environnement virtuel et installez les dépendances
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. Configuration (facultatif, tout a des valeurs par défaut)
cp .env.example .env
# Modifiez .env selon vos besoins

# 3. Lancer
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Ouvrez http://127.0.0.1:8000.

> Aucune variable d'environnement n'est nécessaire pour le développement local. Lors d'un déploiement public, définissez `PUBLIC_BASE_URL`,
> sinon les iPhone ne peuvent pas ouvrir `localhost`. Voir [`.env.example`](.env.example) pour la liste complète.

## Déploiement

En production, il est courant de l'exécuter sous systemd, derrière un proxy inverse Nginx :

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

Pour la signature du profil iOS (installation « sans signature »), voir la configuration du certificat dans [`certs/README.md`](certs/README.md).

## Notes de sécurité

- Tous les secrets (R2, Cloudflare, mots de passe de signature) sont lus depuis les variables d'environnement ; le dépôt ne contient aucun identifiant réel.
- **Les clés privées de signature (`certs/*.keystore`, `certs/app-keys/`) et les données d'exécution (`generated/`) sont exclues par défaut via `.gitignore` — ne les versionnez jamais.**
- Chaque application Android générée utilise son propre certificat de signature indépendant, ce qui évite que l'empreinte du certificat soit signalée en masse et garantit que la même application peut être mise à jour sur place.

## Licence

[MIT](LICENSE)
