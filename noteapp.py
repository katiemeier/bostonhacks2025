import tkinter as tk
from tkinter import messagebox, filedialog
import os

class NoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Note App")
        self.root.geometry("600x500")

        # Create frame for buttons
        button_frame = tk.Frame(root)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="New", width=10, command=self.new_note).pack(side="left", padx=5)
        tk.Button(button_frame, text="Open", width=10, command=self.open_note).pack(side="left", padx=5)
        tk.Button(button_frame, text="Save", width=10, command=self.save_note).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete", width=10, command=self.delete_note).pack(side="left", padx=5)

        # Text area for typing notes
        self.text_area = tk.Text(root, wrap="word", font=("Arial", 12))
        self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

        self.current_file = None

    def new_note(self):
        """Clears the text area for a new note."""

        import tkinter as tk
        from tkinter import messagebox, filedialog
        import os
        import datetime

        NOTES_DIR = "notes"

        class NoteApp:
            def __init__(self, root):
                self.root = root
                self.root.title("Simple Note App")
                self.root.geometry("600x500")

                # Ensure notes directory exists
                if not os.path.exists(NOTES_DIR):
                    os.makedirs(NOTES_DIR)

                # Create frame for buttons
                button_frame = tk.Frame(root)
                button_frame.pack(fill="x", pady=10)

                tk.Button(button_frame, text="New", width=10, command=self.new_note).pack(side="left", padx=5)
                tk.Button(button_frame, text="Open", width=10, command=self.open_note).pack(side="left", padx=5)
                tk.Button(button_frame, text="Save", width=10, command=self.save_note).pack(side="left", padx=5)
                tk.Button(button_frame, text="Delete", width=10, command=self.delete_note).pack(side="left", padx=5)

                # Text area for typing notes
                self.text_area = tk.Text(root, wrap="word", font=("Arial", 12))
                self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

                self.current_file = None

            def new_note(self):
                """Clears the text area for a new note."""
                self.text_area.delete(1.0, tk.END)
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
                """Saves the note to a file in the notes folder with an automatic name if new."""
                if not self.current_file:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.current_file = os.path.join(NOTES_DIR, f"note_{timestamp}.md")

                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(self.text_area.get(1.0, tk.END).strip())

                self.root.title(f"Simple Note App - {os.path.basename(self.current_file)}")
                messagebox.showinfo("Saved", "Your note has been saved successfully.")

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

        if __name__ == "__main__":
            root = tk.Tk()
            app = NoteApp(root)
            root.mainloop()
