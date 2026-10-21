"""SSL/TLS certificate checker."""
from __future__ import annotations

import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse


def check_ssl(url: str) -> dict:
    """Check SSL certificate for a URL. Returns has_ssl, ssl_issuer, ssl_expiry."""
    parsed = urlparse(url)
    hostname = parsed.hostname or url
    port = parsed.port or 443

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        issuer_parts = dict(x[0] for x in cert.get("issuer", []))
        issuer = (
            issuer_parts.get("organizationName")
            or issuer_parts.get("commonName")
            or "Unknown"
        )
        expiry_raw = cert.get("notAfter", "")
        try:
            expiry_dt = datetime.strptime(expiry_raw, "%b %d %H:%M:%S %Y %Z")
            expiry = expiry_dt.isoformat()
        except ValueError:
            expiry = expiry_raw

        return {"has_ssl": True, "ssl_issuer": issuer, "ssl_expiry": expiry}

    except (ssl.SSLError, ssl.CertificateError, ConnectionRefusedError,
            socket.timeout, OSError):
        return {"has_ssl": False, "ssl_issuer": None, "ssl_expiry": None}
