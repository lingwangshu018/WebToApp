"""
Server-wide configuration loaded from environment variables.

For iOS "免签" (signed .mobileconfig) support, set the following env vars
(or create certs/ios-cert.pem, certs/ios-key.pem, certs/ios-chain.pem files):

    IOS_CERT_FILE   - PEM-encoded signing certificate (the leaf cert for your domain)
    IOS_KEY_FILE    - PEM-encoded private key
    IOS_CHAIN_FILE  - (optional) intermediate cert chain; greatly improves trust

    PUBLIC_BASE_URL - public URL of this server (e.g. https://example.com).
                      Used as the Web Clip target so target URL can be swapped
                      later without re-installing the profile.
                      If unset, the request Host header is used at build time.
"""

import os
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).parent.parent
_DEFAULT_CERT_DIR = _ROOT / "certs"


def _first_existing(*paths):
    for p in paths:
        if p and os.path.isfile(p):
            return str(p)
    return None


def ios_cert_file() -> Optional[str]:
    return _first_existing(
        os.environ.get("IOS_CERT_FILE"),
        _DEFAULT_CERT_DIR / "ios-cert.pem",
    )


def ios_key_file() -> Optional[str]:
    return _first_existing(
        os.environ.get("IOS_KEY_FILE"),
        _DEFAULT_CERT_DIR / "ios-key.pem",
    )


def ios_chain_file() -> Optional[str]:
    return _first_existing(
        os.environ.get("IOS_CHAIN_FILE"),
        _DEFAULT_CERT_DIR / "ios-chain.pem",
    )


def ios_signing_available() -> bool:
    """True when both certificate and private key are configured and readable."""
    return bool(ios_cert_file() and ios_key_file())


def public_base_url() -> Optional[str]:
    """Return the configured public base URL, without trailing slash. May be None."""
    url = os.environ.get("PUBLIC_BASE_URL", "").strip()
    return url.rstrip("/") if url else None


def android_package_prefix() -> str:
    """Return the default Android package prefix."""
    prefix = os.environ.get("ANDROID_PACKAGE_PREFIX", "").strip().lower()
    return prefix or "com.webtoapp"


def android_keystore_dir() -> str:
    """Directory holding per-app Android signing keystores.

    Each generated app gets its own keystore here (keyed by app_id) so that
    no two apps share a signing certificate — this avoids the "test key"
    family being flagged en masse by mobile AV engines. Override the location
    with ANDROID_KEYSTORE_DIR; defaults to ``certs/app-keys`` (gitignored).

    Keep this OUTSIDE any publicly served directory. These files are private
    signing keys; leaking one lets an attacker forge updates for that app.
    """
    custom = os.environ.get("ANDROID_KEYSTORE_DIR", "").strip()
    if custom:
        return custom
    return str(_DEFAULT_CERT_DIR / "app-keys")


def android_template_keystore_password() -> str:
    """Password for the internal template-build keystore.

    This keystore only signs the throwaway base template APK (which is then
    re-signed per-app), so it is not security-critical, but we still avoid the
    hard-coded weak default by allowing an env override.
    """
    return os.environ.get("ANDROID_TEMPLATE_KEYSTORE_PASSWORD", "").strip() or "android"


def daily_build_quota_per_device() -> int:
    """Per device-fingerprint daily build quota. 0 disables quota."""
    try:
        return max(0, int(os.environ.get("DAILY_BUILD_QUOTA", "10").strip() or "10"))
    except ValueError:
        return 10


# ---------- Cloudflare R2 (S3-compatible) ----------
#
# Set ALL of the following to enable R2 offload. Once configured, every
# build's APK/ZIP/mobileconfig is uploaded to R2 after generation, and
# /a/{id}/download/{platform} 302-redirects to the public CDN URL — so the
# origin server stops paying for download bandwidth.
#
#   R2_ACCOUNT_ID         Cloudflare account ID (URL-safe, hex)
#   R2_ACCESS_KEY_ID      API token's S3 access key
#   R2_SECRET_ACCESS_KEY  API token's S3 secret
#   R2_BUCKET             Bucket name
#   R2_PUBLIC_BASE_URL    Public URL prefix, e.g. https://files.example.com
#                         or https://pub-xxxxxxxx.r2.dev. Trailing slash optional.

def r2_endpoint_url() -> Optional[str]:
    account_id = os.environ.get("R2_ACCOUNT_ID", "").strip()
    if not account_id:
        return None
    return f"https://{account_id}.r2.cloudflarestorage.com"


def r2_access_key_id() -> str:
    return os.environ.get("R2_ACCESS_KEY_ID", "").strip()


def r2_secret_access_key() -> str:
    return os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()


def r2_bucket() -> str:
    return os.environ.get("R2_BUCKET", "").strip()


def r2_public_base_url() -> Optional[str]:
    base = os.environ.get("R2_PUBLIC_BASE_URL", "").strip()
    return base.rstrip("/") if base else None


def r2_configured() -> bool:
    return bool(
        r2_endpoint_url()
        and r2_access_key_id()
        and r2_secret_access_key()
        and r2_bucket()
        and r2_public_base_url()
    )


# ---------- Cloudflare API (cache purge) ----------
#
# Optional. When set, PATCH /api/app/{id}/url calls the CF purge API to
# evict the cached /launch redirect immediately. Without it, edge caches
# expire on their own after ``launch_cache_max_age`` seconds.
#
#   CLOUDFLARE_API_TOKEN  Scoped token with "Zone Cache Purge" permission
#   CLOUDFLARE_ZONE_ID    Target zone ID

def cloudflare_api_token() -> str:
    return os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()


def cloudflare_zone_id() -> str:
    return os.environ.get("CLOUDFLARE_ZONE_ID", "").strip()


def cloudflare_purge_available() -> bool:
    return bool(cloudflare_api_token() and cloudflare_zone_id())


def launch_cache_max_age() -> int:
    """Seconds the iOS /launch 302 may be cached at the CDN edge.

    Lower = faster URL hot-swap propagation, higher = less origin traffic.
    Default 60s strikes a reasonable balance.
    """
    try:
        return max(0, int(os.environ.get("LAUNCH_CACHE_MAX_AGE", "60").strip() or "60"))
    except ValueError:
        return 60
