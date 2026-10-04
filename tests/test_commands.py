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


# ---------------- reminders & timers ----------------
from datetime import datetime  # noqa: E402


@pytest.mark.parametrize("text, seconds", [
    ("10 minutes", 600), ("an hour", 3600), ("half an hour", 1800), ("1 hour 30 minutes", 5400),
    ("30 seconds", 30), ("five minutes", 300), ("2 hours", 7200), ("hello", None),
])
def test_parse_duration(text, seconds):
    assert main.parse_duration(text) == seconds


def test_parse_clock_time_picks_next_occurrence():
    now = datetime(2026, 10, 4, 15, 0)
    assert datetime.fromtimestamp(main.parse_clock_time("at 6 pm", now)) == datetime(2026, 10, 4, 18, 0)
    assert datetime.fromtimestamp(main.parse_clock_time("at 9 am", now)) == datetime(2026, 10, 5, 9, 0)
    assert datetime.fromtimestamp(main.parse_clock_time("at 18:30", now)) == datetime(2026, 10, 4, 18, 30)
    assert main.parse_clock_time("no time here", now) is None


@pytest.mark.parametrize("phrase, delay, message", [
    ("remind me in 10 minutes to call raj", 600, "call raj"),
    ("remind me to call raj in 10 minutes", 600, "call raj"),
    ("set a timer for 5 minutes", 300, "Your timer is done"),
    ("remind me in an hour to take medicine", 3600, "take medicine"),
])
def test_parse_reminder_command(phrase, delay, message):
    now = datetime(2026, 10, 4, 12, 0)
    due, msg = main.parse_reminder_command(phrase, now)
    assert due - now.timestamp() == delay
    assert msg == message


def test_parse_reminder_command_clock():
    now = datetime(2026, 10, 4, 12, 0)
    due, msg = main.parse_reminder_command("remind me at 6 pm to call mom", now)
    assert datetime.fromtimestamp(due) == datetime(2026, 10, 4, 18, 0) and msg == "call mom"


def test_non_reminder_phrases_are_ignored():
    assert main.parse_reminder_command("who wrote hamlet") is None
    assert main.parse_reminder_command("remind me to breathe") is None  # no time given


class TestReminderStorage:
    @pytest.fixture(autouse=True)
    def temp_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main, "REMINDERS_FILE", str(tmp_path / "reminders.json"))

    def test_set_list_and_cancel(self, log):
        main.process_command("remind me in 10 minutes to call raj")
        assert len(main._load_reminders()) == 1
        main.process_command("what are my reminders")
        assert any("call raj" in e for e in log if e.startswith("say:You have"))
        main.process_command("cancel all reminders")
        assert main._load_reminders() == []

    def test_due_reminder_is_spoken_and_removed(self, log, monkeypatch):
        main.add_reminder(0, "call raj")           # already due
        main.add_reminder(9e12, "far future")
        sleeps = []

        def fake_sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) > 1:                    # allow exactly one pass through the loop
                raise StopIteration

        monkeypatch.setattr(main.time, "sleep", fake_sleep)
        monkeypatch.setattr(main, "beep", lambda f: None)
        with pytest.raises(StopIteration):
            main._reminder_loop()
        assert "say:Reminder: call raj" in log
        assert [r["text"] for r in main._load_reminders()] == ["far future"]


