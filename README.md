# 🤖 Maya AI 1.2 (Windows & macOS)

Maya AI is a personal voice assistant built with Python and powered by Ollama. It can understand voice commands, open applications, search the web, play music, capture screenshots, and assist you with everyday tasks using natural voice interaction.

> **Version:** 1.2  
> **Platform:** Windows, macOS  
> **Language:** Python

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
- 🎯 Push-to-Talk (hold Right Ctrl or F9) or Wake Word Detection ("Maya")
- ⚡ Fast Voice Command Processing

---

# 🎙️ Available Voice Commands

| Voice Command | Action |
|---------------|--------|
| Maya | Activate the assistant |
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
| Tell me about yourself | Maya introduces itself |
| Introduce yourself | Maya introduces itself |
| Who are you | Maya introduces itself |
| Stop Maya | Closes Maya AI |
| Remind me in 10 minutes to call Raj / set a timer for 5 minutes / what are my reminders / cancel reminders | Spoken reminders that survive restarts |
| Weather in Delhi / weather / tell me the news / who is Sundar Pichai / tell me about the moon | Live info (Open-Meteo, Google News, Wikipedia) |
| Switch to Hindi / switch to English | Sets which language is tried first (the other is the automatic fallback). Core commands also work in Hindi/Hinglish, e.g. "क्रोम खोलो", "awaaz badhao". Answers are always spoken in English. |
| Open <name> (anything in apps.json) | Opens the URL / folder / program you listed in `apps.json` |
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
git clone https://github.com/YOUR_USERNAME/Maya-AI-1.2.git
```

### Go to the project folder

```bash
cd Maya-AI-1.2
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run Maya AI

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
Maya-AI-1.2
│
├── main.py
├── requirements.txt
├── README.md
├── maya_animation.gif
├── maya_animation.html
├── screenshots/
└── assets/
```

---

# ⚙️ How It Works

**Default: push-to-talk.** Hold **Right Ctrl** (or **F9**), speak, release. Maya transcribes only that recording, so room noise is ignored. Change it with the `MAYA_PTT_KEY` environment variable: a comma-separated list such as `right ctrl,f9` (`mouse:x2` / `mouse:x` use mouse side buttons if your mouse reports them; anything else is a keyboard key like `f8`).

**Wake-word mode:** set `MAYA_MODE=wake` and use the steps below.

1. Launch Maya AI.
2. The startup animation will appear.
3. Maya activates the microphone.
4. Say **"Maya"** to wake the assistant.
5. Maya replies **"Yes Boss"**.
6. Speak your command.
7. Maya processes and executes your request.

---

# 💬 Example

```
You: Maya

Maya: Yes Boss

You: Open Chrome

Maya: Opening Chrome
```

---

# ⚠️ Notes

- The startup GIF animation is off by default. Set `MAYA_ANIMATION=1` to show it.
- Press **Esc** (or a talk key) while Maya is speaking to cut her off. Spoken answers are kept short (about two sentences). Tune with the `MAYA_MAX_TOKENS` environment variable (default 100).
- Works on **Windows** and **macOS**. Safari is macOS-only; on Windows it is skipped.
- Microphone capture uses `sounddevice`, so PyAudio / C++ build tools are not needed.
- Ollama must be installed for AI chat functionality.
- Make sure your microphone permission is enabled.

---

# 🚀 Maya AI 1.7 — Coming Soon

Maya AI 1.7 is currently under active development and will introduce a major upgrade over version 1.2.

### Planned Features

- 🌍 Windows Support
- 🍎 macOS Support
- 🐧 Linux Support
- 🧠 Smarter AI Engine
- ⚡ Faster Performance
- 🎨 Modern User Interface
- 🎙️ Improved Voice Recognition
- 🤖 Advanced AI Automation
- 🔥 More Powerful Voice Commands
- 💎 Exclusive Premium Features

Stay tuned for future updates.

Visit the official Maya AI website regularly to check the latest announcements, new releases, feature updates, and upcoming versions.

Thank you for supporting Maya AI! ❤️

---

# 👨‍💻 Author

Developed with ❤️ by **Taha**

If you like this project, please consider giving it a ⭐ on GitHub.

---

# 📄 License

This project is licensed under the MIT License.