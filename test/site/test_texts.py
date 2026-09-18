"""The site speaks exactly like the design export: same strings in the seven languages, same lists.

site/app.js carries the constants block of design/label-generator.dc.html (PT, FONTS, MAT, VERSION,
SOURCE, DICT, LANGS, detectLang, fmt, newRow) byte for byte. A copy that drifts, or an export updated
without the site, fails here.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"^const PT = .*?^const newRow = .*?;$", re.S | re.M)


def block(path):
    match = BLOCK.search(path.read_text(encoding="utf-8"))
    assert match, f"{path}: constants block not found"
    return match.group(0)


def test_constants_are_copied_byte_for_byte_from_the_export():
    assert block(REPO / "site" / "app.js") == block(REPO / "design" / "label-generator.dc.html")


def test_every_language_has_the_same_keys():
    text = block(REPO / "site" / "app.js")
    dict_body = text[text.index("const DICT = {") : text.index("const LANGS")]
    languages = re.findall(r"^  (\w\w): \{(.*?)\}(?:,)?$", dict_body, re.S | re.M)
    assert [code for code, _ in languages] == ["fr", "en", "es", "de", "it", "pt", "nl"]
    keys = [re.findall(r"(\w+):(?=\"|\[)", body) for _, body in languages]
    assert len(keys[0]) == 82  # 81 interface strings + the demo rows
    assert all(k == keys[0] for k in keys)
