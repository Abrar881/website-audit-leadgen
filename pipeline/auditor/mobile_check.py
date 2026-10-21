"""Mobile-friendliness heuristic checker."""
from __future__ import annotations

from bs4 import BeautifulSoup
import httpx

_MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def check_mobile(url: str) -> dict:
    """Check viewport meta and basic responsive layout signals.

    Returns:
        has_viewport_meta: bool — <meta name="viewport"> present
        is_responsive: bool — viewport meta present AND no table-layout patterns
    """
    try:
        resp = httpx.get(url, headers={"User-Agent": _MOBILE_UA}, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        html = resp.content
    except Exception:
        return {"has_viewport_meta": False, "is_responsive": False}

    soup = BeautifulSoup(html, "html.parser")

    # Check for viewport meta
    viewport = soup.find("meta", attrs={"name": lambda n: n and n.lower() == "viewport"})
    has_viewport = viewport is not None

    # Heuristic: table-layout = old non-responsive design
    # A site with viewport meta and no table-based layout is considered responsive
    tables_with_width = soup.find_all("table", attrs={"width": True})
    uses_table_layout = len(tables_with_width) > 2

    is_responsive = has_viewport and not uses_table_layout

    return {
        "has_viewport_meta": has_viewport,
        "is_responsive": is_responsive,
    }
