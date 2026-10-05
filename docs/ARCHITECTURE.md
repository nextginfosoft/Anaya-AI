# Architecture

Anaya is deliberately one Python file, [`main.py`](../main.py), organised in labelled sections. Tests live in [`tests/`](../tests).

## The path of one request

1. **Wait for the talk key.** `wait_for_ptt()` polls the talk keys: hold Space (`SmartSpace`), F9, or optional mouse buttons. Nothing records before the key goes down. `SmartSpace` intercepts only the Space key: a tap is held back briefly and re-sent as a normal space, a hold of about 0.3 s becomes the talk key, and during typing Space passes straight through.
2. **Record.** `record_while_held()` captures 16 kHz mono audio with `sounddevice` while the key is held (max 15 s; taps under 0.3 s are ignored).
   `frames_to_audio()` boosts quiet audio up to 40x.
3. **Recognise.** `recognize_with_fallback()` tries offline **Whisper** first, then Google (English, then Hindi) if allowed.
   Whisper's language is chosen from its own probabilities, restricted to English or Hindi, with a vocabulary hint for commands.
   `clean_whisper_text()` drops the usual hallucinations on noise (foreign scripts, repetition loops, subtitle boilerplate).
4. **Route.** `process_command()` translates Hindi/Hinglish (`hindi_to_english`), normalises the text (`normalize_command`), then tries handlers in order:
   dictation mode → text tools → briefing → language switch / forget → reminders → live info → `apps.json` → system commands → built-in apps → the local model.
5. **Speak.** `speak()` uses the Microsoft neural voice when online and allowed, falling back to the offline Windows voice. Playback is interruptible.

## Sections of main.py

| Section | Responsibility |
|---|---|
| Platform helpers | `open_path`, `open_app`, `IS_WINDOWS` / `IS_MAC` |
| Settings | `_env()` reads `ANAYA_*` then the legacy `MAYA_*` |
| Voice | Neural voice via `edge-tts` played through Windows MCI; offline fallback through `System.Speech`; `stop_requested()` |
| AI chat | `ask_local_ai()` with conversation memory, short-answer prompt, `clean_for_speech()`, specific error messages |
| Audio capture | `record_phrase()` (wake-word mode), `record_while_held()` (push-to-talk), `frames_to_audio()` |
| Recognition | Google (`recognize_google_both`), Whisper (`transcribe_whisper`), language switching |
| Hindi | Word and phrase tables that map Hindi/Hinglish to the English commands |
| Custom apps | `load_custom_apps()`, `handle_custom_app()` |
| Live info | Open-Meteo weather, Google News RSS, Wikipedia summaries |
| Text tools | Dictation, clipboard/selection reading, translate, summarise |
| Briefing | Sign-in briefing with a 4-hour cooldown |
| Reminders | Parsing ("in 10 minutes", "at 6 pm"), JSON storage, background thread |
| System commands | Volume, brightness, lock, time, battery, Windows apps |
| Command processor | `normalize_command`, `process_command` |
| Loops | `start_push_to_talk()` (default), `start_anaya()` (wake word) |
| Reliability | Single-instance mutex, `supervise()` crash restarts, problem reporting |

## Design decisions

- **Offline first.** Recognition and chat run locally; online services are used only where they add something (neural voice, weather, news) and each can be turned off.
- **Private text never goes to an online voice.** Anything derived from your clipboard or selection calls `speak(..., offline=True)`.
- **Hold-to-talk instead of a wake word.** It avoids the open microphone, background chatter being transcribed, and false wake-ups, and it is far more reliable on a quiet microphone.
- **Boost, then filter.** A quiet laptop microphone is amplified up to 40x; Whisper's output is then filtered for hallucinations.
- **Space as a talk key, carefully.** Intercepting a typing key is invasive, so `SmartSpace` only acts after a quiet moment with no modifiers held, always answers the hook with a real True/False (the keyboard library also swallows a key on `None`), lets the key through on any error, and expires a stuck "talking" state after 20 s.
- **Safe by default.** No shutdown, restart or sleep by voice. Recordings are not saved unless you turn that on. A second copy refuses to start.
- **Degrade, don't fail.** Every online feature has a fallback or a clear spoken message (no internet, Ollama down, model missing, microphone unavailable).
- **Normalisation matters.** `normalize_command` rewrites a leading "start"/"launch" to "open" and drops "the/my/a", so any new pattern has to be written against the normalised text.

## Testing

Run `python -m pytest`. The tests never touch a real microphone, speaker, clipboard or the internet: speech, keys, the clipboard, HTTP calls and the local model are replaced
with fakes. They cover command parsing, Hindi translation, reminders, live info, dictation and text tools, the Whisper and Google routing, voice selection, the
briefing, single-instance and crash recovery, the rename and licence, and `apps.json`.

Things the tests cannot cover, and which were checked by hand: real voice recognition on a given microphone, the real key and mouse hooks, how the neural voice sounds,
and typing into a real window.

## Platform notes

Windows is the primary target. The macOS code paths (`say`, `open -a`, `mdfind`) are kept from the original project but are not covered by CI or tested on current macOS.
