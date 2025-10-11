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
    TEXT_BTN = "white"       # Button text
    TEXT_EXIT = "#6a0b3a"     # Exit button text
    
    # Button Colors
    BTN_UNLOCK = "#ff5f9e"       # Unlock button
    BTN_UNLOCK_ACTIVE = "#ff3f84"  # Unlock button hover
    BTN_EXIT = "#ffb6d9"         # Exit button
    BTN_EXIT_ACTIVE = "#ffa2d1"    # Exit button hover
    BTN_CHANGE = "#ff7fbf"         # Change password button
    BTN_CHANGE_ACTIVE = "#ff5fa8"    # Change password button hover


class App:
    """A secure journal application with voice authentication."""
    
    # UI Constants
    WINDOW_SIZE = "720x880"
    CANVAS_SIZE = (700, 800)
    NOTEBOOK_PADDING = 40
    
    # Component positions and sizes as dicts for place() method
    NOTEBOOK_MARGINS = {"x": 110, "y": 300, "width": 500, "height": 340}
    TITLE_POSITION = {"x": 360, "y": 110}
    SUBTITLE_POSITION = {"x": 360, "y": 150}
    STATUS_POSITION = {"x": 110, "y": 220, "width": 500, "height": 60}
    UNLOCK_BTN_POSITION = {"x": 300, "y": 670, "width": 150, "height": 44}
    EXIT_BTN_POSITION = {"x": 520, "y": 670, "width": 90, "height": 40}
    
    def __init__(self, master=None):
        """Initialize the application with the main window and UI components."""
        self.master = master or tk.Tk()
        self.current_thread = None
        self.setup_window()
        self.create_notebook()
        self.create_controls()
        self.check_authorization()

    def setup_window(self):
        """Configure the main window properties."""
        self.master.title("Secret Voice Journal")
        self.master.geometry(self.WINDOW_SIZE)
        self.master.configure(bg=Colors.BG_MAIN)

    def create_notebook(self):
        """Create the notebook UI with decorative elements."""
        self._create_canvas()
        self._create_notebook_paper()
        self._create_spiral_binding()
        self._add_sparkles()
        self._add_title()

    def _create_canvas(self):
        """Create the main canvas for the notebook."""
        self.canvas = tk.Canvas(
            self.master,
            width=self.CANVAS_SIZE[0], 
            height=self.CANVAS_SIZE[1],
            bg=Colors.BG_CANVAS,
            highlightthickness=0
        )
        self.canvas.place(x=10, y=10)

    def _create_notebook_paper(self):
        """Create the main paper area of the notebook."""
        self.canvas.create_rectangle(
            self.NOTEBOOK_PADDING, self.NOTEBOOK_PADDING,
            660, 760,
            fill=Colors.BG_PAPER,
            outline=Colors.ACCENT_SPIRAL,
            width=3
        )

    def _create_spiral_binding(self):
        """Create decorative spiral binding on the notebook's left side."""
        for i in range(9):
            y = 80 + i * 70
            self.canvas.create_oval(
                30, y, 50, y + 30,
                fill=Colors.ACCENT_SPIRAL,
                outline=Colors.ACCENT_SPIRAL_OUTLINE
            )

    def _add_sparkles(self):
        """Add decorative sparkles to the notebook."""
        for _ in range(120):
            x = random.randint(80, 620)
            y = random.randint(60, 720)
            r = random.randint(1, 4)
            color = random.choice(Colors.ACCENT_SPARKLE)
            self.canvas.create_oval(x, y, x + r, y + r, fill=color, outline=color)

    def _add_title(self):
        """Add the title and subtitle to the notebook."""
        self.canvas.create_text(
            self.TITLE_POSITION["x"], self.TITLE_POSITION["y"],
            text="My Secret Journal",
            fill=Colors.TEXT_TITLE,
            font=("Helvetica", 28, "bold")
        )
        self.canvas.create_text(
            self.SUBTITLE_POSITION["x"], self.SUBTITLE_POSITION["y"],
            text="Unlock with your voice 💖",
            fill=Colors.TEXT_SUBTITLE,
            font=("Helvetica", 12)
        )

    def create_controls(self):
        """Create interactive UI controls."""
        self._create_status_area()
        self._create_journal_area()
        self._create_buttons()

    def _create_status_area(self):
        """Create the status message area."""
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.master,
            textvariable=self.status_var,
            bg=Colors.BG_PAPER,
            fg=Colors.TEXT_STATUS,
            font=("Helvetica", 11),
            wraplength=520,
            justify="center"
        )
        self.status_label.place(**self.STATUS_POSITION)

    def _create_journal_area(self):
        """Create the journal text area."""
        self.journal = tk.Text(
            self.master,
            bg=Colors.BG_PAPER,
            fg=Colors.TEXT_JOURNAL,
            font=("Georgia", 12),
            wrap="word"
        )
        self.journal.insert("1.0", "Dear Journal,\n\nThis is a secret place for your thoughts. Unlock with your voice to read more...")
        self.journal.config(state="disabled")
        self.journal.place(**self.NOTEBOOK_MARGINS)

    def _create_buttons(self):
        """Create the unlock and exit buttons."""
        self.unlock_btn = tk.Button(
            self.master,
            text="🔐 Unlock",
            command=self.on_unlock,
            bg=Colors.BTN_UNLOCK,
            fg=Colors.TEXT_BTN,
            activebackground=Colors.BTN_UNLOCK_ACTIVE,
            font=("Helvetica", 12, "bold"),
            bd=0
        )
        self.unlock_btn.place(**self.UNLOCK_BTN_POSITION)

        self.exit_btn = tk.Button(
            self.master,
            text="Exit",
            command=self.master.quit,
            bg=Colors.BTN_EXIT,
            fg=Colors.TEXT_EXIT,
            activebackground=Colors.BTN_EXIT_ACTIVE,
            font=("Helvetica", 11),
            bd=0
        )
        self.exit_btn.place(**self.EXIT_BTN_POSITION)

    def check_authorization(self):
        """Check if a voice is authorized and show appropriate screen."""
        try:
            import src.voice_unlock as _vu
            if not _vu._authorized_exists():
                self.show_initial_window()
            else:
                self.show_locked_landing()
        except ImportError:
            # If voice_unlock not available, continue showing main window
            pass

    def show_locked_landing(self):
        """Show the landing page for returning users."""
        self.clear_overlay_frames()
        self.home_frame = tk.Frame(
            self.master,
            bg=Colors.BG_PAPER,
            bd=0
        )
        self.home_frame.place(**self.NOTEBOOK_MARGINS)
        title = tk.Label(
            self.home_frame,
            text="Welcome Back 💖",
            bg=Colors.BG_PAPER,
            fg=Colors.TEXT_STATUS,
            font=("Helvetica", 18, "bold")
        )
        title.pack(pady=(12, 6))
        desc = tk.Label(
            self.home_frame,
            text="Unlock your secret journal with your voice.",
            bg=Colors.BG_PAPER,
            fg=Colors.TEXT_SUBTITLE,
            font=("Helvetica", 11),
            wraplength=420,
            justify="center"
        )
        desc.pack(pady=(0, 18))
        # change_btn = tk.Button(
        #     self.home_frame,
        #     text="Change Password",
        #     bg=Colors.BTN_CHANGE,
        #     fg=Colors.TEXT_BTN,
        #     activebackground=Colors.BTN_CHANGE_ACTIVE,
        #     font=("Helvetica", 11),
        #     bd=0,
        #     command=self.show_initial_window
        # )
        # change_btn.pack(pady=(10, 0))

    def show_initial_window(self):
        """Show an initial window to set up voice authentication."""
        self.set_status("Initial setup: Please set your password.")

    def clear_overlay_frames(self):
        """Remove any overlay frames and windows."""
        for name in ("home_frame", "editor_frame", "initial_win"):
            frame = getattr(self, name, None)
            if frame:
                try:
                    frame.destroy()
                except tk.TclError:
                    pass
                setattr(self, name, None)

    def set_status(self, text):
        """Update the status message."""
        self.status_var.set(text)

    def disable_buttons(self):
        """Disable interactive buttons."""
        self.unlock_btn.config(state="disabled")
        self.exit_btn.config(state="disabled")

    def enable_buttons(self):
        """Re-enable interactive buttons."""
        self.unlock_btn.config(state="normal")
        self.exit_btn.config(state="normal")

    def run_in_thread(self, target, *args, **kwargs):
        """Run a function in a background thread with UI state management."""
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

    def on_enroll(self):
        """Handle voice enrollment process."""
        try:
            import src.voice_unlock as voice_unlock
            
            def do_enroll():
                self.set_status("Recording enrollment (3s)... 🎤")
                if voice_unlock.enroll():
                    self.set_status("✅ Voice enrolled. You can now try to unlock.")
                else:
                    self.set_status("Enrollment failed. See console for details.")

            self.run_in_thread(do_enroll)
        except ImportError:
            self.set_status("Could not start enrollment: Voice unlock module not found")
        except Exception as e:
            self.set_status(f"Could not start enrollment: {str(e)}")

    def on_unlock(self):
        """Handle voice verification process."""
        try:
            import src.voice_unlock as voice_unlock
            
            def do_verify():
                if not voice_unlock._authorized_exists():
                    self.set_status("No authorized voice found. Please enroll first.")
                    return
                self.set_status("Recording attempt (3s)... 🎤")
                result = voice_unlock.verify()
                self._handle_verification_result(result)

            self.run_in_thread(do_verify)
        except ImportError:
            self.set_status("Could not start verification: Voice unlock module not found")
        except Exception as e:
            self.set_status(f"Could not start verification: {str(e)}")

    def _handle_verification_result(self, result):
        """Process the verification result and update UI accordingly."""
        if not isinstance(result, dict):
            self.set_status("Verification finished. Check console for details.")
            return

        status = result.get("status")
        score = result.get("score", 0)
        if status == "granted":
            self.set_status(f"✅ Access Granted! Similarity: {score:.3f}")
            self._unlock_journal()
        elif status == "denied":
            self.set_status(f"❌ Access Denied. Similarity: {score:.3f}")
        else:
            self.set_status(result.get("message", "Unknown result"))

    def _unlock_journal(self):
        """Enable the journal text area for editing."""
        self.journal.config(state="normal")
        self.journal.focus_set()

    def run(self):
        """Start the application's main loop."""
        self.master.mainloop()


if __name__ == "__main__":
    App().run()