import tkinter as tk
from tkinter import scrolledtext


class TranslationPanel:
    """A normal, resizable window that lists the current translations as
    scrollable text — useful for reading longer passages or copying text out.

    Unlike the in-place overlay, this is an ordinary window you can move,
    resize, and select text in.
    """

    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self._sig = None

        self.window = tk.Toplevel(root)
        self.window.title('Translation Output')
        self.window.geometry('420x500')
        self.window.minsize(260, 200)
        self.window.configure(bg='#1e1e1e')

        self.text = scrolledtext.ScrolledText(
            self.window, wrap='word', state='disabled',
            bg='#1e1e1e', fg='#e8e8e8', borderwidth=0,
            padx=12, pady=12, font=('Segoe UI', 12),
        )
        self.text.pack(fill='both', expand=True)
        self.text.tag_configure('src', foreground='#8a8a8a', font=('Segoe UI', 9))
        self.text.tag_configure(
            'tr', foreground='#00ff88', font=('Segoe UI', 13, 'bold'), spacing3=12)

        self.window.protocol('WM_DELETE_WINDOW', self._handle_close)

    def _handle_close(self):
        self.window.withdraw()
        if self.on_close:
            self.on_close()

    def update(self, blocks, show_source=True):
        sig = tuple((b.get('src'), b['text']) for b in blocks)
        if sig == self._sig:
            return
        self._sig = sig

        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        if not blocks:
            self.text.insert('end', '(no text detected)', 'src')
        for b in blocks:
            src = b.get('src')
            if show_source and src:
                self.text.insert('end', src + '\n', 'src')
            self.text.insert('end', b['text'] + '\n', 'tr')
        self.text.configure(state='disabled')

    def show(self):
        self.window.deiconify()
        self.window.lift()

    def hide(self):
        self.window.withdraw()

    def close(self):
        self.window.destroy()
