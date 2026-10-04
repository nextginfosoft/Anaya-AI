# Maya AI 1.2 — Product Spec

## Goal
A private, mostly-local voice assistant for Windows (and macOS) that controls the computer and answers questions
by voice, usable hands-free-ish via a hold-to-talk key.

## Users
A single desktop user who wants quick spoken commands and short answers without a cloud chatbot.

## Core features (built)
| Area | Behaviour |
|---|---|
| Input | Hold Right Ctrl / F9 to record; release to send. Optional wake-word mode ("Maya"). |
| Recognition | Google Speech (`en-IN`), audio boosted for quiet mics. |
| Output | Windows SAPI female voice (Heera), interruptible with Esc or the talk key. |
| Apps & web | Open VS Code, Chrome, Safari (mac), WhatsApp, YouTube; search Google/YouTube; play songs. |
| System | Volume, brightness, lock screen, time/date/battery, Notepad/Calculator/Settings/etc., screenshots. |
| Folders | "Open folder downloads" etc. |
| AI chat | Local Ollama model (`llama3.2:3b`), answers limited to ~2 sentences. |
| Startup | Auto-starts at Windows sign-in (Startup-folder shortcut), logs to `maya.log`. |

## Non-goals / safety
- No shutdown/restart/sleep by voice (risk of misrecognition).
- No always-on microphone in the default mode (push-to-talk only records while the key is held).
- Speech audio is sent to Google for transcription; chat stays on the machine.

## Known limitations
- Laptop mic is very quiet; a headset/USB mic or higher Windows input level improves accuracy a lot.
- English (Indian) recognition only; Hindi/Hinglish is unreliable.
- No conversation memory (each question is answered in isolation).

## Backlog (priority order)
1. Conversation memory (last few turns, reset after idle).
2. Reminders and timers.
3. Live info (weather, quick web answers).
4. Hindi/Hinglish recognition.
5. Configurable app list file instead of editing code.
