"""End-to-end scenario on the served site + GUI goldens. Usage: screenshots.py OUT_DIR

Serves APP_STATIC (site/, exactly the folder wrangler deploys) on a free local port and drives it in the
deterministic Chromium of test/ci/golden.py through every screen and state of docs/review.md annex B:
language menu, pasted import, row list edits, the three tabs, presets, QR, auto-fit, fonts, numeric errors,
icon search (loading, results, empty), image import, print modes, full-page view, print media, PDF and
downloads, and two more languages. Each step asserts behaviour (verbatim texts, visible elements, counts)
before its capture. Any page error, console error, request leaving the machine or missing element fails.

Captures are desktop viewport screenshots (1280x820) named NN-state.png in scenario order. Before every
capture the focus is dropped and every scroll position is set: document, main area, fields and icon grid at
their start, the sidebar at its top, at its bottom or with a given element at its top edge, the label list at
its top or bottom. States that live below the fold (the sheets of the full-page view, the printed pages) are
element screenshots.
"""

import os
import re
import struct
import sys
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))
import golden  # noqa: E402
import offline  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
APP_STATIC = Path(os.environ.get("APP_STATIC", REPO / "site"))

PASTED = "\n".join(
    [
        "Vis inox | Atelier — tiroir 2 | M3, M4, M5 | V-001 | 01/2026",
        "Chevilles | Atelier | 6 mm, 8 mm, 10 mm | V-002 | 01/2026 | QR-V-002",
        " | Cave | Bouteilles, bocaux | V-003",
        "Colliers de serrage | Garage | Petits, moyens, grands | V-004 | 02/2026",
    ]
)

# Small fixed SVG for the image import: its data URL is the same on every run.
UPLOAD_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    b'<rect x="2" y="2" width="20" height="20" rx="4" fill="#2f6f4f"/>'
    b'<circle cx="12" cy="12" r="5" fill="#f4c542"/></svg>'
)

# Where the mouse rests during captures: bottom right of the main area, over nothing that reacts to hover.
MOUSE_REST = (1270, 810)

# Focus is dropped first: a focused field would show its caret position (scrolled text) and spin buttons.
_PLACE = """([sidebarAnchor, rowsAt]) => {
  if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur()
  window.scrollTo(0, 0)
  const sidebar = document.querySelector('.sidebar')
  sidebar.scrollTop = 0
  if (sidebarAnchor === 'bottom') {
    sidebar.scrollTop = sidebar.scrollHeight
  } else if (sidebarAnchor) {
    const top = document.querySelector(sidebarAnchor).getBoundingClientRect().top
    sidebar.scrollTop = top - sidebar.getBoundingClientRect().top
  }
  const rows = document.querySelector('.rows')
  rows.scrollTop = rowsAt === 'bottom' ? rows.scrollHeight : 0
  for (const el of document.querySelectorAll('.icon-grid, .canvas, .real-label, .sheets, textarea, input')) {
    el.scrollTop = 0
    el.scrollLeft = 0
  }
}"""


