
BG_PINK = "#ffb6c1"
FG_PURPLE = "#800080"
BTN_PURPLE = "#c084fc"
ENTRY_BG = "#ffe4fa"
BLACK = "#000000"

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import datetime

NOTES_DIR = "notes"

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
                if hasattr(self, 'toc_listbox'):
                    self._populate_toc()
        else:
            messagebox.showwarning("No File", "No note is currently open.")
    def __init__(self, root):
        self.root = root
        self.root.title("Secret Journal")
        self.root.geometry("816x503")
        self.root.configure(bg=BG_PINK)
        self.line_spacing = 26

        # Custom fonts
        self.title_font = font.Font(family="Comic Sans MS", size=32, weight="bold")
        self.header_font = font.Font(family="Comic Sans MS", size=24, weight="bold")
        self.entry_font = font.Font(family="Comic Sans MS", size=16)
        self.journal_font = font.Font(family="Comic Sans MS", size=16)

        # Main frame for sidebar and content
        main_frame = tk.Frame(root, bg=BG_PINK)
        main_frame.pack(fill="both", expand=True)

        # Sidebar for table of contents
        sidebar = tk.Frame(main_frame, width=200, bg=BTN_PINK)
        sidebar.pack(side="left", fill="y")
        tk.Label(sidebar, text="Notes", font=("Comic Sans MS", 14, "bold"), fg=FG_PURPLE, bg=BTN_PINK).pack(pady=(10,0))
        self.toc_listbox = tk.Listbox(sidebar, font=("Comic Sans MS", 12), bg=ENTRY_BG, fg=FG_PURPLE, selectbackground=BTN_PURPLE, selectforeground=BG_PINK, borderwidth=0, highlightthickness=0)
        self.toc_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.toc_listbox.bind("<<ListboxSelect>>", self._on_toc_select)
        self._populate_toc()

        # Hover state for clickable items
        self._hover_item = None
        self._toc_id_to_name = {}
        self._action_id_to_handler = {}

        # Bindings on the background canvas (single surface)
        self.bg_canvas.bind("<Button-1>", self._on_click)
        self.bg_canvas.bind("<Motion>", self._on_mouse_move)
        self.bg_canvas.bind("<Leave>", self._on_mouse_leave)
        self.bg_canvas.bind("<Key>", self._on_key)
        self.bg_canvas.focus_set()
        self.root.after(10, lambda: (self._layout_on_canvas(), self._redraw_all()))

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
            borderwidth=0,
            highlightthickness=0,
        )
        self.text_window = self.paper_canvas.create_window(0, 0, anchor="nw", window=self.text_area)

        # Redraw lines on resize and ensure clicking canvas focuses the text area
        self.paper_canvas.bind("<Configure>", self._on_canvas_resize)
        self.paper_canvas.bind("<Button-1>", lambda e: self.text_area.focus_set())
        self.root.after(10, lambda: self._on_canvas_resize(None))

        # Initialize current file state
        self.current_file = None
    def _on_canvas_resize(self, event):
        w = self.paper_canvas.winfo_width()
        h = self.paper_canvas.winfo_height()
        # Make the text area fill the canvas
        self.paper_canvas.coords(self.text_window, 0, 0)
        if w > 0 and h > 0:
            self.paper_canvas.itemconfigure(self.text_window, width=w, height=h)
        # Draw/refresh notebook lines to span full width/height
        self._draw_notebook_lines()

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
        y = self._dy(self.editor_top) + baseline_offset
        if self.design_h:
            bottom_limit = min(h, int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, h - int(round(self.editor_bottom_margin * self._s)))
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
        # Draw text lines on bg_canvas with content offset
        content_x = self._dx(self.editor_left)
        line_y = self._dy(self.editor_top)
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        for i, line in enumerate(self._lines):
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

    def _draw_cursor(self):
        # Compute cursor pixel position
        content_x = self._dx(self.editor_left)
        x = content_x
        y = self._dy(self.editor_top) + self.cur_row * self.line_spacing
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
        # Editor click: set cursor
        content_x = self._dx(self.editor_left)
        top_y = self._dy(self.editor_top)
        if self.design_h:
            bottom_limit = min(self.bg_canvas.winfo_height(), int(round(self._dy(self.design_h - self.editor_bottom_margin))))
        else:
            bottom_limit = max(0, self.bg_canvas.winfo_height() - int(round(self.editor_bottom_margin * self._s)))
        if (y >= top_y) and (y < bottom_limit):
            row = max(0, min(int((y - top_y) // self.line_spacing), len(self._lines) - 1))
            line = self._lines[row]
            col = 0
            x_rel = max(0, x - content_x)
            for i in range(len(line) + 1):
                w = self.editor_font.measure(line[:i])
                if w >= x_rel:
                    col = i
                    break
                col = i
            self.cur_row, self.cur_col = row, col
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
    def _populate_toc(self):
        notes = [f for f in os.listdir(NOTES_DIR) if f.endswith('.md')]
        self._toc_items = sorted(notes)
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
                name, _ = os.path.splitext(base)
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, name)
                self.root.title(f"Simple Note App - {base}")


    def new_note(self):
        """Clears the text area for a new note and resets the name field."""
        self._set_text("")
        self.current_file = None
        self.root.title("Simple Note App - New Note")

    def open_note(self):
        """Opens a saved note from the notes folder and fills the name field."""
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
                self.root.title(f"Simple Note App - {os.path.basename(file_path)}")

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

        self.root.title(f"Secret Journal - {filename}")
        messagebox.showinfo("Saved", "Your note has been saved successfully.")
        # Refresh TOC after save
        self._populate_toc()

    def open_note(self):
        """Opens a saved note from the notes folder and fills the name field."""
        file_path = filedialog.askopenfilename(
            title="Open Note",
            initialdir=NOTES_DIR,
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                self.current_file = file_path
                # Set the name field to the filename (without extension)
                base = os.path.basename(file_path)
                name, _ = os.path.splitext(base)
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, name)
                self.root.title(f"Simple Note App - {base}")
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

if __name__ == "__main__":
    root = tk.Tk()
    app = NoteApp(root)
    app.run()
