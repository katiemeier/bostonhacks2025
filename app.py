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

        # Base design metrics for proportional scaling
        BASE_W, BASE_H = 816, 503

        # Load background image (prefer Pillow for smooth scaling)
        bg_path = os.path.join(os.path.dirname(__file__), "assets", "intro_screen.png")
        bg_item = None
        init_root._bg_base_pil = None
        init_root._bg_img_full = None  # For Tk-only scaling
        init_root._bg_img_ref = None   # Current PhotoImage reference to avoid GC
        try:
            if Image is not None and ImageTk is not None:
                init_root._bg_base_pil = Image.open(bg_path).convert("RGBA")
                try:
                    bw, bh = init_root._bg_base_pil.size
                    BASE_W, BASE_H = bw, bh
                    init_root.geometry(f"{bw}x{bh}")
                except Exception:
                    pass
                bg_item = canvas.create_image(0, 0, anchor="nw")  # image assigned during relayout
            else:
                # Tk fallback (we will approximate scaling via zoom/subsample)
                orig = tk.PhotoImage(master=init_root, file=bg_path)
                init_root._bg_img_full = orig
                init_root._bg_img_ref = orig
                try:
                    BASE_W, BASE_H = orig.width(), orig.height()
                    init_root.geometry(f"{BASE_W}x{BASE_H}")
                except Exception:
                    pass
                bg_item = canvas.create_image(0, 0, image=orig, anchor="nw")
        except Exception:
            init_root._bg_base_pil = None
            init_root._bg_img_full = None
            # Fallback plain background color
            init_root.configure(bg=INITIAL_BG)

        # Title/description/status as canvas text to avoid opaque label backgrounds
        base_title_size = 16
        base_desc_size = 10
        base_status_size = 10
        title_item = canvas.create_text(0, 0, text=INITIAL_TITLE, fill=TEXT_COLOR_TITLE,
                                        font=("Comic Sans MS", base_title_size, "bold"), anchor="n")
        desc_text = "Please set your voice password to protect your journal."
        desc_item = canvas.create_text(0, 0, text=desc_text, fill=TEXT_COLOR_DESC,
                                       font=("Comic Sans MS", base_desc_size), width=480, justify="center",
                                       anchor="n")
        status_item = canvas.create_text(0, 0, text="Ready", fill=TEXT_COLOR_STATUS,
                                         font=("Comic Sans MS", base_status_size), anchor="n")

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

        # Try to load the talk button image (store base to enable responsive scaling)
        talk_img = None
        talk_path = os.path.join(os.path.dirname(__file__), "assets", "talk_button.png")
        init_root._talk_base_pil = None
        init_root._talk_img_full = None
        init_root._talk_img_ref = None
        init_root._talk_base_size = (0, 0)
        try:
            if Image is not None and ImageTk is not None:
                pil_img = Image.open(talk_path).convert("RGBA")
                w, h = pil_img.size
                # Scale to 1/3 with high-quality resampling
                target = (max(1, w // 3), max(1, h // 3))
                pil_img = pil_img.resize(target, getattr(Image, 'Resampling', Image).LANCZOS)
                talk_img = ImageTk.PhotoImage(image=pil_img, master=init_root)
                # keep base for ongoing scaling
                init_root._talk_base_pil = Image.open(talk_path).convert("RGBA")
                # Store base size as 1/3 of original so resize is relative to this baseline
                init_root._talk_base_size = (max(1, w // 3), max(1, h // 3))
                init_root._talk_img_ref = talk_img
            else:
                # Fallback: use Tk PhotoImage and show at 1/3 via subsample; scale later via zoom/subsample
                orig = tk.PhotoImage(master=init_root, file=talk_path)
                talk_img = orig.subsample(3, 3)
                init_root._talk_img_full = orig
                init_root._talk_img_ref = talk_img
                # Store base size as 1/3 of original
                init_root._talk_base_size = (max(1, orig.width() // 3), max(1, orig.height() // 3))
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

        # Helper for Tk-only approximate scaling using zoom/subsample
        def _scale_photoimage_tk(orig: tk.PhotoImage, tw: int, th: int) -> tk.PhotoImage:
            try:
                bw, bh = max(1, orig.width()), max(1, orig.height())
                tw, th = max(1, tw), max(1, th)
                # Find integer p/r ~ tw/bw and q/s ~ th/bh
                def best_ratio(target, base):
                    best = (1, 1)
                    best_err = float('inf')
                    for p in range(1, 10):
                        for r in range(1, 10):
                            val = base * p / r
                            err = abs(val - target)
                            if err < best_err:
                                best_err = err
                                best = (p, r)
                    return best
                px, rx = best_ratio(tw, bw)
                py, ry = best_ratio(th, bh)
                img = orig.zoom(px, py)
                img = img.subsample(rx, ry)
                return img
            except Exception:
                return orig

        # Responsive layout: center elements on resize and scale assets proportionally
        def relayout(event=None):
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            cx = w // 2

            # Scale factor relative to base design
            s = min(max(w, 1) / max(BASE_W, 1), max(h, 1) / max(BASE_H, 1))

            # Background scaling
            if bg_item is not None:
                if init_root._bg_base_pil is not None and ImageTk is not None:
                    try:
                        scaled = init_root._bg_base_pil.resize((max(1, w), max(1, h)), getattr(Image, 'Resampling', Image).LANCZOS)
                        init_root._bg_img_ref = ImageTk.PhotoImage(scaled)
                        canvas.itemconfigure(bg_item, image=init_root._bg_img_ref)
                    except Exception:
                        pass
                elif getattr(init_root, "_bg_img_full", None) is not None:
                    try:
                        scaled = _scale_photoimage_tk(init_root._bg_img_full, max(1, w), max(1, h))
                        init_root._bg_img_ref = scaled
                        canvas.itemconfigure(bg_item, image=init_root._bg_img_ref)
                    except Exception:
                        pass
                canvas.coords(bg_item, 0, 0)

            # Fonts scaled with clamp
            def clamp_font(px):
                return max(8, min(48, int(round(px))))
            try:
                canvas.itemconfigure(title_item, font=("Comic Sans MS", clamp_font(base_title_size * s), "bold"))
                canvas.itemconfigure(desc_item, font=("Comic Sans MS", clamp_font(base_desc_size * s)))
                canvas.itemconfigure(status_item, font=("Comic Sans MS", clamp_font(base_status_size * s)))
            except Exception:
                pass

            # Description width ~ 60% of window, min 320, max w-40
            try:
                desc_w = max(320, min(w - 40, int(0.6 * w)))
                canvas.itemconfigure(desc_item, width=desc_w)
            except Exception:
                pass

            # Vertical layout positions with scaled spacers
            y = int(24 * s)
            canvas.coords(title_item, cx, y)
            y += int(36 * s)
            canvas.coords(desc_item, cx, y + int(25 * s))
            y += int(64 * s)
            # status_item will be positioned relative to the centered talk button below

            # Scale and position talk/enroll button image if applicable
            if init_root._talk_base_pil is not None and ImageTk is not None:
                try:
                    tbw, tbh = init_root._talk_base_size  # already 1/3 of original
                    tw = max(32, int(tbw * s))
                    th = max(32, int(tbh * s))
                    scaled_btn = init_root._talk_base_pil.resize((tw, th), getattr(Image, 'Resampling', Image).LANCZOS)
                    init_root._talk_img_ref = ImageTk.PhotoImage(scaled_btn)
                    canvas.itemconfigure(enroll_item, image=init_root._talk_img_ref)
                    init_root._talk_last_wh = (tw, th)
                except Exception:
                    pass
            elif getattr(init_root, "_talk_img_full", None) is not None:
                try:
                    # Base target is 1/3 of original
                    tbw = max(1, init_root._talk_img_full.width() // 3)
                    tbh = max(1, init_root._talk_img_full.height() // 3)
                    tw = max(32, int(tbw * s))
                    th = max(32, int(tbh * s))
                    scaled_btn = _scale_photoimage_tk(init_root._talk_img_full, tw, th)
                    init_root._talk_img_ref = scaled_btn
                    canvas.itemconfigure(enroll_item, image=init_root._talk_img_ref)
                    init_root._talk_last_wh = (tw, th)
                except Exception:
                    pass
            # Ensure the talk button is fixed at the center of the screen
            try:
                canvas.itemconfigure(enroll_item, anchor="center")
            except Exception:
                pass
            cy = h // 2
            canvas.coords(enroll_item, cx, cy)
            # Position status text centered, just below the talk button
            try:
                canvas.itemconfigure(status_item, anchor="n")
            except Exception:
                pass
            try:
                th = 48
                if hasattr(init_root, "_talk_last_wh") and isinstance(init_root._talk_last_wh, tuple):
                    th = max(th, int(init_root._talk_last_wh[1]))
                margin = max(12, int(16 * s))
                canvas.coords(status_item, cx, cy + th // 2 + margin)
            except Exception:
                pass
            # Close button near bottom with some padding that scales
            canvas.coords(close_item, cx, h - max(12, int(16 * s)))

        canvas.bind("<Configure>", relayout)
        # Initial layout after a tick so geometry is computed
        init_root.after(10, relayout)

        init_root.mainloop()

    def run(self):
        self.app.run()


if __name__ == "__main__":
    Launcher().run()
