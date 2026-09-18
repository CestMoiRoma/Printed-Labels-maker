"""The seven languages of the site stay complete: same keys everywhere, in DICT and in DICT_FIXES."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"^const PT = .*?^const newRow = .*?;$", re.S | re.M)


def block(path):
    match = BLOCK.search(path.read_text(encoding="utf-8"))
    assert match, f"{path}: constants block not found"
    return match.group(0)


def test_every_language_has_the_same_keys():
    text = block(REPO / "site" / "app.js")
    dict_body = text[text.index("const DICT = {") : text.index("const LANGS")]
    languages = re.findall(r"^  (\w\w): \{(.*?)\}(?:,)?$", dict_body, re.S | re.M)
    assert [code for code, _ in languages] == ["fr", "en", "es", "de", "it", "pt", "nl"]
    keys = [re.findall(r"(\w+):(?=\"|\[)", body) for _, body in languages]
    assert len(keys[0]) == 82  # 81 interface strings + the demo rows
    assert all(k == keys[0] for k in keys)


def test_string_fixes_cover_every_language_with_the_same_keys():
    app = (REPO / "site" / "app.js").read_text(encoding="utf-8")
    fixes = app[app.index("const DICT_FIXES = {") : app.index("for (const code in DICT_FIXES)")]
    languages = re.findall(r"^  (\w\w): \{(.*?)\}(?:,)?$", fixes, re.M)
    assert [code for code, _ in languages] == ["fr", "en", "es", "de", "it", "pt", "nl"]
    keys = [re.findall(r"(\w+):(?=\s*\")", body) for _, body in languages]
    assert keys[0] and all(k == keys[0] for k in keys)
