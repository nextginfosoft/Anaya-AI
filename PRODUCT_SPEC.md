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
| Memory | Remembers the last 6 exchanges for follow-up questions; resets after 5 quiet minutes or "forget that". |
| Reminders | "Remind me in 10 minutes to…", "set a timer for 5 minutes", at a clock time; stored in `reminders.json`, survive restarts. |
| Live info | Weather (Open-Meteo), news (Google News RSS), "who is / tell me about" (Wikipedia). |
| Hindi | Falls back to Hindi recognition automatically; "switch to Hindi/English"; core commands work in Hindi/Hinglish; replies stay English. |
| App list | `apps.json` maps spoken names to URLs, paths or programs; edits apply immediately. |
| Hands-free text | Dictation mode and "type …" paste into the active window; read the clipboard or selection aloud; translate and summarise via the local model. |
| Briefing | At sign-in (once per 4 hours, after a 12 s delay) and on demand: time, battery, weather, reminders, headlines. Esc stops it. |
| Startup | Auto-starts at Windows sign-in (Startup-folder shortcut), logs to `maya.log`. |

## Non-goals / safety
- No shutdown/restart/sleep by voice (risk of misrecognition).
- No always-on microphone in the default mode (push-to-talk only records while the key is held).
- Speech audio is sent to Google for transcription; chat stays on the machine.

## Known limitations
- Laptop mic is very quiet; a headset/USB mic or higher Windows input level improves accuracy a lot.
- Hindi: only the commands in `_HINDI_WORDS` / `_HINDI_PHRASES` are understood; open questions in Hindi go to a small English-centred model, and replies are spoken in English.
- Weather without a city uses an IP-based location guess (set `MAYA_CITY` to fix it).
- Reminders fire only while Maya is running.

## Backlog
1. Confirmation step, then shutdown/restart/sleep by voice.
2. Spoken Hindi replies (needs a Hindi TTS voice).
3. Calendar / email integrations.
