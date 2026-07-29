import speech_recognition as sr
import subprocess
import webbrowser
import os
import pywhatkit
import ollama
import pyautogui
from datetime import datetime

recognizer = sr.Recognizer()

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
        <img src="file://{gif_absolute_path}" alt="Maya AI Animation" class="maya-gif">
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
            webbrowser.open(f"file://{html_path}")
            print("✅ Maya AI animation opened in browser")
            
        else:
            print(f"❌ GIF file not found: {gif_absolute_path}")
            print("💡 Using fallback animation...")
            
            # Open fallback animation
            fallback_path = os.path.abspath("maya_fallback_animation.html")
            webbrowser.open(f"file://{fallback_path}")
            print("✅ Maya AI fallback animation opened in browser")
            
    except Exception as e:
        print(f"❌ GIF Error: {e}")
        print("💡 Continuing without animation...")

def speak(text):
    try:
        print("maya:", text)
        safe_text = text.replace('"', '\\"')
        os.system(f'say "{safe_text}"')
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
def open_folder_anywhere(foldername):
    try:
        # simple search (no complex query)
        result = subprocess.run(
            ["mdfind", foldername],
            capture_output=True,
            text=True
        )

        results = result.stdout.strip().split("\n")

        # sirf folders filter karo
        folders = [f for f in results if os.path.isdir(f)]

        if folders:
            path = folders[0]
            speak("Opening folder")
            subprocess.run(["open", path])
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

def listen_command(timeout=5, phrase_time=6):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time
            )

        text = recognizer.recognize_google(audio, language="en-IN")
        return text

    except sr.WaitTimeoutError:
        return ""
    except:
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

    os.system(f"open {file_path}")
    return file_path

# -------------------- COMMAND PROCESSOR -------------------- #
def process_command(command):
    command = command.lower().strip()

    try:
        if "open visual studio code" in command or "open vs code" in command:
            speak("Opening Visual Studio Code")
            subprocess.run(["open", "-a", "Visual Studio Code"])

        elif "open safari" in command:
            speak("Opening Safari")
            subprocess.run(["open", "-a", "Safari"])

        elif "open chrome" in command:
            speak("Opening Chrome")
            subprocess.run(["open", "-a", "Google Chrome"])

        elif "open youtube" in command:
            speak("Opening YouTube")
            webbrowser.open("https://youtube.com")

        elif "open whatsApp" in command:
            speak("Opening whatsApp ")
            subprocess.run(["open", "-a", "WhatsApp"])    

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
