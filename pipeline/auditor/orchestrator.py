"""Runs all audit modules for a single business URL."""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from auditor.pagespeed import PageSpeedClient
from auditor.ssl_check import check_ssl
from auditor.mobile_check import check_mobile
from auditor.design_age import detect_design_age
from auditor.broken_links import check_broken_links
from auditor.tech_stack import detect_tech_stack

_DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)


class AuditOrchestrator:
    def __init__(self, api_key: str, cache_dir: str | Path) -> None:
        self._psi = PageSpeedClient(api_key=api_key, cache_dir=cache_dir)
        self.api_calls_made = 0

    def audit_url(self, url: str) -> dict:
        """Run all audits for a URL and return a merged dict ready for DB insert."""
        t0 = time.monotonic()
        result: dict = {}

        # 1. PageSpeed
        try:
            psi = self._psi.audit(url)
            self.api_calls_made += self._psi.api_calls_made
            result.update(psi)
        except Exception as e:
            result["psi_error"] = str(e)

        # 2. Fetch raw HTML for remaining checks
        html: bytes = b""
        response_headers: dict = {}
        try:
            resp = httpx.get(
                url,
                headers={"User-Agent": _DESKTOP_UA},
                timeout=20,
                follow_redirects=True,
            )
            resp.raise_for_status()
            html = resp.content
            response_headers = dict(resp.headers)
        except Exception:
            pass

        # 3. SSL
        try:
            result.update(check_ssl(url))
        except Exception:
            result.update({"has_ssl": None, "ssl_issuer": None, "ssl_expiry": None})

        # 4. Mobile
        try:
            result.update(check_mobile(url))
        except Exception:
            result.update({"has_viewport_meta": None, "is_responsive": None})

        if html:
            # 5. Design age
            try:
                result.update(detect_design_age(html))
            except Exception:
                pass

            # 6. Broken links
            try:
                result.update(check_broken_links(url, html))
            except Exception:
                pass

            # 7. Tech stack
            try:
                result["tech_stack"] = detect_tech_stack(html, response_headers)
            except Exception:
                result["tech_stack"] = {}

        result["audit_duration_s"] = round(time.monotonic() - t0, 2)
        return result
