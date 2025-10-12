"""
Lighweight launcher that composes `gui.py` and `voice_unlock.py`.

Behavior:
- Imports the GUI App from `gui.py` and voice functions from `voice_unlock.py`.
- Wraps `voice_unlock.verify` so that when verification returns a dict with status == "granted",
  the GUI is instructed to show the home page (if the App provides `show_home`).
- Starts the Tkinter mainloop.
"""

import tkinter as tk
import threading
from importlib import import_module

import src.voice_unlock as voice_unlock
from src.gui import App

# Constants for styling and behavior
INITIAL_TITLE = "Welcome to Your Secret Journal"
INITIAL_GEOMETRY = "816x503"
INITIAL_BG = "#fff3fb"
TEXT_COLOR_TITLE = "#9b1948"
TEXT_COLOR_DESC = "#a3164a"
TEXT_COLOR_STATUS = "#6a0b3a"
BUTTON_BG = "#ff7fbf"
BUTTON_ACTIVE = "#ff5fa8"
CLOSE_BUTTON_BG = "#ffb6d9"
CLOSE_BUTTON_FG = "#6a0b3a"
AFTER_DELAY = 100


class Launcher:
    def __init__(self):
        # Check for voice authorization, run initial setup if needed
        try:
            if not voice_unlock._authorized_exists():
                self._run_initial_setup_window()
        except Exception:
            pass

        # Initialize main application with a callback for successful unlock
        self.app = App(on_unlocked=self._open_note_app)

        # Show locked landing if voice is authorized
        try:
            if voice_unlock._authorized_exists():
                try:
                    self.app.show_locked_landing()
                except Exception:
                    pass
        except Exception:
            pass

        # No monkey-patching of voice_unlock.verify; GUI will invoke on_unlocked callback

    def _open_note_app(self):
        """Destroy current window and launch note app."""
        try:
            try:
                note_module = import_module('src.noteapp')
                NoteApp = getattr(note_module, 'NoteApp', None)
                if NoteApp is None:
                    print('NoteApp not found in src.noteapp')
                    return

                # Prefer a single Tk root: hide current window and open a Toplevel
                try:
                    self.app.master.withdraw()
                except Exception:
                    pass

                top = tk.Toplevel(self.app.master)
                NoteApp(top)

                # When note window closes, also close the hidden root to exit cleanly
                def on_close():
                    try:
                        top.destroy()
                    finally:
                        try:
                            self.app.master.destroy()
                        except Exception:
                            pass
                top.protocol("WM_DELETE_WINDOW", on_close)
            except Exception as e:
                print(f'Failed to start NoteApp: {e}')
        except Exception as e:
            print(f'Error opening note app: {e}')

    def _run_initial_setup_window(self):
        """Create and run the initial setup window for voice enrollment with background, voice button, and Comic Sans instructions."""
        init_root = tk.Tk()
        init_root.title(INITIAL_TITLE)
        init_root.geometry(INITIAL_GEOMETRY)

        # Use a canvas to draw the background image
        canvas = tk.Canvas(init_root, width=816, height=503, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        try:
            from PIL import Image, ImageTk
            bg_pil = Image.open("assets/intro_screen.png").convert("RGBA")
            bg_scaled = bg_pil.resize((816, 503), Image.LANCZOS)
            bg_img = ImageTk.PhotoImage(bg_scaled)
            canvas.create_image(0, 0, image=bg_img, anchor="nw")
        except Exception:
            bg_img = tk.PhotoImage(file="assets/intro_screen.png")
            canvas.create_image(0, 0, image=bg_img, anchor="nw")

        # Load and place the voice button (64x64px, 20px below center)
        try:
            from PIL import Image, ImageTk
            btn_pil = Image.open("assets/talk_button.png").convert("RGBA")
            btn_scaled = btn_pil.resize((64, 64), Image.LANCZOS)
            btn_img = ImageTk.PhotoImage(btn_scaled)
        except Exception:
            btn_img = tk.PhotoImage(file="assets/talk_button.png")
        center_x = 816 // 2
        center_y = 503 // 2 + 20
        voice_btn = canvas.create_image(center_x, center_y, image=btn_img, anchor="center")

        # Comic Sans text below button
        text_y = center_y + 44
        text_id = canvas.create_text(center_x, text_y, text="Click then say your password aloud", font=("Comic Sans MS", 16), fill="#d6336c", anchor="n")

        # Button click handler
        def start_enroll(_evt=None):
            canvas.itemconfig(voice_btn, state="disabled")
            canvas.itemconfig(text_id, text="Listening")
            def worker():
                try:
                    res = voice_unlock.enroll()
                    if res:
                        init_root.after(500, init_root.destroy)
                except Exception:
                    pass
            threading.Thread(target=worker, daemon=True).start()
        canvas.tag_bind(voice_btn, "<Button-1>", start_enroll)
        canvas.tag_bind(voice_btn, "<Enter>", lambda e: init_root.configure(cursor="hand2"))
        canvas.tag_bind(voice_btn, "<Leave>", lambda e: init_root.configure(cursor=""))

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
