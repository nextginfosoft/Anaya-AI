"""Tests for Maya's command parsing. Side effects (speech, volume keys, apps) are stubbed out."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


@pytest.fixture
def log(monkeypatch):
    """Capture everything Maya would say or do instead of doing it."""
    events = []
    monkeypatch.setattr(main, "speak", lambda t: events.append(f"say:{t}"))
    monkeypatch.setattr(main, "_press_media_key", lambda name, times=1: events.append(f"key:{name}x{times}"))
    monkeypatch.setattr(main, "_get_brightness", lambda: 60)
    monkeypatch.setattr(main, "_set_brightness", lambda lvl: events.append(f"bright:{lvl}") or lvl)
    monkeypatch.setattr(main, "ask_local_ai", lambda c: f"ai:{c}")
    monkeypatch.setattr(main.os, "startfile", lambda x: events.append(f"start:{x}"), raising=False)
    monkeypatch.setattr(main.subprocess, "Popen", lambda a, *k, **kw: events.append(f"run:{a[0]}"))
    monkeypatch.setattr(main.subprocess, "run", lambda a, *k, **kw: events.append(f"run:{a[0]}"))
    monkeypatch.setattr(main.webbrowser, "open", lambda u, *a, **k: events.append(f"web:{u}"))
    return events


@pytest.mark.parametrize("raw, expected", [
    ("Please open the Chrome", "open chrome"),
    ("launch VS Code", "open vs code"),
    ("Open up my downloads folder", "open downloads folder"),
    ("Hey, search Google for python!", "search google for python"),
    ("can you open the youtube", "open youtube"),
])
def test_normalize_command(raw, expected):
    assert main.normalize_command(raw) == expected


@pytest.mark.parametrize("text, woke, rest", [
    ("Maya", True, ""),
    ("maya open chrome", True, "open chrome"),
    ("Maya, search google for cats", True, "search google for cats"),
    ("hello there", False, ""),
    ("Amaya", False, ""),
])
def test_split_wake_word(text, woke, rest):
    assert main.split_wake_word(text) == (woke, rest)


def test_clean_for_speech_strips_markdown_and_trailing_fragment():
    out = main.clean_for_speech("**Paris** is the capital of France. It is also a big city that")
    assert "*" not in out
    assert out.endswith(".")


@pytest.mark.skipif(not main.IS_WINDOWS, reason="Windows-only commands")
class TestSystemCommands:
    def test_volume_up(self, log):
        main.process_command("volume up")
        assert "key:volume upx5" in log

    def test_volume_down_with_filler(self, log):
        main.process_command("please turn the volume down")
        assert "key:volume downx5" in log

    def test_mute(self, log):
        main.process_command("mute")
        assert "key:volume mutex1" in log

    def test_set_volume_exact(self, log):
        main.process_command("set volume to 40")
        assert "key:volume downx50" in log and "key:volume upx20" in log

    def test_brightness_set_and_clamp(self, log):
        main.process_command("set brightness to 30")
        assert "bright:30" in log

    def test_lock_screen(self, log):
        main.process_command("lock the screen")
        assert "run:rundll32.exe" in log

    def test_time_and_date(self, log):
        main.process_command("what time is it")
        main.process_command("what is the date")
        assert sum(e.startswith("say:It is") for e in log) == 1
        assert sum(e.startswith("say:Today is") for e in log) == 1

    @pytest.mark.parametrize("phrase, launcher", [
        ("open notepad", "run:notepad.exe"),
        ("open the calculator", "run:calc.exe"),
        ("open settings", "start:ms-settings:"),
    ])
    def test_open_system_apps(self, log, phrase, launcher):
        main.process_command(phrase)
        assert launcher in log

    def test_volume_word_in_a_normal_question_goes_to_ai(self, log):
        main.process_command("what is the volume of a sphere")
        assert any(e.startswith("say:ai:") for e in log)
        assert not any(e.startswith("key:") for e in log)


def test_general_question_goes_to_ai(log):
    main.process_command("who wrote hamlet")
    assert "say:ai:who wrote hamlet" in log


def test_search_google_opens_browser(log):
    main.process_command("search google for python")
    assert "web:https://www.google.com/search?q=python" in log


def test_stop_maya_exits(log):
    with pytest.raises(SystemExit):
        main.process_command("stop maya")


# ---------------- conversation memory ----------------
class TestMemory:
    @pytest.fixture(autouse=True)
    def fake_ollama(self, monkeypatch):
        self.calls = []

        def chat(model, messages, options=None):
            self.calls.append(messages)
            return {"message": {"content": f"Answer number {len(self.calls)}."}}

        monkeypatch.setattr(main.ollama, "chat", chat)
        main.forget_conversation()
        monkeypatch.setattr(main, "_last_chat_time", 0.0)
        yield
        main.forget_conversation()

    def test_follow_up_includes_previous_turn(self):
        main.ask_local_ai("who wrote hamlet")
        main.ask_local_ai("when was he born")
        second = self.calls[1]
        assert [m["role"] for m in second] == ["system", "user", "assistant", "user"]
        assert second[1]["content"] == "who wrote hamlet"

    def test_history_is_capped(self):
        for i in range(main.HISTORY_MAX_TURNS + 4):
            main.ask_local_ai(f"q{i}")
        assert len(main.HISTORY) == 2 * main.HISTORY_MAX_TURNS

    def test_resets_after_idle(self, monkeypatch):
        main.ask_local_ai("first")
        monkeypatch.setattr(main, "_last_chat_time", main._last_chat_time - main.HISTORY_IDLE_SECONDS - 1)
        main.ask_local_ai("second")
        assert [m["role"] for m in self.calls[1]] == ["system", "user"]

    def test_forget_command_clears_history(self, log):
        main.HISTORY.extend([{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}])
        main.process_command("forget that")
        assert not main.HISTORY
