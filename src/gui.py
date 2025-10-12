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
    # Base design size and normalized coordinates for key items
    BASE_WIDTH = 816
    BASE_HEIGHT = 503
    NORM_POS = {
        "unlock": (0.5, 0.5),
        "indicator": (460/816, 172/503),
        "red_off": (460/816, 360/503),
        "green_off": (460/816, 327/503),
    }
    # Delay after acceptance before opening notebook (ms)
    OPEN_NOTE_DELAY_MS = 800
    
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
        self._current_size = (w, h)
        self._base_size = (self.BASE_WIDTH, self.BASE_HEIGHT)
        self.canvas_main = tk.Canvas(self.master, width=w, height=h, highlightthickness=0, bd=0)
        self.canvas_main.place(x=0, y=0, width=w, height=h)
        # Hide OS cursor and draw a custom big purple pointer on the canvas
        try:
            self.canvas_main.configure(cursor="none")
        except Exception:
            pass
        self._custom_cursor_item = None
        # Load background and draw
        self._bg_item = None
        if _PIL_AVAILABLE:
            try:
                self._bg_base_pil = Image.open("assets/launch2.png").convert("RGBA")
                # Scale to current window
                bg_scaled = self._bg_base_pil.resize((w, h), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(bg_scaled)
                self._bg_item = self.canvas_main.create_image(0, 0, image=self.bg_image, anchor="nw")
            except Exception:
                self._bg_base_pil = None
                self.canvas_main.configure(bg=Colors.BG_MAIN)
        else:
            try:
                self.bg_image = tk.PhotoImage(file="assets/launch2.png")
                self._bg_item = self.canvas_main.create_image(0, 0, image=self.bg_image, anchor="nw")
            except Exception:
                # If image fails to load, use the themed background color
                self.canvas_main.configure(bg=Colors.BG_MAIN)
        # Manage clickability when using canvas items
        self._unlock_clickable = True
        # Draw static off-state lights (red, green) near the listening indicator position
        try:
            self._draw_off_lights()
        except Exception:
            pass

        # Bind resize to stretch and reposition assets
        try:
            self.master.bind("<Configure>", self._on_configure)
        except Exception:
            pass
        try:
            self.canvas_main.bind("<Motion>", self._on_mouse_motion)
            self.canvas_main.bind("<Leave>", self._on_mouse_leave)
        except Exception:
            pass


    def _create_center_unlock_button(self):
        """Create a centered unlock image on the canvas with click handling for transparent PNGs."""
        # Preferred: draw on the main canvas so PNG transparency shows the background
        if hasattr(self, "canvas_main") and self.canvas_main:
            try:
                # Load base unlock image and scale to initial size
                self._unlock_base_size = (98, 98)
                # Track pressed state
                self._unlock_pressed = False
                if _PIL_AVAILABLE:
                    try:
                        self._unlock_base_pil = Image.open("assets/talk_button.png").convert("RGBA")
                        # Also preload the pressed-state image
                        try:
                            self._unlock_pressed_base_pil = Image.open("assets/talk_button_depressed.png").convert("RGBA")
                        except Exception:
                            self._unlock_pressed_base_pil = None
                        uw, uh = self._unlock_base_size
                        scaled = self._unlock_base_pil.resize((uw, uh), Image.LANCZOS)
                        self.unlock_img = ImageTk.PhotoImage(scaled)
                        # Create a matching pressed image if available
                        if getattr(self, "_unlock_pressed_base_pil", None) is not None:
                            pressed_scaled = self._unlock_pressed_base_pil.resize((uw, uh), Image.LANCZOS)
                            self.unlock_img_pressed = ImageTk.PhotoImage(pressed_scaled)
                        else:
                            self.unlock_img_pressed = None
                    except Exception:
                        self._unlock_base_pil = None
                        self.unlock_img = self._load_unlock_image_scaled(98, 98)
                        # Fallback scale for pressed image
                        try:
                            self.unlock_img_pressed = self._load_scaled_image("assets/talk_button_depressed.png", 98, 98)
                        except Exception:
                            self.unlock_img_pressed = None
                else:
                    self._unlock_base_pil = None
                    self.unlock_img = self._load_unlock_image_scaled(98, 98)
                    # Fallback scale for pressed image
                    try:
                        self.unlock_img_pressed = self._load_scaled_image("assets/talk_button_depressed.png", 98, 98)
                    except Exception:
                        self.unlock_img_pressed = None
                try:
                    w, h = (int(x) for x in self.WINDOW_SIZE.split("x", 1))
                except Exception:
                    w, h = 816, 503
                self.unlock_item = self.canvas_main.create_image(
                    w // 2, h // 2, image=self.unlock_img, anchor="center", tags=("unlock",)
                )
                # Bind mouse interactions
                def _maybe_unlock(_evt=None):
                    # Set pressed visual immediately; revert happens on release
                    try:
                        self._set_unlock_pressed(True)
                    except Exception:
                        pass
                    if getattr(self, "_unlock_clickable", True):
                        self.on_unlock()
                self.canvas_main.tag_bind("unlock", "<Button-1>", _maybe_unlock)
                # Swap image on release back to normal (press handled above)
                self.canvas_main.tag_bind("unlock", "<ButtonRelease-1>", lambda e: self._set_unlock_pressed(False))
                self.canvas_main.tag_bind("unlock", "<Enter>", lambda e: self.master.configure(cursor="hand2"))
                self.canvas_main.tag_bind("unlock", "<Leave>", lambda e: self.master.configure(cursor=""))
                return
            except Exception:
                pass
        # Fallback: use a traditional Button with the image/text centered
        try:
            self.unlock_img = self._load_unlock_image_scaled(98, 98)
            # Try to load pressed image as well
            try:
                self.unlock_img_pressed = self._load_scaled_image("assets/talk_button_depressed.png", 98, 98)
            except Exception:
                self.unlock_img_pressed = None
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
            # Bind press/release to swap images if we have a pressed asset
            try:
                self.unlock_btn.bind("<ButtonPress-1>", lambda e: self._set_unlock_pressed(True))
                self.unlock_btn.bind("<ButtonRelease-1>", lambda e: self._set_unlock_pressed(False))
            except Exception:
                pass
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

    def _show_listening_indicator(self):
        """Show the yellow light indicator at fixed coordinates during listening."""
        try:
            if not hasattr(self, "canvas_main") or self.canvas_main is None:
                return
            # Avoid duplicating indicator
            if getattr(self, "_indicator_item", None):
                return
            path = "assets/yellowlight_on.png"
            # Prefer PhotoImage; use PIL when available for consistency
            if _PIL_AVAILABLE:
                try:
                    self._base_yellow_on_pil = getattr(self, "_base_yellow_on_pil", None) or Image.open(path).convert("RGBA")
                except Exception:
                    self._base_yellow_on_pil = None
                if self._base_yellow_on_pil is not None:
                    # Scale to current factor
                    cw, ch = self._current_size
                    s = min(cw / self.BASE_WIDTH, ch / self.BASE_HEIGHT)
                    w = max(1, int(self._base_yellow_on_pil.width * s))
                    h = max(1, int(self._base_yellow_on_pil.height * s))
                    self._indicator_image = ImageTk.PhotoImage(self._base_yellow_on_pil.resize((w, h), Image.LANCZOS))
                else:
                    self._indicator_image = None
            else:
                try:
                    self._indicator_image = tk.PhotoImage(file=path)
                except Exception:
                    self._indicator_image = None
            # Create image at exact requested coordinates
            if self._indicator_image is not None:
                nx, ny = self.NORM_POS["indicator"]
                cw, ch = self._current_size
                self._indicator_item = self.canvas_main.create_image(
                    nx * cw, ny * ch, image=self._indicator_image, anchor="center"
                )
            else:
                self._indicator_item = None
        except Exception:
            # Silently ignore if the asset is missing or fails to load
            self._indicator_item = None

    def _hide_listening_indicator(self):
        """Remove the listening indicator if present."""
        try:
            if getattr(self, "_indicator_item", None) and getattr(self, "canvas_main", None):
                try:
                    self.canvas_main.delete(self._indicator_item)
                except Exception:
                    pass
            self._indicator_item = None
            # Keep a reference to the image var, but allow GC later
            self._indicator_image = None
        except Exception:
            pass

    def _draw_off_lights(self):
        """Draw the red and green OFF lights on the canvas at fixed positions.

        Positions are set to form a horizontal trio with the yellow indicator at x=185.
        Red OFF at x=152, Yellow ON/OFF at x=185, Green OFF at x=218, y=452.
        """
        if not hasattr(self, "canvas_main") or self.canvas_main is None:
            return

        # Avoid duplicates
        if getattr(self, "_item_red_off", None) or getattr(self, "_item_green_off", None):
            return

        red_path = "assets/redlight_off.png"
        green_path = "assets/greenlight_off.png"
        red_on_path = "assets/redlight_on.png"
        green_on_path = "assets/greenlight_on.png"

        # Load images with PIL if available to preserve alpha
        try:
            if _PIL_AVAILABLE:
                red_img = Image.open(red_path).convert("RGBA")
                green_img = Image.open(green_path).convert("RGBA")
                # Store base PIL for scaling on resize
                self._base_red_off_pil = red_img
                self._base_green_off_pil = green_img
                self._img_red_off = ImageTk.PhotoImage(red_img)
                self._img_green_off = ImageTk.PhotoImage(green_img)
                # Preload the ON images for overlays
                try:
                    red_on_img = Image.open(red_on_path).convert("RGBA")
                    self._base_red_on_pil = red_on_img
                    self._img_red_on = ImageTk.PhotoImage(red_on_img)
                except Exception:
                    self._img_red_on = None
                    self._base_red_on_pil = None
                try:
                    green_on_img = Image.open(green_on_path).convert("RGBA")
                    self._base_green_on_pil = green_on_img
                    self._img_green_on = ImageTk.PhotoImage(green_on_img)
                except Exception:
                    self._img_green_on = None
                    self._base_green_on_pil = None
            else:
                self._img_red_off = tk.PhotoImage(file=red_path)
                self._img_green_off = tk.PhotoImage(file=green_path)
                try:
                    self._img_red_on = tk.PhotoImage(file=red_on_path)
                except Exception:
                    self._img_red_on = None
                try:
                    self._img_green_on = tk.PhotoImage(file=green_on_path)
                except Exception:
                    self._img_green_on = None
        except Exception:
            # If either image fails to load, silently skip drawing
            self._img_red_off = None
            self._img_green_off = None
            return

        try:
            nx, ny = self.NORM_POS["red_off"]
            cw, ch = self._current_size
            self._item_red_off = self.canvas_main.create_image(nx * cw, ny * ch, image=self._img_red_off, anchor="center")
        except Exception:
            self._item_red_off = None
        try:
            nx, ny = self.NORM_POS["green_off"]
            cw, ch = self._current_size
            self._item_green_off = self.canvas_main.create_image(nx * cw, ny * ch, image=self._img_green_off, anchor="center")
        except Exception:
            self._item_green_off = None

    def _on_mouse_motion(self, event):
        # Update the custom big purple pointer on the launcher canvas
        try:
            self._update_custom_pointer(event.x, event.y)
        except Exception:
            pass

    def _on_mouse_leave(self, event):
        # Hide the custom pointer when leaving
        try:
            if self._custom_cursor_item is not None:
                self.canvas_main.itemconfigure(self._custom_cursor_item, state="hidden")
        except Exception:
            pass

    def _update_custom_pointer(self, x: int, y: int):
        # Draw a large purple arrow-like cursor that scales with window
        try:
            cw, ch = self._current_size
            s = min(cw / self.BASE_WIDTH, ch / self.BASE_HEIGHT)
        except Exception:
            s = 1.0
        size = max(12, int(round(18 * s)))
        pts = [
            x, y,
            x - size, y + int(size*0.5),
            x - int(size*0.4), y + int(size*0.6),
            x - int(size*0.6), y + size,
            x - int(size*0.2), y + int(size*0.85),
            x - int(size*0.1), y + int(size*0.3),
        ]
        if self._custom_cursor_item is None:
            try:
                self._custom_cursor_item = self.canvas_main.create_polygon(
                    *pts, fill=Colors.TEXT_SUBTITLE, outline="#ffffff", width=2, tags=("__custom_cursor__",)
                )
                self.canvas_main.tag_raise(self._custom_cursor_item)
            except Exception:
                self._custom_cursor_item = None
        else:
            try:
                self.canvas_main.coords(self._custom_cursor_item, *pts)
                self.canvas_main.itemconfigure(self._custom_cursor_item, state="normal")
                self.canvas_main.tag_raise(self._custom_cursor_item)
            except Exception:
                pass

    def _ensure_green_on_image(self):
        """Ensure the green ON image is loaded for overlay."""
        if getattr(self, "_img_green_on", None) is not None:
            return True
        path = "assets/greenlight_on.png"
        try:
            if _PIL_AVAILABLE:
                img = Image.open(path).convert("RGBA")
                self._img_green_on = ImageTk.PhotoImage(img)
            else:
                self._img_green_on = tk.PhotoImage(file=path)
            return True
        except Exception:
            self._img_green_on = None
            return False

    def _show_green_light_on(self):
        """Show the green ON light over the green OFF position."""
        canvas = getattr(self, "canvas_main", None)
        base_item = getattr(self, "_item_green_off", None)
        if not canvas or not base_item:
            return
        if not self._ensure_green_on_image():
            return
        try:
            coords = canvas.coords(base_item)
            if not coords:
                return
            x, y = coords[0], coords[1]
        except Exception:
            return
        overlay = getattr(self, "_item_green_on_overlay", None)
        try:
            if overlay is None:
                self._item_green_on_overlay = canvas.create_image(
                    x, y, image=self._img_green_on, anchor="center", state="normal"
                )
                print("Created green ON overlay")
            else:
                canvas.coords(self._item_green_on_overlay, x, y)
                canvas.itemconfigure(self._item_green_on_overlay, image=self._img_green_on, state="normal")
        except Exception:
            return

    def _hide_green_light_on(self):
        """Hide the green ON overlay if shown."""
        canvas = getattr(self, "canvas_main", None)
        overlay = getattr(self, "_item_green_on_overlay", None)
        if not canvas or overlay is None:
            return
        try:
            canvas.itemconfigure(overlay, state="hidden")
        except Exception:
            pass

    def _ensure_red_on_image(self):
        """Ensure the red ON image is loaded for blinking."""
        if getattr(self, "_img_red_on", None) is not None:
            return True
        path = "assets/redlight_on.png"
        try:
            if _PIL_AVAILABLE:
                img = Image.open(path).convert("RGBA")
                self._img_red_on = ImageTk.PhotoImage(img)
            else:
                self._img_red_on = tk.PhotoImage(file=path)
            return True
        except Exception:
            self._img_red_on = None
            return False

    def _blink_red_light(self, times: int = 2, on_ms: int = 180, off_ms: int = 140):
        """Blink the red light ON image over the red OFF position.

        - Non-blocking UI using after(); safe to call multiple times.
        - If a blink is already in progress, it restarts the sequence.
        """
        # Validate canvas and base position
        canvas = getattr(self, "canvas_main", None)
        base_item = getattr(self, "_item_red_off", None)
        if not canvas or not base_item:
            return

        # Ensure ON image is available
        if not self._ensure_red_on_image():
            return

        # Determine coordinates of the OFF light to overlay exactly
        try:
            coords = canvas.coords(base_item)
            if not coords:
                return
            x, y = coords[0], coords[1]
        except Exception:
            return

        # Create (or move) an overlay item we can toggle hidden/normal
        overlay = getattr(self, "_item_red_on_overlay", None)
        try:
            if overlay is None:
                self._item_red_on_overlay = canvas.create_image(
                    x, y, image=self._img_red_on, anchor="center", state="hidden"
                )
            else:
                # Move overlay to correct position if needed and ensure correct image
                try:
                    canvas.coords(self._item_red_on_overlay, x, y)
                    canvas.itemconfigure(self._item_red_on_overlay, image=self._img_red_on)
                except Exception:
                    pass
        except Exception:
            return

        # Cancel any existing scheduled blink
        after_id = getattr(self, "_red_blink_after_id", None)
        if after_id is not None:
            try:
                self.master.after_cancel(after_id)
            except Exception:
                pass
            self._red_blink_after_id = None

        self._red_blinking = True

        total_steps = max(1, int(times)) * 2  # on/off pairs

        def step(i: int = 0):
            if i >= total_steps:
                # Ensure overlay is hidden at the end
                try:
                    canvas.itemconfigure(self._item_red_on_overlay, state="hidden")
                except Exception:
                    pass
                self._red_blinking = False
                self._red_blink_after_id = None
                return
            try:
                if i % 2 == 0:
                    # ON
                    canvas.itemconfigure(self._item_red_on_overlay, state="normal")
                    delay = on_ms
                else:
                    # OFF
                    canvas.itemconfigure(self._item_red_on_overlay, state="hidden")
                    delay = off_ms
            except Exception:
                # If something goes wrong, stop attempting
                self._red_blinking = False
                self._red_blink_after_id = None
                return
            # Schedule next toggle
            self._red_blink_after_id = self.master.after(delay, lambda: step(i + 1))

        # Start the sequence
        step(0)

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

    def _load_scaled_image(self, path: str, width: int, height: int):
        """Generic helper to load and scale an image to a PhotoImage.

        Attempts to use PIL for high-quality scaling; falls back to tk.PhotoImage with
        subsample approximation when PIL isn't available.
        """
        if _PIL_AVAILABLE:
            img = Image.open(path).convert("RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        base = tk.PhotoImage(file=path)
        bw, bh = base.width(), base.height()
        if bw <= 0 or bh <= 0:
            return base
        sx = max(1, round(bw / max(1, width)))
        sy = max(1, round(bh / max(1, height)))
        try:
            return base.subsample(sx, sy)
        except Exception:
            return base

    def _set_unlock_pressed(self, pressed: bool):
        """Update the talk button image to pressed or normal state."""
        self._unlock_pressed = bool(pressed)
        try:
            # Prefer canvas item if present
            if getattr(self, "unlock_item", None) is not None and getattr(self, "canvas_main", None) is not None:
                img = self.unlock_img_pressed if (self._unlock_pressed and getattr(self, "unlock_img_pressed", None)) else self.unlock_img
                if img is not None:
                    self.canvas_main.itemconfigure(self.unlock_item, image=img)
                return
            # Fallback Button widget
            if getattr(self, "unlock_btn", None) is not None:
                img = self.unlock_img_pressed if (self._unlock_pressed and getattr(self, "unlock_img_pressed", None)) else self.unlock_img
                if img is not None:
                    try:
                        self.unlock_btn.config(image=img)
                    except Exception:
                        pass
        except Exception:
            pass

    def show_locked_landing(self):
        """Show only the background; no welcome back splash screen."""
        self.clear_overlay_frames()
        # Removed welcome back splash screen UI elements

    def _on_configure(self, event):
        """Handle window resize/fullscreen: scale background and reposition assets proportionally."""
        try:
            new_w, new_h = int(event.width), int(event.height)
        except Exception:
            return
        if new_w <= 1 or new_h <= 1:
            return
        # Avoid unnecessary work if size unchanged
        cw, ch = getattr(self, "_current_size", (0, 0))
        if (new_w, new_h) == (cw, ch):
            return
        # Resize canvas to fill window
        try:
            self.canvas_main.place(x=0, y=0, width=new_w, height=new_h)
        except Exception:
            pass
        self._current_size = (new_w, new_h)
        self._rescale_and_reposition()

    def _rescale_and_reposition(self):
        """Rescale images with PIL when available and reposition to normalized coordinates."""
        cw, ch = self._current_size
        bx, by = self.BASE_WIDTH, self.BASE_HEIGHT
        s = min(cw / bx, ch / by)
        # Background
        try:
            if _PIL_AVAILABLE and getattr(self, "_bg_base_pil", None) is not None and getattr(self, "_bg_item", None) is not None:
                bg_scaled = self._bg_base_pil.resize((cw, ch), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(bg_scaled)
                self.canvas_main.itemconfigure(self._bg_item, image=self.bg_image)
            # Reposition background just in case
            if getattr(self, "_bg_item", None) is not None:
                self.canvas_main.coords(self._bg_item, 0, 0)
        except Exception:
            pass

        # Unlock button image scaling and position
        try:
            if getattr(self, "unlock_item", None) is not None:
                if _PIL_AVAILABLE and getattr(self, "_unlock_base_pil", None) is not None:
                    uw, uh = self._unlock_base_size if hasattr(self, "_unlock_base_size") else (98, 98)
                    tw, th = max(24, int(uw * s)), max(24, int(uh * s))
                    # Recreate both normal and pressed images at the new scale
                    scaled = self._unlock_base_pil.resize((tw, th), Image.LANCZOS)
                    self.unlock_img = ImageTk.PhotoImage(scaled)
                    if getattr(self, "_unlock_pressed_base_pil", None) is not None:
                        pressed_scaled = self._unlock_pressed_base_pil.resize((tw, th), Image.LANCZOS)
                        self.unlock_img_pressed = ImageTk.PhotoImage(pressed_scaled)
                    # Choose which to display based on current state
                    current_img = self.unlock_img_pressed if (getattr(self, "_unlock_pressed", False) and getattr(self, "unlock_img_pressed", None)) else self.unlock_img
                    self.canvas_main.itemconfigure(self.unlock_item, image=current_img)
                # Position to center
                nx, ny = self.NORM_POS["unlock"]
                self.canvas_main.coords(self.unlock_item, nx * cw, ny * ch)
        except Exception:
            pass

        # Lights (OFF)
        try:
            if getattr(self, "_item_red_off", None) is not None:
                nx, ny = self.NORM_POS["red_off"]
                self.canvas_main.coords(self._item_red_off, nx * cw, ny * ch)
                if _PIL_AVAILABLE and getattr(self, "_base_red_off_pil", None) is not None:
                    w = max(1, int(self._base_red_off_pil.width * s))
                    h = max(1, int(self._base_red_off_pil.height * s))
                    self._img_red_off = ImageTk.PhotoImage(self._base_red_off_pil.resize((w, h), Image.LANCZOS))
                    self.canvas_main.itemconfigure(self._item_red_off, image=self._img_red_off)
            if getattr(self, "_item_green_off", None) is not None:
                nx, ny = self.NORM_POS["green_off"]
                self.canvas_main.coords(self._item_green_off, nx * cw, ny * ch)
                if _PIL_AVAILABLE and getattr(self, "_base_green_off_pil", None) is not None:
                    w = max(1, int(self._base_green_off_pil.width * s))
                    h = max(1, int(self._base_green_off_pil.height * s))
                    self._img_green_off = ImageTk.PhotoImage(self._base_green_off_pil.resize((w, h), Image.LANCZOS))
                    self.canvas_main.itemconfigure(self._item_green_off, image=self._img_green_off)
        except Exception:
            pass

        # Indicator if present
        try:
            if getattr(self, "_indicator_item", None) is not None:
                nx, ny = self.NORM_POS["indicator"]
                self.canvas_main.coords(self._indicator_item, nx * cw, ny * ch)
                if _PIL_AVAILABLE and getattr(self, "_base_yellow_on_pil", None) is not None:
                    w = max(1, int(self._base_yellow_on_pil.width * s))
                    h = max(1, int(self._base_yellow_on_pil.height * s))
                    self._indicator_image = ImageTk.PhotoImage(self._base_yellow_on_pil.resize((w, h), Image.LANCZOS))
                    self.canvas_main.itemconfigure(self._indicator_item, image=self._indicator_image)
        except Exception:
            pass

        # Overlays for red/green ON if present
        try:
            if getattr(self, "_item_red_on_overlay", None) is not None:
                # Position overlay at red off
                nx, ny = self.NORM_POS["red_off"]
                self.canvas_main.coords(self._item_red_on_overlay, nx * cw, ny * ch)
                if _PIL_AVAILABLE and getattr(self, "_base_red_on_pil", None) is not None:
                    w = max(1, int(self._base_red_on_pil.width * s))
                    h = max(1, int(self._base_red_on_pil.height * s))
                    self._img_red_on = ImageTk.PhotoImage(self._base_red_on_pil.resize((w, h), Image.LANCZOS))
                    self.canvas_main.itemconfigure(self._item_red_on_overlay, image=self._img_red_on)
            if getattr(self, "_item_green_on_overlay", None) is not None:
                nx, ny = self.NORM_POS["green_off"]
                self.canvas_main.coords(self._item_green_on_overlay, nx * cw, ny * ch)
                if _PIL_AVAILABLE and getattr(self, "_base_green_on_pil", None) is not None:
                    w = max(1, int(self._base_green_on_pil.width * s))
                    h = max(1, int(self._base_green_on_pil.height * s))
                    self._img_green_on = ImageTk.PhotoImage(self._base_green_on_pil.resize((w, h), Image.LANCZOS))
                    self.canvas_main.itemconfigure(self._item_green_on_overlay, image=self._img_green_on)
        except Exception:
            pass


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

            # Show indicator before starting background verification
            try:
                self._show_listening_indicator()
            except Exception:
                pass

            def wrapped_verify():
                try:
                    do_verify()
                finally:
                    # Ensure indicator is hidden on completion
                    try:
                        self.master.after(0, self._hide_listening_indicator)
                    except Exception:
                        pass

            self.run_in_thread(wrapped_verify)
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
            # Show green ON light over the OFF position
            try:
                self._show_green_light_on()
            except Exception:
                pass
            # Notify launcher if provided
            try:
                if callable(getattr(self, "on_unlocked", None)):
                    # Ensure callback on main thread
                    self.master.after(self.OPEN_NOTE_DELAY_MS, self.on_unlocked)
            except Exception:
                pass
            self._unlock_journal()
        elif status == "denied":
            self.set_status(f"❌ Access Denied. Similarity: {score:.3f}")
            # Blink the red light twice to indicate denial
            try:
                self._blink_red_light(times=2)
            except Exception:
                pass
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