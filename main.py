import speech_recognition as sr
import subprocess
import webbrowser
import os
import re
import sys
import time
import json
import threading
import shutil
from pathlib import Path
import pywhatkit
import ollama
import pyautogui
from datetime import datetime, timedelta

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
    """Show GIF animation in browser (off by default; set MAYA_ANIMATION=1 to enable)"""
    if os.environ.get("MAYA_ANIMATION", "0") != "1":
        return
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

STOP_KEY = os.environ.get("MAYA_STOP_KEY", "esc")

def stop_requested():
    """True if the stop key (default Esc) or a push-to-talk key is held, so you can cut Maya off mid-sentence."""
    try:
        import keyboard
        if keyboard.is_pressed(STOP_KEY):
            return True
        return ptt_held()
    except Exception:
        return False

_speak_lock = threading.Lock()  # reminders speak from a background thread; never talk over each other

def speak(text):
    with _speak_lock:
        _speak(text)

def _speak(text):
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
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", script],
                env={**os.environ, "MAYA_TEXT": text},  # MAYA_VOICE overrides the voice, e.g. "Microsoft Zira Desktop"
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            started = time.time()
            while proc.poll() is None:
                # Grace period so a talk key still held from the last request doesn't cut her off instantly
                if time.time() - started > 0.4 and stop_requested():
                    proc.kill()
                    print("(interrupted)")
                    break
                time.sleep(0.05)
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

MAYA_SYSTEM_PROMPT = (
    "You are Maya, a friendly voice assistant. Your replies are spoken aloud, so answer in at most "
    "two short sentences. Never use bullet points, markdown or emojis, and skip any preamble. If asked for a "
    "list, name a few items in one spoken sentence. Only go longer if the user explicitly asks for detail. "
    "Always reply in English."
)
MAX_REPLY_TOKENS = int(os.environ.get("MAYA_MAX_TOKENS", "100"))

def clean_for_speech(text):
    """Strip markdown/symbols and cut off any trailing half-finished sentence."""
    text = re.sub(r"[*_`#>~|]+", "", text)
    text = re.sub(r"^\s*(?:[-•]|\d+[.)])\s+", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[-1] not in ".!?":
        cut = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
        if cut > 20:
            text = text[: cut + 1]
    return text

# Conversation memory: the last few turns are sent with each question; it resets after a quiet period.
HISTORY = []                 # list of {"role": ..., "content": ...}
HISTORY_MAX_TURNS = 6        # user+assistant pairs kept
HISTORY_IDLE_SECONDS = 300   # forget after 5 minutes of silence
_last_chat_time = 0.0

def forget_conversation():
    HISTORY.clear()

def ask_local_ai(prompt):
    global _last_chat_time
    try:
        now = time.time()
        if now - _last_chat_time > HISTORY_IDLE_SECONDS:
            forget_conversation()
        messages = [{"role": "system", "content": MAYA_SYSTEM_PROMPT}] + HISTORY + [{"role": "user", "content": prompt}]
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"num_predict": MAX_REPLY_TOKENS},
        )
        reply = clean_for_speech(response["message"]["content"]) or "Sorry boss, I have no answer."
        HISTORY.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": reply}])
        del HISTORY[:-2 * HISTORY_MAX_TURNS]
        _last_chat_time = now
        return reply
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
        text = recognize_with_fallback(audio)
        if text is None:
            raise sr.UnknownValueError()
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

# -------------------- HINDI / HINGLISH -------------------- #
# Recognition tries the main language first and, if Google can't make sense of the audio, the second one.
RECOG_LANGS = {"en": "en-IN", "hi": "hi-IN"}
_recog_primary = os.environ.get("MAYA_LANG", "en-IN")

def _secondary_lang():
    return "hi-IN" if _recog_primary != "hi-IN" else "en-IN"

def set_recognition_language(code):
    global _recog_primary
    _recog_primary = RECOG_LANGS[code]

