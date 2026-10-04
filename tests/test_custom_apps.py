"""Tests for the user-editable app list (apps.json)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


@pytest.fixture
def log(monkeypatch):
    events = []
    monkeypatch.setattr(main, "speak", lambda t, **kw: events.append(f"say:{t}"))
    monkeypatch.setattr(main, "ask_local_ai", lambda c: f"ai:{c}")
    monkeypatch.setattr(main.os, "startfile", lambda x: events.append(f"start:{x}"), raising=False)
    monkeypatch.setattr(main.webbrowser, "open", lambda u, *a, **k: events.append(f"web:{u}"))
    return events


@pytest.fixture
def apps_file(tmp_path, monkeypatch):
    path = tmp_path / "apps.json"
    path.write_text(json.dumps({
        "_help": "ignored",
        "Github": "https://github.com",
        "my project": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "broken": 5,
    }), encoding="utf-8")
    monkeypatch.setattr(main, "APPS_FILE", str(path))
    return path


def test_names_lowercased_and_help_and_bad_entries_skipped(apps_file):
    apps = main.load_custom_apps()
    assert set(apps) == {"github", "my project"}


def test_open_web_app(apps_file, log):
    main.process_command("open the github")
    assert "web:https://github.com" in log


@pytest.mark.skipif(not main.IS_WINDOWS, reason="os.startfile is Windows-only")
def test_open_path_app(apps_file, log):
    main.process_command("open my project")
    assert any(e.startswith("start:") for e in log)


def test_unknown_name_falls_through_to_ai(apps_file, log):
    main.process_command("open totally unknown thing")
    assert not any(e.startswith(("web:", "start:")) for e in log)


def test_edits_apply_without_restart(apps_file, log):
    apps_file.write_text('{"zoom": "https://zoom.us"}', encoding="utf-8")
    main.process_command("open zoom")
    assert "web:https://zoom.us" in log


def test_missing_or_corrupt_file_is_harmless(apps_file):
    apps_file.write_text("{not json", encoding="utf-8")
    assert main.load_custom_apps() == {}
    apps_file.unlink()
    assert main.load_custom_apps() == {}


def test_shipped_apps_json_is_valid():
    real = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps.json")
    with open(real, encoding="utf-8") as f:
        assert isinstance(json.load(f), dict)
