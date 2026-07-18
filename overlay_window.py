import tkinter as tk


class TranslationOverlay:
    """A borderless, always-on-top window that displays translated text
    floating over the captured screen region."""

    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.88)
        bg = '#1e1e1e'
        self.window.configure(bg=bg)

        self.label = tk.Label(
            self.window, text='', fg='#00ff88', bg=bg,
            font=('Segoe UI', 13, 'bold'), justify='left',
            wraplength=600, padx=10, pady=8,
        )
        self.label.pack()
        self.window.withdraw()

    def show_at(self, x, y, width, text):
        if not text:
            self.window.withdraw()
            return
        self.label.configure(wraplength=max(width, 250), text=text)
        self.window.deiconify()
        self.window.update_idletasks()
        self.window.geometry(f'+{x}+{y}')

    def close(self):
        self.window.destroy()
