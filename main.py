import speech_recognition as sr
import subprocess
import webbrowser
import os
import re
import sys
import shutil
from pathlib import Path
import pywhatkit
import ollama
import pyautogui
from datetime import datetime

# Under pythonw (auto-start at login) there is no console: log to maya.log instead
if sys.stdout is None or sys.stderr is None:
    _log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "maya.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log

# Windows consoles default to cp1252, which cannot print the emoji used in log messages
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

recognizer = sr.Recognizer()

# Local Ollama model used for chat answers (override with the MAYA_MODEL env var)
OLLAMA_MODEL = os.environ.get("MAYA_MODEL", "llama3.2:3b")

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# -------------------- PLATFORM HELPERS -------------------- #
def open_path(path):
    """Open a file or folder with the OS default handler."""
    if IS_WINDOWS:
        os.startfile(path)
    elif IS_MAC:
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def open_app(mac_name, win_candidates, fallback_url=None):
    """Launch an application. win_candidates: executables on PATH, full paths, or URI schemes."""
    try:
        if IS_MAC:
            subprocess.run(["open", "-a", mac_name], check=True)
            return True
        if IS_WINDOWS:
            for cand in win_candidates:
                if cand.endswith(":"):  # URI scheme, e.g. whatsapp:
                    try:
                        os.startfile(cand)
                        return True
                    except OSError:
                        continue
                exe = shutil.which(cand) or (cand if os.path.exists(os.path.expandvars(cand)) else None)
                if exe:
                    subprocess.Popen([os.path.expandvars(exe)], shell=exe.lower().endswith((".cmd", ".bat")))
                    return True
    except Exception as e:
        print("Open App Error:", e)
    if fallback_url:
        webbrowser.open(fallback_url)
        return True
    return False

# GIF Animation Configuration
GIF_PATH = "maya_animation.gif"  # Change this to your GIF filename

def show_startup_gif():
    """Show GIF animation in browser"""
    try:
        # Get absolute path
        gif_absolute_path = os.path.abspath(GIF_PATH)
        
        # Check if file exists
        if os.path.exists(gif_absolute_path):
            # Create HTML file with GIF
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Maya AI</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: black;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
       
        .maya-gif {{
            max-width: 90vw;
            max-height: 90vh;
    
        }}
      
    </style>
</head>
<body>
    <div class="maya-container">
        <img src="{Path(gif_absolute_path).as_uri()}" alt="Maya AI Animation" class="maya-gif">
    </div>
</body>
</html>
            """
            
            # Save HTML file
            html_file = "maya_animation.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Open HTML in browser
            html_path = os.path.abspath(html_file)
            webbrowser.open(Path(html_path).as_uri())
            print("✅ Maya AI animation opened in browser")
            
        else:
            print(f"❌ GIF file not found: {gif_absolute_path}")
            print("💡 Using fallback animation...")
            
            # Open fallback animation
            fallback_path = os.path.abspath("maya_fallback_animation.html")
            webbrowser.open(Path(fallback_path).as_uri())
            print("✅ Maya AI fallback animation opened in browser")
            
    except Exception as e:
        print(f"❌ GIF Error: {e}")
        print("💡 Continuing without animation...")

def speak(text):
    try:
        print("maya:", text)
        if IS_WINDOWS:
            # Pass text via environment variable to avoid shell-quoting problems
            script = (
                "Add-Type -AssemblyName System.Speech;"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "try { if ($env:MAYA_VOICE) { $s.SelectVoice($env:MAYA_VOICE) } "
                "else { $s.SelectVoiceByHints('Female','Adult',0,[Globalization.CultureInfo]'en-IN') } } catch {};"
                "$s.Speak($env:MAYA_TEXT)"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                env={**os.environ, "MAYA_TEXT": text},  # MAYA_VOICE overrides the voice, e.g. "Microsoft Zira Desktop"
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        elif IS_MAC:
            subprocess.run(["say", text])
        else:
            subprocess.run(["espeak", text])
    except Exception as e:
        print("Speech Error:", e)

# -------------------- INTRODUCTION -------------------- #
def introduce_yourself():
    speak("""
