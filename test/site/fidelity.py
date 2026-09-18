"""Fidelity proof: the static site renders exactly like the Claude Design export it replaces.

Usage: fidelity.py OUT_DIR

Plays the same scenario on design/label-generator.dc.html (run offline: CDN requests are answered from the
vendored files) and on site/index.html, in the same deterministic browser (test/ci/golden.py). For every
state it compares:
  - full-page screenshots, pixel for pixel, no tolerance;
  - the downloaded "SVG (1 label)" and "SVG sheet" files, byte for byte (in the states that export);
  - the number of pages of the printed PDF.
The site must also log no console error and no page error (the export logs some while booting, they are
reported, not fatal). Each differing state writes export / site / diff PNGs to OUT_DIR. Exit 1 on any
difference. docs/review.md section 6 describes the method.

It proved commit 26dce88 (the faithful rewrite: 20 states identical). The fix: commits after it change
the rendering on purpose (docs/review.md section 4), so today it reports those differences: it is a
one-off proof, not a gate. Re-run it against a new Claude Design export to see what the design changed.
"""

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))
import golden  # noqa: E402
import offline  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TARGETS = {
    "export": (REPO / "design", "label-generator.dc.html", "#dc-root aside"),
    "site": (REPO / "site", "index.html", "aside.sidebar"),
}


def ready(page, font="Archivo"):
    page.wait_for_function(
        """(font) => document.fonts.check('700 16px "' + font + '"') && document.fonts.check('400 16px "' + font + '"')""",
        arg=font,
    )
    page.evaluate("document.fonts.ready.then(() => undefined)")
    golden.settle(page)


def button(page, name):
    return page.get_by_role("button", name=name, exact=True)


def scenario(page):
    """Yield (state name, kind) after each step; kind is None, "export" or "pdf" for extra checks."""
    ready(page)
    yield "01-home", "export"

    button(page, "FR").click()
    yield "02-lang-menu", None
    button(page, "Français").click()

    page.locator("details summary").click()
    page.locator('textarea[data-k="pasteText"]').fill("Vis | Atelier | M3, M4 | V-001 | 01/2026")
    yield "03-import-open", None
    page.locator("details summary").click()

    page.locator('button[data-i="1"]').first.click()
    yield "04-second-row", None
    page.locator('button[data-i="0"]').first.click()

    page.locator('input[data-k="title"]').fill("Visserie inox très longue désignation")
    page.locator('input[data-k="subtitle"]').fill("")
    page.locator('textarea[data-k="contents"]').fill("M3\nM4, M5; M6")
    yield "05-edited", "export"

    button(page, "+ Ajouter une étiquette").click()
    yield "06-added", None
    page.locator('button[title="Dupliquer"]').nth(1).click()
    page.locator('button[title="Supprimer"]').nth(4).click()
    page.locator('input[data-i="0"][type="number"]').fill("12")
    yield "07-copies", None

    button(page, "2 · Style").click()
    yield "08-style-tab", None
    button(page, "70×37").click()
    page.locator('input[data-k="qr"]').check()
    page.locator('input[data-k="autoFit"]').uncheck()
    page.locator('select[data-k="align"]').select_option("center")
    page.locator('select[data-k="listStyle"]').select_option("inline")
    yield "09-style-edited", "export"

    page.locator('select[data-k="font"], select[data-k="fontChoice"]').select_option("Bitter")
    ready(page, "Bitter")
    yield "10-font-bitter", "export"

    button(page, "1 · Contenu").click()
    button(page, "Material").click()
    # same race as MDI below: let the unfiltered list arrive before filtering it
    page.wait_for_function("() => document.querySelectorAll('button[data-name][data-vb]').length === 42")
    page.locator('input[data-k="iconQuery"]').fill("home")
    page.wait_for_function("() => document.querySelectorAll('button[data-name][data-vb]').length === 1")
    golden.settle(page)
    yield "11-material-search", None
    page.locator('button[data-name="home"]').click()
    yield "12-icon-and-qr", "export"

    button(page, "MDI").click()
    # wait for the "home" results first: a second query sent before the first answer races with it (review I10)
    page.locator('button[data-name="home"][data-vb="0 0 24 24"]').wait_for()
    page.locator('input[data-k="iconQuery"]').fill("cable-data")
    page.wait_for_function("() => document.querySelectorAll('button[data-name][data-vb]').length === 1")
    page.locator('button[data-name="cable-data"]').wait_for()
    golden.settle(page)
    yield "13-mdi-search", None
    page.locator('button[data-name="cable-data"]').click()
    button(page, "Aucun").click()
    yield "14-icon-removed", None

    button(page, "3 · Impression").click()
    page.locator('select[data-k="mode"]').select_option("single")
    yield "15-print-single", "pdf"
    page.locator('select[data-k="mode"]').select_option("batch")
    page.locator('input[data-k="cut"]').uncheck()
    page.locator('input[data-k="gap"]').fill("0")
    yield "16-print-batch", "pdf"

    button(page, "Page entière").click()
    yield "17-full-page", "pdf"
    page.emulate_media(media="print")
    golden.settle(page)
    yield "18-print-media", None
    page.emulate_media(media="screen")

    button(page, "FR").click()
    button(page, "Deutsch").click()
    yield "19-deutsch", None
    button(page, "DE").click()
    button(page, "English (US)").click()
    yield "20-english", None


