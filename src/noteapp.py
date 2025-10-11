BG_PINK = "#ffb6c1"
FG_PURPLE = "#800080"
BTN_PINK = "#ff69b4"
BTN_PURPLE = "#c084fc"
ENTRY_BG = "#ffe4fa"
TEXT_BG = "#f3c4fb"
BLACK = "#000000"


import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import font as tkfont
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
                if hasattr(self, 'toc_listbox'):
                    self._populate_toc()
        else:
            messagebox.showwarning("No File", "No note is currently open.")
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Note App")
        self.root.geometry("816x503")
        self.root.configure(bg=BG_PINK)
        # spacing between notebook lines (pixels)
        self.line_spacing = 26

        # Main frame for sidebar and content
        main_frame = tk.Frame(root, bg=BG_PINK)
        main_frame.pack(fill="both", expand=True)

        # Sidebar for table of contents
        sidebar = tk.Frame(main_frame, width=200, bg=BTN_PINK)
        sidebar.pack(side="left", fill="y")
        tk.Label(sidebar, text="Entries", font=("Comic Sans MS", 20, "bold"), fg=FG_PURPLE, bg=BTN_PINK).pack(pady=(10,0))
        self.toc_listbox = tk.Listbox(sidebar, font=("Comic Sans MS", 12), bg=ENTRY_BG, fg=FG_PURPLE, selectbackground=BTN_PURPLE, selectforeground=BG_PINK, borderwidth=0, highlightthickness=0)
        self.toc_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.toc_listbox.bind("<<ListboxSelect>>", self._on_toc_select)
        self._populate_toc()

        # Content frame for note entry and text
        content_frame = tk.Frame(main_frame, bg=BG_PINK)
        content_frame.pack(side="left", fill="both", expand=True)

        name_frame = tk.Frame(content_frame, bg=BG_PINK)
        name_frame.pack(fill="x", pady=(10,0))
        tk.Label(name_frame, text="Title:", font=("Comic Sans MS", 20, "bold"), fg=FG_PURPLE, bg=BG_PINK).pack(side="left", padx=(10,5))
        self.name_entry = tk.Entry(name_frame, font=("Comic Sans MS", 14), width=30, bg=ENTRY_BG, fg=FG_PURPLE, insertbackground=FG_PURPLE)
        self.name_entry.pack(side="left", padx=(0,10))

        # Create frame for buttons
        button_frame = tk.Frame(content_frame, bg=BG_PINK)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="New", width=10, command=self.new_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Open", width=10, command=self.open_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Save", width=10, command=self.save_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", width=10, command=self.delete_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)

        # Canvas for notebook and a simple editor
        self.paper_canvas = tk.Canvas(content_frame, bg=TEXT_BG, highlightthickness=0)
        self.paper_canvas.pack(expand=True, fill="both", padx=0, pady=0)

        # Simple canvas-based editor state
        self.editor_font = tkfont.Font(family="Comic Sans MS", size=16)
        self.text_margin_x = 12
        self.text_margin_y = 6
        # Align line spacing to font metrics so caret and notebook lines match
        try:
            self.line_spacing = int(self.editor_font.metrics("linespace") + 4)
        except Exception:
            # fallback if metrics not available
            self.line_spacing = 26
        self._lines = [""]
        self.cur_row = 0
        self.cur_col = 0

        # Bindings
        self.paper_canvas.bind("<Configure>", self._on_canvas_resize)
        self.paper_canvas.bind("<Button-1>", self._on_click)
        self.paper_canvas.bind("<Key>", self._on_key)
        # Focus so key events are captured
        self.paper_canvas.focus_set()
        self.root.after(10, lambda: self._on_canvas_resize(None))

        # Initialize current file state
        self.current_file = None
    def _on_canvas_resize(self, event):
        # Redraw editor and lines
        self._redraw_editor()

    def _draw_notebook_lines(self):
        # Remove previous lines
        self.paper_canvas.delete("notebook_line")
        # Ensure geometry is up to date before querying size
        try:
            self.paper_canvas.update_idletasks()
        except Exception:
            pass
        w = self.paper_canvas.winfo_width()
        h = self.paper_canvas.winfo_height()
        if w <= 0 or h <= 0:
            return
        # Start lines at the text baseline for row 0 so they visually align
        try:
            baseline_offset = self.editor_font.metrics("ascent") + 2
        except Exception:
            baseline_offset = int(self.line_spacing * 0.75)
        y = self.text_margin_y + baseline_offset
        while y < h:
            self.paper_canvas.create_line(
                0, y, w, y, fill=BLACK, width=2, tags=("notebook_line",)
            )
            y += self.line_spacing
        # Ensure lines are visible above the text window
        try:
            # Raise lines to the absolute top so they are visible
            self.paper_canvas.tag_raise("notebook_line")
        except Exception:
            pass

    def _redraw_editor(self):
        # Clear previous text and cursor
        self.paper_canvas.delete("editor_text")
        self.paper_canvas.delete("cursor")
        # Draw lines first
        self._draw_notebook_lines()
        # Draw text lines
        line_y = self.text_margin_y
        for i, line in enumerate(self._lines):
            self.paper_canvas.create_text(
                self.text_margin_x,
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
        x = self.text_margin_x
        y = self.text_margin_y + self.cur_row * self.line_spacing
        if 0 <= self.cur_row < len(self._lines):
            prefix = self._lines[self.cur_row][: self.cur_col]
            x += self.editor_font.measure(prefix)
        # Caret as a vertical line
        self.paper_canvas.create_line(
            x,
            y + 2,
            x,
            y + self.line_spacing - 4,
            fill=FG_PURPLE,
            width=2,
            tags=("cursor",),
        )

    def _on_click(self, event):
        # Focus canvas to receive key events
        self.paper_canvas.focus_set()
        # Set cursor from click position
        row = max(0, min(int((event.y - self.text_margin_y) // self.line_spacing), len(self._lines) - 1))
        line = self._lines[row]
        # Determine column by measuring substrings
        col = 0
        x_rel = max(0, event.x - self.text_margin_x)
        # Iterate characters to find closest column
        for i in range(len(line) + 1):
            w = self.editor_font.measure(line[:i])
            if w >= x_rel:
                col = i
                break
            col = i
        self.cur_row, self.cur_col = row, col
        self._redraw_editor()

    def _on_key(self, event):
        ks = event.keysym
        ch = event.char
        # Navigation
        if ks == "Left":
            if self.cur_col > 0:
                self.cur_col -= 1
            elif self.cur_row > 0:
                self.cur_row -= 1
                self.cur_col = len(self._lines[self.cur_row])
        elif ks == "Right":
            if self.cur_col < len(self._lines[self.cur_row]):
                self.cur_col += 1
            elif self.cur_row < len(self._lines) - 1:
                self.cur_row += 1
                self.cur_col = 0
        elif ks == "Up":
            if self.cur_row > 0:
                self.cur_row -= 1
                self.cur_col = min(self.cur_col, len(self._lines[self.cur_row]))
        elif ks == "Down":
            if self.cur_row < len(self._lines) - 1:
                self.cur_row += 1
                self.cur_col = min(self.cur_col, len(self._lines[self.cur_row]))
        elif ks in ("BackSpace",):
            if self.cur_col > 0:
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
        elif ks in ("Return", "KP_Enter"):
            line = self._lines[self.cur_row]
            left, right = line[: self.cur_col], line[self.cur_col :]
            self._lines[self.cur_row] = left
            self._lines.insert(self.cur_row + 1, right)
            self.cur_row += 1
            self.cur_col = 0
        elif ch and ch >= " " and ch != "\x7f":
            # printable character
            line = self._lines[self.cur_row]
            self._lines[self.cur_row] = line[: self.cur_col] + ch + line[self.cur_col :]
            self.cur_col += 1
        else:
            return "break"
        self._redraw_editor()
    def _populate_toc(self):
        self.toc_listbox.delete(0, tk.END)
        notes = [f for f in os.listdir(NOTES_DIR) if f.endswith('.md')]
        for note in sorted(notes):
            self.toc_listbox.insert(tk.END, note)

    def _on_toc_select(self, event):
        selection = self.toc_listbox.curselection()
        if selection:
            filename = self.toc_listbox.get(selection[0])
            self._open_note_by_name(filename)

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
        self.name_entry.delete(0, tk.END)
        self.current_file = None
        self.root.title("Simple Note App - New Note")

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
                self.root.title(f"Simple Note App - {os.path.basename(file_path)}")

    def save_note(self):
        """Saves the note to a file in the notes folder using the entered name or a timestamp. Always uses .md extension."""
        note_name = self.name_entry.get().strip()
        if not note_name:
            # Use timestamp if no name entered
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

        self.root.title(f"Simple Note App - {filename}")
        messagebox.showinfo("Saved", "Your note has been saved successfully.")
        # Refresh TOC after save
        if hasattr(self, 'toc_listbox'):
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
                self._set_text(content)
                self.current_file = file_path
                # Set the name field to the filename (without extension)
                base = os.path.basename(file_path)
                name, _ = os.path.splitext(base)
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, name)
                self.root.title(f"Simple Note App - {base}")

    # Editor helpers
    def _set_text(self, text: str):
        lines = text.split("\n") if text else [""]
        if not lines:
            lines = [""]
        self._lines = lines
        self.cur_row = 0
        self.cur_col = 0
        self._redraw_editor()

    def _get_text(self) -> str:
        return "\n".join(self._lines)
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

if __name__ == "__main__":
    print("App started")
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()
