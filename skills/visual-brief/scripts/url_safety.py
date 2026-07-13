#!/usr/bin/env python3
"""Shared URL checks for Visual Brief manifests and generated channel drafts."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import parse_qs, urlparse


SENSITIVE_QUERY_KEYS = {
    "token",
    "key",
    "signature",
    "sig",
    "authorization",
    "credential",
    "password",
    "secret",
}
SENSITIVE_COMPACT_QUERY_KEYS = {
    "accesstoken",
    "idtoken",
    "refreshtoken",
    "apikey",
    "xamzcredential",
    "xamzsignature",
    "xgoogcredential",
    "xgoogsignature",
}


def http_url_issues(value: object) -> list[str]:
    if not isinstance(value, str):
        return ["must be a URL string"]
    try:
        parsed = urlparse(value)
        scheme = parsed.scheme.lower()
        hostname_value = parsed.hostname
        parsed.port
        username = parsed.username
        password = parsed.password
    except ValueError:
        return ["must be a valid absolute http(s) URL"]
    if scheme not in {"https", "http"} or not parsed.netloc or not hostname_value:
        return ["must use an absolute http(s) URL"]

    issues: list[str] = []
    if username is not None or password is not None:
        issues.append("must not contain URL userinfo or embedded credentials")

    hostname = hostname_value.rstrip(".").lower()
    if "%" in hostname:
        issues.append("must not contain a percent-encoded hostname")
        return issues
    try:
        hostname.encode("idna")
    except UnicodeError:
        issues.append("contains invalid hostname text")
        return issues

    local_address = hostname == "localhost" or hostname.endswith(".localhost")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            address = ipaddress.ip_address(socket.inet_aton(hostname))
        except (OSError, UnicodeError):
            address = None
    host_port = parsed.netloc.rsplit("@", 1)[-1]
    if host_port.startswith("[") and not isinstance(address, ipaddress.IPv6Address):
        issues.append("contains an invalid bracketed IP host")
        return issues
    if address is not None:
        mapped = getattr(address, "ipv4_mapped", None)
        if address.is_loopback or address.is_unspecified:
            local_address = True
        elif mapped is not None and (mapped.is_loopback or mapped.is_unspecified):
            local_address = True
    if local_address:
        issues.append("must not expose a local URL")

    exposed = []
    for key in parse_qs(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        parts = {part for part in re.split(r"[^a-z0-9]+", lowered) if part}
        compact = re.sub(r"[^a-z0-9]", "", lowered)
        if parts & SENSITIVE_QUERY_KEYS or compact in SENSITIVE_COMPACT_QUERY_KEYS:
            exposed.append(key)
    if exposed:
        issues.append(f"contains sensitive-looking query keys: {', '.join(sorted(exposed))}")
    return issues