def run_target(browser, name, out_dir):
    folder, entry, marker = TARGETS[name]
    base, server = offline.serve(folder)
    blocked, errors = [], []
    page = golden.new_page(browser)
    offline.route_offline(page.context, blocked)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    page.goto(base + entry)
    page.wait_for_selector(marker)
    states = {}
    for state, kind in scenario(page):
        golden.settle(page)
        entry_data = {"png": page.screenshot(full_page=True, animations="disabled", caret="hide", scale="css")}
        if kind == "export":
            for label, button_name in (("svg", "SVG (1 étiquette)"), ("sheet", "SVG planche")):
                with page.expect_download() as download:
                    button(page, button_name).click()
                entry_data[label] = Path(download.value.path()).read_bytes()
        if kind == "pdf":
            entry_data["pdf_pages"] = len(re.findall(rb"/Type\s*/Page(?!s)", page.pdf(prefer_css_page_size=True)))
        states[state] = entry_data
    page.context.close()
    server.shutdown()
    return states, blocked, errors


def compare(export, site, out_dir):
    failures = []
    for state, ref in export.items():
        got = site.get(state)
        if got is None:
            failures.append(f"{state}: missing on the site")
            continue
        a = Image.open(io.BytesIO(ref["png"])).convert("RGB")
        b = Image.open(io.BytesIO(got["png"])).convert("RGB")
        if a.size != b.size:
            failures.append(f"{state}: size {a.size} (export) vs {b.size} (site)")
            bbox = "size"
        else:
            bbox = ImageChops.difference(a, b).getbbox()
            if bbox:
                failures.append(f"{state}: pixels differ in {bbox}")
        if bbox:
            golden.write_png(out_dir / f"{state}-export.png", ref["png"])
            golden.write_png(out_dir / f"{state}-site.png", got["png"])
            if bbox != "size":
                diff = ImageChops.difference(a, b).point(lambda v: 255 if v else 0)
                buffer = io.BytesIO()
                diff.save(buffer, "PNG")
                golden.write_png(out_dir / f"{state}-diff.png", buffer.getvalue())
        for key in ("svg", "sheet", "pdf_pages"):
            if key in ref and ref[key] != got.get(key):
                failures.append(f"{state}: {key} differs")
                if key != "pdf_pages":
                    (out_dir / f"{state}-export.{key}.svg").write_bytes(ref[key])
                    (out_dir / f"{state}-site.{key}.svg").write_bytes(got.get(key, b""))
    return failures


def main(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*"):
        old.unlink()
    with sync_playwright() as p:
        browser = golden.launch(p)
        export, export_blocked, export_errors = run_target(browser, "export", out_dir)
        site, site_blocked, site_errors = run_target(browser, "site", out_dir)
        browser.close()
    failures = compare(export, site, out_dir)
    failures += [f"site: blocked request {u}" for u in site_blocked]
    failures += [f"export: blocked request {u}" for u in export_blocked]
    # The site may reproduce an error the export also logs (fixed in a later commit), never add one
    failures += [f"site: {e}" for e in site_errors if e not in export_errors]
    for e in sorted(set(site_errors) & set(export_errors)):
        print(f"(site and export, inherited) {e}")
    for e in export_errors:
        print(f"(export, not fatal) {e}")
    for state in export:
        status = "DIFFERENT" if any(f.startswith(state + ":") for f in failures) else "identical"
        print(f"{state}: {status}")
    for f in failures:
        print(f"FAIL {f}")
    print(f"{len(export)} states, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
