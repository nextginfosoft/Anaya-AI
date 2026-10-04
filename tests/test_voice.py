"""Tests for which voice speaks what (neural online voice vs. private offline voice)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

pytestmark = pytest.mark.skipif(not main.IS_WINDOWS, reason="Windows voices")


@pytest.fixture
def voices(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "TTS_ENGINE", "edge")
    monkeypatch.setattr(main, "_speak_edge", lambda t: calls.append(("edge", t)) or False)
    monkeypatch.setattr(main, "_speak_system", lambda t: calls.append(("system", t)) or False)
    return calls


def test_normal_replies_use_the_neural_voice(voices):
    main.speak("Opening Chrome")
    assert voices == [("edge", "Opening Chrome")]


def test_offline_flag_forces_local_voice(voices):
    main.speak("private clipboard text", offline=True)
    assert voices == [("system", "private clipboard text")]


def test_windows_engine_setting_never_uses_neural(voices, monkeypatch):
    monkeypatch.setattr(main, "TTS_ENGINE", "windows")
    main.speak("hello")
    assert voices == [("system", "hello")]


def test_falls_back_when_neural_voice_fails(voices, monkeypatch):
    monkeypatch.setattr(main, "_speak_edge", lambda t: voices.append(("edge", t)) or None)   # None = unavailable
    main.speak("hello")
    assert voices == [("edge", "hello"), ("system", "hello")]


def test_interrupt_flag_is_returned_and_no_fallback(voices, monkeypatch):
    monkeypatch.setattr(main, "_speak_edge", lambda t: voices.append(("edge", t)) or True)
    assert main.speak("long text") is True
    assert voices == [("edge", "long text")]


def test_private_tools_use_offline_voice(voices, monkeypatch):
    monkeypatch.setattr(main, "_clip_get", lambda: "secret text")
    monkeypatch.setattr(main, "_clip_set", lambda t: True)
    main.process_command("read the clipboard")
    assert voices == [("system", "secret text")]


def test_hindi_text_picks_the_hindi_voice(monkeypatch):
    picked = []

    class FakeCommunicate:
        def __init__(self, text, voice):
            picked.append(voice)

        async def save(self, path):
            open(path, "wb").write(b"x")

    import edge_tts
    monkeypatch.setattr(edge_tts, "Communicate", FakeCommunicate)
    path = os.path.join(os.path.dirname(__file__), "_tmp_voice.mp3")
    try:
        main.synthesize_edge("Hello", path)
        main.synthesize_edge("नमस्ते", path)
    finally:
        if os.path.exists(path):
            os.remove(path)
    assert picked == [main.EDGE_VOICE_EN, main.EDGE_VOICE_HI]
