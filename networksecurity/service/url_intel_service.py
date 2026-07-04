import ipaddress
import os
from typing import Any
from urllib.parse import urlparse

import requests
from pydantic import BaseModel


SHORTENER_DOMAINS = {
    "bit.ly",
    "goo.gl",
    "tinyurl.com",
    "ow.ly",
    "t.co",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
    "s.id",
}


class URLPayload(BaseModel):
    url: str


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL is required")
    if "://" not in url:
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("URL must include a domain")
    return url


def _host(url: str) -> str:
    return urlparse(url).hostname or ""


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _subdomain_score(host: str) -> int:
    labels = host.split(".")
    subdomains = max(len(labels) - 2, 0)
    if subdomains == 0:
        return 1
    if subdomains == 1:
        return 0
    return -1


def extract_url_features(url: str) -> dict[str, int]:
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = _host(normalized)
    url_length = len(normalized)

    return {
        "having_IP_Address": -1 if _is_ip(host) else 1,
        "URL_Length": -1 if url_length >= 75 else 0 if url_length >= 54 else 1,
        "Shortining_Service": -1 if host.lower() in SHORTENER_DOMAINS else 1,
        "having_At_Symbol": -1 if "@" in normalized else 1,
        "double_slash_redirecting": -1 if "//" in normalized.split("://", 1)[-1] else 1,
        "Prefix_Suffix": -1 if "-" in host else 1,
        "having_Sub_Domain": _subdomain_score(host),
        "SSLfinal_State": 1 if parsed.scheme == "https" else -1,
        "port": -1 if parsed.port not in (None, 80, 443) else 1,
        "HTTPS_token": -1 if "https" in host.lower() else 1,
    }


def _safe_browsing(url: str) -> dict[str, Any]:
    api_key = os.getenv("SAFE_BROWSING_API_KEY")
    if not api_key:
        return {"provider": "google_safe_browsing", "configured": False}

    response = requests.post(
        f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}",
        json={
            "client": {"clientId": "phisherman", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "provider": "google_safe_browsing",
        "configured": True,
        "matched": bool(data.get("matches")),
        "raw": data,
    }


def enrich_with_reputation(url: str) -> tuple[dict[str, int], list[dict[str, Any]]]:
    normalized = normalize_url(url)
    features = extract_url_features(normalized)
    checks = []

    try:
        result = _safe_browsing(normalized)
    except requests.RequestException as exc:
        result = {"provider": "google_safe_browsing", "configured": True, "error": str(exc)}
    checks.append(result)

    matched = any(result.get("matched") for result in checks)
    configured = any(result.get("configured") for result in checks)
    if configured:
        features["Statistical_report"] = -1 if matched else 1

    return features, checks
