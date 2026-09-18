"""golden.py drives the Chromium of the CI image: fixed context, frozen CSS, reproducible captures."""

import io
import urllib.parse

import golden
import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<style>
  body { margin: 0; font: 16px "DejaVu Sans", sans-serif; background: #f7f4f1; color: #1b1917; }
  .box { width: 200px; height: 80px; background: oklch(0.52 0.14 300); transition: width 5s; animation: spin 3s infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style></head>
<body><h1>Étiquettes à imprimer</h1><div class="box"></div><input value="caret" autofocus></body></html>"""

URL = "data:text/html;charset=utf-8," + urllib.parse.quote(PAGE)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = golden.launch(playwright)
        yield browser
        browser.close()


def test_context_is_fixed(browser):
    page = golden.new_page(browser)
    page.goto(URL)
    state = page.evaluate(
        """() => ({
            language: navigator.language,
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            now: Date.now(),
            width: innerWidth, height: innerHeight, dpr: devicePixelRatio,
            dark: matchMedia('(prefers-color-scheme: dark)').matches,
            frozen: document.querySelectorAll('style[data-golden]').length,
            animation: getComputedStyle(document.querySelector('.box')).animationName,
        })"""
    )
    page.context.close()
    assert state == {
        "language": "fr-FR",
        "timeZone": "Europe/Paris",
        "now": int(golden.GOLDEN_TIME.timestamp() * 1000),
        "width": 1280,
        "height": 820,
        "dpr": 1,
        "dark": False,
        "frozen": 1,
        "animation": "none",
    }


def test_two_captures_are_byte_identical(browser, tmp_path):
    shots = []
    for run in range(2):
        page = golden.new_page(browser)
        page.goto(URL)
        golden.settle(page)
        shots.append(golden.screenshot(page, tmp_path / f"{run}.png").read_bytes())
        page.context.close()
    assert shots[0] == shots[1]
    with Image.open(io.BytesIO(shots[0])) as image:
        image.load()
        assert image.size == (1280, 820)
        assert shots[0] == golden.encode_png(image)
