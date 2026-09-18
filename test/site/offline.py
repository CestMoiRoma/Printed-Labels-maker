"""Serve a folder locally and answer every CDN request from the vendored files: nothing leaves the machine.

Shared by the end-to-end scenario and the fidelity harness. The design export requests its libraries and
fonts from unpkg, jsdelivr and Google Fonts; `route_offline` answers those URLs from `site/vendor/` and
`test/site/reference/vendor/` (the manifests map each source URL to its local file). Any other external
request is aborted and recorded, so a new dependency fails the run instead of silently hitting the network.
"""

import functools
import http.server
import json
import mimetypes
import threading
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
SITE_VENDOR = REPO / "site" / "vendor"
REF_VENDOR = REPO / "test" / "site" / "reference" / "vendor"

CONTENT_TYPES = {".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".woff2": "font/woff2"}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(folder):
    """Serve `folder` over HTTP on a free local port in a daemon thread; returns (base_url, server)."""
    handler = functools.partial(_QuietHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}/", server


def _url_map():
    mapping = {}
    for base, manifest in (
        (SITE_VENDOR, SITE_VENDOR / "SOURCES.json"),
        (REF_VENDOR, REF_VENDOR.parent / "SOURCES.json"),
    ):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for rel, entry in data["files"].items():
            mapping[entry["url"]] = base / rel
    return mapping


def _missing_icon_urls():
    data = json.loads((SITE_VENDOR / "SOURCES.json").read_text(encoding="utf-8"))
    template = "https://cdn.jsdelivr.net/npm/@material-symbols/svg-400/outlined/{}.svg"
    return {template.format(name) for name in data["meta"]["material-symbols"]["missing"]}


def route_offline(context, blocked):
    """Answer CDN URLs from the vendored files on every page of `context`; append refused URLs to `blocked`."""
    mapping = _url_map()
    missing = _missing_icon_urls()

    def handle(route):
        url = route.request.url
        host = urlsplit(url).hostname
        if host in ("127.0.0.1", "localhost") or url.startswith(("data:", "blob:")):
            route.continue_()
            return
        path = mapping.get(url)
        if path is None and host == "fonts.googleapis.com" and not urlsplit(url).path.startswith("/css"):
            # woff2 files referenced relatively from a vendored stylesheet served under that origin
            path = SITE_VENDOR / "fonts" / urlsplit(url).path.lstrip("/")
        headers = {"access-control-allow-origin": "*"}
        if path is not None and path.is_file():
            content_type = (
                CONTENT_TYPES.get(path.suffix) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            )
            route.fulfill(status=200, headers=headers, content_type=content_type, body=path.read_bytes())
        elif url in missing:
            route.fulfill(status=404, headers=headers, content_type="text/plain", body="Not found")
        else:
            blocked.append(url)
            route.abort()

    context.route("**/*", handle)
