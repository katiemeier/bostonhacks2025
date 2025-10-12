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
import os
try:
    from PIL import Image, ImageTk  # Pillow for image scaling
except Exception:
    Image = None
    ImageTk = None
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
            # Capture whether the current app window is in fullscreen (or equivalent)
            was_fullscreen = False
            try:
                if hasattr(self.app, "is_fullscreen_like") and callable(self.app.is_fullscreen_like):
                    was_fullscreen = bool(self.app.is_fullscreen_like())
                else:
                    # fallback minimal check
                    was_fullscreen = bool(self.app.master.attributes("-fullscreen"))
            except Exception:
                was_fullscreen = False
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
                # If we were fullscreen at unlock, force the note window fullscreen too
                try:
                    if was_fullscreen:
                        # macOS honors -fullscreen; ensure it's applied after window creation
                        top.attributes("-fullscreen", True)
                except Exception:
                    pass
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
        """Create and run the initial setup window for voice enrollment with a background image."""
        init_root = tk.Tk()
        init_root.title(INITIAL_TITLE)
        init_root.geometry(INITIAL_GEOMETRY)

        # Canvas-based layout to support a background image
        canvas = tk.Canvas(init_root, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)

        # Load background image
        bg_path = os.path.join(os.path.dirname(__file__), "assets", "intro_screen.png")
        bg_img = None
        try:
            bg_img = tk.PhotoImage(master=init_root, file=bg_path)
            # Keep a reference to avoid garbage collection
            init_root._bg_img_ref = bg_img
        except Exception:
            bg_img = None

        bg_item = None
        if bg_img is not None:
            # If we know image dimensions, prefer sizing window to match the image
            try:
                init_root.geometry(f"{bg_img.width()}x{bg_img.height()}")
            except Exception:
                pass
            bg_item = canvas.create_image(0, 0, image=bg_img, anchor="nw")
        else:
            # Fallback plain background color
            init_root.configure(bg=INITIAL_BG)

        # Title/description/status as canvas text to avoid opaque label backgrounds
        title_item = canvas.create_text(0, 0, text=INITIAL_TITLE, fill=TEXT_COLOR_TITLE,
                                        font=("Comic Sans MS", 16, "bold"), anchor="n")
        desc_text = "Please set your voice password to protect your journal."
        desc_item = canvas.create_text(0, 0, text=desc_text, fill=TEXT_COLOR_DESC,
                                       font=("Comic Sans MS", 10), width=480, justify="center",
                                       anchor="n")
        status_item = canvas.create_text(0, 0, text="Ready", fill=TEXT_COLOR_STATUS,
                                         font=("Comic Sans MS", 10), anchor="n")

        # Enrollment control: image-based button on the canvas
        enrolling = False

        def start_enroll(event=None):
            nonlocal enrolling
            if enrolling:
                return
            enrolling = True

            def worker():
                try:
                    canvas.itemconfigure(status_item, text="Recording enrollment (3s)... 🎤")
                    res = voice_unlock.enroll()
                    if res:
                        canvas.itemconfigure(status_item, text="Enrollment successful. Opening app...")
                        init_root.after(500, init_root.destroy)
                    else:
                        canvas.itemconfigure(status_item, text="Enrollment failed. Try again.")
                        init_root.after(1500, lambda: set_enrolling(False))
                except Exception as e:
                    canvas.itemconfigure(status_item, text=f"Enrollment error: {e}")
                    init_root.after(1500, lambda: set_enrolling(False))

            threading.Thread(target=worker, daemon=True).start()

        def set_enrolling(value: bool):
            nonlocal enrolling
            enrolling = value

        # Try to load the talk button image
        talk_img = None
        talk_path = os.path.join(os.path.dirname(__file__), "assets", "talk_button.png")
        try:
            if Image is not None and ImageTk is not None:
                pil_img = Image.open(talk_path)
                w, h = pil_img.size
                # Scale to 1/3 with high-quality resampling
                target = (max(1, w // 3), max(1, h // 3))
                pil_img = pil_img.resize(target, getattr(Image, 'Resampling', Image).LANCZOS)
                talk_img = ImageTk.PhotoImage(image=pil_img, master=init_root)
                # keep references to prevent GC
                init_root._talk_pil_img_ref = pil_img
                init_root._talk_img_ref = talk_img
            else:
                # Fallback: use Tk PhotoImage and subsample by 3
                orig = tk.PhotoImage(master=init_root, file=talk_path)
                scaled = orig.subsample(3, 3)
                talk_img = scaled
                init_root._talk_img_full = orig
                init_root._talk_img_ref = scaled
        except Exception:
            talk_img = None

        if talk_img is not None:
            enroll_item = canvas.create_image(0, 0, image=talk_img, anchor="n")
            # Click handler
            canvas.tag_bind(enroll_item, "<Button-1>", start_enroll)
        else:
            # Fallback to a simple text button if image missing
            fallback_btn = tk.Button(init_root, text="Set Voice Password", bg=BUTTON_BG, fg="white",
                                     activebackground=BUTTON_ACTIVE, font=("Comic Sans MS", 12, "bold"), bd=0,
                                     command=start_enroll)
            enroll_item = canvas.create_window(0, 0, window=fallback_btn, anchor="n")

        close_btn = tk.Button(init_root, text="Close", bg=CLOSE_BUTTON_BG, fg=CLOSE_BUTTON_FG, bd=0,
                              command=init_root.destroy)
        close_item = canvas.create_window(0, 0, window=close_btn, anchor="s")

        # Responsive layout: center elements on resize
        def relayout(event=None):
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            cx = w // 2

            # Resize background image positioning
            if bg_item is not None:
                canvas.coords(bg_item, 0, 0)

            y = 24
            canvas.coords(title_item, cx, y)
            y += 36
            canvas.coords(desc_item, cx, y + 25)
            y += 64
            canvas.coords(status_item, cx, y + 215)
            y += 28
            # Move the talk button down by an additional 20 pixels
            y += 80
            canvas.coords(enroll_item, cx, y)
            # Close button near bottom with some padding
            canvas.coords(close_item, cx, h - 16)

        canvas.bind("<Configure>", relayout)
        # Initial layout after a tick so geometry is computed
        init_root.after(10, relayout)

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