Hello! I am Maya.

Created by Taha.

I am not just a simple assistant — I am smart, fast, and always ready to help.

I can control your system, search anything, play music and write code, 
and assist you like a real AI companion.

What do you want me to do?
""")

# -------------------- FOLDER SEARCH -------------------- #
def find_folder(foldername):
    """Locate a folder by name. Returns a path or None."""
    home = Path.home()
    # Well-known folders first
    known = home / foldername.strip().title()
    if known.is_dir():
        return str(known)

    if IS_MAC:
        result = subprocess.run(["mdfind", foldername], capture_output=True, text=True)
        folders = [f for f in result.stdout.strip().split(chr(10)) if os.path.isdir(f)]
        return folders[0] if folders else None

    # Windows/Linux: bounded walk of the home directory
    target = foldername.strip().lower()
    max_depth = 4
    base_depth = len(home.parts)
    for root, dirs, _ in os.walk(home):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "AppData"]
        if len(Path(root).parts) - base_depth >= max_depth:
            dirs[:] = []
        for d in dirs:
            if target in d.lower():
                return os.path.join(root, d)
    return None

def open_folder_anywhere(foldername):
    try:
        path = find_folder(foldername)
        if path:
            speak("Opening folder")
            open_path(path)
        else:
            speak("Folder not found boss")

    except Exception as e:
        print("Folder Search Error:", e)
        speak("Error while opening folder")

def ask_local_ai(prompt):
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        print("Ollama Error:", e)
        return "Sorry boss, AI is not responding."

def frames_to_audio(frames, rate=16000, max_gain=40.0, loud_chunks=0):
    """Join recorded int16 chunks into sr.AudioData, boosting quiet mics up to max_gain."""
    import numpy as np
    samples = np.concatenate(frames).astype(np.float32)
    raw_peak = float(np.abs(samples).max())
    gain = 1.0
    if raw_peak > 0:
        # Quiet laptop mics: boost toward a usable level, capped at max_gain
        gain = min(20000.0 / raw_peak, max_gain)
        samples = np.clip(samples * gain, -32768, 32767)
    LAST_CLIP.update(raw_peak=int(raw_peak), gain=round(gain, 1), loud_chunks=loud_chunks)
    return sr.AudioData(samples.astype(np.int16).tobytes(), rate, 2)

LAST_CLIP = {}

def record_phrase(timeout=5, phrase_time=6, rate=16000):
    """Record one phrase from the default microphone using sounddevice (no PyAudio needed).
    Returns sr.AudioData, or None if no speech started within `timeout` seconds."""
    import numpy as np
    import sounddevice as sd

    chunk = int(rate * 0.1)
    # Calibrate on ambient noise
    ambient = sd.rec(int(rate * 0.5), samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    threshold = max(float(np.abs(ambient).mean()) * 3, 40.0)

    MIN_LOUD_CHUNKS = 3   # need >= 0.3 s of sound above threshold, otherwise it's a click/tap, not speech
    MAX_GAIN = 40.0       # cap on the volume boost so noise isn't blown up into a loud burst

    frames, preroll, started, silent_chunks, loud_chunks = [], [], False, 0, 0
    waited, spoken = 0.0, 0.0
    with sd.InputStream(samplerate=rate, channels=1, dtype="int16", blocksize=chunk) as stream:
        while True:
            data, _ = stream.read(chunk)
            loud = float(np.abs(data).mean()) > threshold
            if not started:
                waited += 0.1
                if loud:
                    started = True
                    loud_chunks = 1
                    # Include the quiet moments just before the trigger so soft onsets aren't clipped
                    frames.extend(preroll)
                    frames.append(data.copy())
                else:
                    preroll.append(data.copy())
                    preroll = preroll[-4:]
                    if waited >= timeout:
                        return None
            else:
                frames.append(data.copy())
                spoken += 0.1
                waited += 0.1
                loud_chunks += 1 if loud else 0
                silent_chunks = 0 if loud else silent_chunks + 1
                if silent_chunks >= 10 or spoken >= phrase_time:
                    if loud_chunks >= MIN_LOUD_CHUNKS:
                        break
                    # Too short to be speech: discard and keep waiting (time already spent still counts)
                    frames, preroll, started, silent_chunks, loud_chunks, spoken = [], [], False, 0, 0, 0.0
                    if waited >= timeout:
                        return None
    return frames_to_audio(frames, rate, MAX_GAIN, loud_chunks)

def listen_command(timeout=5, phrase_time=6):
    try:
        print("Listening...")
        audio = record_phrase(timeout, phrase_time)
        if audio is None:
            return ""
        text = recognizer.recognize_google(audio, language="en-IN")
        print("Heard:", text)
        return text
    except sr.UnknownValueError:
        try:
            os.makedirs("debug_audio", exist_ok=True)
            name = f"debug_audio/reject_{datetime.now().strftime('%H-%M-%S')}.wav"
            with open(name, "wb") as f:
                f.write(audio.get_wav_data())
            import numpy as np
            pcm = np.frombuffer(audio.frame_data, dtype=np.int16)
            print(f"Heard speech but could not understand it ({len(pcm)/audio.sample_rate:.1f}s, raw peak {LAST_CLIP.get('raw_peak')}, gain x{LAST_CLIP.get('gain')}, saved {name})")
        except Exception:
            print("Heard speech but could not understand it")
        return ""
    except Exception as e:
        print("Listen Error:", e)
        return ""

def play_song(command):
    try:
        song = command.lower().replace("play", "", 1).strip()

        if not song:
            speak("Please tell me the song name.")
            return

        speak(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)

    except:
        speak("Sorry boss")

def take_screenshot():
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"screenshots/screenshot_{timestamp}.png"

    screenshot = pyautogui.screenshot()
    screenshot.save(file_path)

    open_path(os.path.abspath(file_path))
    return file_path

# -------------------- COMMAND PROCESSOR -------------------- #
def normalize_command(command):
    """Lowercase, drop punctuation and polite filler so 'Please open the Chrome' matches 'open chrome'."""
    command = re.sub(r"[^\w\s]", " ", command.lower())
    command = re.sub(r"^(?:(?:hey|ok|okay|please|kindly|can you|could you|will you|would you)\s+)+", "", command.strip())
    command = re.sub(r"^(?:launch|start)\s+", "open ", command)
    command = re.sub(r"^open\s+(?:up\s+)?(?:the\s+|my\s+|a\s+)?", "open ", command)
    command = re.sub(r"\bplease\b", "", command)
    return re.sub(r"\s+", " ", command).strip()

def process_command(command):
    command = normalize_command(command)

    try:
        if "open visual studio code" in command or "open vs code" in command:
            speak("Opening Visual Studio Code")
            if not open_app("Visual Studio Code", [
                "code",
                r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ]):
                speak("Visual Studio Code not found")

        elif "open safari" in command:
            if IS_MAC:
                speak("Opening Safari")
                open_app("Safari", [])
            else:
                speak("Safari is not available on this system")

        elif "open chrome" in command:
            speak("Opening Chrome")
            if not open_app("Google Chrome", [
                "chrome",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
            ], fallback_url="https://www.google.com"):
                speak("Chrome not found")

        elif "open youtube" in command:
            speak("Opening YouTube")
            webbrowser.open("https://youtube.com")

        elif "open whatsapp" in command:
            speak("Opening WhatsApp")
            open_app("WhatsApp", ["whatsapp:"], fallback_url="https://web.whatsapp.com")

        elif "tell me about yourself" in command or "introduce yourself" in command or "who are you" in command:
            introduce_yourself()

        elif "folder" in command and command.startswith("open"):
            foldername = command.replace("open", "").replace("folder", "").strip()
            open_folder_anywhere(foldername)

        elif command.startswith("play "):
            play_song(command)


        elif "search youtube for" in command:
            query = command.replace("search youtube for", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

        elif "search google for" in command:
            query = command.replace("search google for", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")

        elif "screenshot" in command:
            take_screenshot()
            speak("Screenshot taken")

        elif "stop maya" in command:
            speak("Goodbye boss")
            raise SystemExit
      
        else:
            speak("Thinking boss")
            reply = ask_local_ai(command)
            speak(reply)

    except Exception as e:
        print("Command Error:", e)
        speak("Error boss")

# -------------------- MAIN LOOP -------------------- #
IDLE_LIMIT = 3  # empty listens in a row before Maya goes back to waiting for the wake word

def split_wake_word(text):
    """Return (woke, command_after_wake_word). 'Maya open chrome' -> (True, 'open chrome')."""
    match = re.search(r"\bmaya\b", text.lower())
    if not match:
        return False, ""
    return True, text[match.end():].strip(" ,.!?")

def start_maya():
    # Show GIF in browser first
    show_startup_gif()

    speak("Maya is activated")

    awake = False
    idle = 0

    while True:
        try:
            text = listen_command(timeout=5, phrase_time=8 if awake else 6)

            if not awake:
                woke, command = split_wake_word(text) if text else (False, "")
                if not woke:
                    continue
                awake, idle = True, 0
                if command:
                    process_command(command)
                else:
                    speak("Yes boss")
                continue

            # Awake: accept follow-up commands without the wake word
            if not text:
                idle += 1
                if idle >= IDLE_LIMIT:
                    awake = False
                    print("Maya is idle. Say 'Maya' to wake.")
                continue

            idle = 0
            _, command = split_wake_word(text)
            process_command(command or text)

        except SystemExit:
            break
        except Exception as e:
            print("Loop Error:", e)

# -------------------- PUSH TO TALK -------------------- #
PTT_KEY = os.environ.get("MAYA_PTT_KEY", "f9")

def beep(freq):
    if IS_WINDOWS:
        try:
            import winsound
            winsound.Beep(freq, 80)
        except Exception:
            pass

def record_while_held(key, rate=16000, max_seconds=15):
    """Record from the mic for as long as `key` is held. Returns sr.AudioData or None if too short."""
    import numpy as np
    import sounddevice as sd
    import keyboard
    import time

    chunk = int(rate * 0.05)
    frames, start = [], time.time()
    with sd.InputStream(samplerate=rate, channels=1, dtype="int16", blocksize=chunk) as stream:
        while keyboard.is_pressed(key) and time.time() - start < max_seconds:
            data, _ = stream.read(chunk)
            frames.append(data.copy())
    if len(frames) * 0.05 < 0.3:  # accidental tap
        return None
    return frames_to_audio(frames, rate)

def start_push_to_talk():
    import keyboard

    show_startup_gif()
    speak(f"Maya is ready. Hold {PTT_KEY} and speak.")
    print(f"Hold [{PTT_KEY.upper()}] to talk, release to send. Say 'stop maya' or press Ctrl+C to quit.")

    while True:
        try:
            keyboard.wait(PTT_KEY)
            beep(880)
            print("Recording...")
            audio = record_while_held(PTT_KEY)
            beep(440)
            if audio is None:
                print("Too short, ignored")
                continue
            try:
                text = recognizer.recognize_google(audio, language="en-IN")
            except sr.UnknownValueError:
                print(f"Could not understand it (raw peak {LAST_CLIP.get('raw_peak')}, gain x{LAST_CLIP.get('gain')})")
                speak("Sorry boss, I did not catch that")
                continue
            print("Heard:", text)
            _, after_wake = split_wake_word(text)
            process_command(after_wake or text)
        except SystemExit:
            break
        except Exception as e:
            print("Push-to-talk Error:", e)

if __name__ == "__main__":
    try:
        # MAYA_MODE=wake uses the "Maya" wake word; the default is hold-to-talk
        if os.environ.get("MAYA_MODE", "ptt").lower() == "wake":
            start_maya()
        else:
            start_push_to_talk()
    except KeyboardInterrupt:
        print("\nMaya AI stopped by user")
