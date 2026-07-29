import tkinter as tk
from PIL import Image, ImageTk
import os
import threading
import time

class GIFViewer(tk.Toplevel):
    def __init__(self, parent, gif_path, title="Maya AI"):
        super().__init__(parent)
        self.gif_path = gif_path
        self.title(title)
        self.overrideredirect(True)  # Remove window decorations
        self.attributes("-topmost", True)  # Keep window on top

        self.frames = []
        self.delay = 0
        self.current_frame = 0
        self.animation_id = None
        self.stop_event = threading.Event()

        self.load_gif()

        if not self.frames:
            self.destroy()
            return

        self.label = tk.Label(self, bg="black")
        self.label.pack()

        self.center_window()
        self.animate_gif()

    def load_gif(self):
        try:
            image = Image.open(self.gif_path)
            self.delay = image.info['duration'] if 'duration' in image.info else 100

            for i in range(image.n_frames):
                image.seek(i)
                # Ensure the image is in a format Tkinter can use
                frame = ImageTk.PhotoImage(image.convert('RGBA'))
                self.frames.append(frame)
        except FileNotFoundError:
            print(f"Error: GIF file not found at {self.gif_path}")
            self.frames = []
        except Exception as e:
            print(f"Error loading GIF: {e}")
            self.frames = []

    def animate_gif(self):
        if not self.frames or self.stop_event.is_set():
            return

        frame = self.frames[self.current_frame]
        self.label.config(image=frame)
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.animation_id = self.after(self.delay, self.animate_gif)

    def center_window(self):
        self.update_idletasks()
        width = self.label.winfo_width()
        height = self.label.winfo_height()
        
        if width == 0 or height == 0: # If label not yet rendered, use first frame size
            if self.frames:
                width = self.frames[0].width()
                height = self.frames[0].height()
            else: # Fallback if GIF failed to load
                width, height = 300, 300 

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.geometry(f'{width}x{height}+{x}+{y}')

    def stop_animation(self):
        self.stop_event.set()
        if self.animation_id:
            self.after_cancel(self.animation_id)
        self.destroy()

def show_startup_gif(root, gif_path):
    gif_window = GIFViewer(root, gif_path)
    # Important: Don't block the mainloop
    # Return the window object so it can be managed externally
    return gif_window
