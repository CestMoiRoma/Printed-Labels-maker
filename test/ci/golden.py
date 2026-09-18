"""Deterministic GUI captures shared by every screenshot script (Playwright, sync API)."""

import io
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path

GOLDEN_TIME = datetime(2026, 1, 15, 9, 30, 0, tzinfo=timezone.utc)
LOCALE = "fr-FR"
TIMEZONE = "Europe/Paris"

# Desktop only: the mobile viewport (390x844) comes with a mobile layout.
DESKTOP = {"width": 1280, "height": 820}

CHROMIUM_ARGS = [
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-accelerated-2d-canvas",
    "--disable-lcd-text",
    "--font-render-hinting=none",
    "--disable-font-subpixel-positioning",
    "--force-color-profile=srgb",
    "--disable-skia-runtime-opts",
    "--disable-smooth-scrolling",
    "--disable-partial-raster",
    "--disable-threaded-animation",
    "--disable-threaded-scrolling",
    "--disable-checker-imaging",
    "--disable-image-animation-resync",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
]

FREEZE_CSS = """
*, *::before, *::after {
  transition: none !important; animation: none !important;
  caret-color: transparent !important; scroll-behavior: auto !important;
}
"""

_INJECT_CSS = """((css) => {
  const add = () => {
    if (document.querySelector('style[data-golden]')) return
    const s = document.createElement('style'); s.setAttribute('data-golden', ''); s.textContent = css
    ;(document.head || document.documentElement).appendChild(s)
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add()
})"""


def launch(playwright):
    return playwright.chromium.launch(args=CHROMIUM_ARGS)


def new_page(browser, viewport=DESKTOP, now=GOLDEN_TIME):
    context = browser.new_context(
        viewport=viewport, device_scale_factor=1, locale=LOCALE, timezone_id=TIMEZONE, color_scheme="light"
    )
    context.add_init_script(f"{_INJECT_CSS}({FREEZE_CSS!r})")
    page = context.new_page()
    if now is not None:
        page.clock.set_fixed_time(now.timestamp() if isinstance(now, datetime) else now)
    return page


def settle(page):
    """Web fonts loaded, no running animation, two rendered frames."""
    page.evaluate("document.fonts.ready.then(() => undefined)")
    page.wait_for_function("() => document.getAnimations().every((a) => a.playState !== 'running')")
    page.evaluate("() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))")


def screenshot(target, path):
    data = target.screenshot(animations="disabled", caret="hide", scale="css")
    write_png(path, data)
    return Path(path)


def write_png(path, data):
    from PIL import Image

    with Image.open(io.BytesIO(data)) as image:
        image.load()
        Path(path).write_bytes(encode_png(image))


def encode_png(image):
    """PNG bytes depending only on the pixels: RGB(A) 8-bit, "Up" filter, zlib level 9, no ancillary chunk."""
    from PIL import Image, ImageChops

    has_alpha = "A" in image.getbands() and image.convert("RGBA").getextrema()[3][0] < 255
    image = image.convert("RGBA" if has_alpha else "RGB")
    width, height = image.size
    above = Image.new(image.mode, image.size)
    above.paste(image.crop((0, 0, width, height - 1)), (0, 1))
    filtered = ImageChops.subtract_modulo(image, above).tobytes()
    stride = width * len(image.getbands())
    rows = b"".join(b"\x02" + filtered[y * stride : (y + 1) * stride] for y in range(height))

    def chunk(tag, payload):
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6 if has_alpha else 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )
