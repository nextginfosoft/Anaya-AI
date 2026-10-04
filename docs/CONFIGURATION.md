# Configuration

## Settings (environment variables)

Every setting starts with `ANAYA_`. The old `MAYA_` names still work; if both are set, `ANAYA_` wins.

Set one for the current PowerShell window:

```powershell
$env:ANAYA_PTT_KEY = "f8"
python main.py
```

Or permanently for your Windows account (takes effect for newly started programs):

```powershell
setx ANAYA_CITY "Mumbai"
```

| Setting | Default | Meaning |
|---|---|---|
| `ANAYA_MODE` | `ptt` | `ptt` = hold-to-talk, `wake` = say "Anaya" first |
| `ANAYA_PTT_KEY` | `right ctrl,f9` | Talk keys, comma separated. `mouse:x` and `mouse:x2` use the mouse side buttons if your mouse reports them |
| `ANAYA_STOP_KEY` | `esc` | Key that interrupts speech |
| `ANAYA_STT` | `whisper` | `whisper` (offline) or `google` |
| `ANAYA_STT_FALLBACK` | `1` | `0` = never use Google, even if Whisper hears nothing |
| `ANAYA_WHISPER_MODEL` | `base` | `tiny`, `base`, `small`, `medium`. Larger is more accurate and slower |
| `ANAYA_LANG` | `en-IN` | Language tried first (`hi-IN` for Hindi) |
| `ANAYA_TTS` | `edge` | `edge` = neural voice (online), `windows` = offline voice |
| `ANAYA_EDGE_VOICE` | `en-IN-NeerjaNeural` | English neural voice |
| `ANAYA_EDGE_VOICE_HI` | `hi-IN-SwaraNeural` | Voice used for Devanagari text |
| `ANAYA_VOICE` | automatic (female) | Name of an installed Windows voice, e.g. `Microsoft Zira Desktop` |
| `ANAYA_MODEL` | `llama3.2:3b` | Ollama model for chat, summaries and translation |
| `ANAYA_MAX_TOKENS` | `100` | Length cap for spoken answers |
| `ANAYA_CITY` | from your IP | Default city for weather and the briefing |
| `ANAYA_BRIEFING` | `1` | `0` = no briefing after sign-in |
| `ANAYA_BRIEFING_DELAY` | `12` | Seconds to wait after start before the briefing |
| `ANAYA_ANIMATION` | `0` | `1` = open the startup animation in the browser |
| `ANAYA_DEBUG_AUDIO` | `0` | `1` = keep the last 30 rejected recordings in `debug_audio/` |
| `ANAYA_ALLOW_MULTIPLE` | `0` | `1` = allow more than one copy to run |

## apps.json

Your own spoken shortcuts. Say "open &lt;name&gt;" and Anaya launches whatever you listed. The file is read every time, so edits apply immediately.

```json
{
  "_help": "Lines starting with _ are ignored.",
  "github": "https://github.com",
  "gmail": "https://mail.google.com",
  "spotify": "spotify:",
  "my project": "D:\\work\\my-project",
  "notepad plus": "C:\\Program Files\\Notepad++\\notepad++.exe"
}
```

The value can be a web address, a URI scheme (ending in `:`), a file or folder path (use `\\` in JSON), or a command on your PATH.
Words like "the", "my" and "a" in front of a name are ignored when matching.

## Files Anaya creates

| File | Purpose | In git? |
|---|---|---|
| `anaya.log` (and `anaya.log.1`) | Log when started at sign-in without a console. Rotated at 1 MB | No |
| `reminders.json` | Pending reminders and timers | No |
| `last_briefing.json` | When the briefing last played (the 4-hour cooldown) | No |
| `screenshots/` | Screenshots from "screenshot" | No |
| `debug_audio/` | Rejected recordings, only if `ANAYA_DEBUG_AUDIO=1` | No |

Downloaded models live outside the project: Whisper in `%USERPROFILE%\.cache\huggingface`, Ollama models in `%USERPROFILE%\.ollama`.

## Starting with Windows

```powershell
.\scripts\install_startup.ps1      # adds "Anaya AI.lnk" to your Startup folder
.\scripts\uninstall_startup.ps1    # removes it
```

The shortcut runs `pythonw.exe main.py` (no console window) from the project folder, using the project's `venv` if there is one.
Ollama installs its own Startup entry, so the chat model is available at sign-in too.
