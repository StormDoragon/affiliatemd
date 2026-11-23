import base64
import ipaddress
import json
import re
import socket
import ssl
from http.client import HTTPException as HTTPClientError
from http.client import HTTPSConnection
from urllib.parse import urlencode, urlsplit, urlunsplit

import nh3
from fastapi import HTTPException
from markdown_it import MarkdownIt

from ..config import settings
from .provider_errors import IntegrationFailed

_TLS = ssl.create_default_context()
_MARKDOWN = MarkdownIt("commonmark", {"html": False})


def site_url(value: str) -> str:
    """Accept public HTTPS WordPress origins and installations in a subdirectory."""
    try:
        url = urlsplit(value)
        hostname = url.hostname
        if (
            url.scheme != "https"
            or not hostname
            or url.username is not None
            or url.password is not None
            or url.port not in (None, 443)
            or url.query
            or url.fragment
            or not hostname.isascii()
            or not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", hostname)
            or not re.fullmatch(r"(?:/[A-Za-z0-9._~-]+)*/?", url.path)
            or any(part in (".", "..") for part in url.path.split("/"))
        ):
            raise ValueError
        return urlunsplit(("https", hostname, url.path.rstrip("/"), "", ""))
    except ValueError as exc:
        raise ValueError("Enter a public HTTPS WordPress URL without a query or port") from exc


class PublicHTTPSConnection(HTTPSConnection):
    def connect(self) -> None:
        # Resolve once and connect to a checked address. Keep the original host for TLS and Host.
        addresses = socket.getaddrinfo(
            self.host, 443, family=socket.AF_INET, type=socket.SOCK_STREAM
        )
        for _, _, _, _, address in addresses:
            ip = ipaddress.ip_address(address[0])
            if not ip.is_global or ip.is_multicast or ip.is_reserved:
                raise HTTPException(422, "WordPress must resolve only to public addresses")
        last_error = None
        for family, kind, protocol, _, address in addresses[:4]:
            sock = socket.socket(family, kind, protocol)
            sock.settimeout(self.timeout)
            try:
                sock.connect(address)
                self.sock = _TLS.wrap_socket(sock, server_hostname=self.host)
                return
            except OSError as exc:
                sock.close()
                last_error = exc
        raise OSError("WordPress connection failed") from last_error


class WordpressService:
    def _request(self, wp_url, wp_username, wp_app_password, method, path, payload=None):
        try:
            url = urlsplit(site_url(wp_url))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        credentials = base64.b64encode(f"{wp_username}:{wp_app_password}".encode()).decode()
        connection = PublicHTTPSConnection(url.hostname, timeout=6, context=_TLS)
        headers = {"Authorization": f"Basic {credentials}", "Accept": "application/json"}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        try:
            connection.request(method, f"{url.path}/wp-json/wp/v2/{path}", body, headers)
            response = connection.getresponse()
            if response.status in (401, 403):
                raise HTTPException(
                    422, "WordPress rejected the application password or account permissions"
                )
            if response.status not in (200, 201):
                raise IntegrationFailed("WordPress")
            data = response.read(1_000_001)
            if len(data) > 1_000_000:
                raise IntegrationFailed("WordPress")
            return json.loads(data)
        except (OSError, HTTPClientError, ValueError) as exc:
            raise IntegrationFailed("WordPress") from exc
        finally:
            connection.close()

    def verify(self, wp_url: str, wp_username: str, wp_app_password: str) -> None:
        if not settings.demo_mode:
            user = self._request(
                wp_url, wp_username, wp_app_password, "GET", "users/me?context=edit"
            )
            capabilities = user.get("capabilities") if isinstance(user, dict) else None
            if not isinstance(capabilities, dict) or not capabilities.get("publish_posts"):
                raise HTTPException(422, "The WordPress account needs permission to publish posts")

    def publish_post(self, wp_url, wp_username, wp_app_password, title, content, slug):
        if settings.demo_mode:
            return {"status": "demo", "url": None}

        lookup = "posts?" + urlencode(
            {"slug": slug, "status": "publish", "_fields": "slug,link,status"}
        )
        existing = self._request(wp_url, wp_username, wp_app_password, "GET", lookup)
        if not isinstance(existing, list):
            raise IntegrationFailed("WordPress")
        if existing:
            post = existing[0]
        else:
            post = self._request(
                wp_url,
                wp_username,
                wp_app_password,
                "POST",
                "posts?_fields=slug,link,status",
                {
                    "title": title,
                    "content": nh3.clean(_MARKDOWN.render(content)),
                    "status": "publish",
                    "slug": slug,
                },
            )

        if not isinstance(post, dict):
            raise IntegrationFailed("WordPress")
        link = post.get("link")
        try:
            link_url = urlsplit(link) if isinstance(link, str) else None
        except ValueError as exc:
            raise IntegrationFailed("WordPress") from exc
        if (
            post.get("slug") != slug
            or post.get("status") != "publish"
            or not link_url
            or link_url.scheme != "https"
            or not link_url.hostname
            or link_url.username is not None
            or len(link) > 2048
        ):
            raise IntegrationFailed("WordPress")
        return {"status": "published", "url": link}
