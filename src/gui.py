import tkinter as tk
from tkinter import ttk
import threading
import random
import time


class App:
    def __init__(self, master=None):
        self.master = master or tk.Tk()
        self.master.title("Secret Voice Journal")
        self.master.geometry("720x880")
        self.master.configure(bg="#ffe6f2")

        # Main canvas to draw a "sparkly pink notebook"
        self.canvas = tk.Canvas(self.master, width=700, height=800, bg="#ffd6ea", highlightthickness=0)
        self.canvas.place(x=10, y=10)

        # Notebook body (paper)
        pad = 40
        self.canvas.create_rectangle(pad, pad, 660, 760, fill="#fff3fb", outline="#ffd1ea", width=3)

        # Spiral binding on left
        for i in range(9):
            y = 80 + i * 70
            self.canvas.create_oval(30, y, 50, y + 30, fill="#ffd1ea", outline="#ffb6da")

        # Sparkles (random small stars)
        for _ in range(120):
            x = random.randint(80, 620)
            y = random.randint(60, 720)
            r = random.randint(1, 4)
            color = random.choice(["#fff7fb", "#fff0f6", "#fff1f4", "#fffaf8"])
            self.canvas.create_oval(x, y, x + r, y + r, fill=color, outline=color)

        # Title
        self.canvas.create_text(360, 110, text="My Secret Journal", fill="#d6336c", font=("Helvetica", 28, "bold"))
        self.canvas.create_text(360, 150, text="Unlock with your voice 💖", fill="#a3164a", font=("Helvetica", 12))

        # Status area (inside the notebook)
        self.status_var = tk.StringVar(value="Welcome — please enroll or unlock.")
        self.status_label = tk.Label(self.master, textvariable=self.status_var, bg="#fff3fb", fg="#9b1948",
                                     font=("Helvetica", 11), wraplength=520, justify="center")
        self.status_label.place(x=110, y=220, width=500, height=60)

        # Secret text area (hidden until unlocked)
        self.journal = tk.Text(self.master, bg="#fffafc", fg="#5a1633", font=("Georgia", 12), wrap="word")
        self.journal.insert("1.0", "Dear Journal,\n\nThis is a secret place for your thoughts. Unlock with your voice to read more...")
        self.journal.config(state="disabled")
        self.journal.place(x=110, y=300, width=500, height=340)

        # Pretty buttons
        self.enroll_btn = tk.Button(self.master, text="✦ Enroll Voice", command=self.on_enroll,
                                    bg="#ff7fbf", fg="white", activebackground="#ff5fa8",
                                    font=("Helvetica", 12, "bold"), bd=0)
        self.enroll_btn.place(x=160, y=670, width=150, height=44)

        self.unlock_btn = tk.Button(self.master, text="🔐 Unlock", command=self.on_unlock,
                                    bg="#ff5f9e", fg="white", activebackground="#ff3f84",
                                    font=("Helvetica", 12, "bold"), bd=0)
        self.unlock_btn.place(x=340, y=670, width=150, height=44)

        self.exit_btn = tk.Button(self.master, text="Exit", command=self.master.quit,
                                  bg="#ffb6d9", fg="#6a0b3a", activebackground="#ffa2d1",
                                  font=("Helvetica", 11), bd=0)
        self.exit_btn.place(x=520, y=670, width=90, height=40)

        # Keep a reference to the thread so we can disable buttons while running
        self.current_thread = None

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

    def set_status(self, text):
        self.status_var.set(text)

    def disable_buttons(self):
        self.enroll_btn.config(state="disabled")
        self.unlock_btn.config(state="disabled")
        self.exit_btn.config(state="disabled")

    def enable_buttons(self):
        self.enroll_btn.config(state="normal")
        self.unlock_btn.config(state="normal")
        self.exit_btn.config(state="normal")

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