def recognize_with_fallback(audio):
    """Transcribe with the primary language, then the secondary. Returns None if neither works."""
    for lang in (_recog_primary, _secondary_lang()):
        try:
            text = recognizer.recognize_google(audio, language=lang)
            if text.strip():
                return text
        except sr.UnknownValueError:
            continue
    return None

# Devanagari and Hinglish words -> the English command words the rest of Maya understands.
_HINDI_WORDS = [
    (r"खोलो|खोल दो|खोलिए|खोल|kholo|khol do|kholiye|chalu karo", "open"),
    (r"क्रोम", "chrome"), (r"यूट्यूब|यू ट्यूब", "youtube"), (r"व्हाट्सएप|व्हाट्सऐप|वाट्सऐप", "whatsapp"),
    (r"नोटपैड", "notepad"), (r"कैलकुलेटर|कैलक्यूलेटर", "calculator"), (r"सेटिंग्स|सेटिंग", "settings"),
    (r"वॉल्यूम|वाल्यूम|आवाज़|आवाज|awaaz|awaz", "volume"),
    (r"बढ़ाओ|बढ़ा दो|बढ़ाइए|बढ़ा|badhao|badha do", "up"),
    (r"घटाओ|घटा दो|कम करो|कम कर दो|कम|ghatao|kam karo", "down"),
    (r"म्यूट|चुप", "mute"), (r"स्क्रीनशॉट", "screenshot"),
    (r"ब्राइटनेस|brightness", "brightness"),
]
_HINDI_PHRASES = [
    (r"(समय|टाइम|samay|time) (क्या|कितना|kya|kitna)", "what time is it"),
    (r"(तारीख|आज की तारीख|aaj ki tarikh|tarikh)", "what is the date"),
    (r"(मौसम|mausam)", "weather"),
    (r"(खबर|ख़बर|समाचार|khabar|samachar)", "tell me the news"),
    (r"(बैटरी|battery) (कितनी|kitni|कितना)", "battery level"),
    (r"(स्क्रीन लॉक|screen lock)", "lock the screen"),
]

def hindi_to_english(text):
    """Translate common Hindi/Hinglish command phrases. English input passes through unchanged."""
    t = text.strip().lower()
    for pattern, english in _HINDI_PHRASES:
        if re.search(pattern, t):
            return english
    changed = False
    for pattern, english in _HINDI_WORDS:
        new = re.sub(pattern, english, t)
        changed = changed or new != t
        t = new
    if not changed:
        return text
    t = re.sub(r"\s+", " ", t).strip()
    m = re.match(r"^(.+?) open$", t)                 # Hindi puts the verb last: "chrome open" -> "open chrome"
    if m:
        t = "open " + m.group(1)
    return t

# -------------------- LIVE INFO (weather, news, Wikipedia) -------------------- #
# Free services, no API keys: Open-Meteo (weather), Google News RSS, Wikipedia. Your question text is sent to them.
HTTP_HEADERS = {"User-Agent": "MayaAI/1.2 (personal voice assistant)"}
HTTP_TIMEOUT = 6
_WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "foggy", 48: "foggy",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "heavy showers",
    95: "a thunderstorm", 96: "a thunderstorm with hail", 99: "a thunderstorm with hail",
}
_home_city_cache = {}

def _http_json(url, params=None):
    import requests
    r = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()

def home_city():
    """MAYA_CITY if set, otherwise a one-time guess from your IP address."""
    if os.environ.get("MAYA_CITY"):
        return os.environ["MAYA_CITY"]
    if "city" not in _home_city_cache:
        try:
            _home_city_cache["city"] = _http_json("https://ipwho.is/").get("city") or ""
        except Exception:
            _home_city_cache["city"] = ""
    return _home_city_cache["city"]

