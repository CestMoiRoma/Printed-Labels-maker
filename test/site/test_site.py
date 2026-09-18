"""Structural guards on site/, the folder served as is (tests) and deployed as is (wrangler).

- every asset the HTML references exists, and every site file is referenced (no orphan), the Cloudflare
  configuration file _headers apart (not an asset, see test_headers.py);
- no URL outside the allow-list: the site loads nothing from a CDN but its fonts (Google Fonts);
- site/vendor/ holds exactly the files of its manifest, byte for byte (tools/vendor.py);
- the vendored icons and libraries cover what app.js asks for, and no font is vendored.
"""

import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
VENDOR = SITE / "vendor"
REFERENCE = REPO / "test" / "site" / "reference"

# Google Fonts stylesheets: the interface font (index.html) and a label font as loadFont() builds it
# (FONT_CSS in app.js).
UI_FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)
FONT_CSS_PREFIX = "https://fonts.googleapis.com/css2?family="
FONT_CSS_SUFFIX = ":wght@400;500;700&display=swap"
# Absolute URLs allowed in the site's own files: the SVG namespace (not fetched), the source link and the
# Google Fonts stylesheets.
ALLOWED_URLS = {
    "http://www.w3.org/2000/svg",
    "https://github.com/CestMoiRoma/Printed-Labels-maker",
    UI_FONTS_URL,
    FONT_CSS_PREFIX,
}
OWN_FILES = ["index.html", "styles.css", "app.js"]
# Cloudflare configuration read at deploy time, never served (wrangler leaves it out of the upload);
# checked by test_headers.py.
CONFIG_FILES = ["_headers"]


def manifest(path):
    return json.loads(path.read_text(encoding="utf-8"))


def own_text():
    return {name: (SITE / name).read_text(encoding="utf-8") for name in OWN_FILES}


def test_site_holds_only_its_own_files_and_vendor():
    top = sorted(p.name for p in SITE.iterdir() if not p.name.startswith("."))
    assert top == sorted(OWN_FILES + CONFIG_FILES + ["vendor"])


def test_html_references_exist():
    html = own_text()["index.html"]
    refs = re.findall(r'(?<![\w-])(?:src|href)="([^"#:]+)"', html)
    assert sorted(refs) == ["app.js", "styles.css", "vendor/qrcode-svg/qrcode.min.js"]
    for ref in refs:
        assert (SITE / ref).is_file(), ref
    assert '<link rel="stylesheet" href="' + UI_FONTS_URL + '">' in html


def test_no_url_outside_the_allow_list():
    for name, text in own_text().items():
        urls = set(re.findall(r"https?://[^\s\"'<>)]+", text))
        assert urls <= ALLOWED_URLS, f"{name}: {sorted(urls - ALLOWED_URLS)}"


def test_vendor_matches_its_manifest_byte_for_byte():
    for base, data in (
        (VENDOR, manifest(VENDOR / "SOURCES.json")),
        (REFERENCE / "vendor", manifest(REFERENCE / "SOURCES.json")),
    ):
        on_disk = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and p.name != "SOURCES.json")
        assert on_disk == sorted(data["files"])
        for rel, entry in data["files"].items():
            assert hashlib.sha256((base / rel).read_bytes()).hexdigest() == entry["sha256"], rel


def test_vendored_files_cover_what_the_app_loads():
    app = own_text()["app.js"]
    fonts = json.loads(re.search(r"const FONTS = (\[.*?\]);", app).group(1))
    icons = json.loads(re.search(r"const MAT = (\[.*?\]);", app).group(1))
    files = set(manifest(VENDOR / "SOURCES.json")["files"])
    missing_icons = set(manifest(VENDOR / "SOURCES.json")["meta"]["material-symbols"]["missing"])
    assert "vendor/mdi/mdi.js" in app and "mdi/mdi.js" in files
    # fonts come from Google Fonts, never from the site
    assert not any(rel.startswith("fonts/") for rel in files)
    assert '"' + FONT_CSS_PREFIX + '"' in app and '"' + FONT_CSS_SUFFIX + '"' in app
    assert fonts and all(re.fullmatch(r"[A-Z][A-Za-z ]+", family) for family in fonts), fonts
    for name in icons:
        assert name in missing_icons or "material-symbols/" + name + ".svg" in files, name
