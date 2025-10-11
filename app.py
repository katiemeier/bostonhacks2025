"""
Lightweight launcher that composes `gui.py` and `voice_unlock.py`.

Behavior:
- Imports the GUI App from `gui.py` and voice functions from `voice_unlock.py`.
- Wraps `voice_unlock.verify` so that when verification returns a dict with status=="granted",
  the GUI is instructed to show the home page (if the App provides `show_home`).
- Starts the Tkinter mainloop.
"""

import voice_unlock
from gui import App


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
                        # schedule GUI update on main thread
                        try:
                            self.app.master.after(100, getattr(self.app, "show_home", lambda: None))
                        except Exception:
                            pass
                except Exception:
                    pass
                return res

            voice_unlock.verify = wrapped_verify

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
