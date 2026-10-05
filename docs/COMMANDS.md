# Voice commands

Hold **Space** for about a third of a second until you hear the beep (or hold **F9**), speak, release. A quick tap of Space still types a space. Filler words such as "please", "the", "my", "can you" and "hey" are ignored, and
"launch" or "start" mean "open". Phrases are matched loosely, so "please open the Chrome" works like "open Chrome".

In wake-word mode (`ANAYA_MODE=wake`) say **"Anaya"** first, either alone ("Anaya" ... "open Chrome") or in one go ("Anaya, open Chrome").

## Open things

| Say | What happens |
|---|---|
| open Chrome / open VS Code / open WhatsApp / open YouTube | Launches the app, or its website when the app is missing |
| open Safari | macOS only |
| open Notepad / Calculator / Task Manager / File Explorer / Settings / Control Panel / Command Prompt / Terminal / Paint / Snipping Tool | Opens the Windows tool |
| open folder downloads (or desktop, documents, ...) | Finds the folder by name and opens it |
| open github, open my project, ... | Anything listed in [`apps.json`](CONFIGURATION.md#appsjson) |

## Computer control (Windows)

| Say | What happens |
|---|---|
| volume up / volume down / louder / quieter | Changes the volume (about 10% per command) |
| set volume to 40 | Sets the volume |
| mute / unmute | Toggles mute |
| brightness up / brightness down / set brightness to 30 | Changes the screen brightness (laptop screens) |
| lock the screen | Locks Windows |
| screenshot | Saves to `screenshots/` and opens it |

Shutdown, restart and sleep are deliberately **not** available by voice, because a misheard command could lose your work.

## Web

| Say | What happens |
|---|---|
| search Google for python | Opens the search |
| search YouTube for jazz | Opens the search |
| play Believer | Plays the song on YouTube |

## Information

| Say | What happens |
|---|---|
| what time is it / what is the date | Spoken answer |
| battery level | Percentage and whether it is charging |
| weather in Delhi / weather | Current temperature and sky. Without a city: `ANAYA_CITY`, else a guess from your IP address |
| tell me the news | Top 3 headlines (Google News) |
| who is Sundar Pichai / tell me about the moon | Two-sentence Wikipedia summary; the AI answers if there is no page |

## Reminders and timers

| Say | What happens |
|---|---|
| remind me in 10 minutes to call Raj | Speaks "Reminder: call Raj" when due |
| remind me at 6 pm to call mom | Next 6 pm, today or tomorrow |
| set a timer for 5 minutes | Speaks "Your timer is done". Also "half an hour", "1 hour 30 minutes", "30 seconds" |
| what are my reminders | Lists them |
| cancel all reminders | Clears them |

Reminders are saved in `reminders.json`, so they survive restarts. They fire only while Anaya is running.

## Typing and reading

| Say | What happens |
|---|---|
| start dictation ... stop dictation | Everything you say is typed into the window you are in. Say *comma*, *full stop*, *question mark*, *exclamation mark*, *colon*, *new line*, *new paragraph* for punctuation. Sentences are capitalised. |
| type hello comma world | Types just that phrase |
| read the clipboard / read what I copied | Reads the clipboard aloud (first 2000 characters) |
| read this / read the selection | Copies the selected text, reads it aloud, then restores your clipboard |

Private text is always spoken with the offline Windows voice.

## Text tools (local model)

| Say | What happens |
|---|---|
| translate this to Hindi | Translates the selection; the result is put on the clipboard |
| translate the clipboard to English | Translates; English is also spoken |
| summarise what I copied / summarise this | Two-sentence spoken summary |

Translation targets: Hindi, English, Marathi, Gujarati, Tamil, Telugu, Bengali, Spanish, French, German. The installed voice speaks English only,
so other languages go to the clipboard.

## Briefing

| Say | What happens |
|---|---|
| give me my briefing | Time, battery, weather, your reminders and 3 headlines. Esc stops it. |

It also plays automatically after sign-in, 12 seconds after Anaya starts, at most once every 4 hours.

## Chat and memory

Anything that is not a command goes to the local model. Answers are kept to about two spoken sentences.
Anaya remembers the last 6 exchanges for follow-up questions ("who wrote Hamlet" ... "when was he born") and forgets after 5 quiet minutes.

| Say | What happens |
|---|---|
| forget that / new topic / start over | Clears the conversation memory |
| who are you / introduce yourself | She introduces herself |

## Languages

| Say | What happens |
|---|---|
| switch to Hindi / switch to English | Chooses which language is tried first (the other is the fallback) |

Core commands also work in Hindi and Hinglish, for example *chrome kholo*, *awaaz badhao*, *volume kam karo*, or the Devanagari
equivalents of open Chrome, volume up/down, time, date, weather and news. Replies are always spoken in English.

## Stopping

| Do | What happens |
|---|---|
| Esc, or hold a talk key | Cuts Anaya off mid-sentence |
| say "stop Anaya" | Quits the assistant |
