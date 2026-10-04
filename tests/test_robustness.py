"""Tests for crash recovery, single instance, and the specific error messages."""
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


# ---------------- supervise ----------------
class TestSupervise:
    def test_normal_return_is_not_restarted(self):
        runs = []
        assert main.supervise(lambda: runs.append(1), sleep=lambda s: None) is True
        assert runs == [1]

    def test_system_exit_means_clean_stop(self):
        def target():
            raise SystemExit
        assert main.supervise(target, sleep=lambda s: None) is True

    def test_keyboard_interrupt_propagates(self):
        def target():
            raise KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            main.supervise(target, sleep=lambda s: None)

    def test_restarts_after_a_crash_then_succeeds(self, capsys):
        runs, sleeps = [], []

        def target():
            runs.append(1)
            if len(runs) < 3:
                raise RuntimeError("boom")

        assert main.supervise(target, sleep=sleeps.append) is True
        assert len(runs) == 3 and sleeps == [2, 4]            # backoff grows
        assert "RuntimeError: boom" in capsys.readouterr().err   # the traceback is logged

    def test_gives_up_after_too_many_crashes(self, monkeypatch):
        said = []
        monkeypatch.setattr(main, "speak", lambda t, **kw: said.append(t))

        def target():
            raise RuntimeError("always")

        assert main.supervise(target, max_crashes=3, sleep=lambda s: None) is False
        assert said == ["I keep crashing. Please check the Anaya log."]


# ---------------- single instance ----------------
@pytest.mark.skipif(not main.IS_WINDOWS, reason="Windows mutex")
def test_second_instance_is_refused(monkeypatch):
    monkeypatch.setattr(main, "INSTANCE_MUTEX_NAME", "Local\\AnayaTest_" + uuid.uuid4().hex)
    monkeypatch.delenv("ANAYA_ALLOW_MULTIPLE", raising=False)
    assert main.acquire_single_instance() is True
    assert main.acquire_single_instance() is False


def test_multiple_instances_can_be_allowed(monkeypatch):
    monkeypatch.setenv("ANAYA_ALLOW_MULTIPLE", "1")
    assert main.acquire_single_instance() is True
    assert main.acquire_single_instance() is True


# ---------------- messages ----------------
@pytest.mark.parametrize("error, expected", [
    (ConnectionError("Failed to connect to Ollama"), "The AI is not running. Please start Ollama."),
    (RuntimeError("model 'x' not found"), f"The AI model {main.OLLAMA_MODEL} is not installed. Run ollama pull {main.OLLAMA_MODEL}."),
    (RuntimeError("weird"), "Sorry boss, the AI had a problem."),
])
def test_explain_ollama_error(error, expected):
    assert main.explain_ollama_error(error) == expected


def test_ai_failure_message_reaches_the_user(monkeypatch):
    def boom(**kw):
        raise ConnectionError("Failed to connect to Ollama")
    monkeypatch.setattr(main.ollama, "chat", boom)
    assert main.ask_local_ai("hi") == "The AI is not running. Please start Ollama."


def test_not_understood_message_depends_on_connectivity(monkeypatch):
    monkeypatch.setitem(main._stt_status, "google_unreachable", False)
    assert main.not_understood_message() == "Sorry boss, I did not catch that"
    monkeypatch.setitem(main._stt_status, "google_unreachable", True)
    monkeypatch.setitem(main._whisper, "state", "loading")
    assert "cannot reach the speech service" in main.not_understood_message()
    monkeypatch.setitem(main._whisper, "state", "ready")          # offline model works: ordinary miss
    assert main.not_understood_message() == "Sorry boss, I did not catch that"


def test_report_problem_is_rate_limited(monkeypatch):
    said = []
    monkeypatch.setattr(main, "speak", lambda t, **kw: said.append(t))
    monkeypatch.setattr(main, "_last_reported", {})
    for _ in range(5):
        main.report_problem("mic", "mic broken", every=60)
    assert said == ["mic broken"]
    main.report_problem("other", "different problem", every=60)
    assert said == ["mic broken", "different problem"]


def test_microphone_error_detection():
    import sounddevice as sd
    assert main.is_microphone_error(sd.PortAudioError("Error opening InputStream"))
    assert main.is_microphone_error(RuntimeError("audio device unavailable"))
    assert not main.is_microphone_error(RuntimeError("something else"))


# ---------------- debug audio privacy ----------------
class FakeAudio:
    def get_wav_data(self):
        return b"RIFF"


def test_rejected_audio_is_not_saved_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANAYA_DEBUG_AUDIO", raising=False)
    assert main.save_rejected_audio(FakeAudio()) is None
    assert not (tmp_path / "debug_audio").exists()


def test_rejected_audio_kept_only_when_enabled_and_pruned(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANAYA_DEBUG_AUDIO", "1")
    monkeypatch.setattr(main, "DEBUG_AUDIO_KEEP", 3)
    for _ in range(6):
        assert main.save_rejected_audio(FakeAudio())
    assert len(list((tmp_path / "debug_audio").glob("*.wav"))) == 3
