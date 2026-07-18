import sys
import tkinter as tk

# A color that is unlikely to occur in real screen content; areas painted with
# it become fully transparent (and click-through) via Windows' -transparentcolor.
TRANSPARENT_KEY = '#010203'
FONT_FAMILY = 'Segoe UI'
MIN_FONT = 7


class TranslationOverlay:
    """A borderless, always-on-top, see-through window sized to the captured
    region. Each translated block is drawn as a filled rectangle (covering the
    original text) with the translation auto-sized to fit inside it."""

    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        try:
            self.window.attributes('-transparentcolor', TRANSPARENT_KEY)
        except tk.TclError:
            pass
        self.window.configure(bg=TRANSPARENT_KEY)

        self.canvas = tk.Canvas(
            self.window, highlightthickness=0, bd=0, bg=TRANSPARENT_KEY)
        self.canvas.pack(fill='both', expand=True)

        self._region = None
        self._sig = None
        self.window.withdraw()
        self.window.update_idletasks()
        self._apply_window_flags()

    def set_region(self, region):
        self._region = region
        self._sig = None

    def _apply_window_flags(self):
        """Configure the overlay window at the Win32 level:
        - WS_EX_TRANSPARENT: make the whole window click-through, so mouse and
          scroll input passes to the app behind it (not just transparent areas).
        - WDA_EXCLUDEFROMCAPTURE: hide it from screen-capture APIs (incl. mss)
          so we don't OCR our own overlay and translate English into English.
        """
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetAncestor(self.window.winfo_id(), 2)  # GA_ROOT

            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

            WDA_EXCLUDEFROMCAPTURE = 0x11
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

    def update_blocks(self, blocks):
        if not self._region:
            return
        sig = self._signature(blocks)
        if sig == self._sig:
            return
        self._sig = sig

        self.canvas.delete('all')
        if not blocks:
            self.window.withdraw()
            return

        left, top, width, height = self._region
        self.window.geometry(f'{width}x{height}+{left}+{top}')
        self.canvas.configure(width=width, height=height)
        for b in blocks:
            self._draw_block(b)

        self.window.deiconify()
        self.window.lift()
        self._apply_window_flags()

    def _draw_block(self, b):
        x, y, w, h = b['x'], b['y'], b['w'], b['h']
        bg = b.get('bg', '#000000')
        fg = b.get('fg', '#ffffff')
        if bg.lower() == TRANSPARENT_KEY:
            bg = '#000000'  # avoid accidentally becoming transparent

        self.canvas.create_rectangle(x, y, x + w, y + h, fill=bg, outline=bg)
        self._draw_fitted_text(x, y, w, h, b['text'], fg)

    def _draw_fitted_text(self, x, y, w, h, text, fg):
        """Draw text centered in the box, shrinking the font until the rendered
        text (with wrapping) fits inside the box."""
        cx, cy = x + w / 2, y + h / 2
        inner_w = max(1, w - 6)
        size = max(MIN_FONT, int(h * 0.82))
        item = self.canvas.create_text(
            cx, cy, text=text, fill=fg, anchor='center', justify='center',
            width=inner_w, font=(FONT_FAMILY, size, 'bold'))

        while size > MIN_FONT:
            bx0, by0, bx1, by1 = self.canvas.bbox(item)
            if (bx1 - bx0) <= w and (by1 - by0) <= h:
                break
            size -= 1
            self.canvas.itemconfigure(item, font=(FONT_FAMILY, size, 'bold'))

    @staticmethod
    def _signature(blocks):
        # Quantize positions so tiny OCR jitter doesn't force a redraw/flicker.
        return tuple(
            (round(b['x'] / 6), round(b['y'] / 6),
             round(b['w'] / 6), round(b['h'] / 6),
             b['text'], b['bg'])
            for b in blocks
        )

    def close(self):
        self.window.destroy()