class Scenario:
    def __init__(self, page, out_dir):
        self.page = page
        self.out_dir = out_dir
        self.captures = []

    # ---------- helpers ----------

    def button(self, name):
        return self.page.get_by_role("button", name=name, exact=True)

    def bind(self, name):
        return self.page.locator(f'[data-bind="{name}"]')

    def field(self, key):
        return self.page.locator(f'[data-k="{key}"]')

    def preview_svg(self):
        return self.page.locator(".label-preview").inner_html()

    def fonts_ready(self, font):
        """The label font's 400 and 700 faces are loaded and every label text of the preview uses it."""
        self.page.wait_for_function(
            """(font) => document.fonts.check('700 16px "' + font + '"') && document.fonts.check('400 16px "' + font + '"')
              && document.querySelectorAll('.label-preview text').length > 0
              && [...document.querySelectorAll('.label-preview text')]
                   .every((t) => t.getAttribute('font-family').startsWith(font + ','))""",
            arg=font,
        )

    def icon_cells(self, count):
        """Exactly `count` icon results are shown (the answer to the latest search has arrived)."""
        expect(self.page.locator(".icon-grid .icon-cell")).to_have_count(count)

    def rows(self, titles):
        expect(self.page.locator(".rows .row-title")).to_have_text(titles)

    def shot(self, name, sidebar=None, rows="top", element=None):
        """Deterministic scroll positions, mouse at rest, settled page, then the capture."""
        self.page.evaluate(_PLACE, [sidebar, rows])
        self.page.mouse.move(*MOUSE_REST)
        golden.settle(self.page)
        target = self.page.locator(element) if element else self.page
        number = len(self.captures) + 1
        path = self.out_dir / f"{number:02d}-{name}.png"
        golden.screenshot(target, path)
        self.captures.append(path.name)

    def download(self, button_name, filename, magic):
        with self.page.expect_download() as info:
            self.button(button_name).click()
        assert info.value.suggested_filename == filename, info.value.suggested_filename
        data = Path(info.value.path()).read_bytes()
        assert data.startswith(magic), (filename, data[:40])
        return data

    def pdf_pages(self):
        pdf = self.page.pdf(prefer_css_page_size=True)
        pages = len(re.findall(rb"/Type\s*/Page(?!s)", pdf))
        sheets = self.page.locator(".print-sheet").count()
        assert pages == sheets, f"PDF has {pages} page(s), the print area {sheets} sheet(s)"
        return pages

    # ---------- the scenario ----------

    def run(self):
        page = self.page
        self.fonts_ready("Archivo")

        # home: the three demo labels, default size and grid (docs/review.md annex B, initial state)
        expect(page.locator("h1.app-title")).to_have_text("Étiquettes de boîtes")
        expect(page.locator(".kicker")).to_have_text("Générateur")
        expect(page.locator(".app-sub")).to_have_text("SVG en millimètres, planche A4 avec traits de coupe.")
        self.rows(["Câbles & chargeurs", "Outils à main", "Papeterie"])
        expect(page.locator(".rows .row-sub")).to_have_text(
            ["B-014 · Bureau — étagère haute", "B-015 · Atelier", "B-016 · Bureau"]
        )
        expect(page.locator(".row-main.is-selected")).to_have_count(1)
        expect(self.bind("countsLine")).to_have_text("3 modèle(s) · 3 au total")
        expect(self.bind("gridInfo")).to_have_text("2 × 5 = 10 étiquettes par page A4 · 3 au total")
        expect(self.bind("editLine")).to_have_text("Édition — 90 × 50 mm · zoom ×1,59")
        expect(self.bind("selNo")).to_have_text("1")
        expect(self.bind("iconSourceLabel")).to_have_text("aucun")
        expect(page.locator(".side-foot > span")).to_have_text("v1.0.0")
        expect(page.locator(".source-link")).to_have_text("Code source")
        expect(page.locator(".source-link")).to_have_attribute(
            "href", "https://github.com/CestMoiRoma/Printed-Labels-maker"
        )
        expect(page.locator(".tab")).to_have_text(["1 · Contenu", "2 · Style", "3 · Impression"])
        expect(page.locator(".tab.is-active")).to_have_text("1 · Contenu")
        for name in ("SVG (1 étiquette)", "PNG 300 dpi", "SVG planche", "Imprimer / PDF A4"):
            expect(self.button(name)).to_be_visible()
        expect(self.field("title")).to_have_value("Câbles & chargeurs")
        expect(self.field("qrText")).to_be_hidden()
        expect(page.locator(".icon-search")).to_be_hidden()
        expect(page.locator(".lang-menu")).to_be_hidden()
        expect(page.locator(".real-label svg")).to_be_visible()
        expect(page.locator(".real-page")).to_be_hidden()
        assert "Câbles &amp; chargeurs" in self.preview_svg()
        self.shot("home")

        # downloads: well-formed SVG files of the label and of the first sheet, the label as a 300 dpi PNG
        label = self.download("SVG (1 étiquette)", "etiquette-90x50mm.svg", b"<svg")
        assert ElementTree.fromstring(label).get("width") == "90mm"
        sheet = self.download("SVG planche", "planche-a4.svg", b"<svg")
        assert ElementTree.fromstring(sheet).get("height") == "297mm" and sheet.count(b"clip-path=") == 3
        png = self.download("PNG 300 dpi", "etiquette-90x50mm@300dpi.png", b"\x89PNG\r\n\x1a\n")
        assert struct.unpack(">II", png[16:24]) == (1063, 591)

        # language menu: seven languages, the current one highlighted
        self.button("FR").click()
        expect(page.locator(".lang-menu")).to_be_visible()
        expect(page.locator(".lang-option")).to_have_text(
            ["Français", "English (US)", "Español", "Deutsch", "Italiano", "Português", "Nederlands"]
        )
        expect(page.locator(".lang-option.is-current")).to_have_text("Français")
        self.shot("language-menu")
        self.button("Français").click()
        expect(page.locator(".lang-menu")).to_be_hidden()

        # pasted import: open, text typed, then applied
        page.locator("details.import summary").click()
        expect(page.locator(".import-format")).to_have_text("Titre | Sous-titre | contenu, contenu | code | date")
        expect(self.field("pasteText")).to_have_attribute("placeholder", "Une ligne par étiquette")
        self.field("pasteText").fill(PASTED)
        expect(self.button("Remplacer la liste")).to_be_visible()
        self.shot("import-open")
        self.button("Remplacer la liste").click()
        self.rows(["Vis inox", "Chevilles", "(sans titre)", "Colliers de serrage"])
        expect(page.locator(".rows .row-sub")).to_have_text(
            ["V-001 · Atelier — tiroir 2", "V-002 · Atelier", "V-003 · Cave", "V-004 · Garage"]
        )
        expect(self.bind("countsLine")).to_have_text("4 modèle(s) · 4 au total")
        expect(self.field("pasteText")).to_have_value("")
        expect(self.field("title")).to_have_value("Vis inox")
        expect(self.field("date")).to_have_value("01/2026")
        self.shot("import-applied")
        page.locator("details.import summary").click()
        expect(self.field("pasteText")).to_be_hidden()

        # row selection
        page.locator(".row-main").nth(1).click()
        expect(page.locator(".row-main").nth(1)).to_have_class(re.compile(r"\bis-selected\b"))
        expect(page.locator(".row-main.is-selected")).to_have_count(1)
        expect(self.bind("selNo")).to_have_text("2")
        expect(self.field("title")).to_have_value("Chevilles")
        expect(self.field("contents")).to_have_value("6 mm, 8 mm, 10 mm")
        self.shot("row-selected")

        # content edited: a long title and a long code, fitted in the label's width and height
        self.field("title").fill("Chevilles à frapper nylon pour béton plein et creux")
        self.field("subtitle").fill("")
        self.field("code").fill("V-002-NYLON-BETON-PLEIN")
        expect(page.locator(".rows .row-title").nth(1)).to_have_text(
            "Chevilles à frapper nylon pour béton plein et creux"
        )
        expect(page.locator(".rows .row-sub").nth(1)).to_have_text("V-002-NYLON-BETON-PLEIN")
        expect(page.locator(".label-preview text").last).to_have_text("V-002-NYLON-BETON-PLEIN   01/2026")
        overflow = page.evaluate(
            """() => {
              const svg = document.querySelector('.label-preview svg')
              const [, , w, h] = svg.getAttribute('viewBox').split(' ').map(Number)
              const boxes = [...svg.querySelectorAll('text')].map((t) => t.getBBox())
              return { right: Math.max(...boxes.map((b) => b.x + b.width)), bottom: Math.max(...boxes.map((b) => b.y + b.height)), w, h }
            }"""
        )
        assert overflow["right"] <= overflow["w"] and overflow["bottom"] <= overflow["h"], overflow
        self.shot("content-edited")

        # add a label: the form of a new label, only the date kept
        self.button("+ Ajouter une étiquette").click()
        self.rows(
            [
                "Vis inox",
                "Chevilles à frapper nylon pour béton plein et creux",
                "(sans titre)",
                "Colliers de serrage",
                "Nouvelle étiquette",
            ]
        )
        expect(self.bind("selNo")).to_have_text("5")
        expect(self.field("title")).to_have_value("Nouvelle étiquette")
        for key, placeholder in (
            ("subtitle", "Sous-titre"),
            ("contents", "Contenu, séparé par des virgules ou des retours à la ligne"),
            ("code", "Code / n°"),
        ):
            expect(self.field(key)).to_have_value("")
            expect(self.field(key)).to_have_attribute("placeholder", placeholder)
        expect(self.field("date")).to_have_value("01/2026")
        expect(self.bind("countsLine")).to_have_text("5 modèle(s) · 5 au total")
        self.shot("row-added", rows="bottom")

        # duplicate, delete, copies: the list scrolls past 220 px
        page.locator('.row-btn[title="Dupliquer"]').nth(0).click()
        expect(self.bind("selNo")).to_have_text("2")
        page.locator('.row-btn-remove[title="Supprimer"]').nth(5).click()
        page.locator(".row-copies").nth(0).fill("12")
        self.rows(
            [
                "Vis inox",
                "Vis inox",
                "Chevilles à frapper nylon pour béton plein et creux",
                "(sans titre)",
                "Colliers de serrage",
            ]
        )
        expect(page.locator(".row-copies").nth(0)).to_have_value("12")
        page.locator(".row-main").nth(2).click()
        expect(self.bind("selNo")).to_have_text("3")
        expect(page.locator(".row-main").nth(2)).to_have_class(re.compile(r"\bis-selected\b"))
        expect(self.bind("countsLine")).to_have_text("5 modèle(s) · 16 au total")
        expect(self.bind("gridInfo")).to_have_text("2 × 5 = 10 étiquettes par page A4 · 16 au total")
        assert page.evaluate("() => document.querySelector('.rows').scrollHeight > 220")
        self.shot("rows-edited")

        # style tab
        self.button("2 · Style").click()
        expect(page.locator(".tab.is-active")).to_have_text("2 · Style")
        expect(page.locator('[data-panel="style"]')).to_be_visible()
        expect(page.locator('[data-panel="content"]')).to_be_hidden()
        expect(self.field("w")).to_have_value("90")
        expect(self.field("h")).to_have_value("50")
        expect(self.field("fontChoice")).to_have_value("Archivo")
        expect(page.locator(".preset")).to_have_text(["90×50", "70×37", "105×48", "50×50"])
        self.shot("style-tab", sidebar=".tabs")

        # preset
        self.button("70×37").click()
        expect(self.field("w")).to_have_value("70")
        expect(self.field("h")).to_have_value("37")
        expect(self.bind("editLine")).to_have_text("Édition — 70 × 37 mm · zoom ×2,04")
        expect(self.bind("gridInfo")).to_have_text("2 × 7 = 14 étiquettes par page A4 · 16 au total")
        self.shot("preset-70x37", sidebar=".tabs")

        # QR code on: a QR column next to the text
        self.field("qr").check()
        expect(self.field("qr")).to_be_checked()
        expect(page.locator(".label-preview svg > g")).to_have_count(1)
        self.shot("qr-on", sidebar="bottom")

        # auto-fit off, centred text, inline list
        self.field("autoFit").uncheck()
        self.field("align").select_option("center")
        self.field("listStyle").select_option("inline")
        expect(self.field("autoFit")).not_to_be_checked()
        expect(page.locator('.label-preview text[text-anchor="middle"]').first).to_be_visible()
        expect(page.locator('.label-preview text[text-anchor="start"]')).to_have_count(0)
        # the inline separator is glued to the next item by a no-break space
        assert "6 mm ·\u00a08 mm" in page.locator(".label-preview svg").text_content()
        self.shot("autofit-off-centred-inline", sidebar="bottom")

        # another font: the labels switch once its faces are loaded
        self.field("fontChoice").select_option("Bitter")
        expect(self.field("fontChoice")).to_have_value("Bitter")
        self.fonts_ready("Bitter")
        self.shot("font-bitter", sidebar=".tabs")

        # numeric errors: an emptied width and an out-of-range size are shown, never applied
        self.field("w").fill("")
        self.field("titlePt").fill("100")
        expect(self.field("w")).to_have_attribute("aria-invalid", "")
        expect(self.field("titlePt")).to_have_attribute("aria-invalid", "")
        expect(page.locator("#err-w")).to_have_text("Entre 12 et 194")
        expect(page.locator("#err-titlePt")).to_have_text("Entre 4 et 72")
        expect(page.locator(".fld-error:visible")).to_have_count(2)
        expect(self.bind("editLine")).to_have_text("Édition — 70 × 37 mm · zoom ×2,04")
        expect(page.locator(".label-preview svg text").first).to_be_visible()
        assert "Chevilles" in self.preview_svg()
        self.shot("numeric-errors", sidebar=".tabs")
        self.field("w").fill("70")
        self.field("titlePt").fill("15")
        expect(page.locator("input[aria-invalid]")).to_have_count(0)
        expect(page.locator(".fld-error:visible")).to_have_count(0)

        # MDI icons: loading state (the icon set is held back until the capture), results, search, pick
        self.button("1 · Contenu").click()
        expect(self.field("qrText")).to_be_visible()
        expect(self.field("qrText")).to_have_attribute("placeholder", "Contenu du QR (défaut : le code)")
        held = []
        page.route("**/vendor/mdi/mdi.js", lambda route: held.append(route))
        with page.expect_request("**/vendor/mdi/mdi.js"):
            self.button("MDI").click()
        expect(page.locator(".icon-status")).to_have_text("Chargement…")
        expect(page.locator(".icon-grid .icon-cell")).to_have_count(0)
        expect(self.field("iconQuery")).to_have_attribute("placeholder", "chercher un picto…")
        self.shot("mdi-loading", sidebar="bottom")
        for _ in range(100):  # the route handler runs on the next event dispatch after the request
            if held:
                break
            page.wait_for_timeout(20)
        assert len(held) == 1, held
        held[0].continue_()  # a local URL: nothing for the offline router to answer
        page.unroute("**/vendor/mdi/mdi.js")
        self.icon_cells(56)
        expect(page.locator(".icon-status")).to_be_hidden()
        self.field("iconQuery").fill("cable-data")
        self.icon_cells(1)
        expect(page.locator(".icon-grid .icon-cell")).to_have_attribute("title", "cable-data")
        self.shot("mdi-search", sidebar="bottom")
        page.locator('.icon-cell[data-name="cable-data"]').click()
        expect(self.bind("iconSourceLabel")).to_have_text("mdi · cable-data")
        expect(page.locator(".logo-icon")).to_be_visible()
        # icon and QR: two cells in the column, split by a horizontal divider
        expect(page.locator(".label-preview svg > g")).to_have_count(2)
        expect(page.locator(".label-preview svg > line")).to_have_count(2)
        self.shot("icon-and-qr", sidebar="bottom")
        # with an icon and a QR code the exports stay well-formed and the PNG renders
        label = self.download("SVG (1 étiquette)", "etiquette-70x37mm.svg", b"<svg")
        assert ElementTree.fromstring(label).get("width") == "70mm"
        ElementTree.fromstring(self.download("SVG planche", "planche-a4.svg", b"<svg"))
        png = self.download("PNG 300 dpi", "etiquette-70x37mm@300dpi.png", b"\x89PNG\r\n\x1a\n")
        assert struct.unpack(">II", png[16:24]) == (827, 437)

        # downloads of the selected label and of the first sheet
        label = self.download("SVG (1 étiquette)", "etiquette-70x37mm.svg", b"<svg")
        assert b'width="70mm" height="37mm"' in label and b"Chevilles" in label
        sheet = self.download("SVG planche", "planche-a4.svg", b"<svg")
        assert b'width="210mm" height="297mm"' in sheet and sheet.count(b"clip-path=") == 14

        # Material icons: the full list first, then a search without result, then a match
        self.field("iconQuery").fill("")
        self.icon_cells(56)
        self.button("Material").click()
        self.icon_cells(42)
        expect(page.locator(".icon-grid .icon-cell").first).to_have_attribute("data-vb", "0 -960 960 960")
        self.field("iconQuery").fill("zzz")
        self.icon_cells(0)
        expect(page.locator(".icon-status")).to_have_text("Aucun picto ne correspond.")
        self.shot("material-no-match", sidebar="bottom")
        self.field("iconQuery").fill("home")
        self.icon_cells(1)
        expect(page.locator(".icon-grid .icon-cell")).to_have_attribute("title", "home")
        page.locator('.icon-cell[data-name="home"]').click()
        expect(self.bind("iconSourceLabel")).to_have_text("material · home")
        self.shot("material-picked", sidebar="bottom")

        # the picked icon applied to every label: every label of the print area draws it
        home = page.locator(".icon-cell[data-name='home']").get_attribute("data-d")
        self.button("Appliquer ce picto à toutes").click()
        page.wait_for_function(
            """(d) => document.querySelectorAll('.print-sheets path[d="' + d + '"]').length === 16""", arg=home
        )

        # image import: the thumbnail next to "Logo / picto", the image in the label
        page.locator(".upload-input").set_input_files(
            files=[{"name": "logo.svg", "mimeType": "image/svg+xml", "buffer": UPLOAD_SVG}]
        )
        expect(page.locator(".logo-img")).to_be_visible()
        expect(page.locator(".logo-img")).to_have_attribute("src", re.compile(r"^data:image/svg\+xml;base64,"))
        expect(page.locator(".logo-icon")).to_be_hidden()
        expect(self.bind("iconSourceLabel")).to_have_text("logo.svg")
        expect(page.locator(".icon-search")).to_be_hidden()
        expect(page.locator(".label-preview svg image")).to_have_count(1)
        expect(page.locator(".chips label.chip")).to_have_text("Importer")
        self.shot("image-imported", sidebar="bottom")

        # print tab, all labels
        self.button("3 · Impression").click()
        expect(page.locator(".tab.is-active")).to_have_text("3 · Impression")
        expect(self.field("mode")).to_have_value("batch")
        expect(page.locator(".fill-line")).to_be_hidden()
        expect(self.field("cut")).to_be_checked()
        self.shot("print-tab", sidebar=".tabs")

        # single mode: the page is filled with the selected label
        self.field("mode").select_option("single")
        expect(page.locator(".fill-line")).to_have_text(
            "La page est remplie automatiquement avec l'étiquette sélectionnée (14 par A4)."
        )
        expect(self.bind("gridInfo")).to_have_text("2 × 7 = 14 étiquettes par page A4 · 14 au total")
        assert self.pdf_pages() == 1
        self.shot("print-single", sidebar=".tabs")

        # full-page view of the whole list: two sheets
        self.field("mode").select_option("batch")
        self.button("Page entière").click()
        expect(page.locator(".real-page")).to_be_visible()
        expect(page.locator(".real-label")).to_be_hidden()
        expect(page.locator(".page-info")).to_have_text("A4 — 2 page(s)")
        expect(page.locator(".sheets .sheet")).to_have_count(2)
        assert self.pdf_pages() == 2
        self.shot("full-page", sidebar=".tabs")
        self.shot("full-page-sheets", element=".sheets")

        # print media: only the A4 sheets are rendered
        page.emulate_media(media="print")
        expect(page.locator(".screen")).to_be_hidden()
        expect(page.locator(".print-sheet")).to_have_count(2)
        expect(page.locator(".print-root")).to_be_visible()
        self.shot("print-media", element=".print-sheets")
        page.emulate_media(media="screen")
        expect(page.locator(".screen")).to_be_visible()

        # Deutsch, then English: every text follows, the edited list stays
        self.button("FR").click()
        self.button("Deutsch").click()
        expect(page.locator(".lang-btn")).to_have_text("DE")
        expect(page.locator("h1.app-title")).to_have_text("Kistenetiketten")
        expect(page.locator(".tab")).to_have_text(["1 · Inhalt", "2 · Stil", "3 · Druck"])
        expect(self.bind("countsLine")).to_have_text("5 Vorlage(n) · 16 insgesamt")
        expect(self.bind("gridInfo")).to_have_text("2 × 7 = 14 Etiketten pro A4-Seite · 16 insgesamt")
        expect(self.bind("editLine")).to_have_text("Bearbeiten — 70 × 37 mm · Zoom ×2,04")
        expect(page.locator(".page-info")).to_have_text("A4 — 2 Seite(n)")
        for name in ("SVG (1 Etikett)", "SVG Bogen", "Drucken / PDF A4", "Ganze Seite"):
            expect(self.button(name)).to_be_visible()
        self.rows(
            [
                "Vis inox",
                "Vis inox",
                "Chevilles à frapper nylon pour béton plein et creux",
                "(ohne Titel)",
                "Colliers de serrage",
            ]
        )
        expect(page.locator(".source-link")).to_have_text("Quellcode")
        self.shot("deutsch")

        self.button("DE").click()
        expect(page.locator(".lang-option.is-current")).to_have_text("Deutsch")
        self.button("English (US)").click()
        expect(page.locator(".lang-btn")).to_have_text("EN")
        expect(page.locator("h1.app-title")).to_have_text("Box labels")
        expect(page.locator(".tab")).to_have_text(["1 · Content", "2 · Style", "3 · Printing"])
        expect(self.bind("countsLine")).to_have_text("5 template(s) · 16 total")
        expect(self.bind("gridInfo")).to_have_text("2 × 7 = 14 labels per A4 page · 16 total")
        expect(self.bind("editLine")).to_have_text("Editing — 70 × 37 mm · zoom ×2.04")
        expect(page.locator(".page-info")).to_have_text("A4 — 2 page(s)")
        expect(page.locator(".rows .row-title").nth(3)).to_have_text("(untitled)")
        expect(page.locator(".source-link")).to_have_text("Source code")
        self.shot("english")


def main(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    base, server = offline.serve(APP_STATIC)
    blocked, errors = [], []
    scenario = None
    try:
        with sync_playwright() as playwright:
            browser = golden.launch(playwright)
            page = golden.new_page(browser, golden.DESKTOP)
            offline.route_offline(page.context, blocked)
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
            page.goto(base)
            scenario = Scenario(page, out_dir)
            scenario.run()
            browser.close()
    finally:
        server.shutdown()
        for url in blocked:
            print(f"blocked request (the site must load nothing external): {url}")
        for error in errors:
            print(error)
    if scenario is not None:
        print(f"{len(scenario.captures)} captures: {', '.join(scenario.captures)}")
    return 1 if blocked or errors else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