def get_weather(city):
    """Return a spoken weather sentence for `city`, or None if it can't be found."""
    geo = _http_json("https://geocoding-api.open-meteo.com/v1/search", {"name": city, "count": 1}).get("results")
    if not geo:
        return None
    place = geo[0]
    cur = _http_json("https://api.open-meteo.com/v1/forecast", {
        "latitude": place["latitude"], "longitude": place["longitude"],
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
    })["current"]
    sky = _WEATHER_CODES.get(cur["weather_code"], "unsettled")
    return (f"In {place['name']} it is {round(cur['temperature_2m'])} degrees with {sky}, "
            f"feels like {round(cur['apparent_temperature'])}.")

def get_news(count=3):
    import xml.etree.ElementTree as ET
    import requests
    r = requests.get("https://news.google.com/rss", params={"hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
                     headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    titles = [i.findtext("title", "") for i in ET.fromstring(r.content).iter("item")][:count]
    titles = [re.sub(r"\s+-\s+[^-]+$", "", t) for t in titles if t]   # drop the " - Publisher" suffix
    return titles

def get_wikipedia_summary(topic, sentences=2):
    """Short summary for `topic`, or None if there's no good match."""
    found = _http_json("https://en.wikipedia.org/w/rest.php/v1/search/title", {"q": topic, "limit": 1}).get("pages")
    if not found:
        return None
    from urllib.parse import quote
    page = _http_json("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(found[0]["key"], safe=""))
    extract = re.sub(r"\s*\([^)]*\)", "", page.get("extract", ""))      # drop pronunciation/date brackets
    parts = re.split(r"(?<=[.!?])\s+", extract)
    return " ".join(parts[:sentences]) or None

def handle_info_command(command):
    """Weather, news and 'who is / tell me about' lookups. Returns True if handled."""
    try:
        if re.search(r"\bweather\b|\btemperature\b", command):
            m = re.search(r"\b(?:in|at|for)\s+([a-z][a-z .'-]+?)(?:\s+(?:today|now|tomorrow|right now))?$", command)
            city = m.group(1).strip() if m else home_city()
            if not city:
                speak("Tell me which city, for example weather in Delhi")
                return True
            reply = get_weather(city)
            speak(reply or f"I could not find weather for {city}")
            return True

        if re.search(r"\b(news|headlines)\b", command):
            titles = get_news()
            speak("Here are the top headlines. " + " ... ".join(titles) if titles else "I could not get the news")
            return True

        m = re.match(r"^(?:who is|who was|tell me about|search wikipedia for|wikipedia)\s+(.+)$", command)
        if m:
            topic = re.sub(r"^(?:the|a|an)\s+", "", m.group(1).strip())
            if topic in ("you", "yourself"):
                return False                                  # handled by the introduction
            summary = get_wikipedia_summary(topic)
            if summary:
                speak(summary)
                return True
            return False                                      # no page: let the AI try
    except Exception as e:
        print("Info error:", e)
        speak("I could not reach the internet for that")
        return True
    return False

# -------------------- REMINDERS & TIMERS -------------------- #
import json
import threading

REMINDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")
_reminder_lock = threading.Lock()
_reminder_thread = None

_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
    "forty": 40, "forty five": 45, "sixty": 60,
}
_UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600}

def parse_duration(text):
    """'10 minutes', 'an hour', 'half an hour', '1 hour 30 minutes' -> seconds (None if no duration found)."""
    text = text.lower()
    if re.search(r"\bhalf an? hour\b", text):
        return 1800
    total, found = 0, False
    number = r"(\d+(?:\.\d+)?|" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True)) + r")"
    for m in re.finditer(number + r"\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b", text):
        raw, unit = m.group(1), re.sub(r"s$", "", m.group(2))
        value = float(raw) if raw[0].isdigit() else _NUMBER_WORDS[raw]
        total += value * _UNIT_SECONDS[unit]
        found = True
    return int(total) if found else None

def parse_clock_time(text, now=None):
    """'at 6 pm', 'at 6:30 pm', 'at 18:30' -> epoch seconds of the next such time (None if not found)."""
    now = now or datetime.now()
    m = re.search(r"\bat (\d{1,2})(?::(\d{2}))?\s*(a m|p m|am|pm)?\b", text.lower())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").replace(" ", "")
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target.timestamp()

