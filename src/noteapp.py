BG_PINK = "#ee95e3"
FG_PURPLE = "#7B157B"
BTN_PURPLE = "#c084fc"
ENTRY_BG = "#ffe4fa"
BLACK = "#000000"
SELECT_BG = "#ffd6ea"


import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import font as tkfont
from tkinter import ttk
try:
    from PIL import Image, ImageTk  # type: ignore
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False
import os
import datetime

NOTES_DIR = "notes"

# Ensure notes directory exists
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

class NoteApp:
    def delete_note(self):
        """Deletes the current note file from the notes folder."""
        if self.current_file and os.path.exists(self.current_file):
            confirm = messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?")
            if confirm:
                os.remove(self.current_file)
                self.new_note()
                messagebox.showinfo("Deleted", "Note deleted successfully.")
                # Refresh TOC after deletion
                self._populate_toc()
        else:
            messagebox.showwarning("No File", "No note is currently open.")
    def __init__(self, root):
        self.root = root
        self.root.title("My Diary")
        self.root.geometry("816x503")
        self.root.configure(bg=BG_PINK)
        # spacing between notebook lines (pixels)
        self.line_spacing = 26

        # Background canvas with Frame5.png
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self._bg_image_raw = None
        self._bg_image_tk = None
        # Uniform scaling state (design-space background size, scale and offsets)
        self.design_w = None
        self.design_h = None
        self._s = 1.0
        self._offx = 0.0
        self._offy = 0.0
        self._bg_img_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "Frame5.png"))
        self._load_background_image()
        # Repaint background and relayout on resize
        self.root.bind("<Configure>", self._on_root_resize)

        # Layout constants and state for canvas-based UI
        self.sidebar_width = 200
    # header_height removed (no explicit header container)
        # Editor content bounds: start typing at exact x=454; stop lines before right edge
        self.editor_left = 454
    # editor_right_margin removed (not used)
        # Vertical clip within Frame5.png page area
        self.editor_top = 120
        self.editor_bottom_margin = 40
        # Fixed right boundary for editor content and lines
        self.editor_right = 750
        # TOC (sidebar) design-space placement
        self.d_toc_x = 50
        self.d_toc_y = 100
        self.d_toc_line_h = 22
        self.action_buttons = []  # list of dicts: {label, bbox, handler}
        # Simple editor state (drawn on bg_canvas directly)
        self.editor_font = tkfont.Font(family="Comic Sans MS", size=16)
    # text margins removed (not used)
        # Align line spacing to font metrics so caret and notebook lines match
        try:
            self.line_spacing = int(self.editor_font.metrics("linespace") + 4)
        except Exception:
            # fallback if metrics not available
            self.line_spacing = 26
        self._lines = [""]
        self.cur_row = 0
        self.cur_col = 0
        # Selection state: (row, col) pairs or None
        self.sel_anchor = None  # type: tuple[int, int] | None
        self.sel_active = None  # type: tuple[int, int] | None

        # Scrolling state (vertical)
        self.scroll_y = 0  # vertical offset in pixels
        self._init_scrollbar_style()
        self.vscroll = ttk.Scrollbar(self.bg_canvas, orient="vertical", command=self._on_scrollbar, style="Pink.Vertical.TScrollbar")
        self.vscroll_window_id = None

        # TOC scrolling state (vertical)
        self.toc_scroll_y = 0  # vertical offset in pixels for the sidebar TOC
        self.toc_scroll = ttk.Scrollbar(self.bg_canvas, orient="vertical", command=self._on_toc_scrollbar, style="Pink.Vertical.TScrollbar")
        self.toc_scroll_window_id = None

        # Populate TOC items (filenames)
        self._toc_items = []
        self._populate_toc()

        # Hover state for clickable items
        self._hover_item = None
        self._toc_id_to_name = {}
        self._action_id_to_handler = {}

        # Bindings on the background canvas (single surface)
        self.bg_canvas.bind("<Button-1>", self._on_click)
        self.bg_canvas.bind("<B1-Motion>", self._on_drag_select)
        self.bg_canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.bg_canvas.bind("<Motion>", self._on_mouse_move)
        self.bg_canvas.bind("<Leave>", self._on_mouse_leave)
        self.bg_canvas.bind("<Key>", self._on_key)
        # Mouse wheel scroll (Windows)
        self.bg_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.bg_canvas.focus_set()
        self.root.after(10, lambda: (self._layout_on_canvas(), self._redraw_all()))

        # If the window was created with -fullscreen, keep it; otherwise, noop.
        try:
            if bool(self.root.attributes("-fullscreen")):
                # On some platforms, applying fullscreen twice ensures proper layout
                self.root.after(50, lambda: self.root.attributes("-fullscreen", True))
        except Exception:
            pass

        # Initialize current file state
        self.current_file = None

        # Inline Title widget state (independent from note content)
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(
            self.bg_canvas,
            textvariable=self.title_var,
            font=("Comic Sans MS", 14),
            bg=ENTRY_BG,
            fg=FG_PURPLE,
            insertbackground=FG_PURPLE,
            bd=1,
            relief="solid",
            width=30,
        )
        self.title_window_id = None
        # Note: Title is not synced with the note's first line.

    # Background handling
    def _load_background_image(self):
        try:
            if _PIL_AVAILABLE:
                self._bg_image_raw = Image.open(self._bg_img_path).convert("RGBA")
                try:
                    self.design_w, self.design_h = self._bg_image_raw.size
                except Exception:
                    self.design_w, self.design_h = None, None
            else:
                # Fallback: load base image for zoom/subsample scaling
                self._bg_image_base = tk.PhotoImage(file=self._bg_img_path)
                self._bg_image_tk = self._bg_image_base
                try:
                    self.design_w = self._bg_image_base.width()
                    self.design_h = self._bg_image_base.height()
                except Exception:
                    self.design_w, self.design_h = None, None
        except Exception as e:
            # If image fails to load, leave canvas with default bg
            self._bg_image_raw = None
            self._bg_image_tk = None
            self._bg_image_base = None
            self.design_w, self.design_h = None, None

    def _compute_scale(self, w: int, h: int):
        if not self.design_w or not self.design_h:
            self.design_w = max(1, w)
            self.design_h = max(1, h)
        dw, dh = self.design_w, self.design_h
        s = min(w / dw, h / dh)
        self._s = s
        self._offx = (w - dw * s) / 2.0
        self._offy = (h - dh * s) / 2.0

    def _dx(self, x: float) -> float:
        return self._offx + x * self._s

    def _dy(self, y: float) -> float:
        return self._offy + y * self._s

    def _init_scrollbar_style(self):
        # Configure a pink-themed vertical scrollbar using ttk
        try:
            style = ttk.Style()
            # Pick a theme with element support; 'clam' is reliable for styling
            try:
                style.theme_use('clam')
            except Exception:
                pass
            # Base colors
            pink = BG_PINK
            purple = FG_PURPLE
            trough = '#ffe9f7'
            hover = '#f5a6e8'
            pressed = '#e984d6'
            # Configure colors for the scrollbar elements
            style.configure(
                'Pink.Vertical.TScrollbar',
                troughcolor=trough,
                background=pink,
                bordercolor=pink,
                lightcolor=pink,
                darkcolor=pink,
                arrowcolor=purple
            )
            # Map dynamic states so hover/pressed slightly vary
            style.map(
                'Pink.Vertical.TScrollbar',
                background=[('active', hover), ('pressed', pressed)],
                arrowcolor=[('active', purple), ('pressed', purple)],
            )
        except Exception:
            # If styling fails, silently continue with default look
            pass

    def _apply_scaled_fonts(self):
        s = max(0.5, float(self._s))
        try:
            self.editor_font.configure(size=max(10, int(round(16 * s))))
        except Exception:
            pass
        try:
            # Create additional fonts lazily if not set
            if not hasattr(self, 'action_font'):
                self.action_font = tkfont.Font(family="Comic Sans MS", size=14, weight="bold")
            if not hasattr(self, 'toc_font'):
                self.toc_font = tkfont.Font(family="Comic Sans MS", size=12)
            if not hasattr(self, 'title_font'):
                self.title_font = tkfont.Font(family="Comic Sans MS", size=14, weight="bold")
            sz_action = max(8, int(round(14 * s)))
            # Make TOC font larger for readability
            sz_toc = max(10, int(round(16 * s)))
            self.action_font.configure(size=sz_action, weight="bold")
            self.title_font.configure(size=sz_action, weight="bold")
            self.toc_font.configure(size=sz_toc)
        except Exception:
            pass
        try:
            self.line_spacing = int(self.editor_font.metrics("linespace") + max(2, round(4 * s)))
        except Exception:
            self.line_spacing = max(16, int(round(26 * s)))
        # Compute TOC line spacing to avoid overlap (fallback to scaled default)
        try:
            self.toc_line_spacing = int(self.toc_font.metrics("linespace") + max(4, round(6 * s)))
        except Exception:
            self.toc_line_spacing = max(20, int(round((self.d_toc_line_h if hasattr(self, 'd_toc_line_h') else 22) * self._s)))

    def _draw_background(self, w: int, h: int):
        # Clear previous bg
        self.bg_canvas.delete("__bg__")
        if self._bg_image_raw and _PIL_AVAILABLE and w > 0 and h > 0:
            try:
                dw = self.design_w or w
                dh = self.design_h or h
                sw = max(1, int(round(dw * self._s)))
                sh = max(1, int(round(dh * self._s)))
                img = self._bg_image_raw.resize((sw, sh), Image.LANCZOS)
                self._bg_image_tk = ImageTk.PhotoImage(img)
                self.bg_canvas.create_image(self._offx, self._offy, image=self._bg_image_tk, anchor="nw", tags=("__bg__",))
                return
            except Exception:
                self._bg_image_tk = None
        elif getattr(self, "_bg_image_base", None) is not None and w > 0 and h > 0:
            # Approximate scaling using integer zoom/subsample to fill the canvas
            try:
                bw, bh = self._bg_image_base.width(), self._bg_image_base.height()
                if bw > 0 and bh > 0:
                    mul = 8
                    zx = max(1, int(round(self._s * mul)))
                    scaled = self._bg_image_base.zoom(zx, zx)
                    self._bg_image_tk = scaled.subsample(mul, mul)
                    self.bg_canvas.create_image(self._offx, self._offy, image=self._bg_image_tk, anchor="nw", tags=("__bg__",))
                    return
                else:
                    self._bg_image_tk = self._bg_image_base
            except Exception:
                self._bg_image_tk = self._bg_image_base

        if self._bg_image_tk:
            self.bg_canvas.create_image(self._offx, self._offy, image=self._bg_image_tk, anchor="nw", tags=("__bg__",))
        else:
            # fallback background color
            self.bg_canvas.configure(bg=BG_PINK)

    def _layout_on_canvas(self):
        try:
            self.bg_canvas.update_idletasks()
        except Exception:
            pass
        w = self.bg_canvas.winfo_width()
        h = self.bg_canvas.winfo_height()
        if w <= 0 or h <= 0:
            return
        # Redraw everything to fit new size
        self._redraw_all()

    def _on_root_resize(self, event):
        # Reposition canvas windows and redraw background
        self._layout_on_canvas()

    # ====== Drawing on the background canvas ======
    def _redraw_all(self):
        # Clear dynamic layers
        self.bg_canvas.delete("__bg__")
        self.bg_canvas.delete("toc")
        self.bg_canvas.delete("actions")
        self.bg_canvas.delete("notebook_line")
        self.bg_canvas.delete("selection")
        self.bg_canvas.delete("editor_text")
        self.bg_canvas.delete("cursor")

        w = self.bg_canvas.winfo_width()
        h = self.bg_canvas.winfo_height()
        if w <= 0 or h <= 0:
            return
        # Compute scale and apply font scaling
        self._compute_scale(w, h)
        self._apply_scaled_fonts()
        # Background image
        self._draw_background(w, h)
        # Clamp scroll and update scrollbar
        self._clamp_scroll()
        self._update_scrollbar()

        # Clamp TOC scroll and update its scrollbar
        self._clamp_toc_scroll()
        self._update_toc_scrollbar()

        # Sidebar title and items (text only, no backgrounds)
        self._draw_sidebar()

        # Actions in header area
        self._draw_actions()

        # Editor area
        self._redraw_editor()

    def _draw_sidebar(self):
        # Items (scaled from design coordinates) with TOC scrolling/clipping
        top_y = self._dy(self.d_toc_y)
        # Visible bottom limit aligned with editor's bottom margin for consistency
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        # Use dynamic TOC line spacing based on current font metrics
        line_h = getattr(self, 'toc_line_spacing', self.d_toc_line_h * self._s)
        xpad = self._dx(self.d_toc_x)
        # Start y based on scroll offset
        y = top_y - self.toc_scroll_y
        # Skip off-screen items above top boundary
        start_idx = 0
        if y < top_y and line_h > 0:
            steps = int((top_y - y + line_h - 1) // line_h)
            y += steps * line_h
            start_idx = steps
        self._toc_id_to_name = {}
        for idx in range(start_idx, len(self._toc_items)):
            if y >= bottom_limit:
                break
            name = self._toc_items[idx]
            # Display without extension, but keep mapping to the real filename
            try:
                display_name = os.path.splitext(name)[0]
            except Exception:
                display_name = name
            item_id = self.bg_canvas.create_text(
                xpad, y, text=display_name, font=self.toc_font, fill=FG_PURPLE, anchor="nw",
                tags=("toc", "toc_item", f"toc_index_{idx}")
            )
            self._toc_id_to_name[item_id] = name
            y += line_h

    def _draw_actions(self):
        # Render actions as clickable text; store hitboxes
        # Header actions (exclude 'Change Password' which will be placed above the TOC)
        labels = [
            ("New", self.new_note),
            ("Open", self.open_note),
            ("Save", self.save_note),
            ("Delete", self.delete_note),
        ]
        self.action_buttons = []
        self._action_id_to_handler = {}
        # Shift header action buttons slightly to the right (~10px in design space)
        x = self._dx(self.sidebar_width + 52)
        y = self._dy(12)
        spacing = 100 * self._s
        for label, handler in labels:
            # Create underlined action text with no background
            try:
                # Temporarily apply underline to action font
                self.action_font.configure(underline=1)
            except Exception:
                pass
            item_id = self.bg_canvas.create_text(
                x, y, text=label, font=self.action_font, fill=FG_PURPLE, anchor="nw",
                tags=("actions", "action_item", f"action_{label}")
            )
            # Reset underline after creating this item (font is shared)
            try:
                self.action_font.configure(underline=0)
            except Exception:
                pass
            bbox = self.bg_canvas.bbox(item_id)
            # Track action hitboxes/handlers
            self.action_buttons.append({"label": label, "bbox": bbox, "handler": handler, "item_id": item_id})
            self._action_id_to_handler[item_id] = handler
            x += spacing

        # Render the 'Change Password' action above the TOC in the sidebar
        cp_x = self._dx(self.d_toc_x)
        # Place it slightly above the first TOC item; lower a bit so it's below the New button height
        cp_y = self._dy(self.d_toc_y - 88)
        cp_item = self.bg_canvas.create_text(
            cp_x, cp_y, text="Change Password", font=self.action_font, fill=FG_PURPLE, anchor="nw",
            tags=("actions", "action_item", "action_Change Password")
        )
        cp_bbox = self.bg_canvas.bbox(cp_item)
        if cp_bbox is not None:
            pad_x = max(4, int(round(8 * self._s)))
            pad_y = max(2, int(round(4 * self._s)))
            rx1 = cp_bbox[0] - pad_x
            ry1 = cp_bbox[1] - pad_y
            rx2 = cp_bbox[2] + pad_x
            ry2 = cp_bbox[3] + pad_y
            cp_rect = self.bg_canvas.create_rectangle(
                rx1, ry1, rx2, ry2,
                fill=BG_PINK, outline="", tags=("actions", "action_bg", "action_bg_Change Password")
            )
            try:
                self.bg_canvas.tag_lower(cp_rect, cp_item)
            except Exception:
                pass
        # Track handler for the moved action
        self.action_buttons.append({"label": "Change Password", "bbox": cp_bbox, "handler": self.change_password, "item_id": cp_item})
        self._action_id_to_handler[cp_item] = self.change_password

        # Add a non-clickable Title label near the typing boundary (~454 px), moved up by 50px
        try:
            title_x = self._dx(self.editor_left)
        except Exception:
            title_x = self._dx(454)
        title_y = self._dy(12 + 50)
        title_item = self.bg_canvas.create_text(
            title_x, title_y, text="Title:", font=self.title_font, fill=BLACK, anchor="nw",
            tags=("actions", "title_label")
        )
        # Position the inline Entry to the right of the Title label
        tbbox = self.bg_canvas.bbox(title_item)
        if tbbox:
            entry_x = tbbox[2] + 10
        else:
            entry_x = title_x + 60 * self._s
        # Ensure the right end of the title box is at design x=700
        target_right = self._dx(700)
        entry_width_px = max(20, int(round(target_right - entry_x)))
        if self.title_window_id is None:
            self.title_window_id = self.bg_canvas.create_window(
                entry_x, title_y - 2, anchor="nw", window=self.title_entry, width=entry_width_px
            )
        else:
            self.bg_canvas.coords(self.title_window_id, entry_x, title_y - 2)
            try:
                self.bg_canvas.itemconfigure(self.title_window_id, width=entry_width_px)
            except Exception:
                pass
            try:
                self.bg_canvas.tag_raise(self.title_window_id)
            except Exception:
                pass

    def _draw_notebook_lines(self):
        # Remove previous lines
        self.bg_canvas.delete("notebook_line")
        # Canvas size
        w = self.bg_canvas.winfo_width()
        h = self.bg_canvas.winfo_height()
        if w <= 0 or h <= 0:
            return
        # Start lines at the text baseline for row 0 so they visually align
        try:
            baseline_offset = self.editor_font.metrics("ascent") + 2
        except Exception:
            baseline_offset = int(self.line_spacing * 0.75)
        content_x = self._dx(self.editor_left)
        top_y = self._dy(self.editor_top)
        y = top_y + baseline_offset - self.scroll_y
        if self.design_h:
            bottom_limit = min(h, int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, h - int(round(self.editor_bottom_margin * self._s)))
        # Ensure we don't draw lines above the top boundary: advance to first visible line
        if y < top_y:
            steps = int((top_y - y + self.line_spacing - 1) // self.line_spacing)
            y += steps * self.line_spacing
        while y < bottom_limit:
            right = min(self._dx(self.editor_right), w)
            self.bg_canvas.create_line(
                content_x, y, right, y, fill=BLACK, width=max(1, int(round(2 * self._s))), tags=("notebook_line",)
            )
            y += self.line_spacing
        # Keep lines behind text, but visible

    def _redraw_editor(self):
        # Clear previous text and cursor
        self.bg_canvas.delete("editor_text")
        self.bg_canvas.delete("cursor")
        # Draw lines first
        self._draw_notebook_lines()
        # Draw selection highlight behind text (if any)
        self._draw_selection()
        # Draw text lines on bg_canvas with content offset
        content_x = self._dx(self.editor_left)
        top_y = self._dy(self.editor_top)
        line_y = top_y - self.scroll_y
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        # Skip rows above the top boundary so text doesn't render outside the box
        start_idx = 0
        if line_y < top_y:
            start_idx = int((top_y - line_y + self.line_spacing - 1) // self.line_spacing)
            line_y += start_idx * self.line_spacing
        for i in range(start_idx, len(self._lines)):
            line = self._lines[i]
            if line_y >= bottom_limit:
                break
            self.bg_canvas.create_text(
                content_x,
                line_y,
                anchor="nw",
                text=line,
                font=self.editor_font,
                fill=FG_PURPLE,
                tags=("editor_text",),
            )
            line_y += self.line_spacing
        # Draw caret
        self._draw_cursor()

    # ====== Selection support ======
    def _has_selection(self) -> bool:
        return bool(self.sel_anchor and self.sel_active and self.sel_anchor != self.sel_active)

    def _clear_selection(self):
        self.sel_anchor = None
        self.sel_active = None
        try:
            self.bg_canvas.delete("selection")
        except Exception:
            pass

    def _normalized_selection(self):
        if not self._has_selection():
            return None
        (ar, ac) = self.sel_anchor  # type: ignore
        (br, bc) = self.sel_active  # type: ignore
        if (br, bc) < (ar, ac):
            return (br, bc), (ar, ac)
        return (ar, ac), (br, bc)

    def _draw_selection(self):
        if not self._has_selection():
            return
        norm = self._normalized_selection()
        if not norm:
            return
        (sr, sc), (er, ec) = norm
        content_x = self._dx(self.editor_left)
        top_y = self._dy(self.editor_top) - self.scroll_y
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        # Clamp selection drawing to start at top boundary
        line_y = top_y
        start_idx = 0
        if self.scroll_y > 0:
            # same computation as text: derive first visible row
            start_idx = int(self.scroll_y // self.line_spacing)
            line_y = top_y + (self.scroll_y - start_idx * self.line_spacing)
        for i in range(start_idx, len(self._lines)):
            line = self._lines[i]
            if line_y >= bottom_limit:
                break
            if sr <= i <= er:
                start_col = sc if i == sr else 0
                end_col = ec if i == er else len(line)
                if start_col != end_col:
                    x1 = content_x + self.editor_font.measure(line[: start_col])
                    x2 = content_x + self.editor_font.measure(line[: end_col])
                    y1 = line_y
                    y2 = line_y + self.line_spacing
                    try:
                        self.bg_canvas.create_rectangle(
                            x1, y1, x2, y2,
                            fill=SELECT_BG, outline="",
                            tags=("selection",)
                        )
                    except Exception:
                        pass
            line_y += self.line_spacing

    def _point_to_row_col(self, x: int, y: int):
        content_x = self._dx(self.editor_left)
        top_y = self._dy(self.editor_top)
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        # Constrain y within editor region
        if y < top_y:
            row = 0
        elif y >= bottom_limit:
            row = len(self._lines) - 1
        else:
            row = max(0, min(int((y - top_y + self.scroll_y) // self.line_spacing), len(self._lines) - 1))
        line = self._lines[row]
        col = 0
        x_rel = max(0, x - content_x)
        for i in range(len(line) + 1):
            w = self.editor_font.measure(line[:i])
            if w >= x_rel:
                col = i
                break
            col = i
        return row, col

    # ====== Scrolling support ======
    def _editor_view_heights(self):
        top_y = self._dy(self.editor_top)
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        return top_y, bottom_limit

    def _content_pixel_height(self):
        return max(0, len(self._lines) * self.line_spacing)

    def _max_scroll(self):
        top_y, bottom_limit = self._editor_view_heights()
        view_h = max(0, int(bottom_limit - top_y))
        content_h = self._content_pixel_height()
        return max(0, content_h - view_h)

    def _clamp_scroll(self):
        max_sc = self._max_scroll()
        if self.scroll_y < 0:
            self.scroll_y = 0
        elif self.scroll_y > max_sc:
            self.scroll_y = max_sc

    def _ensure_cursor_visible(self):
        # Adjust scroll so current row is visible
        top_y, bottom_limit = self._editor_view_heights()
        view_h = max(1, int(bottom_limit - top_y))
        cur_y = self.cur_row * self.line_spacing
        if cur_y < self.scroll_y:
            self.scroll_y = cur_y
        elif cur_y + self.line_spacing > self.scroll_y + view_h:
            self.scroll_y = cur_y + self.line_spacing - view_h
        self._clamp_scroll()

    def _on_mouse_wheel(self, event):
        # On Windows, event.delta is multiples of 120
        # Route wheel to TOC when cursor is over the sidebar TOC region; else scroll editor
        try:
            toc_top, toc_bottom = self._toc_view_heights()
            in_toc_x = event.x <= self._dx(self.sidebar_width)
            in_toc_y = toc_top <= event.y < toc_bottom
        except Exception:
            in_toc_x = False
            in_toc_y = False
        if in_toc_x and in_toc_y:
            step_toc = max(1, int(getattr(self, 'toc_line_spacing', 20) // 2))
            self.toc_scroll_y += -int(event.delta / 120) * step_toc
            self._clamp_toc_scroll()
            self._update_toc_scrollbar()
            # Redraw only sidebar and actions (actions unaffected, but safe); simplest: redraw all
            self._redraw_all()
        else:
            step = max(1, int(self.line_spacing // 2))
            self.scroll_y += -int(event.delta / 120) * step
            self._clamp_scroll()
            self._update_scrollbar()
            self._redraw_editor()

    def _on_scrollbar(self, *args):
        if not args:
            return
        cmd = args[0]
        if cmd == 'moveto' and len(args) > 1:
            try:
                frac = float(args[1])
            except Exception:
                frac = 0.0
            self.scroll_y = int(round(frac * self._max_scroll()))
        elif cmd == 'scroll' and len(args) > 2:
            try:
                amt = int(args[1])
            except Exception:
                amt = 0
            what = args[2]
            if what == 'units':
                self.scroll_y += amt * max(1, int(self.line_spacing // 2))
            elif what == 'pages':
                top_y, bottom_limit = self._editor_view_heights()
                view_h = max(1, int(bottom_limit - top_y))
                self.scroll_y += amt * view_h
        self._clamp_scroll()
        self._update_scrollbar()
        self._redraw_editor()

    def _update_scrollbar(self):
        # Position the scrollbar to the right of the editor area and update thumb
        top_y, bottom_limit = self._editor_view_heights()
        # Scale the horizontal inset so it resizes with the UI
        x = self._dx(self.editor_right) + int(round(6 * self._s))
        h = max(10, int(bottom_limit - top_y))
        # Scale the scrollbar width so it resizes with the UI
        try:
            sb_width = max(8, int(round(12 * self._s)))
            self.vscroll.configure(width=sb_width)
        except Exception:
            pass
        if self.vscroll_window_id is None:
            self.vscroll_window_id = self.bg_canvas.create_window(
                x, top_y, anchor='nw', window=self.vscroll, height=h
            )
        else:
            self.bg_canvas.coords(self.vscroll_window_id, x, top_y)
            try:
                self.bg_canvas.itemconfigure(self.vscroll_window_id, height=h)
            except Exception:
                pass
        content_h = self._content_pixel_height()
        view_h = max(1, int(bottom_limit - top_y))
        if content_h <= 0:
            first, last = 0.0, 1.0
        else:
            first = self.scroll_y / content_h
            last = min(1.0, (self.scroll_y + view_h) / content_h)
        try:
            self.vscroll.set(first, last)
        except Exception:
            pass

    # ====== TOC Scrolling support ======
    def _toc_view_heights(self):
        top_y = self._dy(self.d_toc_y)
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        return top_y, bottom_limit

    def _toc_content_pixel_height(self):
        line_h = getattr(self, 'toc_line_spacing', max(20, int(round(self.d_toc_line_h * self._s))))
        return max(0, len(self._toc_items) * line_h)

    def _toc_max_scroll(self):
        top_y, bottom_limit = self._toc_view_heights()
        view_h = max(0, int(bottom_limit - top_y))
        content_h = self._toc_content_pixel_height()
        return max(0, content_h - view_h)

    def _clamp_toc_scroll(self):
        max_sc = self._toc_max_scroll()
        if self.toc_scroll_y < 0:
            self.toc_scroll_y = 0
        elif self.toc_scroll_y > max_sc:
            self.toc_scroll_y = max_sc

    def _on_toc_scrollbar(self, *args):
        if not args:
            return
        cmd = args[0]
        if cmd == 'moveto' and len(args) > 1:
            try:
                frac = float(args[1])
            except Exception:
                frac = 0.0
            self.toc_scroll_y = int(round(frac * self._toc_max_scroll()))
        elif cmd == 'scroll' and len(args) > 2:
            try:
                amt = int(args[1])
            except Exception:
                amt = 0
            what = args[2]
            if what == 'units':
                step = max(1, int(getattr(self, 'toc_line_spacing', 20) // 2))
                self.toc_scroll_y += amt * step
            elif what == 'pages':
                top_y, bottom_limit = self._toc_view_heights()
                view_h = max(1, int(bottom_limit - top_y))
                self.toc_scroll_y += amt * view_h
        self._clamp_toc_scroll()
        self._update_toc_scrollbar()
        self._redraw_all()

    def _update_toc_scrollbar(self):
        # Position the TOC scrollbar at the right edge of the sidebar and update thumb
        top_y, bottom_limit = self._toc_view_heights()
        # Pin the scrollbar's right edge to design-space x=376 (scaled to canvas)
        x = self._dx(376)
        h = max(10, int(bottom_limit - top_y))
        # Scale the scrollbar width so it resizes with the UI
        try:
            sb_width = max(8, int(round(12 * self._s)))
            self.toc_scroll.configure(width=sb_width)
        except Exception:
            pass
        if self.toc_scroll_window_id is None:
            self.toc_scroll_window_id = self.bg_canvas.create_window(
                x, top_y, anchor='ne', window=self.toc_scroll, height=h
            )
        else:
            self.bg_canvas.coords(self.toc_scroll_window_id, x, top_y)
            try:
                self.bg_canvas.itemconfigure(self.toc_scroll_window_id, height=h)
            except Exception:
                pass
        content_h = self._toc_content_pixel_height()
        view_h = max(1, int(bottom_limit - top_y))
        if content_h <= 0:
            first, last = 0.0, 1.0
        else:
            first = self.toc_scroll_y / content_h
            last = min(1.0, (self.toc_scroll_y + view_h) / content_h)
        try:
            self.toc_scroll.set(first, last)
        except Exception:
            pass

    def _on_drag_select(self, event):
        # Update active selection during mouse drag
        row, col = self._point_to_row_col(event.x, event.y)
        if self.sel_anchor is None:
            self.sel_anchor = (row, col)
        self.sel_active = (row, col)
        self.cur_row, self.cur_col = row, col
        self._redraw_editor()

    def _on_mouse_up(self, event):
        # Finalize selection on mouse release
        if self.sel_anchor is None:
            return
        row, col = self._point_to_row_col(event.x, event.y)
        self.sel_active = (row, col)
        self.cur_row, self.cur_col = row, col
        self._redraw_editor()

    def change_password(self):
        """Show a pink "Listening..." popup and re-record the voice password without freezing UI."""
        try:
            import src.voice_unlock as voice_unlock
        except Exception:
            messagebox.showerror("Change Password", "Voice module not found. Please ensure dependencies are installed.")
            return

        # Create a centered, minimal pink popup indicating listening
        popup = tk.Toplevel(self.root)
        popup.transient(self.root)
        popup.title("Change Password")
        try:
            popup.configure(bg=BG_PINK)
        except Exception:
            pass
        msg = tk.Label(popup, text="Listening...", font=("Cosmic Sans MS", 20, "bold"), fg=FG_PURPLE, bg=BG_PINK)
        msg.pack(padx=30, pady=30)
        popup.update_idletasks()
        try:
            # Center over parent
            px = self.root.winfo_rootx()
            py = self.root.winfo_rooty()
            pw = self.root.winfo_width()
            ph = self.root.winfo_height()
            w = popup.winfo_reqwidth()
            h = popup.winfo_reqheight()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            popup.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass
        try:
            popup.grab_set()
        except Exception:
            pass

        def worker():
            success = False
            err = None
            try:
                success = bool(voice_unlock.enroll())
            except Exception as e:
                err = str(e)

            def finish():
                try:
                    popup.destroy()
                except Exception:
                    pass
                if success:
                    messagebox.showinfo("Change Password", "Your new voice password has been recorded.")
                else:
                    msg = "Could not record a new voice password."
                    if err:
                        msg = f"{msg}\n{err}"
                    messagebox.showerror("Change Password", msg)

            # Return to UI thread
            try:
                self.root.after(0, finish)
            except Exception:
                finish()

        # Run enrollment in the background to keep UI responsive
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _draw_cursor(self):
        # Compute cursor pixel position
        content_x = self._dx(self.editor_left)
        x = content_x
        top_y = self._dy(self.editor_top)
        y = top_y - self.scroll_y + self.cur_row * self.line_spacing
        # If cursor would be above the top, clamp to top so it doesn't draw outside
        if y < top_y:
            y = top_y
        if 0 <= self.cur_row < len(self._lines):
            prefix = self._lines[self.cur_row][: self.cur_col]
            x += self.editor_font.measure(prefix)
        # Caret as a vertical line
        self.bg_canvas.create_line(
            x,
            y + 2,
            x,
            y + self.line_spacing - 4,
            fill=FG_PURPLE,
            width=max(1, int(round(2 * self._s))),
            tags=("cursor",),
        )

    def _on_click(self, event):
        # Focus canvas to receive key events
        self.bg_canvas.focus_set()
        x, y = event.x, event.y
        # Prefer item-id based targeting for accuracy
        item = self._find_clickable_item_at(x, y)
        if item:
            tags = self.bg_canvas.gettags(item)
            if "action_item" in tags:
                handler = self._action_id_to_handler.get(item)
                if handler:
                    handler()
                    return
            if "toc_item" in tags:
                name = self._toc_id_to_name.get(item)
                if name:
                    self._open_note_by_name(name)
                    return
        # Editor click: set caret and start selection anchor
        row, col = self._point_to_row_col(x, y)
        self.cur_row, self.cur_col = row, col
        self.sel_anchor = (row, col)
        self.sel_active = (row, col)
        self._redraw_editor()

    def _find_clickable_item_at(self, x: int, y: int):
        # Return top-most clickable item id at x,y or None
        ids = self.bg_canvas.find_overlapping(x, y, x, y)
        for item in reversed(ids):  # last is top-most
            tags = self.bg_canvas.gettags(item)
            if tags and ("action_item" in tags or "toc_item" in tags):
                return item
        return None

    def _on_mouse_move(self, event):
        item = self._find_clickable_item_at(event.x, event.y)
        if item != getattr(self, "_hover_item", None):
            self._clear_hover()
            if item:
                self._apply_hover(item)
                self._hover_item = item
                self.bg_canvas.configure(cursor="hand2")
            else:
                self.bg_canvas.configure(cursor="")

    def _on_mouse_leave(self, event):
        self._clear_hover()
        self.bg_canvas.configure(cursor="")

    def _clear_hover(self):
        item = getattr(self, "_hover_item", None)
        if item and self._canvas_item_exists(item):
            tags = self.bg_canvas.gettags(item)
            # Reset to default color
            try:
                self.bg_canvas.itemconfigure(item, fill=FG_PURPLE)
            except Exception:
                pass
        self._hover_item = None

    def _apply_hover(self, item):
        # Apply a highlight color when hovering
        try:
            self.bg_canvas.itemconfigure(item, fill=BTN_PURPLE)
        except Exception:
            pass

    def _canvas_item_exists(self, item_id: int) -> bool:
        try:
            return item_id in self.bg_canvas.find_all()
        except Exception:
            return False

    def _on_key(self, event):
        ks = event.keysym
        ch = event.char
        # Navigation
        if ks in ("BackSpace", "Delete"):
            if self._has_selection():
                self._delete_selection()
                self._redraw_editor()
                return "break"
        if ks == "Left":
            self._clear_selection()
            if self.cur_col > 0:
                self.cur_col -= 1
            elif self.cur_row > 0:
                self.cur_row -= 1
                self.cur_col = len(self._lines[self.cur_row])
        elif ks == "Right":
            self._clear_selection()
            if self.cur_col < len(self._lines[self.cur_row]):
                self.cur_col += 1
            elif self.cur_row < len(self._lines) - 1:
                self.cur_row += 1
                self.cur_col = 0
        elif ks == "Up":
            self._clear_selection()
            if self.cur_row > 0:
                self.cur_row -= 1
                self.cur_col = min(self.cur_col, len(self._lines[self.cur_row]))
        elif ks == "Down":
            self._clear_selection()
            if self.cur_row < len(self._lines) - 1:
                self.cur_row += 1
                self.cur_col = min(self.cur_col, len(self._lines[self.cur_row]))
        elif ks in ("Prior", "Page_Up"):
            # Page up: move up by visible rows
            top_y, bottom_limit = self._editor_view_heights()
            rows = max(1, int((bottom_limit - top_y) // self.line_spacing))
            self.cur_row = max(0, self.cur_row - rows)
        elif ks in ("Next", "Page_Down"):
            # Page down: move down by visible rows
            top_y, bottom_limit = self._editor_view_heights()
            rows = max(1, int((bottom_limit - top_y) // self.line_spacing))
            self.cur_row = min(len(self._lines) - 1, self.cur_row + rows)
        elif ks in ("BackSpace",):
            if self._has_selection():
                self._delete_selection()
            elif self.cur_col > 0:
                line = self._lines[self.cur_row]
                self._lines[self.cur_row] = line[: self.cur_col - 1] + line[self.cur_col :]
                self.cur_col -= 1
            elif self.cur_row > 0:
                # merge with previous line
                prev_len = len(self._lines[self.cur_row - 1])
                self._lines[self.cur_row - 1] += self._lines[self.cur_row]
                del self._lines[self.cur_row]
                self.cur_row -= 1
                self.cur_col = prev_len
            self._clear_selection()
        elif ks in ("Delete",):
            if self._has_selection():
                self._delete_selection()
            else:
                line = self._lines[self.cur_row]
                if self.cur_col < len(line):
                    self._lines[self.cur_row] = line[: self.cur_col] + line[self.cur_col + 1:]
                elif self.cur_row < len(self._lines) - 1:
                    # merge with next line
                    self._lines[self.cur_row] += self._lines[self.cur_row + 1]
                    del self._lines[self.cur_row + 1]
        elif ks in ("Return", "KP_Enter"):
            if self._has_selection():
                self._delete_selection()
            line = self._lines[self.cur_row]
            left, right = line[: self.cur_col], line[self.cur_col :]
            self._lines[self.cur_row] = left
            self._lines.insert(self.cur_row + 1, right)
            self.cur_row += 1
            self.cur_col = 0
        elif ch and ch >= " " and ch != "\x7f":
            # printable character
            if self._has_selection():
                self._delete_selection()
            line = self._lines[self.cur_row]
            self._lines[self.cur_row] = line[: self.cur_col] + ch + line[self.cur_col :]
            self.cur_col += 1
            # Enforce wrapping within editor bounds
            self._wrap_line_at(self.cur_row)
        else:
            return "break"
        # Keep caret in view and update scrollbar
        self._ensure_cursor_visible()
        self._update_scrollbar()
        self._redraw_editor()

    def _delete_selection(self):
        norm = self._normalized_selection()
        if not norm:
            return
        (sr, sc), (er, ec) = norm
        if sr == er:
            line = self._lines[sr]
            self._lines[sr] = line[:sc] + line[ec:]
        else:
            first = self._lines[sr][:sc]
            last = self._lines[er][ec:]
            self._lines[sr] = first + last
            # delete lines between sr+1 and er inclusive
            del self._lines[sr + 1 : er + 1]
        self.cur_row, self.cur_col = sr, sc
        self._clear_selection()

    
    def _populate_toc(self):
        notes = [f for f in os.listdir(NOTES_DIR) if f.endswith('.md')]
        self._toc_items = sorted(notes)
        # Reset/clamp TOC scroll to reflect new content
        self._clamp_toc_scroll()
        try:
            self._update_toc_scrollbar()
        except Exception:
            pass
        # Redraw to reflect new list
        try:
            self._redraw_all()
        except Exception:
            pass

    def _on_toc_select(self, event):
        # Not used in canvas-based sidebar
        pass

    def _open_note_by_name(self, filename):
        file_path = os.path.join(NOTES_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self._set_text(content)
                self.current_file = file_path
                base = os.path.basename(file_path)
                self.root.title(f"My Diary - {base}")
                # Set title box from filename (without extension)
                try:
                    name_wo_ext = os.path.splitext(base)[0]
                except Exception:
                    name_wo_ext = base
                self.title_var.set(name_wo_ext)


    def new_note(self):
        """Clears the text area for a new note and resets the name field."""
        self._set_text("")
        self.current_file = None
        self.root.title("My Diary - New Note")
        self.title_var.set("")

    def open_note(self):
        """Opens a saved note from the notes folder."""
        file_path = filedialog.askopenfilename(
            title="Open Note",
            initialdir=NOTES_DIR,
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self._set_text(content)
                self.current_file = file_path
                base = os.path.basename(file_path)
                self.root.title(f"My Diary - {base}")
                # Set title box from filename (without extension)
                try:
                    name_wo_ext = os.path.splitext(base)[0]
                except Exception:
                    name_wo_ext = base
                self.title_var.set(name_wo_ext)

    def save_note(self):
        """Saves the note to the notes folder.

        The filename is derived from the Title box (max 40 chars),
        or falls back to a timestamp. Always uses .md extension.
        """
        # Derive note name: use Title box, else timestamp
        raw_title = (self.title_var.get() or "").strip()
        # Normalize single-line title
        raw_title = raw_title.replace("\n", " ")
        note_name = raw_title[:40] if raw_title else ""
        if not note_name:
            note_name = datetime.datetime.now().strftime("note_%Y%m%d_%H%M%S")
        # Remove invalid filename characters
        note_name = "".join(c for c in note_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        # Ensure .md extension
        if not note_name.lower().endswith('.md'):
            filename = f"{note_name}.md"
        else:
            filename = note_name
        self.current_file = os.path.join(NOTES_DIR, filename)

        with open(self.current_file, "w", encoding="utf-8") as file:
            file.write(self._get_text().strip())

        self.root.title(f"My Diary - {filename}")
        messagebox.showinfo("Saved", "Your note has been saved successfully.")
        # Refresh TOC after save
        self._populate_toc()

    # Removed second open_note variant; single method remains

    # Editor helpers
    def _set_text(self, text: str):
        lines = text.split("\n") if text else [""]
        if not lines:
            lines = [""]
        # Wrap incoming text to fit editor width
        wrapped: list[str] = []
        for ln in lines:
            wrapped.extend(self._wrap_text_to_width(ln))
        if not wrapped:
            wrapped = [""]
        self._lines = wrapped
        self.cur_row = 0
        self.cur_col = 0
        self.scroll_y = 0
        self._clear_selection()
        self._update_scrollbar()
        self._redraw_editor()

    def _get_text(self) -> str:
        return "\n".join(self._lines)

    # ====== Wrapping helpers ======
    def _max_text_width(self) -> int:
        # Current pixel width between scaled editor left and right bounds
        return max(0, int(round((self.editor_right - self.editor_left) * getattr(self, "_s", 1.0))))

    def _wrap_text_to_width(self, text_line: str) -> list[str]:
        """Wrap a single line of text to fit within the editor width by measuring pixels.
        Tries to wrap on spaces; if no space, performs a hard break.
        """
        maxw = self._max_text_width()
        if maxw <= 0:
            return [text_line]
        out = []
        s = text_line
        while s:
            # If it already fits, append and stop
            if self.editor_font.measure(s) <= maxw:
                out.append(s)
                break
            # Find the largest prefix that fits
            lo, hi = 0, len(s)
            fit = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if self.editor_font.measure(s[:mid]) <= maxw:
                    fit = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            # Try to wrap at last space before fit
            break_at = s.rfind(" ", 0, max(1, fit))
            if break_at <= 0:
                break_at = max(1, fit)
            out.append(s[:break_at].rstrip())
            s = s[break_at:].lstrip()
        if not out:
            out = [""]
        return out

    def _wrap_line_at(self, row: int):
        """Ensure the line at index row fits; wrap overflow to subsequent lines.
        Adjusts current cursor position if it falls into wrapped segments.
        """
        if row < 0 or row >= len(self._lines):
            return
        maxw = self._max_text_width()
        if maxw <= 0:
            return
        line = self._lines[row]
        # If it fits, nothing to do
        if self.editor_font.measure(line) <= maxw:
            return
        # Wrap this line into segments
        segments = self._wrap_text_to_width(line)
        # Replace current line and insert the rest
        self._lines[row] = segments[0]
        for i, seg in enumerate(segments[1:], start=1):
            self._lines.insert(row + i, seg)
        # Adjust cursor if it exceeds first segment
        if self.cur_row == row:
            # Recompute cur_col relative to first segment length
            first_len = len(self._lines[row])
            if self.cur_col > first_len:
                remaining = self.cur_col - first_len
                self.cur_row = row + 1
                self.cur_col = min(remaining, len(self._lines[self.cur_row]))

    

if __name__ == "__main__":
    print("App started")
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()
