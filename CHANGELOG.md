# Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.0] - 2026-10-04 - Anaya AI

The project is renamed from **Maya AI** to **Anaya AI** and is developed by Santosh Pandit. It is based on Maya AI 1.2 by Taha Shaikh (MIT).

### Added
- **Windows support** (the original targeted macOS only): speech, apps, folders, screenshots and microphone capture.
- **Push-to-talk:** hold Right Ctrl or F9 to speak; optional mouse side button; Esc or a talk key interrupts speech. The wake word is still available with `ANAYA_MODE=wake`.
- **Offline speech recognition** with Whisper, with Google as an optional fallback; English and Hindi with automatic language choice; filtering of Whisper's hallucinations on noise.
- **Natural voice:** Microsoft neural voices (English and Hindi), falling back to the offline Windows voice; private text always uses the offline voice.
- **Conversation memory** for follow-up questions, with "forget that".
- **Reminders and timers** that survive restarts.
- **Live information:** weather, news headlines and Wikipedia summaries.
- **Morning briefing** after sign-in and on request.
- **Hands-free text:** dictation, "type ...", read the clipboard or selection aloud, translate and summarise through the local model.
- **Windows commands:** volume, brightness, lock screen, time, date, battery, and common Windows apps.
- **Hindi and Hinglish** command support and "switch to Hindi / English".
- **`apps.json`:** your own spoken shortcuts to websites, folders and programs.
- **Reliability:** single-instance guard, crash recovery with backoff, specific spoken errors (Ollama down, model missing, microphone unavailable, no internet), log rotation.
- **Start with Windows** via a Startup shortcut; setup and startup scripts in `scripts/`.
- Automated tests, GitHub Actions workflow, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and the `docs/` folder with a PDF feature guide.

### Changed
- Chat model is `llama3.2:3b` (much faster than `llama3` on a laptop); answers are kept to about two spoken sentences.
- Settings use the `ANAYA_` prefix; the old `MAYA_` names still work.
- Recording of rejected audio is off by default.
- `requirements.txt` replaced a macOS-only package freeze with the packages the project actually uses.
- The startup animation is off by default (`ANAYA_ANIMATION=1` to enable).

### Fixed
- Emoji in log messages crashed on Windows consoles.
- The "open WhatsApp" command never matched.
- The README's licence claim now has a matching `LICENSE` file.

## [1.2.0-maya] - 2026-07-29 - Maya AI (original)

Initial release by Taha Shaikh: macOS voice assistant using SpeechRecognition, Ollama (Llama 3), PyWhatKit and PyAutoGUI, with wake word "Maya".