def parse_reminder_command(command, now=None):
    """Return (due_epoch, message) for timer/reminder phrases, or None if the command isn't one."""
    now_ts = (now or datetime.now()).timestamp()
    c = command.lower()

    if re.search(r"\btimer\b", c) and re.search(r"\b(set|start)\b|\btimer for\b", c):
        seconds = parse_duration(c)
        return (now_ts + seconds, "Your timer is done") if seconds else None

    if re.search(r"\bremind me\b", c):
        due = None
        seconds = parse_duration(c)
        if seconds is not None:
            due = now_ts + seconds
        else:
            due = parse_clock_time(c, now)
        if due is None:
            return None
        msg = re.sub(r"^.*?\bremind me\b", "", c)
        msg = re.sub(r"\b(in|after)\s+(\d+(?:\.\d+)?|[a-z ]+?)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b", "", msg)
        msg = re.sub(r"\bhalf an? hour\b", "", msg)
        msg = re.sub(r"\bat \d{1,2}(?::\d{2})?\s*(a m|p m|am|pm)?\b", "", msg)
        msg = re.sub(r"^\s*(to|that|about)\s+", "", msg.strip())
        msg = re.sub(r"\s+", " ", msg).strip()
        return due, (msg or "your reminder")
    return None

def _load_reminders():
    try:
        with open(REMINDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_reminders(items):
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f)
    except Exception as e:
        print("Reminder save error:", e)

def add_reminder(due, text):
    with _reminder_lock:
        items = _load_reminders()
        items.append({"due": due, "text": text})
        _save_reminders(items)

def describe_delay(seconds):
    seconds = max(0, round(seconds))
    if seconds < 90:
        return f"{seconds} second" + ("" if seconds == 1 else "s")
    if seconds < 5400:
        minutes = round(seconds / 60)
        return f"{minutes} minute" + ("" if minutes == 1 else "s")
    hours = round(seconds / 3600, 1)
    return f"{hours:g} hour" + ("" if hours == 1 else "s")

def _reminder_loop():
    while True:
        time.sleep(1)
        try:
            with _reminder_lock:
                items = _load_reminders()
                now = time.time()
                due = [i for i in items if i["due"] <= now]
                if due:
                    _save_reminders([i for i in items if i["due"] > now])
            for item in due:
                beep(1000)
                speak(item["text"] if item["text"].startswith("Your") else f"Reminder: {item['text']}")
        except Exception as e:
            print("Reminder loop error:", e)

def start_reminder_thread():
    """Start the background thread that fires due reminders (also catches ones that came due while Maya was off)."""
    global _reminder_thread
    if _reminder_thread is None or not _reminder_thread.is_alive():
        _reminder_thread = threading.Thread(target=_reminder_loop, daemon=True)
        _reminder_thread.start()

def handle_reminder_command(command):
    """Returns True if the command was a reminder/timer command."""
    if re.search(r"\b(cancel|clear|delete|remove)\b.*\b(reminders?|timers?)\b", command):
        with _reminder_lock:
            _save_reminders([])
        speak("All reminders cancelled")
        return True
    if re.search(r"\b(list|what are|show)\b.*\b(my )?(reminders?|timers?)\b|\bany reminders\b", command):
        with _reminder_lock:
            items = sorted(_load_reminders(), key=lambda i: i["due"])
        if not items:
            speak("You have no reminders")
        else:
            now = time.time()
            parts = [f"{i['text']} in {describe_delay(i['due'] - now)}" for i in items[:5]]
            speak(f"You have {len(items)} reminder" + ("s" if len(items) > 1 else "") + ". " + ". ".join(parts))
        return True
    parsed = parse_reminder_command(command)
    if parsed:
        due, text = parsed
        add_reminder(due, text)
        speak(f"Okay boss, I will remind you in {describe_delay(due - time.time())}" if not text.startswith("Your")
              else f"Timer set for {describe_delay(due - time.time())}")
        return True
    return False

