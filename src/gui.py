import tkinter as tk
from tkinter import ttk
import threading
import random
import time


# Color Palette
class Colors:
    # Background Colors
    BG_MAIN = "#ffe6f2"  # Main window background
    BG_CANVAS = "#ffd6ea"  # Canvas background
    BG_PAPER = "#fff3fb"  # Notebook paper background
    
    # Accent Colors
    ACCENT_SPIRAL = "#ffd1ea"  # Spiral binding color
    ACCENT_SPIRAL_OUTLINE = "#ffb6da"  # Spiral binding outline
    ACCENT_SPARKLE = ["#fff7fb", "#fff0f6", "#fff1f4", "#fffaf8"]  # Sparkle colors
    
    # Text Colors
    TEXT_TITLE = "#d6336c"  # Main title
    TEXT_SUBTITLE = "#a3164a"  # Subtitle
    TEXT_STATUS = "#9b1948"  # Status text
    TEXT_JOURNAL = "#5a1633"  # Journal text
    TEXT_BTN = "white"  # Button text
    TEXT_EXIT = "#6a0b3a"  # Exit button text
    
    # Button Colors
    BTN_UNLOCK = "#ff5f9e"  # Unlock button
    BTN_UNLOCK_ACTIVE = "#ff3f84"  # Unlock button hover
    BTN_EXIT = "#ffb6d9"  # Exit button
    BTN_EXIT_ACTIVE = "#ffa2d1"  # Exit button hover
    BTN_CHANGE = "#ff7fbf"  # Change password button
    BTN_CHANGE_ACTIVE = "#ff5fa8"  # Change password button hover


