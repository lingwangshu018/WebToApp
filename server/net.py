import asyncio
import ipaddress
import socket
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

from server import config


class UnsafeOutboundTarget(ValueError):
    pass


def _normalized_http_url(url: str) -> str:
    value = str(url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise UnsafeOutboundTarget("URL must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise UnsafeOutboundTarget("URL credentials are not allowed")
    return value


def _port_for(parsed) -> int:
    if parsed.port:
        return int(parsed.port)
    return 443 if parsed.scheme == "https" else 80


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_public_http_url(url: str) -> str:
    normalized = _normalized_http_url(url)
    parsed = urlparse(normalized)
    infos = socket.getaddrinfo(parsed.hostname, _port_for(parsed), type=socket.SOCK_STREAM)
    seen = set()
    for info in infos:
        address = info[4][0]
        seen.add(address)
        if _is_forbidden_ip(address):
            raise UnsafeOutboundTarget("URL resolves to a non-public address")
    if not seen:
        raise UnsafeOutboundTarget("URL does not resolve to a public address")
    return normalized


async def avalidate_public_http_url(url: str) -> str:
    return await asyncio.to_thread(validate_public_http_url, url)


def redirect_target(current_url: str, location: str) -> str:
    if not str(location or "").strip():
        raise UnsafeOutboundTarget("Redirect response is missing a location")
    return validate_public_http_url(urljoin(current_url, location))


def read_limited_response(resp, max_bytes: int) -> bytes:
    length = resp.headers.get("content-length")
    if length:
        try:
            parsed_length = int(length)
        except ValueError:
            parsed_length = None
        if parsed_length is not None and parsed_length > max_bytes:
            raise ValueError("Response too large")
    chunks = []
    total = 0
    for chunk in resp.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise ValueError("Response too large")
        chunks.append(chunk)
    return b"".join(chunks)


async def aread_limited_response(resp, max_bytes: int) -> bytes:
    length = resp.headers.get("content-length")
    if length:
        try:
            parsed_length = int(length)
        except ValueError:
            parsed_length = None
        if parsed_length is not None and parsed_length > max_bytes:
            raise ValueError("Response too large")
    chunks = []
    total = 0
    async for chunk in resp.aiter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise ValueError("Response too large")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_public_url_bytes(
    url: str,
    *,
    timeout: float,
    headers: Optional[dict] = None,
    max_bytes: Optional[int] = None,
    max_redirects: Optional[int] = None,
) -> bytes:
    current_url = validate_public_http_url(url)
    byte_limit = int(max_bytes or config.outbound_response_max_bytes())
    redirect_limit = int(max_redirects or config.outbound_redirect_limit())
    client = httpx.Client(
        follow_redirects=False,
        timeout=httpx.Timeout(timeout, connect=min(float(timeout), 10.0)),
        headers=headers or None,
    )
    try:
        for _ in range(redirect_limit + 1):
            with client.stream("GET", current_url) as resp:
                if resp.status_code in {301, 302, 303, 307, 308}:
                    current_url = redirect_target(current_url, resp.headers.get("location", ""))
                    continue
                resp.raise_for_status()
                return read_limited_response(resp, byte_limit)
        raise httpx.TooManyRedirects(f"Exceeded redirect limit for {url}")
    finally:
        client.close()
