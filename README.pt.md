<div align="center">

<img src="assets/site-logo.jpg" alt="WebToApp" width="120" height="120" style="border-radius: 24px;">

# WebToApp

**Transforme qualquer site em um app instalável, em segundos.**

Um link de entrada, produtos prontos para **iPhone / iPad · Android · Windows · macOS · Linux**.

[![Demo](https://img.shields.io/badge/Live_Demo-shiaho.sbs-c97953?style=for-the-badge)](https://shiaho.sbs)
[![Licença: MIT](https://img.shields.io/badge/License-MIT-1e1914?style=for-the-badge)](LICENSE)
[![Plataformas](https://img.shields.io/badge/Plataformas-5-736357?style=for-the-badge)](#features)

[English](README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [العربية](README.ar.md) · [Русский](README.ru.md) · [Español](README.es.md) · **Português** · [Français](README.fr.md) · [Deutsch](README.de.md)

</div>

---

<div align="center">
  <img src="assets/screenshot.png" alt="WebToApp" width="860">
</div>

---

Insira uma URL e, em segundos, obtenha um produto pronto que você pode instalar, compartilhar e usar como um app.
Um único resultado gerado abrange **iPhone / iPad, Android, Windows, macOS e Linux**.

Código aberto · Grátis · Sem cadastro. Experimente ao vivo em **[shiaho.sbs](https://shiaho.sbs)**.

---

## Recursos

- **Análise do site**: busca a página de destino e extrai o nome, a cor do tema e o ícone, e conta anúncios / rastreadores / pop-ups (estimativas apenas para exibição).
- **Empacotamento multiplataforma**: cria instaladores para cinco plataformas de uma só vez
  - **Android** — um APK WebView real e instalável (assinado com v1+v2+v3). Cada app usa seu **próprio certificado de assinatura dedicado**.
  - **iOS** — um perfil Web Clip `.mobileconfig`, com assinatura CMS opcional usando um certificado de uma AC pública (instalação "sem assinatura").
  - **Windows / macOS / Linux** — inicializadores leves com um ícone nativo.
- **Troca dinâmica de URL no iOS**: o Web Clip aponta para `/a/<id>/launch`, então você pode alterar a URL de destino no servidor sem reinstalar.
- **Histórico**: o histórico de compilações é salvo por impressão digital do dispositivo, com exportação / importação para outros dispositivos.
- **Limpeza automática**: apps sem visitas por 30 dias são recuperados automaticamente.
- **Descarregamento opcional via Cloudflare R2**: os downloads passam pela CDN, economizando banda da origem.
- **Interface multilíngue**: 9 idiomas integrados (inglês, chinês simplificado, japonês, árabe, russo, espanhol, português, francês, alemão), que segue automaticamente o idioma do navegador, com layout RTL para o árabe. Troque manualmente no canto superior direito.

## Tecnologias

- Backend: Python + FastAPI + Uvicorn
- Frontend: HTML / CSS / JS puro (arquivos estáticos servidos diretamente pelo backend)
- Cadeia de empacotamento: Android SDK (aapt2 / d8 / apksigner / zipalign), apktool, Pillow, openssl

## Estrutura do projeto

```
.
├── index.html              Página inicial
├── css/ js/ assets/        Recursos estáticos do frontend
│   └── js/i18n.js          Runtime i18n leve
│       js/i18n.strings.js  Traduções para 9 idiomas
├── server/
│   ├── main.py             Aplicativo FastAPI e rotas
│   ├── config.py           Configuração por variáveis de ambiente
│   ├── history_store.py    Armazenamento de histórico por dispositivo (JSON)
│   └── engine/
│       ├── analyzer.py     Análise do site
│       ├── distiller.py    Gera os pacotes por plataforma (núcleo)
│       ├── apk_builder.py  Compilação e assinatura do APK Android
│       ├── mobileconfig_signer.py  Assinatura do perfil iOS
│       ├── storage.py      Descarregamento via Cloudflare R2
│       └── recipe.py       Dados de receitas de exemplo
├── certs/                  Material de assinatura (chaves privadas não são versionadas)
└── generated/              Apps e dados gerados em tempo de execução (não versionados)
```

## Início rápido

Requer Python 3.10+. Compilar um APK Android requer o Android SDK e o `apktool` (recorre automaticamente a um pacote PWA offline quando ausentes).

```bash
# 1. Crie um ambiente virtual e instale as dependências
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 2. Configuração (opcional, tudo tem valores padrão)
cp .env.example .env
# Edite o .env conforme necessário

# 3. Executar
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000.

> Nenhuma variável de ambiente é necessária para o desenvolvimento local. Ao implantar publicamente, defina `PUBLIC_BASE_URL`,
> caso contrário os iPhones não conseguem abrir `localhost`. Veja [`.env.example`](.env.example) para a lista completa.

## Implantação

Em produção é comum executá-lo com systemd, atrás de um proxy reverso Nginx:

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

Para a assinatura do perfil iOS (instalação "sem assinatura"), veja a configuração do certificado em [`certs/README.md`](certs/README.md).

## Notas de segurança

- Todos os segredos (R2, Cloudflare, senhas de assinatura) são lidos de variáveis de ambiente; o repositório não contém credenciais reais.
- **As chaves privadas de assinatura (`certs/*.keystore`, `certs/app-keys/`) e os dados de tempo de execução (`generated/`) são excluídos por padrão pelo `.gitignore` — nunca os versione.**
- Cada app Android gerado usa seu próprio certificado de assinatura independente, o que evita que a impressão digital do certificado seja sinalizada em massa e garante que o mesmo app possa ser atualizado no lugar.

## Licença

[MIT](LICENSE)