class App:
    def __init__(self, master=None):
        self.master = master or tk.Tk()
        self.master.title("Secret Voice Journal")
        self.master.geometry("720x880")
        self.master.configure(bg=Colors.BG_MAIN)

        # Main canvas to draw a "sparkly pink notebook"
        self.canvas = tk.Canvas(self.master, width=700, height=800, bg=Colors.BG_CANVAS, highlightthickness=0)
        self.canvas.place(x=10, y=10)

        # Notebook body (paper)
        pad = 40
        self.canvas.create_rectangle(pad, pad, 660, 760, fill=Colors.BG_PAPER, outline=Colors.ACCENT_SPIRAL, width=3)

        # Spiral binding on left
        for i in range(9):
            y = 80 + i * 70
            self.canvas.create_oval(30, y, 50, y + 30, fill=Colors.ACCENT_SPIRAL, outline=Colors.ACCENT_SPIRAL_OUTLINE)

        # Sparkles (random small stars)
        for _ in range(120):
            x = random.randint(80, 620)
            y = random.randint(60, 720)
            r = random.randint(1, 4)
            color = random.choice(Colors.ACCENT_SPARKLE)
            self.canvas.create_oval(x, y, x + r, y + r, fill=color, outline=color)

        # Title
        self.canvas.create_text(360, 110, text="My Secret Journal", fill=Colors.TEXT_TITLE, font=("Helvetica", 28, "bold"))
        self.canvas.create_text(360, 150, text="Unlock with your voice 💖", fill=Colors.TEXT_SUBTITLE, font=("Helvetica", 12))

        # Status area (inside the notebook)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self.master, textvariable=self.status_var, bg=Colors.BG_PAPER, fg=Colors.TEXT_STATUS,
                                    font=("Helvetica", 11), wraplength=520, justify="center")
        self.status_label.place(x=110, y=220, width=500, height=60)

        # Secret text area (hidden until unlocked)
        self.journal = tk.Text(self.master, bg=Colors.BG_PAPER, fg=Colors.TEXT_JOURNAL, font=("Georgia", 12), wrap="word")
        self.journal.insert("1.0", "Dear Journal,\n\nThis is a secret place for your thoughts. Unlock with your voice to read more...")
        self.journal.config(state="disabled")
        self.journal.place(x=110, y=300, width=500, height=340)

        # Pretty buttons (enroll button removed; initial setup handles enrollment)

        self.unlock_btn = tk.Button(self.master, text="🔐 Unlock", command=self.on_unlock,
                                    bg=Colors.BTN_UNLOCK, fg=Colors.TEXT_BTN, activebackground=Colors.BTN_UNLOCK_ACTIVE,
                                    font=("Helvetica", 12, "bold"), bd=0)
        self.unlock_btn.place(x=300, y=670, width=150, height=44)

        self.exit_btn = tk.Button(self.master, text="Exit", command=self.master.quit,
                                  bg=Colors.BTN_EXIT, fg=Colors.TEXT_EXIT, activebackground=Colors.BTN_EXIT_ACTIVE,
                                  font=("Helvetica", 11), bd=0)
        self.exit_btn.place(x=520, y=670, width=90, height=40)

        # Keep a reference to the thread so we can disable buttons while running
        self.current_thread = None
        
        # After building the main window, decide startup flow based on whether an authorized voice exists
        try:
            import src.voice_unlock as _vu
            if not _vu._authorized_exists():
                # No authorized voice yet -> open a separate initial window to set password
                self.show_initial_window()
            else:
                # Authorized voice exists -> show a landing page that only offers Unlock
                self.show_locked_landing()
        except Exception:
            # If voice_unlock not available, just continue showing main window
            pass

    def run_in_thread(self, target, *args, **kwargs):
        if self.current_thread and self.current_thread.is_alive():
            return False

        def wrapper():
            try:
                target(*args, **kwargs)
            except Exception as e:
                self.set_status(f"Error: {e}")
            finally:
                self.current_thread = None
                self.enable_buttons()

        self.disable_buttons()
        t = threading.Thread(target=wrapper, daemon=True)
        self.current_thread = t
        t.start()
        return True

    def clear_overlay_frames(self):
        # destroy dynamic frames (home/editor)
        for name in ("home_frame", "editor_frame"):
            f = getattr(self, name, None)
            if f:
                try:
                    f.destroy()
                except Exception:
                    pass
                setattr(self, name, None)

        # if an initial separate window exists, try to destroy it
        if getattr(self, 'initial_win', None):
            try:
                self.initial_win.destroy()
            except Exception:
                pass
            self.initial_win = None

    def set_status(self, text):
        self.status_var.set(text)

    def disable_buttons(self):
        self.unlock_btn.config(state="disabled")
        self.exit_btn.config(state="disabled")

    def enable_buttons(self):
        self.unlock_btn.config(state="normal")
        self.exit_btn.config(state="normal")

    def show_locked_landing(self):
        # Show a landing area in the main window that only allows unlocking (no enroll)
        self.clear_overlay_frames()
    # enroll handled during initial setup; don't show it on locked landing

        self.home_frame = tk.Frame(self.master, bg=Colors.BG_PAPER, bd=0)
        self.home_frame.place(x=110, y=300, width=500, height=340)

        title = tk.Label(self.home_frame, text="Welcome Back 💖", bg=Colors.BG_PAPER, fg=Colors.TEXT_STATUS,
                         font=("Helvetica", 18, "bold"))
        title.pack(pady=(12, 6))

        desc = tk.Label(self.home_frame, text="Unlock your secret journal with your voice.",
                        bg=Colors.BG_PAPER, fg=Colors.TEXT_SUBTITLE, font=("Helvetica", 11), wraplength=420, justify="center")
        desc.pack(pady=(0, 18))

        # unlock_btn = tk.Button(self.home_frame, text="🔐 Unlock", bg=Colors.BTN_UNLOCK, fg=Colors.TEXT_BTN,
        #                        activebackground=Colors.BTN_UNLOCK_ACTIVE, font=("Helvetica", 12, "bold"), bd=0,
        #                        command=self.on_unlock)
        # unlock_btn.pack(pady=6, ipadx=10, ipady=6)

        # provide a change password option that opens the initial window
        change_btn = tk.Button(self.home_frame, text="Change Password", bg=Colors.BTN_CHANGE, fg=Colors.TEXT_BTN,
                               activebackground=Colors.BTN_CHANGE_ACTIVE, font=("Helvetica", 11), bd=0,
                               command=self.show_initial_window)
        change_btn.pack(pady=(10,0))

    def on_enroll(self):
        # run enroll in background and update status
        try:
            import src.voice_unlock as voice_unlock

            def do_enroll():
                self.set_status("Recording enrollment (3s)... 🎤")
                res = voice_unlock.enroll()
                # enroll() returns True on success
                if res:
                    self.set_status("✅ Voice enrolled. You can now try to unlock.")
                else:
                    self.set_status("Enrollment failed. See console for details.")

            self.run_in_thread(do_enroll)
        except Exception as e:
            self.set_status(f"Could not start enrollment: {e}")

    def on_unlock(self):
        try:
            import src.voice_unlock as voice_unlock

            def do_verify():
                if not voice_unlock._authorized_exists():
                    self.set_status("No authorized voice found. Please enroll first.")
                    return
                self.set_status("Recording attempt (3s)... 🎤")
                result = voice_unlock.verify()
                # verify() returns a dict with status and score
                if isinstance(result, dict):
                    status = result.get("status")
                    score = result.get("score")
                    if status == "granted":
                        self.set_status(f"✅ Access Granted! Similarity: {score:.3f}")
                        # reveal journal
                        self.journal.config(state="normal")
                        self.journal.focus_set()
                    elif status == "denied":
                        self.set_status(f"❌ Access Denied. Similarity: {score:.3f}")
                    else:
                        self.set_status(result.get("message", "Unknown result"))
                else:
                    # fallback: show generic message
                    self.set_status("Verification finished. Check console for details.")

            self.run_in_thread(do_verify)
        except Exception as e:
            self.set_status(f"Could not start verification: {e}")

    def run(self):
        self.master.mainloop()


if __name__ == "__main__":
    App().run()