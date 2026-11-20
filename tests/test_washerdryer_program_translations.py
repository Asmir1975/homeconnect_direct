"""Programs of the WNC244070 washer-dryer resolve to translated labels."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "wnc244070_washerdryer.json"
TRANSLATIONS = Path(__file__).parents[1] / "custom_components/homeconnect_ws/translations"


def _label(program: str) -> str:
    """Build the label generate_program uses for a program."""
    favorite = "BSH.Common.Program.Favorite."
    if program.startswith(favorite):
        return "favorite_" + program.removeprefix(favorite)
    return program.lower().replace(".", "_")


@pytest.mark.parametrize("lang", ["en", "de"])
def test_every_washerdryer_program_is_translated(lang: str) -> None:
    """Raw program keys must not reach the dropdown or the active program sensor."""
    texts = json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    programs = fixture["entry_data"]["description"]["program"]
    select_states = texts["entity"]["select"]["select_program"]["state"]
    sensor_states = texts["entity"]["sensor"]["sensor_active_program"]["state"]
    for program in programs:
        label = _label(program["name"])
        assert label in select_states, (lang, program["name"])
        assert label in sensor_states, (lang, program["name"])
