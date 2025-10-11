BG_PINK = "#ffb6c1"
FG_PURPLE = "#800080"
BTN_PINK = "#ff69b4"
BTN_PURPLE = "#c084fc"
ENTRY_BG = "#ffe4fa"
TEXT_BG = "#f3c4fb"

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
        else:
            messagebox.showwarning("No File", "No note is currently open.")
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Note App")
        self.root.geometry("600x500")
        self.root.configure(bg=BG_PINK)

        # Entry for note name
        name_frame = tk.Frame(root, bg=BG_PINK)
        name_frame.pack(fill="x", pady=(10,0))
        tk.Label(name_frame, text="Note Name:", font=("Arial", 11, "bold"), fg=FG_PURPLE, bg=BG_PINK).pack(side="left", padx=(10,5))
        self.name_entry = tk.Entry(name_frame, font=("Arial", 11), width=30, bg=ENTRY_BG, fg=FG_PURPLE, insertbackground=FG_PURPLE)
        self.name_entry.pack(side="left", padx=(0,10))

        # Create frame for buttons
        button_frame = tk.Frame(root, bg=BG_PINK)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="New", width=10, command=self.new_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Open", width=10, command=self.open_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Save", width=10, command=self.save_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", width=10, command=self.delete_note, bg=BTN_PINK, fg=FG_PURPLE, activebackground=BTN_PURPLE, activeforeground=BG_PINK).pack(side="left", padx=5)

        # Text area for typing notes
        self.text_area = tk.Text(root, wrap="word", font=("Arial", 12), bg=TEXT_BG, fg=FG_PURPLE, insertbackground=FG_PURPLE)
        self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

        self.current_file = None


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
