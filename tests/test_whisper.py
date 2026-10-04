"""Tests for the offline (Whisper) speech path. The model itself is faked; see the benchmark notes in CLAUDE.md."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


@pytest.mark.parametrize("probs, primary, expected", [
    ([("en", 0.9), ("hi", 0.05)], "en-IN", "en"),
    ([("hi", 0.8), ("en", 0.1)], "en-IN", "hi"),
    ([("hi", 0.55), ("en", 0.4)], "en-IN", "en"),       # not confident enough to switch away from English
    ([("el", 0.5), ("en", 0.3), ("hi", 0.1)], "en-IN", "en"),   # wild guesses (Greek) never win
    ([("hi", 0.6), ("en", 0.3)], "hi-IN", "hi"),
    ([("en", 0.9), ("hi", 0.05)], "hi-IN", "en"),
])
def test_choose_whisper_language(probs, primary, expected):
    assert main.choose_whisper_language(probs, primary) == expected


@pytest.mark.parametrize("text, kept", [
    ("Open Chrome.", True),
    ("नमस्ते आज आप कैसे हैं", True),
    ("What is the weather in Delhi?", True),
    ("λιγκα η φιριαίδη δύνατος", False),                          # Greek hallucination
    ("We will be on the next one. " * 6, False),                  # repetition loop
    ("Thanks for watching!", False),                              # subtitle boilerplate
    ("", False),
    ("   ", False),
])
def test_clean_whisper_text(text, kept):
    assert (main.clean_whisper_text(text) is not None) == kept


class FakeAudio:
    frame_data = b"\x00\x00" * 1600


class TestEngineOrder:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.calls = []
        monkeypatch.setattr(main, "STT_ENGINE", "whisper")
        monkeypatch.setattr(main, "STT_FALLBACK_TO_GOOGLE", True)
        monkeypatch.setitem(main._whisper, "state", "ready")
        monkeypatch.setattr(main, "recognize_google_both", lambda a: self.calls.append("google") or "from google")

    def whisper_says(self, monkeypatch, text):
        monkeypatch.setattr(main, "transcribe_whisper", lambda a: self.calls.append("whisper") or text)

    def test_whisper_first(self, monkeypatch):
        self.whisper_says(monkeypatch, "open chrome")
        assert main.recognize_with_fallback(FakeAudio()) == "open chrome"
        assert self.calls == ["whisper"] and main.LAST_ENGINE == "whisper"

    def test_google_when_whisper_hears_nothing(self, monkeypatch):
        self.whisper_says(monkeypatch, None)
        assert main.recognize_with_fallback(FakeAudio()) == "from google"
        assert self.calls == ["whisper", "google"]

    def test_no_google_when_fallback_off(self, monkeypatch):
        monkeypatch.setattr(main, "STT_FALLBACK_TO_GOOGLE", False)
        self.whisper_says(monkeypatch, None)
        assert main.recognize_with_fallback(FakeAudio()) is None
        assert self.calls == ["whisper"]

    def test_whisper_crash_falls_back(self, monkeypatch):
        def boom(a):
            raise RuntimeError("model broke")
        monkeypatch.setattr(main, "transcribe_whisper", boom)
        assert main.recognize_with_fallback(FakeAudio()) == "from google"

    def test_google_used_while_model_still_loading(self, monkeypatch):
        monkeypatch.setitem(main._whisper, "state", "loading")
        self.whisper_says(monkeypatch, "never called")
        assert main.recognize_with_fallback(FakeAudio()) == "from google"
        assert "whisper" not in self.calls

    def test_google_only_mode(self, monkeypatch):
        monkeypatch.setattr(main, "STT_ENGINE", "google")
        assert main.recognize_with_fallback(FakeAudio()) == "from google"

    def test_offline_google_failure_returns_none(self, monkeypatch):
        monkeypatch.setattr(main, "STT_ENGINE", "google")

        def offline(a):
            raise OSError("no internet")
        monkeypatch.setattr(main, "recognize_google_both", offline)
        assert main.recognize_with_fallback(FakeAudio()) is None
