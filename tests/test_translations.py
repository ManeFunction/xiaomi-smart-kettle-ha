"""Tests that the translation files stay in sync."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

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


# Entities under Configuration, which the device page shows in another card
CONFIG_KEYS = {
    "lift_remember_temp",
    "boiling_reminder",
    "keep_warm_reminder",
    "no_disturb",
}


@pytest.mark.parametrize("language", ["en", "ru"])
def test_keep_warm_thermostat_is_listed_first(language: str) -> None:
    """The device page lists controls alphabetically after the main kettle."""
    entity = _load(f"translations/{language}.json")["entity"]
    names = [
        translation["name"]
        for domain in ("button", "number", "switch", "water_heater")
        for key, translation in entity[domain].items()
        if "name" in translation and key not in CONFIG_KEYS
    ]

    assert min(names, key=str.casefold) == entity["water_heater"]["keep_warm"]["name"]
