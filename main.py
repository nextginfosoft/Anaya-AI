import speech_recognition as sr
import subprocess
import webbrowser
import os
import sys
import shutil
from pathlib import Path
import pywhatkit
import ollama
import pyautogui
from datetime import datetime

# Windows consoles default to cp1252, which cannot print the emoji used in log messages
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

recognizer = sr.Recognizer()

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
                "$s.Speak($env:MAYA_TEXT)"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                env={**os.environ, "MAYA_TEXT": text},
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
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        print("Ollama Error:", e)
        return "Sorry boss, AI is not responding."

def record_phrase(timeout=5, phrase_time=6, rate=16000):
    """Record one phrase from the default microphone using sounddevice (no PyAudio needed).
    Returns sr.AudioData, or None if no speech started within `timeout` seconds."""
    import numpy as np
    import sounddevice as sd

    chunk = int(rate * 0.1)
    # Calibrate on ambient noise
    ambient = sd.rec(int(rate * 0.5), samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    threshold = max(float(np.abs(ambient).mean()) * 3, 300.0)

    frames, started, silent_chunks = [], False, 0
    waited, spoken = 0.0, 0.0
    with sd.InputStream(samplerate=rate, channels=1, dtype="int16", blocksize=chunk) as stream:
        while True:
            data, _ = stream.read(chunk)
            loud = float(np.abs(data).mean()) > threshold
            if not started:
                waited += 0.1
                if loud:
                    started = True
                    frames.append(data.copy())
                elif waited >= timeout:
                    return None
            else:
                frames.append(data.copy())
                spoken += 0.1
                silent_chunks = 0 if loud else silent_chunks + 1
                if silent_chunks >= 8 or spoken >= phrase_time:
                    break
    return sr.AudioData(np.concatenate(frames).tobytes(), rate, 2)

def listen_command(timeout=5, phrase_time=6):
    try:
        print("Listening...")
        audio = record_phrase(timeout, phrase_time)
        if audio is None:
            return ""
        return recognizer.recognize_google(audio, language="en-IN")
    except Exception:
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
def process_command(command):
    command = command.lower().strip()

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
def start_maya():
    # Show GIF in browser first
    show_startup_gif()
    
    speak("Maya is activated")

    while True:
        try:
            word = listen_command(timeout=5, phrase_time=3)

            if not word:
                continue

            if "maya" in word.lower():
                speak("Yes boss")

                command = listen_command(timeout=7, phrase_time=8)

                if command:
                    process_command(command)

        except SystemExit:
            break
        except:
            pass

if __name__ == "__main__":
    try:
        start_maya()
    except KeyboardInterrupt:
        print("\nMaya AI stopped by user")
