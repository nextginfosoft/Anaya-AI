# Maya AI — project notes for Claude

Voice assistant (Python, Windows + macOS). Hold a talk key, speak, Maya transcribes (Google Speech), runs a
command or asks a local Ollama model, and answers out loud. Single file: `main.py`.

## Run
- `pip install -r requirements.txt` then `python main.py` (hold **Right Ctrl** or **F9** to talk).
- Auto-start: a shortcut `Maya AI.lnk` in the Windows Startup folder runs `pythonw.exe main.py` (no console; logs to `maya.log`).
- Tests: `pip install -r requirements-dev.txt` then `python -m pytest tests -q` (side effects are stubbed).
- Ollama must be running with the model in `OLLAMA_MODEL` (default `llama3.2:3b`).

## Environment variables
`MAYA_MODE` (`ptt` default | `wake`), `MAYA_PTT_KEY` (default `right ctrl,f9`; `mouse:x2` supported),
`MAYA_STOP_KEY` (default `esc`), `MAYA_MODEL`, `MAYA_MAX_TOKENS` (default 100), `MAYA_VOICE`, `MAYA_ANIMATION=1`, `MAYA_CITY` (default weather city), `MAYA_LANG` (first recognition language, default `en-IN`).

## Structure of main.py
platform helpers → speech (`speak`, interruptible) → folder search → AI (`ask_local_ai`, short answers) →
audio capture (`sounddevice`, **not** PyAudio — no wheel for Python 3.14) → `normalize_command` →
`recognize_with_fallback` (en-IN then hi-IN) → `hindi_to_english` → `handle_custom_app` (apps.json) → `handle_info_command` (weather/news/Wikipedia) → `handle_reminder_command` (reminders.json + background thread) → `handle_system_command` (volume, brightness, lock, time, apps) → `process_command` → wake-word loop (`start_maya`)
and push-to-talk loop (`start_push_to_talk`).

## Gotchas
- Commands are lower-cased and de-fluffed by `normalize_command` before matching; match on the normalized text.
- This laptop's mic is very quiet (raw peaks ~300–1500). Audio is boosted up to 40x in `frames_to_audio`.
- Don't add shutdown/restart voice commands without a confirmation step (misheard speech).
- Write patches with the Edit/Write tools, not shell heredocs: shell layers mangle backslashes in regexes and JSON paths (twice produced backspace characters).
- `debug_audio/` (rejected clips), `screenshots/`, `maya.log`, `reminders.json` and `venv/` are git-ignored; `apps.json` is committed and user-editable.
- Shell: PowerShell/Git Bash on Windows. Commit messages: present tense. Never commit `.env`.
