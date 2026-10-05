# Security and privacy

## Reporting a vulnerability

Please **do not open a public issue** for a security or privacy problem.
Use GitHub's private reporting: **Security tab > Report a vulnerability** on this repository.
Include what you found, how to reproduce it, and what it affects. You will get a reply as soon as the maintainer can read it.

## What Anaya does on your machine

Anaya is a voice assistant that can control the computer, so it is worth knowing exactly what it can reach:

| Capability | Detail |
|---|---|
| Microphone | Records **only while you hold the talk key** (default mode). In wake-word mode it listens continuously. |
| Global keyboard and mouse hooks | Needed to see the talk key and the stop key. Anaya only checks whether those keys are held; it does not log what you type. The Space key is intercepted: a tap is held back for up to 0.3 s and re-sent as a normal space, and a hold becomes the talk key. If the handler fails, the key is let through. |
| Clipboard and selection | Read and temporarily changed by dictation, "read this", translate and summarise; your clipboard is restored afterwards. |
| Typing into windows | Dictation and "type ..." paste text into whichever window has focus. |
| Running programs | Opens apps, folders and addresses you ask for, and anything you list in `apps.json`. |
| Network | Whisper model download (first start), weather, news, Wikipedia, the neural voice, and optional Google speech. |

## Where data goes

| Data | Where |
|---|---|
| Your voice | Processed locally by Whisper. Sent to Google only if Whisper hears nothing usable and `ANAYA_STT_FALLBACK` is not `0`. |
| Chat questions and answers | Local model through Ollama; not sent anywhere. |
| Spoken reply text | Sent to Microsoft's neural voice service unless `ANAYA_TTS=windows`. Text from your clipboard or selection is never sent: it uses the offline voice. |
| Weather, news and Wikipedia requests | Sent to Open-Meteo, Google News and Wikipedia respectively. A bare "weather" uses a one-time IP-based location lookup (set `ANAYA_CITY` to avoid it). |
| Recordings | Not stored. `ANAYA_DEBUG_AUDIO=1` stores the last 30 rejected clips in `debug_audio/` (ignored by git). |
| Reminders | Stored in `reminders.json` on your disk. |

## Safety choices

- No shutdown, restart, sleep or delete by voice.
- Only one copy can run, so commands are never executed twice.
- `apps.json` is trusted input: anything listed there can be launched. Do not paste entries from untrusted sources.
- Secrets never belong in the repository; `.env` files are git-ignored.

## Supported versions

Only the latest release on `main` receives fixes.
