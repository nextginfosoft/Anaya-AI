# 🤖 Anaya AI 1.2 (Windows & macOS)

Anaya AI is a personal voice assistant built with Python and powered by Ollama. It can understand voice commands, open applications, search the web, play music, capture screenshots, and assist you with everyday tasks using natural voice interaction.

> **Version:** 1.2  
> **Platform:** Windows, macOS  
> **Language:** Python

---

# 📘 Documentation

A printable feature guide is in [docs/Anaya_AI_Features.pdf](docs/Anaya_AI_Features.pdf).

---

# ✨ Features

- 🎤 Voice Recognition
- 🤖 Local AI Chat using Ollama (Llama 3.2 3B)
- 🗣️ Text-to-Speech Responses
- 💻 Open Visual Studio Code
- 🌐 Open Google Chrome
- 🧭 Open Safari
- 💬 Open WhatsApp
- ▶️ Open YouTube
- 📂 Smart Folder Search
- 🎵 Play Songs on YouTube
- 🔎 Google Search
- 📺 YouTube Search
- 📸 Screenshot Capture
- 🎬 Startup GIF Animation
- 🎯 Push-to-Talk (hold Right Ctrl or F9) or Wake Word Detection ("Anaya")
- ⚡ Fast Voice Command Processing

---

# 🎙️ Available Voice Commands

| Voice Command | Action |
|---------------|--------|
| Anaya | Activate the assistant |
| Open Visual Studio Code | Opens VS Code |
| Open VS Code | Opens VS Code |
| Open Safari | Opens Safari |
| Open Chrome | Opens Google Chrome |
| Open YouTube | Opens YouTube |
| Open WhatsApp | Opens WhatsApp |
| Open Folder Downloads | Opens Downloads folder |
| Open Folder Desktop | Opens Desktop folder |
| Open Folder Documents | Opens Documents folder |
| Play Believer | Plays the requested song on YouTube |
| Search Google for Python | Searches Google |
| Search YouTube for AI | Searches YouTube |
| Screenshot | Captures a screenshot |
| Tell me about yourself | Anaya introduces itself |
| Introduce yourself | Anaya introduces itself |
| Who are you | Anaya introduces itself |
| Stop Anaya | Closes Anaya AI |
| Remind me in 10 minutes to call Raj / set a timer for 5 minutes / what are my reminders / cancel reminders | Spoken reminders that survive restarts |
| Weather in Delhi / weather / tell me the news / who is Sundar Pichai / tell me about the moon | Live info (Open-Meteo, Google News, Wikipedia) |
| Switch to Hindi / switch to English | Sets which language is tried first (the other is the automatic fallback). Core commands also work in Hindi/Hinglish, e.g. "क्रोम खोलो", "awaaz badhao". Answers are always spoken in English. |
| Open <name> (anything in apps.json) | Opens the URL / folder / program you listed in `apps.json` |
| Start dictation / stop dictation | Everything you say is typed into the active window (say "comma", "full stop", "new line", "new paragraph", "question mark") |
| Type hello comma world | Types that one phrase into the active window |
| Read the clipboard / read this | Reads the clipboard, or the currently selected text, aloud |
| Translate this to Hindi / the clipboard to English | Translates with the local model; English is spoken, other languages are put on the clipboard |
| Summarise what I copied / summarise this | Two-sentence spoken summary from the local model |
| Give me my briefing | Time, battery, weather, reminders and headlines. Also runs automatically after sign-in (`ANAYA_BRIEFING=0` turns it off) |
| Forget that / new topic | Clears conversation memory |
| Volume up / down / mute / set volume to 40 | Controls system volume |
| Brightness up / down / set brightness to 30 | Controls screen brightness |
| Lock the screen | Locks Windows |
| What time is it / what is the date / battery | Spoken answers |
| Open Notepad / Calculator / Task Manager / Settings / File Explorer | Opens the app |

---

# 🛠️ Technologies Used

- Python
- SpeechRecognition
- Ollama
- PyWhatKit
- PyAutoGUI
- Webbrowser
- Subprocess
- Windows SAPI (System.Speech) / macOS `say`
- sounddevice (microphone capture)

---

# 📦 Requirements

- Python 3.10 or later
- Windows 10/11 or macOS
- Ollama Installed
- Llama 3.2 (3B) Model Installed (`ollama pull llama3.2:3b`)
- Working Microphone
- Internet Connection (for online features)

---

# 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/nextginfosoft/Anaya-AI.git
```

### Go to the project folder

```bash
cd Anaya-AI
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run Anaya AI

```bash
python main.py
```

---

# 📄 requirements.txt

```text
SpeechRecognition
sounddevice
numpy
PyAutoGUI
pywhatkit
ollama
Pillow
```

---

# 📁 Project Structure

```
Anaya-AI
│
├── main.py
├── requirements.txt
├── README.md
├── anaya_animation.gif
├── anaya_animation.html
├── screenshots/
└── assets/
```

---

# ⚙️ How It Works

**Default: push-to-talk.** Hold **Right Ctrl** (or **F9**), speak, release. Anaya transcribes only that recording, so room noise is ignored. Change it with the `ANAYA_PTT_KEY` environment variable: a comma-separated list such as `right ctrl,f9` (`mouse:x2` / `mouse:x` use mouse side buttons if your mouse reports them; anything else is a keyboard key like `f8`).

**Wake-word mode:** set `ANAYA_MODE=wake` and use the steps below.

1. Launch Anaya AI.
2. The startup animation will appear.
3. Anaya activates the microphone.
4. Say **"Anaya"** to wake the assistant.
5. Anaya replies **"Yes Boss"**.
6. Speak your command.
7. Anaya processes and executes your request.

---

# 💬 Example

```
You: Anaya

Anaya: Yes Boss

You: Open Chrome

Anaya: Opening Chrome
```

---

# ⚠️ Notes

- **Renamed from Maya:** settings now start with `ANAYA_`; the old `MAYA_` names are still accepted. The wake word is "Anaya" (similar-sounding spellings like "Ananya" also work).
- **Offline recognition:** the first start downloads the Whisper `base` model (~150 MB); until it is ready Google is used. Set `ANAYA_STT_FALLBACK=0` to never send audio to Google.
- **Voice:** a natural Microsoft neural voice is used when online (the reply text goes to Microsoft); set `ANAYA_TTS=windows` for the offline voice.
- Only one Anaya runs at a time; a second copy exits immediately.

- The startup GIF animation is off by default. Set `ANAYA_ANIMATION=1` to show it.
- Press **Esc** (or a talk key) while Anaya is speaking to cut her off. Spoken answers are kept short (about two sentences). Tune with the `ANAYA_MAX_TOKENS` environment variable (default 100).
- Works on **Windows** and **macOS**. Safari is macOS-only; on Windows it is skipped.
- Microphone capture uses `sounddevice`, so PyAudio / C++ build tools are not needed.
- Ollama must be installed for AI chat functionality.
- Make sure your microphone permission is enabled.

---

# 🗺️ Roadmap

See [PRODUCT_SPEC.md](PRODUCT_SPEC.md) for what is built, the known limits and the backlog.

---

# 👨‍💻 Author

**Anaya AI** is developed by **Santosh Pandit**.

Anaya is based on the original **Maya AI 1.2** by **Taha Shaikh**, released under the MIT License. The full history of
that original work is preserved in this repository.

---

# 📄 License

Released under the [MIT License](LICENSE).
Copyright (c) 2026 Taha Shaikh (original Maya AI) and Santosh Pandit (Anaya AI changes and additions).
