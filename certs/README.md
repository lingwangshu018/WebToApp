# iOS 描述文件签名证书 (苹果免签)

把域名 SSL 证书放在这个目录，生成的 `.mobileconfig` 会被自动签名，
iOS 安装时会显示 **签名者为你的域名**，而不是红色的"未签名"警告。

## 需要的文件

| 文件 | 说明 | 必需 |
|---|---|---|
| `ios-cert.pem` | 证书本体（PEM 格式，对应域名的叶子证书） | ✅ |
| `ios-key.pem` | 私钥（PEM 格式） | ✅ |
| `ios-chain.pem` | 中间 CA 证书链 | ⚠️ 强烈建议 |

若未放置这些文件，系统回退到 **未签名模式**（生成纯 XML 描述文件，iOS 仍可安装，只是显示"未签名"）。

## 证书来源

任何被 iOS 信任的公共 CA 颁发的 SSL 证书都行：

- **Let's Encrypt** 免费（3 个月有效）— 推荐
- **Sectigo / DigiCert / GlobalSign** 等付费 CA（1 年起）
- **宝塔面板** 一键申请免费证书（同为 Let's Encrypt）

⚠️ **自签名证书不行** — iOS 会把它当作未签名处理。

## Let's Encrypt 示例（certbot）

```bash
# 1. 申请证书
sudo certbot certonly --standalone -d your-domain.com

# 2. 拷到项目 certs/ 目录
cp /etc/letsencrypt/live/your-domain.com/cert.pem      certs/ios-cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem   certs/ios-key.pem
cp /etc/letsencrypt/live/your-domain.com/chain.pem     certs/ios-chain.pem
```

## 自定义路径（替代默认位置）

也可以用环境变量指向任意位置：

```bash
export IOS_CERT_FILE=/path/to/cert.pem
export IOS_KEY_FILE=/path/to/privkey.pem
export IOS_CHAIN_FILE=/path/to/chain.pem
```

## 验证签名

```bash
openssl cms -in generated/<app_id>/downloads/ios.mobileconfig \
  -inform DER -verify -noverify -out /tmp/inner.plist
# 成功则输出 "CMS Verification successful"
```

## 动态 URL 切换（后台换链接）

Web Clip 的 target URL 指向 `<PUBLIC_BASE_URL>/a/<app_id>/launch`，
服务器收到后 302 重定向到 `recipe.json` 里的 `url` 字段。

想换目标：

```bash
curl -X PATCH https://your-domain.com/api/app/<app_id>/url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://new-target.com"}'
```

之后用户再点桌面图标就会打开新 URL，**不用重新安装描述文件**。

## PUBLIC_BASE_URL

生产部署请设置（否则 iPhone 打不开 localhost）：

```bash
export PUBLIC_BASE_URL=https://your-domain.com
```

未设置时，程序从 HTTP 请求的 `Host` 头推断。
