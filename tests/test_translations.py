"""Tests that the translation files stay in sync."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

COMPONENT = Path(__file__).parents[1] / "custom_components" / "xiaomi_smart_kettle"


def _load(name: str) -> dict[str, Any]:
    return json.loads((COMPONENT / name).read_text(encoding="utf-8"))


def _keys(data: dict[str, Any], prefix: str = "") -> set[str]:
    keys = set()
    for key, value in data.items():
        path = f"{prefix}{key}"
        keys |= _keys(value, f"{path}.") if isinstance(value, dict) else {path}
    return keys


def test_english_matches_strings() -> None:
    assert _load("translations/en.json") == _load("strings.json")


def test_russian_has_every_key() -> None:
    assert _keys(_load("translations/ru.json")) == _keys(_load("strings.json"))
