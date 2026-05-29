"""
Site Intelligence Engine — Analyzes any URL.
Extracts structure, detects bloat, calculates optimization potential.
"""

import asyncio
import base64
import httpx
import re
from urllib.parse import urlparse

from server.engine.distiller import Distiller


# Common ad/tracker domains
AD_DOMAINS = {
    'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
    'facebook.net', 'analytics.google.com', 'googletagmanager.com',
    'hotjar.com', 'mixpanel.com', 'segment.com', 'amplitude.com',
    'taboola.com', 'outbrain.com', 'criteo.com', 'quantserve.com',
    'scorecardresearch.com', 'bluekai.com', 'chartbeat.com',
    'baidu.com/hm', 'cnzz.com', 'umeng.com', '51.la', 'tongji.baidu.com',
}

# Popup/overlay patterns
POPUP_PATTERNS = [
    r'cookie[_-]?(banner|consent|notice|popup)',
    r'newsletter[_-]?(modal|popup|signup)',
    r'subscribe[_-]?(modal|popup|overlay)',
    r'overlay[_-]?(backdrop|modal)',
    r'interstitial',
    r'gdpr',
]


class SiteAnalyzer:
    """Analyzes a website's structure, performance, and bloat."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"},
        )
        self.icon_distiller = Distiller()

    async def analyze(self, url: str) -> dict:
        if not url.startswith('http'):
            url = 'https://' + url
        parsed = urlparse(url)
        host = parsed.hostname or ''

        resp = await self.client.get(url)
        resp.raise_for_status()
        html = resp.text
        content_length = len(resp.content)

        title = self._extract_tag(html, 'title') or host
        site_name, site_name_source = self._extract_site_name(html)
        description = self._extract_meta(html, 'description')
        theme_color = self._extract_meta(html, 'theme-color') or '#7c3aed'
        favicon = self._extract_favicon(html, url)
        favicon_data_url = await asyncio.to_thread(self._favicon_data_url, url)
        suggested_name, suggested_name_source = self._suggest_app_name(
            title,
            host,
            site_name,
            site_name_source,
        )

        # Detect bloat
        scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)', html)
        ad_scripts = [s for s in scripts if any(ad in s for ad in AD_DOMAINS)]
        tracker_scripts = [s for s in scripts if self._is_tracker(s)]
        popup_elements = sum(1 for p in POPUP_PATTERNS if re.search(p, html, re.I))

        # Size analysis
        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S)
        inline_css_size = sum(len(s) for s in style_blocks)
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
        inline_js_size = sum(len(s) for s in script_blocks)
        total_bloat = len(ad_scripts) * 45000 + inline_js_size * 0.3  # estimated

        original_kb = content_length / 1024
        estimated_distilled_kb, speed_boost = self._estimate_distilled_metrics(
            original_kb=original_kb,
            total_scripts=len(scripts),
            ad_count=len(ad_scripts),
            tracker_count=len(tracker_scripts),
            popup_count=popup_elements,
            inline_js_kb=inline_js_size / 1024,
            inline_css_kb=inline_css_size / 1024,
            total_bloat_kb=total_bloat / 1024,
        )

        return {
            "title": title,
            "suggestedName": suggested_name,
            "suggestedNameSource": suggested_name_source,
            "siteName": site_name,
            "url": url,
            "host": host,
            "favicon": favicon,
            "faviconDataUrl": favicon_data_url,
            "themeColor": theme_color,
            "description": description,
            "ads": len(ad_scripts),
            "trackers": len(tracker_scripts),
            "popups": popup_elements,
            "totalScripts": len(scripts),
            "originalSize": f"{original_kb:.0f} KB" if original_kb < 1024 else f"{original_kb/1024:.1f} MB",
            "distilledSize": f"{estimated_distilled_kb:.0f} KB",
            "speedBoost": f"{speed_boost}x",
        }

    def _extract_tag(self, html: str, tag: str) -> str:
        m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.I | re.S)
        return m.group(1).strip() if m else ''

    def _extract_meta(self, html: str, name: str) -> str:
        m = re.search(rf'<meta[^>]*(?:name|property)=["\'](?:og:)?{name}["\'][^>]*content=["\']([^"\']*)', html, re.I)
        if not m:
            m = re.search(rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*(?:name|property)=["\'](?:og:)?{name}', html, re.I)
        return m.group(1) if m else ''

    def _estimate_distilled_metrics(
        self,
        *,
        original_kb: float,
        total_scripts: int,
        ad_count: int,
        tracker_count: int,
        popup_count: int,
        inline_js_kb: float,
        inline_css_kb: float,
        total_bloat_kb: float,
    ) -> tuple[float, float]:
        original_kb = max(float(original_kb or 0), 0.5)
        total_scripts = max(int(total_scripts or 0), 0)
        ad_count = max(int(ad_count or 0), 0)
        tracker_count = max(int(tracker_count or 0), 0)
        popup_count = max(int(popup_count or 0), 0)
        inline_js_kb = max(float(inline_js_kb or 0), 0.0)
        inline_css_kb = max(float(inline_css_kb or 0), 0.0)
        total_bloat_kb = max(float(total_bloat_kb or 0), 0.0)

        if original_kb < 24:
            retained_ratio = 0.74 if total_scripts <= 4 else 0.62
            estimated_distilled_kb = max(original_kb * retained_ratio, 0.5)
            speed_boost = max(round(original_kb / estimated_distilled_kb, 1), 1.1)
            return estimated_distilled_kb, speed_boost

        estimated_savings_kb = (
            total_bloat_kb * 0.35
            + max(total_scripts - 4, 0) * 8.0
            + ad_count * 42.0
            + tracker_count * 18.0
            + popup_count * 6.0
            + inline_js_kb * 0.75
            + inline_css_kb * 0.35
        )
        min_savings_kb = original_kb * 0.08
        max_savings_kb = original_kb * 0.82
        bounded_savings_kb = min(max(estimated_savings_kb, min_savings_kb), max_savings_kb)
        estimated_distilled_kb = max(12.0, original_kb - bounded_savings_kb)
        estimated_distilled_kb = min(estimated_distilled_kb, original_kb * 0.92)
        speed_boost = max(round(original_kb / max(estimated_distilled_kb, 0.5), 1), 1.1)
        return estimated_distilled_kb, speed_boost

    def _extract_site_name(self, html: str) -> tuple[str, str]:
        candidates = [
            ("site_name", self._extract_meta(html, 'site_name')),
            ("application_name", self._extract_meta(html, 'application-name')),
            ("apple_mobile_web_app_title", self._extract_meta(html, 'apple-mobile-web-app-title')),
        ]
        for source, value in candidates:
            if self._normalize_text(value):
                return value, source
        return "", ""

    def _suggest_app_name(
        self,
        title: str,
        host: str,
        site_name: str = '',
        site_name_source: str = '',
    ) -> tuple[str, str]:
        host_label = self._host_label(host)
        clean_site_name = self._normalize_text(site_name)
        clean_title = self._normalize_text(title)

        if clean_site_name:
            return self._trim_app_name(clean_site_name), (site_name_source or "site_name")

        if not clean_title:
            return self._trim_app_name(host_label or host or "WebToApp"), "host_fallback"

        parts = self._split_title_parts(clean_title)
        host_matches = [part for part in parts if self._part_matches_host(part, host_label)]
        if host_matches:
            best = min(host_matches, key=lambda part: (len(part), parts.index(part)))
            return self._trim_app_name(best), "title_host_match"

        short_parts = [part for part in parts if 1 < len(part) <= 36]
        if short_parts:
            source = "title_first_part" if len(parts) > 1 else "title_full"
            return self._trim_app_name(short_parts[0]), source

        return self._trim_app_name(clean_title), "title_full"

    def _normalize_text(self, value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        text = re.sub(r"\s*([|｜\-—–·•:：])\s*", r" \1 ", text)
        return re.sub(r"\s+", " ", text).strip(" -—–|｜·•:：")

    def _split_title_parts(self, title: str) -> list[str]:
        parts = re.split(r"\s*[|｜\-—–·•:：]\s*", title)
        ordered = []
        seen = set()
        for part in parts:
            token = self._normalize_text(part)
            key = token.casefold()
            if len(token) < 2 or key in seen:
                continue
            seen.add(key)
            ordered.append(token)
        return ordered or ([title] if title else [])

    def _host_label(self, host: str) -> str:
        labels = [label for label in str(host or "").lower().split(".") if label]
        while labels and labels[0] in {"www", "m", "mobile"}:
            labels.pop(0)
        return labels[0] if labels else ""

    def _part_matches_host(self, part: str, host_label: str) -> bool:
        if not host_label:
            return False
        lowered = re.sub(r"[^a-z0-9]+", "", part.lower())
        return host_label in lowered or lowered in host_label

    def _trim_app_name(self, value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        if len(text) <= 40:
            return text
        return text[:40].rstrip() + "..."

    def _extract_favicon(self, html: str, base_url: str) -> str:
        m = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)', html, re.I)
        if m:
            href = m.group(1)
            if href.startswith('//'): return 'https:' + href
            if href.startswith('/'): return urlparse(base_url)._replace(path=href).geturl()
            if href.startswith('http'): return href
        parsed = urlparse(base_url)
        return f"https://www.google.com/s2/favicons?domain={parsed.hostname}&sz=64"

    def _favicon_data_url(self, url: str) -> str:
        try:
            candidates = self.icon_distiller._collect_icon_candidates(url)
            icon_png = self.icon_distiller._choose_best_icon(candidates)
        except Exception:
            return ""
        if not icon_png:
            return ""
        return "data:image/png;base64," + base64.b64encode(icon_png).decode("ascii")

    def _is_tracker(self, src: str) -> bool:
        tracker_kw = ['analytics', 'tracking', 'pixel', 'beacon', 'telemetry', 'metrics']
        return any(kw in src.lower() for kw in tracker_kw) or any(ad in src for ad in AD_DOMAINS)
