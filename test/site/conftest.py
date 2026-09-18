"""Shared pytest setup: the scripts of test/ci are importable as top-level modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ci"))
