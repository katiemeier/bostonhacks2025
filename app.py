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
        """Show intro_screen.png and a centered animated microphone button for enrollment."""
        init_root = tk.Tk()
        init_root.title(INITIAL_TITLE)
        init_root.geometry(INITIAL_GEOMETRY)
        init_root.resizable(False, False)

        # Load intro image
        try:
            intro_img = tk.PhotoImage(file="assets/intro_screen.png")
        except Exception:
            intro_img = None

        canvas = tk.Canvas(init_root, width=816, height=503, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        if intro_img:
            canvas.create_image(0, 0, image=intro_img, anchor="nw")
        else:
            canvas.configure(bg=INITIAL_BG)



        # Load and resize button image using PIL
        try:
            from PIL import Image, ImageTk
            pil_img = Image.open("assets/talk_button.png")
            pil_img = pil_img.resize((64, 64), Image.LANCZOS)
            btn_img = ImageTk.PhotoImage(pil_img)
        except Exception:
            btn_img = None

        # Button position (20 pixels below center)
        cx, cy = 816 // 2, (503 // 2) + 20

        def on_press(event=None):
            start_enroll()

        def start_enroll():
            # Disable button during enroll
            canvas.tag_unbind("mic_btn", "<Button-1>")
            # Show status text
            status_id = canvas.create_text(cx, cy + 60, text="Listening for password...", font=("Helvetica", 14), fill="#000000", tags="status")
            def worker():
                try:
                    res = voice_unlock.enroll()
                    if res:
                        canvas.itemconfig(status_id, text="Enrollment successful! Opening app...")
                        init_root.after(800, init_root.destroy)
                    else:
                        canvas.itemconfig(status_id, text="Enrollment failed. Try again.")
                        init_root.after(1500, lambda: reset_button())
                except Exception as e:
                    canvas.itemconfig(status_id, text=f"Enrollment error: {e}")
                    init_root.after(1500, lambda: reset_button())
            threading.Thread(target=worker, daemon=True).start()

        def reset_button():
            canvas.delete("status")
            canvas.tag_bind("mic_btn", "<Button-1>", on_press)

        # Draw button (smaller, lower, no depressed version)
        if btn_img:
            btn_item = canvas.create_image(cx, cy, image=btn_img, anchor="center", tags="mic_btn")
        else:
            btn_width, btn_height = 64, 64
            btn_item = canvas.create_oval(cx-btn_width//2, cy-btn_height//2, cx+btn_width//2, cy+btn_height//2, fill="#ff7fbf", outline="", tags="mic_btn")
        canvas.tag_bind("mic_btn", "<Button-1>", on_press)

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
