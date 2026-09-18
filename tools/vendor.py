#!/usr/bin/env python3
"""Download the third-party files the site needs and pin them in a manifest.

Usage: tools/vendor.py            fetch everything, write the files and the manifests
       tools/vendor.py --check    verify the files on disk against the manifests (no network)

Outputs:
  site/vendor/                    files served by the site (QR generator, icons)
  site/vendor/SOURCES.json        local path -> source URL (as the Claude Design export requested it) + SHA-256
  test/site/reference/vendor/     React UMD builds, only needed to run a Claude Design export offline (fidelity.py)
  test/site/reference/SOURCES.json

A Claude Design export loads these from CDNs; the static site and the fidelity harness load them from
here. Fonts are not vendored: the site loads them from Google Fonts (tools/local.py downloads a copy to run
the site offline).
Native host tool (a build step): stdlib only.
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_VENDOR = ROOT / "site" / "vendor"
REF_VENDOR = ROOT / "test" / "site" / "reference" / "vendor"
APP = ROOT / "site" / "app.js"

MATERIAL_VERSION = "0.47.4"
MATERIAL_URL = "https://cdn.jsdelivr.net/npm/@material-symbols/svg-400/outlined/{name}.svg"
MATERIAL_PINNED = "https://cdn.jsdelivr.net/npm/@material-symbols/svg-400@{version}/outlined/{name}.svg"
# MAT names renamed upstream since the export was designed: the file is saved under the MAT name.
MATERIAL_RENAMED = {"cut": "content_cut", "smartphone": "mobile", "push_pin": "keep"}

SCRIPTS = {
    "qrcode-svg/qrcode.min.js": "https://cdn.jsdelivr.net/npm/qrcode-svg@1.1.0/lib/qrcode.min.js",
    "mdi/mdi.js": "https://cdn.jsdelivr.net/npm/@mdi/js@7.4.47/mdi.js",
}
REFERENCE_SCRIPTS = {
    "react.production.min.js": "https://unpkg.com/react@18.3.1/umd/react.production.min.js",
    "react-dom.production.min.js": "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
}


def app_icons():
    """The MAT array, read from site/app.js so the list never drifts."""
    match = re.search(r"const MAT = (\[.*?\]);", APP.read_text(encoding="utf-8"))
    return json.loads(match.group(1))


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "printed-labels-maker-vendor"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write(base, rel, data, manifest, url):
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest[rel] = {"url": url, "sha256": sha256(data)}


def run_fetch():
    site_manifest, ref_manifest = {}, {}

    for rel, url in SCRIPTS.items():
        write(SITE_VENDOR, rel, fetch(url), site_manifest, url)
    for rel, url in REFERENCE_SCRIPTS.items():
        write(REF_VENDOR, rel, fetch(url), ref_manifest, url)

    missing = []
    for name in app_icons():
        upstream = MATERIAL_RENAMED.get(name, name)
        pinned = MATERIAL_PINNED.format(version=MATERIAL_VERSION, name=upstream)
        try:
            data = fetch(pinned)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            missing.append(name)
            continue
        # a renamed icon records its real source: the design export's URL for the old name would 404
        source = pinned if upstream != name else MATERIAL_URL.format(name=name)
        write(SITE_VENDOR, "material-symbols/" + name + ".svg", data, site_manifest, source)

    meta = {"material-symbols": {"version": MATERIAL_VERSION, "missing": missing}}
    dump(SITE_VENDOR / "SOURCES.json", {"meta": meta, "files": site_manifest})
    dump(REF_VENDOR.parent / "SOURCES.json", {"files": ref_manifest})
    print(f"site/vendor: {len(site_manifest)} files; reference: {len(ref_manifest)} files; missing icons: {missing}")
    return 0


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_check():
    failures = 0
    for base in (SITE_VENDOR, REF_VENDOR):
        manifest = json.loads(
            (base.parent / "SOURCES.json" if base == REF_VENDOR else base / "SOURCES.json").read_text()
        )
        for rel, entry in manifest["files"].items():
            path = base / rel
            if not path.is_file() or sha256(path.read_bytes()) != entry["sha256"]:
                failures += 1
                print(f"{path.relative_to(ROOT)}: missing or modified")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the files against the manifests")
    sys.exit(run_check() if parser.parse_args().check else run_fetch())