# -------------------- WINDOWS SYSTEM COMMANDS -------------------- #
def _press_media_key(name, times=1):
    import keyboard
    for _ in range(times):
        keyboard.send(name)

def _powershell(script):
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
    ).stdout.strip()

def _get_brightness():
    out = _powershell("(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness")
    return int(out.split()[0]) if out else None

def _set_brightness(level):
    level = max(5, min(100, level))
    _powershell(
        "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods)"
        f".WmiSetBrightness(1,{level})"
    )
    return level

# phrase -> (spoken reply, launcher). Launchers are executables or URI schemes handled by os.startfile.
SYSTEM_APPS = {
    "notepad": ("Opening Notepad", "notepad.exe"),
    "calculator": ("Opening Calculator", "calc.exe"),
    "task manager": ("Opening Task Manager", "taskmgr.exe"),
    "file explorer": ("Opening File Explorer", "explorer.exe"),
    "explorer": ("Opening File Explorer", "explorer.exe"),
    "settings": ("Opening Settings", "ms-settings:"),
    "control panel": ("Opening Control Panel", "control.exe"),
    "command prompt": ("Opening Command Prompt", "cmd.exe"),
    "terminal": ("Opening Terminal", "wt.exe"),
    "paint": ("Opening Paint", "mspaint.exe"),
    "snipping tool": ("Opening Snipping Tool", "snippingtool.exe"),
}

