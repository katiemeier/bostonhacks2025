import tkinter as tk
import threading
try:
    from PIL import Image, ImageTk  # type: ignore
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False


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
    WINDOW_SIZE = "816x503"  # modified from "720x880"
    CANVAS_SIZE = (796, 280)  # modified from (700, 800)
    NOTEBOOK_PADDING = 40
    
    # Component positions and sizes as dicts for place() method
    NOTEBOOK_MARGINS = {"x": 20, "y": 20, "width": 756, "height": 240}  # modified from {"x": 110, "y": 300, "width": 500, "height": 340}
    TITLE_POSITION = {"x": 398, "y": 40}  # modified from {"x": 360, "y": 110}
    SUBTITLE_POSITION = {"x": 398, "y": 80}  # modified from {"x": 360, "y": 150}
    STATUS_POSITION = {"x": 10, "y": 300, "width": 796, "height": 30}  # modified from {"x": 110, "y": 220, "width": 500, "height": 60}
    UNLOCK_BTN_POSITION = {"x": 216, "y": 340, "width": 150, "height": 40}  # modified from {"x": 300, "y": 670, "width": 150, "height": 44}
    EXIT_BTN_POSITION = {"x": 450, "y": 340, "width": 150, "height": 40}  # modified from {"x": 520, "y": 670, "width": 90, "height": 40}
    
    def __init__(self, master=None, on_unlocked=None):
        """Initialize the application with the main window and UI components."""
        self.master = master or tk.Tk()
        # Optional callback invoked when access is granted
        self.on_unlocked = on_unlocked
        self.current_thread = None
        self.setup_window()
        # Show only the background; skip creating overlays and auth screens
        # self.create_notebook()
        # self.create_controls()
        # self.check_authorization()
        # Add a centered unlock image button
        self._create_center_unlock_button()

    def setup_window(self):
        """Configure the main window properties with a custom background image."""
        self.master.title("Secret Voice Journal")
        self.master.geometry(self.WINDOW_SIZE)
        # Create a canvas covering the window; draw background image on it to support PNG layering
        try:
            w, h = (int(x) for x in self.WINDOW_SIZE.split("x", 1))
        except Exception:
            w, h = 816, 503
        self.canvas_main = tk.Canvas(self.master, width=w, height=h, highlightthickness=0, bd=0)
        self.canvas_main.place(x=0, y=0, width=w, height=h)
        try:
            self.bg_image = tk.PhotoImage(file="assets/launch2.png")
            self.canvas_main.create_image(0, 0, image=self.bg_image, anchor="nw")
        except Exception:
            # If image fails to load, use the themed background color
            self.canvas_main.configure(bg=Colors.BG_MAIN)
        # Manage clickability when using canvas items
        self._unlock_clickable = True


    def _create_center_unlock_button(self):
        """Create a centered unlock image on the canvas with click handling for transparent PNGs."""
        # Preferred: draw on the main canvas so PNG transparency shows the background
        if hasattr(self, "canvas_main") and self.canvas_main:
            try:
                self.unlock_img = self._load_unlock_image_scaled(98, 98)
                try:
                    w, h = (int(x) for x in self.WINDOW_SIZE.split("x", 1))
                except Exception:
                    w, h = 816, 503
                self.unlock_item = self.canvas_main.create_image(
                    w // 2, h // 2, image=self.unlock_img, anchor="center", tags=("unlock",)
                )
                # Bind mouse interactions
                def _maybe_unlock(_evt=None):
                    if getattr(self, "_unlock_clickable", True):
                        self.on_unlock()
                self.canvas_main.tag_bind("unlock", "<Button-1>", _maybe_unlock)
                self.canvas_main.tag_bind("unlock", "<Enter>", lambda e: self.master.configure(cursor="hand2"))
                self.canvas_main.tag_bind("unlock", "<Leave>", lambda e: self.master.configure(cursor=""))
                return
            except Exception:
                pass
        # Fallback: use a traditional Button with the image/text centered
        try:
            self.unlock_img = self._load_unlock_image_scaled(98, 98)
            self.unlock_btn = tk.Button(
                self.master,
                image=self.unlock_img,
                command=self.on_unlock,
                bd=0,
                highlightthickness=0,
                relief="flat",
                cursor="hand2",
                borderwidth=0,
                background=self.master.cget("bg")
            )
        except Exception:
            self.unlock_btn = tk.Button(
                self.master,
                text="Unlock",
                command=self.on_unlock,
                bg=Colors.BTN_UNLOCK,
                fg=Colors.TEXT_BTN,
                activebackground=Colors.BTN_UNLOCK_ACTIVE,
                font=("Helvetica", 12, "bold"),
                bd=0
            )
        self.unlock_btn.place(relx=0.5, rely=0.5, anchor="center")

    def _load_unlock_image_scaled(self, width: int, height: int):
        """Load the talk_button image scaled to exact width/height, preserving transparency.

        Uses Pillow if available for high-quality resizing; otherwise falls back to PhotoImage
        and nearest subsample/zoom approximation.
        Returns a Tk-compatible PhotoImage (either ImageTk.PhotoImage or tk.PhotoImage).
        """
        path = "assets/talk_button.png"
        if _PIL_AVAILABLE:
            img = Image.open(path).convert("RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        # Fallback without PIL: load and approximate scaling
        base = tk.PhotoImage(file=path)
        bw, bh = base.width(), base.height()
        # Avoid division by zero
        if bw <= 0 or bh <= 0:
            return base
        # Compute subsample factors to approximate target size
        sx = max(1, round(bw / max(1, width)))
        sy = max(1, round(bh / max(1, height)))
        try:
            approx = base.subsample(sx, sy)
            return approx
        except Exception:
            return base


    # def _create_journal_area(self):
    #     """Create the journal text area."""
    #     self.journal = tk.Text(
    #         self.master,
    #         bg=Colors.BG_PAPER,
    #         fg=Colors.TEXT_JOURNAL,
    #         font=("Georgia", 12),
    #         wrap="word"
    #     )
    #     self.journal.insert("1.0", "Dear Journal,\n\nThis is a secret place for your thoughts. Unlock with your voice to read more...")
    #     self.journal.config(state="disabled")
    #     self.journal.place(**self.NOTEBOOK_MARGINS)

    

    def show_locked_landing(self):
        """Show only the background; no welcome back splash screen."""
        self.clear_overlay_frames()
        # Removed welcome back splash screen UI elements


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
        try:
            if hasattr(self, "status_var"):
                self.status_var.set(text)
        except Exception:
            # No status area present; ignore
            pass

    def disable_buttons(self):
        """Disable interactive buttons."""
        # For canvas-based button, gate clicks via flag
        self._unlock_clickable = False
        try:
            if hasattr(self, "unlock_btn") and self.unlock_btn:
                self.unlock_btn.config(state="disabled")
            if hasattr(self, "exit_btn") and self.exit_btn:
                self.exit_btn.config(state="disabled")
        except Exception:
            pass

    def enable_buttons(self):
        """Re-enable interactive buttons."""
        self._unlock_clickable = True
        try:
            if hasattr(self, "unlock_btn") and self.unlock_btn:
                self.unlock_btn.config(state="normal")
            if hasattr(self, "exit_btn") and self.exit_btn:
                self.exit_btn.config(state="normal")
        except Exception:
            pass

    def run_in_thread(self, target, *args, **kwargs):
        """Run a function in a background thread with UI state management."""
        if self.current_thread and self.current_thread.is_alive():
            return False

        def wrapper():
            try:
                target(*args, **kwargs)
            except Exception as e:
                # Schedule UI update on the main thread
                try:
                    self.master.after(0, self.set_status, f"Error: {e}")
                except Exception:
                    pass
            finally:
                self.current_thread = None
                # Re-enable buttons on the main thread
                try:
                    self.master.after(0, self.enable_buttons)
                except Exception:
                    pass

        self.disable_buttons()
        t = threading.Thread(target=wrapper, daemon=True)
        self.current_thread = t
        t.start()
        return True


    def on_unlock(self):
        """Handle voice verification process."""
        try:
            import src.voice_unlock as voice_unlock
            
            def do_verify():
                if not voice_unlock._authorized_exists():
                    try:
                        self.master.after(0, self.set_status, "No authorized voice found. Please enroll first.")
                    except Exception:
                        pass
                    return
                # Perform verification in background thread
                result = voice_unlock.verify()
                # Hand result back to main thread for UI updates
                try:
                    self.master.after(0, self._handle_verification_result, result)
                except Exception:
                    pass

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
            # Notify launcher if provided
            try:
                if callable(getattr(self, "on_unlocked", None)):
                    # Ensure callback on main thread
                    self.master.after(0, self.on_unlocked)
            except Exception:
                pass
            self._unlock_journal()
        elif status == "denied":
            self.set_status(f"❌ Access Denied. Similarity: {score:.3f}")
        else:
            self.set_status(result.get("message", "Unknown result"))

    def _unlock_journal(self):
        """No-op: journal UI removed on background-only screen."""
        pass

    def run(self):
        """Start the application's main loop."""
        self.master.mainloop()


if __name__ == "__main__":
    App().run()