# ---------------- live info (network mocked) ----------------
class TestLiveInfo:
    @pytest.fixture(autouse=True)
    def fake_http(self, monkeypatch):
        def fake(url, params=None):
            if "geocoding" in url:
                return {"results": [{"name": "Delhi", "latitude": 28.6, "longitude": 77.2}]} if params["name"].lower() == "delhi" else {}
            if "open-meteo.com/v1/forecast" in url:
                return {"current": {"temperature_2m": 31.4, "apparent_temperature": 35.2, "weather_code": 0, "wind_speed_10m": 5}}
            if "search/title" in url:
                return {"pages": [{"key": "Moon"}]} if params["q"] == "moon" else {"pages": []}
            if "page/summary" in url:
                return {"extract": "The Moon (Latin: Luna) is Earth's satellite. It orbits Earth. A third sentence."}
            raise AssertionError(url)

        monkeypatch.setattr(main, "_http_json", fake)

    def test_weather_for_named_city(self, log):
        main.process_command("what is the weather in Delhi")
        assert "say:In Delhi it is 31 degrees with clear sky, feels like 35." in log

    def test_unknown_city(self, log):
        main.process_command("weather in Nowhereville")
        assert any("could not find weather" in e for e in log)

    def test_wikipedia_summary_is_two_sentences(self, log):
        main.process_command("tell me about the moon")
        said = [e for e in log if e.startswith("say:The Moon")][0]
        assert "Latin" not in said and "third sentence" not in said

    def test_unknown_topic_falls_back_to_ai(self, log):
        main.process_command("who is zzzz")
        assert any(e.startswith("say:ai:") for e in log)

    def test_network_failure_is_handled(self, log, monkeypatch):
        def boom(url, params=None):
            raise OSError("offline")
        monkeypatch.setattr(main, "_http_json", boom)
        main.process_command("weather in Delhi")
        assert any("could not reach the internet" in e for e in log)

    def test_what_is_questions_still_go_to_ai(self, log):
        main.process_command("what is two plus two")
        assert any(e.startswith("say:ai:") for e in log)


# ---------------- Hindi / Hinglish ----------------
@pytest.mark.parametrize("heard, english", [
    ("क्रोम खोलो", "open chrome"), ("chrome kholo", "open chrome"), ("यूट्यूब खोल दो", "open youtube"),
    ("आवाज़ बढ़ाओ", "volume up"), ("volume kam karo", "volume down"), ("awaaz badhao", "volume up"),
    ("समय क्या हुआ", "what time is it"), ("तारीख क्या है", "what is the date"),
    ("मौसम कैसा है", "weather"), ("खबर सुनाओ", "tell me the news"),
    ("open chrome", "open chrome"), ("who wrote hamlet", "who wrote hamlet"),
])
def test_hindi_to_english(heard, english):
    assert main.hindi_to_english(heard) == english


def test_hindi_command_runs_english_action(log):
    main.process_command("आवाज़ बढ़ाओ")
    assert "key:volume upx5" in log


class TestRecognitionFallback:
    @pytest.fixture(autouse=True)
    def reset_lang(self, monkeypatch):
        monkeypatch.setattr(main, "_recog_primary", "en-IN")
        monkeypatch.setattr(main, "STT_ENGINE", "google")      # these tests are about the Google path

    def fake(self, monkeypatch, outcomes):
        calls = []

        def recognize_google(audio, language):
            calls.append(language)
            result = outcomes[language]
            if result is None:
                raise main.sr.UnknownValueError()
            return result

        monkeypatch.setattr(main.recognizer, "recognize_google", recognize_google)
        return calls

    def test_uses_primary_when_it_works(self, monkeypatch):
        calls = self.fake(monkeypatch, {"en-IN": "open chrome", "hi-IN": "ignored"})
        assert main.recognize_with_fallback(object()) == "open chrome"
        assert calls == ["en-IN"]

    def test_falls_back_to_hindi(self, monkeypatch):
        calls = self.fake(monkeypatch, {"en-IN": None, "hi-IN": "क्रोम खोलो"})
        assert main.recognize_with_fallback(object()) == "क्रोम खोलो"
        assert calls == ["en-IN", "hi-IN"]

    def test_returns_none_when_both_fail(self, monkeypatch):
        self.fake(monkeypatch, {"en-IN": None, "hi-IN": None})
        assert main.recognize_with_fallback(object()) is None

    def test_switch_language_by_voice(self, log, monkeypatch):
        main.process_command("switch to hindi")
        assert main._recog_primary == "hi-IN"
        calls = self.fake(monkeypatch, {"en-IN": "x", "hi-IN": "namaste"})
        main.recognize_with_fallback(object())
        assert calls == ["hi-IN"]
        main.process_command("switch to english")
        assert main._recog_primary == "en-IN"
