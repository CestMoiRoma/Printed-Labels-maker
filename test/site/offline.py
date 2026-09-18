"""Serve a folder locally and answer every CDN request from the vendored files: only Google Fonts is reached.

Shared by the end-to-end scenario and the fidelity harness. The design export requests its libraries from
unpkg and jsdelivr; `route_offline` answers those URLs from `site/vendor/` and `test/site/reference/vendor/`
(the manifests map each source URL to its local file). Fonts, the site's and the export's, are loaded from
Google Fonts for real, as in production. Any other external request is aborted and recorded, so a new
dependency fails the run instead of silently hitting the network.

`serve` applies the served folder's Cloudflare `_headers` file (site/_headers) to every response, so the
scenario runs under the production headers, Content-Security-Policy included.
"""

import functools
import http.server
import json
import mimetypes
import re
import threading
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
SITE_VENDOR = REPO / "site" / "vendor"
REF_VENDOR = REPO / "test" / "site" / "reference" / "vendor"

CONTENT_TYPES = {".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml"}
# Loaded from the network: the fonts are not vendored (index.html, loadFont in app.js).
GOOGLE_FONTS_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")

HEADERS_FILE = "_headers"
# Limits of the Cloudflare parser (wrangler's parseHeaders): over them, lines or rules are dropped.
MAX_HEADER_RULES = 100
MAX_LINE_LENGTH = 2000


def parse_headers_file(path):
    """Rules of a Cloudflare `_headers` file, in file order: [(path pattern, {name: value}, [removed names])].

    Same grammar as Cloudflare's parser: `#` comments, a line starting with `/` opens a rule, then indented
    `Name: value` lines (names lowercased, a repeated name joined with ", ") or `! Name` to remove a header
    set by an earlier rule. Cloudflare skips what it cannot parse; here any such line raises ValueError, so
    a typo fails the tests instead of silently dropping a header in production. `*` splats are supported,
    `:placeholder` patterns and absolute URLs are not (the site uses neither).
    """
    rules = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        where = f"{path.name}:{number}"
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if len(line) > MAX_LINE_LENGTH:
            raise ValueError(f"{where}: longer than {MAX_LINE_LENGTH} characters")
        if line.startswith("/"):
            if ":" in line or " " in line or line.count("*") > 1:
                raise ValueError(f"{where}: unsupported path pattern {line!r}")
            if rules and not (rules[-1][1] or rules[-1][2]):
                raise ValueError(f"{where}: rule {rules[-1][0]!r} has no header")
            rules.append((line, {}, []))
        elif not rules:
            raise ValueError(f"{where}: header line before any path")
        elif line.startswith("! "):
            rules[-1][2].append(line[2:].strip().lower())
        elif ":" in line:
            name, value = (part.strip() for part in line.split(":", 1))
            name = name.lower()
            if not name or " " in name or not value:
                raise ValueError(f"{where}: expected 'Name: value', got {line!r}")
            headers = rules[-1][1]
            headers[name] = f"{headers[name]}, {value}" if name in headers else value
        else:
            raise ValueError(f"{where}: expected 'Name: value' or '! Name', got {line!r}")
    if rules and not (rules[-1][1] or rules[-1][2]):
        raise ValueError(f"{path.name}: rule {rules[-1][0]!r} has no header")
    if len(rules) > MAX_HEADER_RULES:
        raise ValueError(f"{path.name}: more than {MAX_HEADER_RULES} rules")
    return rules


def rule_matches(pattern, url_path):
    """A rule's path pattern matches the whole URL path; `*` matches anything, `/` included."""
    return re.fullmatch(re.escape(pattern).replace(r"\*", ".*"), url_path) is not None


def headers_for(rules, url_path):
    """Headers the rules give to `url_path`: every matching rule in order, removals first, repeats joined."""
    result = {}
    for pattern, headers, removed in rules:
        if not rule_matches(pattern, url_path):
            continue
        for name in removed:
            result.pop(name, None)
        for name, value in headers.items():
            result[name] = f"{result[name]}, {value}" if name in result else value
    return result


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    # Rules of the served folder's _headers file (set per server by `serve`); empty when it has none.
    header_rules = ()

    def log_message(self, *args):
        pass

    def send_head(self):
        # Like Cloudflare, the _headers file configures the responses and is never served itself.
        if self.header_rules and urlsplit(self.path).path == "/" + HEADERS_FILE:
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        for name, value in headers_for(self.header_rules, urlsplit(self.path).path).items():
            self.send_header(name, value)
        super().end_headers()


def serve(folder):
    """Serve `folder` over HTTP on a free local port in a daemon thread; returns (base_url, server).

    When `folder` holds a Cloudflare `_headers` file (site/ does), every response carries the headers its
    rules give in production: the scenario runs under the production Content-Security-Policy.
    """
    headers_file = Path(folder) / HEADERS_FILE
    rules = tuple(parse_headers_file(headers_file)) if headers_file.is_file() else ()
    handler = functools.partial(type("_Handler", (_QuietHandler,), {"header_rules": rules}), directory=str(folder))
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
        if host in ("127.0.0.1", "localhost", *GOOGLE_FONTS_HOSTS) or url.startswith(("data:", "blob:")):
            route.continue_()
            return
        path = mapping.get(url)
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
