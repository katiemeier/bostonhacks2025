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
        """Create and run the initial setup window for voice enrollment."""
        init_root = tk.Tk()
        init_root.title(INITIAL_TITLE)
        init_root.geometry(INITIAL_GEOMETRY)

        frame = tk.Frame(init_root, bg=INITIAL_BG)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text=INITIAL_TITLE, bg=INITIAL_BG, fg=TEXT_COLOR_TITLE,
                          font=("Helvetica", 16, "bold"))
        title.pack(pady=(18, 6))

        desc = tk.Label(frame, text="Please set your voice password to protect your journal.",
                         bg=INITIAL_BG, fg=TEXT_COLOR_DESC, font=("Helvetica", 10),
                         wraplength=460, justify="center")
        desc.pack(pady=(0, 14))

        status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(frame, textvariable=status_var, bg=INITIAL_BG, fg=TEXT_COLOR_STATUS)
        status_label.pack(pady=(0, 8))

        def start_enroll():
            enroll_btn.config(state="disabled")

            def worker():
                try:
                    status_var.set("Recording enrollment (3s)... 🎤")
                    res = voice_unlock.enroll()
                    if res:
                        status_var.set("Enrollment successful. Opening app...")
                        init_root.after(500, init_root.destroy)
                    else:
                        status_var.set("Enrollment failed. Try again.")
                        init_root.after(1500, lambda: enroll_btn.config(state="normal"))
                except Exception as e:
                    status_var.set(f"Enrollment error: {e}")
                    init_root.after(1500, lambda: enroll_btn.config(state="normal"))

            threading.Thread(target=worker, daemon=True).start()

        enroll_btn = tk.Button(frame, text="Set Voice Password", bg=BUTTON_BG, fg="white",
                               activebackground=BUTTON_ACTIVE, font=("Helvetica", 12, "bold"), bd=0,
                               command=start_enroll)
        enroll_btn.pack(pady=6, ipadx=10, ipady=6)

        close_btn = tk.Button(frame, text="Close", bg=CLOSE_BUTTON_BG, fg=CLOSE_BUTTON_FG, bd=0,
                              command=init_root.destroy)
        close_btn.pack(side="bottom", pady=12)

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
