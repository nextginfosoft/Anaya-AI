"""Tests for the hold-Space-to-talk key handler. Time, timers and key sending are all faked."""
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeTimer:
    """Stands in for threading.Timer; the test fires it by hand."""
    instances = []

    def __init__(self, interval, function, args=()):
        self.interval, self.function, self.args = interval, function, args
        self.cancelled = False
        self.daemon = False
        FakeTimer.instances.append(self)

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True

    def fire(self):
        if not self.cancelled:
            self.function(*self.args)


def down():
    return SimpleNamespace(event_type="down", name="space")


def up():
    return SimpleNamespace(event_type="up", name="space")


@pytest.fixture
def space(monkeypatch):
    FakeTimer.instances = []
    clock = Clock()
    sent = []
    s = main.SmartSpace(hold_seconds=0.3, clock=clock, send=lambda: sent.append("space"),
                        timer_factory=FakeTimer, modifier_down=lambda: False)
    # run the re-send inline instead of on a thread so tests are deterministic
    monkeypatch.setattr(main.threading, "Thread", lambda target, daemon=None: SimpleNamespace(start=target))
    s.clock, s.sent = clock, sent
    s.clock.advance(5)                       # keyboard has been quiet for a while
    return s


# ---------------- a tap still types a space ----------------
def test_quick_tap_is_held_back_then_resent_once(space):
    assert space.on_space(down()) is False                  # swallowed while we decide
    space.clock.advance(0.1)
    assert space.on_space(up()) is False
    assert space.sent == ["space"]                          # re-sent as a normal tap
    assert FakeTimer.instances[0].cancelled
    assert space.talking is False


def test_our_resent_tap_is_not_intercepted_again(space):
    space.on_space(down()); space.on_space(up())
    assert space.on_space(down()) is True                   # the re-sent key-down passes
    assert space.on_space(up()) is True                     # and the key-up
    assert space.sent == ["space"]                          # still exactly one re-send


def test_resent_events_expire_so_real_presses_are_not_ignored(space):
    space.on_space(down()); space.on_space(up())
    space.clock.advance(2)                                  # the re-sent events never arrived
    assert space.on_space(down()) is False                  # a real press is handled normally again


# ---------------- hold to talk ----------------
def test_hold_becomes_talking_and_release_ends_it(space):
    assert space.on_space(down()) is False
    assert space.talking is False                           # not yet: still might be a tap
    space.clock.advance(0.3)
    FakeTimer.instances[0].fire()
    assert space.talking is True
    space.clock.advance(2)
    assert space.on_space(up()) is False                    # release is swallowed, no space typed
    assert space.talking is False
    assert space.sent == []                                 # nothing was typed into the active window


def test_key_repeat_while_holding_is_swallowed(space):
    space.on_space(down())
    for _ in range(5):
        assert space.on_space(down()) is False              # auto-repeat events
    space.clock.advance(0.3)
    FakeTimer.instances[0].fire()
    for _ in range(5):
        assert space.on_space(down()) is False
    assert space.sent == []


def test_stale_timer_from_an_earlier_tap_cannot_start_talking(space):
    space.on_space(down()); space.clock.advance(0.1); space.on_space(up())     # tap: timer cancelled
    first = FakeTimer.instances[0]
    space.clock.advance(1)
    space.on_space(down())                                                      # a new press is pending
    first.cancelled = False
    first.fire()                                                                # old timer fires late
    assert space.talking is False


def test_talking_expires_if_the_key_up_is_missed(space):
    space.on_space(down()); space.clock.advance(0.3); FakeTimer.instances[0].fire()
    assert space.talking is True
    space.clock.advance(main.SmartSpace.MAX_TALK_SECONDS + 1)
    assert space.talking is False                           # never stuck recording forever


# ---------------- normal typing is never touched ----------------
def test_space_during_typing_passes_straight_through(space):
    space.note_key(SimpleNamespace(name="h"))
    space.clock.advance(0.1)                                # typed a letter 0.1 s ago
    assert space.on_space(down()) is True
    assert space.on_space(up()) is True
    assert space.sent == [] and not FakeTimer.instances     # no hold-back, no timer, no talking


def test_fast_rollover_keeps_letters_in_order(space):
    """Letter, Space down, next letter, Space up: Space must not be delayed behind the next letter."""
    space.note_key(SimpleNamespace(name="o"))
    space.clock.advance(0.05)
    assert space.on_space(down()) is True                   # passes immediately, before the next letter arrives
    space.note_key(SimpleNamespace(name="w"))
    assert space.on_space(up()) is True


def test_holding_a_normal_space_while_typing_repeats_normally(space):
    space.note_key(SimpleNamespace(name="a"))
    space.clock.advance(0.1)
    assert space.on_space(down()) is True
    for _ in range(4):
        assert space.on_space(down()) is True               # repeats of an ordinary space pass
    assert space.talking is False


def test_idle_threshold_is_respected(space):
    space.note_key(SimpleNamespace(name="a"))
    space.clock.advance(main.SmartSpace.IDLE_SECONDS + 0.05)
    assert space.on_space(down()) is False                  # quiet long enough: talk candidate


def test_pressing_space_itself_does_not_count_as_typing(space):
    space.note_key(SimpleNamespace(name="space"))
    assert space.on_space(down()) is False


def test_modifier_held_means_normal_shortcut_not_talking(space):
    space._modifier_down = lambda: True                     # e.g. Ctrl+Space or Win+Space
    assert space.on_space(down()) is True
    assert space.on_space(up()) is True
    assert not FakeTimer.instances


# ---------------- robustness ----------------
def test_hook_always_returns_a_real_bool(space):
    """The keyboard library swallows a key on None as well as False, so the hook must never return None."""
    for event in (down(), up(), down(), up(), up()):
        assert isinstance(space.on_space(event), bool)


def test_errors_let_the_key_through(space, capsys):
    def boom():
        raise RuntimeError("clock broke")
    space._clock = boom
    assert space.on_space(down()) is True
    assert "letting the key through" in capsys.readouterr().out


def test_failure_to_resend_does_not_crash(space, capsys):
    def broken():
        raise OSError("no input")
    space._send = broken
    space.on_space(down()); space.on_space(up())
    assert "Could not re-send the space key" in capsys.readouterr().out


# ---------------- wiring into push-to-talk ----------------
def test_smart_space_counts_as_the_talk_key(monkeypatch):
    monkeypatch.setattr(main, "PTT_KEYS", ["smart space"])
    monkeypatch.setattr(main.SMART_SPACE, "_state", "talking")
    monkeypatch.setattr(main.SMART_SPACE, "_talk_started", main.SMART_SPACE._clock())
    assert main.ptt_held() is True
    monkeypatch.setattr(main.SMART_SPACE, "_state", "idle")
    assert main.ptt_held() is False


def test_default_talk_keys_are_space_and_f9():
    assert main.PTT_KEYS[:2] == ["smart space", "f9"] or os.environ.get("ANAYA_PTT_KEY") or os.environ.get("MAYA_PTT_KEY")
    assert "SPACE" in main.PTT_LABEL.upper()


def test_hold_seconds_setting(monkeypatch):
    monkeypatch.setenv("ANAYA_SPACE_HOLD", "0.45")
    assert float(main._env("SPACE_HOLD", "0.30")) == 0.45
