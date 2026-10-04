"""Tests for dictation, read aloud, translate, summarise and the morning briefing."""
import json
import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


class Desktop:
    """Fake clipboard + fake keyboard + a fake 'selected text' in the active window."""

    def __init__(self):
        self.clipboard = "original clipboard"
        self.selection = "selected words"
        self.typed = []        # what ended up pasted into the active window
        self.said = []


@pytest.fixture
def desk(monkeypatch):
    d = Desktop()
    monkeypatch.setattr(main, "_clip_get", lambda: d.clipboard)
    monkeypatch.setattr(main, "_clip_set", lambda t, **kw: setattr(d, "clipboard", t) or True)
    monkeypatch.setattr(main.time, "sleep", lambda s: None)

    import keyboard

    def send(keys):
        if keys == "ctrl+c":
            d.clipboard = d.selection
        elif keys == "ctrl+v":
            d.typed.append(d.clipboard)

    monkeypatch.setattr(keyboard, "send", send)
    monkeypatch.setattr(main, "speak", lambda t, **kw: d.said.append(t) or False)
    monkeypatch.setattr(main, "ask_local_ai", lambda c: f"ai:{c}")
    monkeypatch.setattr(main, "DICTATING", False)
    yield d
    main.DICTATING = False


# ---------------- formatting ----------------
@pytest.mark.parametrize("spoken, typed", [
    ("hello comma how are you question mark", "Hello, how are you? "),
    ("dear sir new line thank you full stop", "Dear sir\nThank you. "),
    ("first new paragraph second", "First\n\nSecond "),
    ("it is done exclamation mark", "It is done! "),
])
def test_format_dictation(spoken, typed):
    assert main.format_dictation(spoken) == typed


# ---------------- type / dictation ----------------
def test_type_command_pastes_text_and_restores_clipboard(desk):
    main.process_command("type hello comma world")
    assert desk.typed == ["Hello, world "]
    assert desk.clipboard == "original clipboard"


def test_type_of_question_is_not_a_typing_command(desk):
    main.process_command("type of engine in a car")
    assert desk.typed == [] and any(s.startswith("ai:") or s == "Thinking boss" for s in desk.said)


def test_dictation_mode_lifecycle(desk):
    main.process_command("start dictation")
    assert main.DICTATING and "Dictation on" in desk.said[0]
    main.process_command("this is a note full stop")
    main.process_command("क्रोम खोलो")                      # would normally open Chrome; in dictation it is just text
    assert desk.typed == ["This is a note. ", "क्रोम खोलो "]
    main.process_command("stop dictation")
    assert not main.DICTATING and desk.said[-1] == "Dictation off"
    main.process_command("what is two plus two")             # back to normal
    assert any(s.startswith("ai:") or s == "Thinking boss" for s in desk.said)


# ---------------- read aloud ----------------
def test_read_clipboard(desk):
    desk.clipboard = "Line one.\n\nLine   two."
    main.process_command("read the clipboard")
    assert desk.said == ["Line one. Line two."]


def test_read_selection_restores_clipboard(desk):
    main.process_command("read this")
    assert desk.said == ["selected words"]
    assert desk.clipboard == "original clipboard"


def test_read_empty(desk):
    desk.clipboard = ""
    main.process_command("read what i copied")
    assert desk.said == ["There is nothing to read"]


def test_read_is_capped(desk):
    desk.clipboard = "x" * 10000
    main.process_command("read the clipboard")
    assert len(desk.said[0]) == main.MAX_READ_CHARS


# ---------------- translate / summarise ----------------
@pytest.fixture
def llm(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "llm_once", lambda instr, text, max_tokens=300: calls.append((instr, text)) or "RESULT")
    return calls


def test_translate_to_english_is_spoken(desk, llm):
    desk.clipboard = "नमस्ते दोस्त"
    main.process_command("translate the clipboard to english")
    assert "English" in llm[0][0] and llm[0][1] == "नमस्ते दोस्त"
    assert desk.said[-1] == "RESULT" and desk.clipboard == "RESULT"


def test_translate_to_hindi_goes_to_clipboard_not_voice(desk, llm):
    main.process_command("translate this to hindi")
    assert llm[0][1] == "selected words"                      # 'this' = the selected text
    assert desk.clipboard == "RESULT"
    assert desk.said[-1] == "The Hindi translation is on your clipboard"


def test_summarise_clipboard(desk, llm):
    main.process_command("summarise what i copied")
    assert llm[0][1] == "original clipboard"
    assert desk.said[-1] == "RESULT"


def test_summarise_without_text(desk, llm):
    desk.clipboard = ""
    main.process_command("summarize the clipboard")
    assert "nothing to summarise" in desk.said[-1] and not llm


# ---------------- morning briefing ----------------
@pytest.fixture
def briefing_env(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "BRIEFING_FILE", str(tmp_path / "b.json"))
    monkeypatch.setattr(main, "REMINDERS_FILE", str(tmp_path / "r.json"))
    monkeypatch.setattr(main, "get_battery_text", lambda: "Battery is at 80 percent.")
    monkeypatch.setattr(main, "home_city", lambda: "Delhi")
    monkeypatch.setattr(main, "get_weather", lambda c: f"In {c} it is 30 degrees.")
    monkeypatch.setattr(main, "get_news", lambda n=3: ["Headline A", "Headline B"])


def test_briefing_contains_all_sections(briefing_env):
    main.add_reminder(9e12, "call raj")
    lines = main.build_briefing_lines(datetime(2026, 10, 5, 8, 30))
    text = " ".join(lines)
    assert lines[0].startswith("Good morning boss. It is 8:30 AM on Monday, 05 October")
    for part in ("Battery is at 80", "In Delhi it is 30", "1 reminder: call raj", "Headline A"):
        assert part in text


def test_greeting_changes_through_the_day(briefing_env):
    assert main.build_briefing_lines(datetime(2026, 10, 5, 14, 0))[0].startswith("Good afternoon")
    assert main.build_briefing_lines(datetime(2026, 10, 5, 20, 0))[0].startswith("Good evening")


def test_failing_sections_are_skipped(briefing_env, monkeypatch):
    def boom(*a, **k):
        raise OSError("offline")
    monkeypatch.setattr(main, "get_weather", boom)
    monkeypatch.setattr(main, "get_news", boom)
    lines = main.build_briefing_lines(datetime(2026, 10, 5, 8, 0))
    assert len(lines) == 2 and "Battery" in lines[1]


def test_cooldown(briefing_env):
    assert main.briefing_due()
    main._mark_briefing_done()
    assert not main.briefing_due()
    with open(main.BRIEFING_FILE, "w") as f:
        json.dump({"time": main.time.time() - 5 * 3600}, f)
    assert main.briefing_due()


def test_briefing_command_speaks_and_stops_when_interrupted(desk, briefing_env):
    spoken = []
    main.speak = lambda t, **kw: spoken.append(t) or len(spoken) == 2     # 'interrupt' after the second line
    main.process_command("give me my briefing")
    assert len(spoken) == 2


def test_startup_briefing_respects_off_switch(briefing_env, monkeypatch):
    started = []
    monkeypatch.setattr(main.threading, "Thread", lambda **k: started.append(k) or type("T", (), {"start": lambda s: None})())
    monkeypatch.setenv("ANAYA_BRIEFING", "0")
    main.maybe_start_morning_briefing()
    assert not started
    monkeypatch.setenv("ANAYA_BRIEFING", "1")
    main.maybe_start_morning_briefing()
    assert len(started) == 1
