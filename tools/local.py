#!/usr/bin/env python3
"""Run the site offline: download its fonts once, then serve site/ with Google Fonts pointed at them.

Usage: tools/local.py [PORT]      (just local), then open http://127.0.0.1:PORT/

In production the fonts come from Google Fonts: the interface font from index.html, the label fonts from
loadFont() in app.js. The first run downloads every stylesheet they request, and the woff2 files those point
to, into local/fonts/ (git-ignored, never deployed). Later runs only fetch what is missing, so once every
font is there the site runs with no network at all. Delete local/fonts/ to download them again.

The server serves site/ as is, except that index.html and app.js get the Google Fonts stylesheet URL
rewritten to /fonts/css2, which answers with the downloaded stylesheet for the same query. The production
code has no local mode: this rewrite is the whole trick. site/_headers is not applied (no CSP locally).
Native host tool: stdlib, plus curl for the downloads (it uses the system's certificates, which a python.org
Python on macOS does not).
"""

import hashlib
import http.server
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
FONTS_DIR = ROOT / "local" / "fonts"
INDEX = FONTS_DIR / "index.json"

GOOGLE_CSS = "https://fonts.googleapis.com/css2"
LOCAL_CSS = "/fonts/css2"
GSTATIC = "https://fonts.gstatic.com/"
# A current Chrome user agent: Google Fonts serves woff2 with unicode-range subsets for it.
CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
# Files whose Google Fonts URLs are rewritten on the fly.
REWRITTEN = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js"}
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8"}


def font_urls():
    """Every Google Fonts stylesheet the site requests, read from index.html and app.js so it never drifts."""
    html = (SITE / "index.html").read_text(encoding="utf-8")
    app = (SITE / "app.js").read_text(encoding="utf-8")
    urls = re.findall(r'href="(' + re.escape(GOOGLE_CSS) + r'\?[^"]+)"', html)
    fonts = re.search(r"const FONTS = (\[.*?\]);", app)
    # FONT_CSS in app.js: prefix + family with its spaces as "+" + suffix
    pattern = re.search(r'const FONT_CSS = \(f\) => "([^"]+)" \+ f\.replace\(/\\s\+/g, "\+"\) \+ "([^"]+)";', app)
    if not urls or not fonts or not pattern:
        sys.exit("tools/local.py: the Google Fonts URLs of index.html or app.js are not where expected")
    prefix, suffix = pattern.groups()
    return urls + [prefix + family.replace(" ", "+") + suffix for family in json.loads(fonts.group(1))]


def fetch(url):
    return subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "60", "-A", CHROME_UA, url],
        check=True,
        capture_output=True,
    ).stdout


def download(url):
    """Save one stylesheet and its woff2 files; returns the stylesheet's name in local/fonts/."""
    css = fetch(url).decode("utf-8")

    def localize(match):
        rel = match.group(1)
        path = FONTS_DIR / "gstatic" / rel
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fetch(GSTATIC + rel))
        return "url(/fonts/gstatic/" + rel + ")"

    css = re.sub(r"url\(" + re.escape(GSTATIC) + r"([^)]+)\)", localize, css)
    name = "css/" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16] + ".css"
    (FONTS_DIR / "css").mkdir(parents=True, exist_ok=True)
    (FONTS_DIR / name).write_text(css, encoding="utf-8")
    return name


def sync_fonts():
    """Download the stylesheets not in local/fonts/ yet; returns {Google URL: stylesheet name}."""
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.is_file() else {}
    missing = [url for url in font_urls() if url not in index or not (FONTS_DIR / index[url]).is_file()]
    for number, url in enumerate(missing, 1):
        print(f"[{number}/{len(missing)}] {url}", flush=True)
        try:
            index[url] = download(url)
        except subprocess.CalledProcessError as error:
            reason = error.stderr.decode("utf-8", "replace").strip()
            sys.exit(f"tools/local.py: cannot download {url} ({reason}); the first run needs the network")
        INDEX.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index


class Handler(http.server.SimpleHTTPRequestHandler):
    index = {}  # {Google URL: stylesheet name}, set by main()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, *args):
        pass

    def send_head(self):
        path, _, query = self.path.partition("?")
        path = unquote(path)
        if path == LOCAL_CSS:
            by_query = {unquote(url.partition("?")[2]): name for url, name in self.index.items()}
            name = by_query.get(unquote(query))
            if name is None:
                return self.not_found()
            return self.send_bytes((FONTS_DIR / name).read_bytes(), "text/css; charset=utf-8")
        if path.startswith("/fonts/gstatic/"):
            file = (FONTS_DIR / path.removeprefix("/fonts/")).resolve()
            if file.is_relative_to(FONTS_DIR) and file.is_file():
                return self.send_bytes(file.read_bytes(), "font/woff2")
            return self.not_found()
        if path in REWRITTEN:
            name = REWRITTEN[path]
            text = (SITE / name).read_text(encoding="utf-8").replace(GOOGLE_CSS, LOCAL_CSS)
            return self.send_bytes(text.encode("utf-8"), CONTENT_TYPES[Path(name).suffix])
        if path == "/_headers":
            # like Cloudflare, the headers file is configuration, never served
            return self.not_found()
        return super().send_head()

    def not_found(self):
        self.send_error(404)

    def send_bytes(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return io.BytesIO(body)


def main(port):
    Handler.index = sync_fonts()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"{len(Handler.index)} font stylesheets in {FONTS_DIR.relative_to(ROOT)}/")
    print(f"serving site/ offline on http://127.0.0.1:{port}/ (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8000))
