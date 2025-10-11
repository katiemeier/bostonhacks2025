BG_PINK = "#ffb6c1"
FG_PURPLE = "#800080"
BTN_PINK = "#ff69b4"
BTN_PURPLE = "#c084fc"
ENTRY_BG = "#ffe4fa"
TEXT_BG = "#f3c4fb"
BLACK = "#000000"


import tkinter as tk
from tkinter import messagebox, filedialog
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
        tk.Label(sidebar, text="Notes", font=("Comic Sans MS", 14, "bold"), fg=FG_PURPLE, bg=BTN_PINK).pack(pady=(10,0))
        self.toc_listbox = tk.Listbox(sidebar, font=("Comic Sans MS", 12), bg=ENTRY_BG, fg=FG_PURPLE, selectbackground=BTN_PURPLE, selectforeground=BG_PINK, borderwidth=0, highlightthickness=0)
        self.toc_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.toc_listbox.bind("<<ListboxSelect>>", self._on_toc_select)
        self._populate_toc()

        # Content frame for note entry and text
        content_frame = tk.Frame(main_frame, bg=BG_PINK)
        content_frame.pack(side="left", fill="both", expand=True)

        name_frame = tk.Frame(content_frame, bg=BG_PINK)
        name_frame.pack(fill="x", pady=(10,0))
        tk.Label(name_frame, text="Note Name:", font=("Comic Sans MS", 14, "bold"), fg=FG_PURPLE, bg=BG_PINK).pack(side="left", padx=(10,5))
        self.name_entry = tk.Entry(name_frame, font=("Comic Sans MS", 14), width=30, bg=ENTRY_BG, fg=FG_PURPLE, insertbackground=FG_PURPLE)
        self.name_entry.pack(side="left", padx=(0,10))

        # Create frame for buttons
        button_frame = tk.Frame(content_frame, bg=BG_PINK)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="New", width=10, command=self.new_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Open", width=10, command=self.open_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Save", width=10, command=self.save_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", width=10, command=self.delete_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)

        # Text area for typing notes with lined notebook paper effect
        self.paper_canvas = tk.Canvas(content_frame, bg=TEXT_BG, highlightthickness=0)
        self.paper_canvas.pack(expand=True, fill="both", padx=0, pady=0)
        self.text_area = tk.Text(
            self.paper_canvas,
            wrap="word",
            font=("Comic Sans MS", 16),
            bg=TEXT_BG,
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
        self.paper_canvas.delete("notebook_line")
        w = self.paper_canvas.winfo_width()
        h = self.paper_canvas.winfo_height()
        if w <= 0 or h <= 0:
            return
        y = 0
        while y < h:
            self.paper_canvas.create_line(
                0, y, w, y, fill=BLACK, width=2, tags=("notebook_line",)
            )
            y += self.line_spacing
        # Ensure lines are visible above the text window
        try:
            self.paper_canvas.tag_raise("notebook_line")
        except Exception:
            pass
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
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                self.current_file = file_path
                base = os.path.basename(file_path)
                name, _ = os.path.splitext(base)
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, name)
                self.root.title(f"Simple Note App - {base}")


    def new_note(self):
        """Clears the text area for a new note and resets the name field."""
        self.text_area.delete(1.0, tk.END)
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
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
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
            file.write(self.text_area.get(1.0, tk.END).strip())

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
    print("App started")
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()
