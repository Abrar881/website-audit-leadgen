"""Lightweight tech stack detection from HTML and HTTP headers."""
from __future__ import annotations

import re


def detect_tech_stack(html: bytes, headers: dict) -> dict:
    """Detect CMS, frameworks, and tools from HTML content and response headers."""
    try:
        text = html.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    stack: dict[str, str | bool] = {}

    # ── CMS ───────────────────────────────────────────────────────────────
    if "/wp-content/" in text or "/wp-includes/" in text:
        stack["cms"] = "WordPress"
    elif "wixstatic.com" in text or "wix-thunderbolt" in text:
        stack["cms"] = "Wix"
    elif "squarespace.com" in text or "squarespace-cdn.com" in text:
        stack["cms"] = "Squarespace"
    elif "cdn.shopify.com" in text:
        stack["cms"] = "Shopify"
    elif "sites.google.com" in text or 'name="generator" content="Google Sites' in text:
        stack["cms"] = "Google Sites"
    elif "weebly.com" in text or "editmysite.com" in text:
        stack["cms"] = "Weebly"
    elif "jimdo.com" in text:
        stack["cms"] = "Jimdo"

    # ── Analytics ─────────────────────────────────────────────────────────
    if "gtag(" in text or "googletagmanager.com/gtag" in text:
        stack["analytics"] = "Google Analytics 4"
    elif "analytics.js" in text and "google-analytics.com" in text:
        stack["analytics"] = "Google Analytics (UA)"

    # ── Tag Manager ───────────────────────────────────────────────────────
    if "googletagmanager.com/gtm.js" in text:
        stack["tag_manager"] = "Google Tag Manager"

    # ── Frameworks (JS) ───────────────────────────────────────────────────
    if "react" in text.lower() and ("__react" in text or "data-reactroot" in text):
        stack["js_framework"] = "React"
    elif "vue.js" in text.lower() or "__vue" in text:
        stack["js_framework"] = "Vue"
    elif "angular" in text.lower() and "ng-version" in text:
        stack["js_framework"] = "Angular"

    # ── Server from headers ───────────────────────────────────────────────
    server = headers.get("server") or headers.get("Server")
    if server:
        stack["server"] = server.split("/")[0]

    powered_by = headers.get("x-powered-by") or headers.get("X-Powered-By")
    if powered_by:
        stack["powered_by"] = powered_by

    # ── Chat / marketing ──────────────────────────────────────────────────
    if "hs-scripts.com" in text or "hubspot" in text.lower():
        stack["crm"] = "HubSpot"
    if "drift.com" in text:
        stack["chat"] = "Drift"
    if "intercom.com" in text:
        stack["chat"] = "Intercom"

    return stack