def handle_system_command(command):
    """Handle Windows system commands. Returns True if the command was handled."""
    if not IS_WINDOWS:
        return False

    # ---- volume ----
    if "volume" in command or command in ("mute", "unmute") or "louder" in command or "quieter" in command:
        m = re.search(r"(\d{1,3})", command)
        if "unmute" in command or ("mute" in command and "un" in command):
            _press_media_key("volume mute"); speak("Volume toggled")
        elif "mute" in command:
            _press_media_key("volume mute"); speak("Muted")
        elif m and re.search(r"\b(set|to|at)\b", command):
            level = max(0, min(100, int(m.group(1))))
            _press_media_key("volume down", 50)          # each key press is 2%
            _press_media_key("volume up", level // 2)
            speak(f"Volume set to {level} percent")
        elif re.search(r"\b(up|increase|raise|louder|higher)\b", command):
            _press_media_key("volume up", 5); speak("Volume up")
        elif re.search(r"\b(down|decrease|lower|reduce|quieter)\b", command):
            _press_media_key("volume down", 5); speak("Volume down")
        else:
            return False
        return True

    # ---- brightness ----
    if "brightness" in command:
        current = _get_brightness()
        if current is None:
            speak("I cannot control brightness on this screen")
            return True
        m = re.search(r"(\d{1,3})", command)
        if m and re.search(r"\b(set|to|at)\b", command):
            level = _set_brightness(int(m.group(1)))
        elif re.search(r"\b(up|increase|raise|higher|more)\b", command):
            level = _set_brightness(current + 20)
        elif re.search(r"\b(down|decrease|lower|reduce|dim|less)\b", command):
            level = _set_brightness(current - 20)
        else:
            return False
        speak(f"Brightness {level} percent")
        return True

    # ---- lock screen ----
    if re.search(r"\block (?:the )?(?:screen|computer|laptop|pc)\b", command) or command == "lock":
        speak("Locking the screen")
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return True

    # ---- time, date, battery ----
    if re.search(r"\bwhat(?:'s| is)? the time\b|\bwhat time is it\b|\bcurrent time\b|\btell me the time\b", command):
        speak("It is " + datetime.now().strftime("%I:%M %p").lstrip("0"))
        return True
    if re.search(r"\bwhat(?:'s| is)? the date\b|\btoday'?s date\b|\bwhat day is it\b|\bwhat is today\b", command):
        speak("Today is " + datetime.now().strftime("%A, %d %B %Y"))
        return True
    if "battery" in command:
        out = _powershell("(Get-CimInstance Win32_Battery | Select-Object -First 1 EstimatedChargeRemaining,BatteryStatus | ConvertTo-Json -Compress)")
        try:
            import json
            info = json.loads(out)
            charging = "and charging" if info.get("BatteryStatus") in (2, 6, 7, 8) else ""
            speak(f"Battery is at {info['EstimatedChargeRemaining']} percent {charging}".strip())
        except Exception:
            speak("I cannot read the battery status")
        return True

    # ---- open system apps ----
    if command.startswith("open "):
        target = command[5:].strip()
        if target in SYSTEM_APPS:
            reply, launcher = SYSTEM_APPS[target]
            speak(reply)
            try:
                os.startfile(launcher) if launcher.endswith(":") else subprocess.Popen([launcher])
            except Exception as e:
                print("System App Error:", e)
                speak("I could not open it")
            return True
    return False

def process_command(command):
    command = normalize_command(hindi_to_english(command))

    try:
        m = re.search(r"\b(?:switch to|speak|use|change to)\s+(hindi|english)\b|\b(hindi|english) mode\b", command)
        if m:
            language = m.group(1) or m.group(2)
            set_recognition_language("hi" if language == "hindi" else "en")
            speak(f"Okay boss, I will listen for {language.capitalize()} first")
            return

        if re.search(r"\b(forget (that|this|everything|it)|new topic|start over|clear (the )?(memory|conversation))\b", command):
            forget_conversation()
            speak("Okay boss, starting fresh")
            return

        if handle_reminder_command(command):
            return

        if handle_info_command(command):
            return

        if handle_system_command(command):
            return

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

    start_reminder_thread()
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
# Comma-separated list. Default: Right Ctrl or F9. "mouse:x2" / "mouse:x" = mouse side buttons (if your mouse reports them), anything else = keyboard key.
PTT_KEYS = [k.strip().lower() for k in os.environ.get("MAYA_PTT_KEY", "right ctrl,f9").split(",") if k.strip()]
PTT_LABEL = " or ".join(("mouse side button" if k == "mouse:x2" else "mouse back button" if k == "mouse:x" else k.upper()) for k in PTT_KEYS)

def ptt_held(keys=None):
    """True while any configured push-to-talk key or mouse button is held."""
    import keyboard
    import mouse
    for k in (keys or PTT_KEYS):
        if k.startswith("mouse:"):
            if mouse.is_pressed(k.split(":", 1)[1]):
                return True
        elif keyboard.is_pressed(k):
            return True
    return False

def wait_for_ptt(poll=0.02):
    """Block until a push-to-talk key/button is pressed."""
    import time
    while not ptt_held():
        time.sleep(poll)

def beep(freq):
    if IS_WINDOWS:
        try:
            import winsound
            winsound.Beep(freq, 80)
        except Exception:
            pass

def record_while_held(rate=16000, max_seconds=15):
    """Record from the mic for as long as a push-to-talk key/button is held. Returns sr.AudioData or None if too short."""
    import numpy as np
    import sounddevice as sd
    import time

    chunk = int(rate * 0.05)
    frames, start = [], time.time()
    with sd.InputStream(samplerate=rate, channels=1, dtype="int16", blocksize=chunk) as stream:
        while ptt_held() and time.time() - start < max_seconds:
            data, _ = stream.read(chunk)
            frames.append(data.copy())
    if len(frames) * 0.05 < 0.3:  # accidental tap
        return None
    return frames_to_audio(frames, rate)

def start_push_to_talk():
    start_reminder_thread()
    show_startup_gif()
    speak("Maya is ready. Hold the talk button and speak.")
    print(f"Hold [{PTT_LABEL}] to talk, release to send. Say 'stop maya' or press Ctrl+C to quit.")

    while True:
        try:
            wait_for_ptt()
            beep(880)
            print("Recording...")
            audio = record_while_held()
            beep(440)
            if audio is None:
                print("Too short, ignored")
                continue
            text = recognize_with_fallback(audio)
            if text is None:
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
