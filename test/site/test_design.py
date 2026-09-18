"""Structural guards on design/: the Claude Design export is byte-pinned (PLAN.md 4.1)."""

import hashlib
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DESIGN = REPO / "design"

PINNED = {
    "label-generator.dc.html": "ac741acabb9e679ee740c5a07a4e5fd3155eb31106118e55179e493b5c958be6",
    "support.js": "8fe7df74405f3c55f49b7249c74ea1397e65d07dea2b1bd3b4a489bec2e28cbe",
}


def test_design_holds_exactly_the_export():
    # dotfiles are skipped: host files like .DS_Store are never committed
    names = sorted(p.name for p in DESIGN.iterdir() if not p.name.startswith("."))
    assert names == sorted(PINNED)


def test_design_files_are_byte_identical_to_the_export():
    actual = {name: hashlib.sha256((DESIGN / name).read_bytes()).hexdigest() for name in PINNED}
    assert actual == PINNED


def test_formatters_never_touch_byte_pinned_files():
    config = tomllib.loads((REPO / "treefmt.toml").read_text(encoding="utf-8"))
    assert {"design/**", "site/vendor/**", "test/screenshot/**"} <= set(config["excludes"])
