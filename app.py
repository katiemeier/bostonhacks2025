"""
Lightweight launcher that composes `gui.py` and `voice_unlock.py`.

Behavior:
- Imports the GUI App from `gui.py` and voice functions from `voice_unlock.py`.
- Wraps `voice_unlock.verify` so that when verification returns a dict with status=="granted",
  the GUI is instructed to show the home page (if the App provides `show_home`).
- Starts the Tkinter mainloop.
"""

import src.voice_unlock as voice_unlock
from src.gui import App
import tkinter as tk
import threading

from importlib import import_module


class Launcher:
    def __init__(self):
        # If no authorized voice exists, open a separate initial window first.
        try:
            if not voice_unlock._authorized_exists():
                self._run_initial_setup_window()
        except Exception:
            pass

        # Now create the main App (after initial setup window closes or if authorized exists)
        self.app = App()

        # ensure the main window shows the locked landing if an authorized voice exists
        try:
            if voice_unlock._authorized_exists():
                try:
                    self.app.show_locked_landing()
                except Exception:
                    pass
        except Exception:
            pass

        # wrap verify so GUI can respond to successful unlock
        if hasattr(voice_unlock, "verify"):
            self._orig_verify = voice_unlock.verify

            def wrapped_verify():
                res = self._orig_verify()
                try:
                    if isinstance(res, dict) and res.get("status") == "granted":
                        # schedule GUI update on main thread to open the NoteApp
                        try:
                            self.app.master.after(100, self._open_note_app)
                        except Exception:
                            pass
                except Exception:
                    pass
                return res

            voice_unlock.verify = wrapped_verify

    def _open_note_app(self):
        # Close the current GUI window and launch the note app in a new Tk root
        try:
            # destroy the existing root
            try:
                self.app.master.destroy()
            except Exception:
                pass

            # import and launch note app
            try:
                note_module = import_module('src.noteapp')
                NoteApp = getattr(note_module, 'NoteApp', None)
                if NoteApp is None:
                    print('NoteApp not found in src.noteapp')
                    return

                new_root = tk.Tk()
                note_app = NoteApp(new_root)
                new_root.mainloop()
            except Exception as e:
                print(f'Failed to start NoteApp: {e}')
        except Exception as e:
            print(f'Error opening note app: {e}')

    def _run_initial_setup_window(self):
        # Create a separate Tk root for the initial setup so it's a distinct window lifecycle.
        init_root = tk.Tk()
        init_root.title("Welcome to Your Secret Journal")
        init_root.geometry("520x280")

        frame = tk.Frame(init_root, bg="#fff3fb")
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="Welcome to Your Secret Journal", bg="#fff3fb", fg="#9b1948",
                         font=("Helvetica", 16, "bold"))
        title.pack(pady=(18, 6))

        desc = tk.Label(frame, text="Please set your voice password to protect your journal.",
                        bg="#fff3fb", fg="#a3164a", font=("Helvetica", 10), wraplength=460, justify="center")
        desc.pack(pady=(0, 14))

        status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(frame, textvariable=status_var, bg="#fff3fb", fg="#6a0b3a")
        status_label.pack(pady=(0, 8))

        def start_enroll():
            # disable button and run enroll in background
            enroll_btn.config(state="disabled")

            def worker():
                try:
                    status_var.set("Recording enrollment (3s)... 🎤")
                    res = voice_unlock.enroll()
                    if res:
                        status_var.set("Enrollment successful. Opening app...")
                        # close the init window on main thread
                        init_root.after(500, init_root.destroy)
                    else:
                        status_var.set("Enrollment failed. Try again.")
                        init_root.after(1500, lambda: enroll_btn.config(state="normal"))
                except Exception as e:
                    status_var.set(f"Enrollment error: {e}")
                    init_root.after(1500, lambda: enroll_btn.config(state="normal"))

            threading.Thread(target=worker, daemon=True).start()

        enroll_btn = tk.Button(frame, text="Set Voice Password", bg="#ff7fbf", fg="white",
                               activebackground="#ff5fa8", font=("Helvetica", 12, "bold"), bd=0,
                               command=start_enroll)
        enroll_btn.pack(pady=6, ipadx=10, ipady=6)

        close_btn = tk.Button(frame, text="Close", bg="#ffb6d9", fg="#6a0b3a", bd=0,
                              command=init_root.destroy)
        close_btn.pack(side="bottom", pady=12)

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
