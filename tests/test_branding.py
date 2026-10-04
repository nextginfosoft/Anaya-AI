"""Tests for the Maya -> Anaya rename: wake word, settings compatibility and credits."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------- settings: ANAYA_ first, legacy MAYA_ still works ----------------
def test_new_setting_name(monkeypatch):
    monkeypatch.delenv("MAYA_TESTSETTING", raising=False)
    monkeypatch.setenv("ANAYA_TESTSETTING", "new")
    assert main._env("TESTSETTING") == "new"


def test_legacy_setting_name_still_works(monkeypatch):
    monkeypatch.delenv("ANAYA_TESTSETTING", raising=False)
    monkeypatch.setenv("MAYA_TESTSETTING", "old")
    assert main._env("TESTSETTING") == "old"


def test_new_name_wins_over_legacy(monkeypatch):
    monkeypatch.setenv("ANAYA_TESTSETTING", "new")
    monkeypatch.setenv("MAYA_TESTSETTING", "old")
    assert main._env("TESTSETTING") == "new"


def test_default_used_when_neither_is_set(monkeypatch):
    monkeypatch.delenv("ANAYA_TESTSETTING", raising=False)
    monkeypatch.delenv("MAYA_TESTSETTING", raising=False)
    assert main._env("TESTSETTING", "fallback") == "fallback"
    assert main._env("TESTSETTING") is None


def test_legacy_setting_actually_changes_behaviour(monkeypatch):
    monkeypatch.delenv("ANAYA_ALLOW_MULTIPLE", raising=False)
    monkeypatch.setenv("MAYA_ALLOW_MULTIPLE", "1")
    assert main.acquire_single_instance() is True and main.acquire_single_instance() is True


# ---------------- wake word ----------------
@pytest.mark.parametrize("text, woke, rest", [
    ("Anaya", True, ""),
    ("anaya open chrome", True, "open chrome"),
    ("Anaya, what time is it", True, "what time is it"),
    ("Ananya open chrome", True, "open chrome"),          # a likely mis-hearing of the new name
    ("Annaya volume up", True, "volume up"),
    ("maya open chrome", True, "open chrome"),            # old name still wakes her
    ("hello there", False, ""),
    ("Amaya", False, ""),
    ("banana", False, ""),
])
def test_wake_word_variants(text, woke, rest):
    assert main.split_wake_word(text) == (woke, rest)


@pytest.mark.parametrize("phrase", ["stop anaya", "Stop Anaya", "stop ananya", "stop maya"])
def test_stop_command_accepts_new_and_old_name(phrase, monkeypatch):
    monkeypatch.setattr(main, "speak", lambda t, **kw: None)
    with pytest.raises(SystemExit):
        main.process_command(phrase)


# ---------------- credits and licence ----------------
def test_introduction_credits_both_authors(monkeypatch):
    said = []
    monkeypatch.setattr(main, "speak", lambda t, **kw: said.append(t))
    main.introduce_yourself()
    text = " ".join(said)
    assert "I am Anaya" in text
    assert "Santosh Pandit" in text and "Taha Shaikh" in text


def test_license_keeps_original_and_new_copyright():
    text = open(os.path.join(ROOT, "LICENSE"), encoding="utf-8").read()
    assert text.startswith("MIT License")
    assert "Taha Shaikh" in text and "Santosh Pandit" in text
    assert "Permission is hereby granted, free of charge" in text      # the notice MIT requires you to keep


def test_readme_credits_both_authors():
    text = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert "Santosh Pandit" in text and "Taha Shaikh" in text
    assert re.search(r"^# Anaya AI$", text, flags=re.M)                # the title heading
    assert "Maya AI" in text and "Credits" in text                     # the original project is credited


def test_old_name_only_appears_where_intended():
    """After removing the intentional mentions, no 'maya' may remain in main.py."""
    intentional = [
        "Maya AI",                                  # credit to the original project
        "MAYA_",                                    # legacy setting prefix
        "|maya)",                                   # legacy wake word / stop word
    ]
    leftovers = []
    for number, line in enumerate(open(os.path.join(ROOT, "main.py"), encoding="utf-8"), 1):
        cleaned = line
        for token in intentional:
            cleaned = cleaned.replace(token, "")
        if re.search("maya", cleaned, re.I):
            leftovers.append((number, line.strip()))
    assert leftovers == []
