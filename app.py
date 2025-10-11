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

from importlib import import_module


class Launcher:
    def __init__(self):
        self.app = App()

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

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
