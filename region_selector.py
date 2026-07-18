import sys
import tkinter as tk


def _get_virtual_screen_bounds(root):
    """Return (left, top, width, height) covering all monitors."""
    if sys.platform == 'win32':
        import ctypes
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        w = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        h = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return x, y, w, h
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def select_region(root):
    """Show a dimmed, all-monitor overlay and let the user drag a selection box.

    Returns (left, top, width, height) in absolute screen coordinates, or
    None if the user cancelled (Esc or a zero-size drag).
    """
    result = {}
    vx, vy, vw, vh = _get_virtual_screen_bounds(root)

    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.geometry(f'{vw}x{vh}+{vx}+{vy}')
    overlay.attributes('-alpha', 0.3)
    overlay.attributes('-topmost', True)
    overlay.configure(bg='gray10')
    overlay.config(cursor='cross')

    canvas = tk.Canvas(overlay, bg='gray10', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    canvas.create_text(
        vw // 2, 30, text='Drag to select a region.  Esc to cancel.',
        fill='white', font=('Segoe UI', 14, 'bold'),
    )

    state = {'x0': None, 'y0': None, 'rect': None}

    def on_press(event):
        state['x0'], state['y0'] = event.x, event.y
        state['rect'] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline='#00ff88', width=2)

    def on_drag(event):
        if state['rect'] is not None:
            canvas.coords(state['rect'], state['x0'], state['y0'], event.x, event.y)

    def on_release(event):
        if state['x0'] is None:
            overlay.destroy()
            return
        x0, y0 = state['x0'], state['y0']
        x1, y1 = event.x, event.y
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if right - left > 5 and bottom - top > 5:
            result['region'] = (vx + left, vy + top, right - left, bottom - top)
        overlay.destroy()

    def on_escape(_event):
        overlay.destroy()

    canvas.bind('<ButtonPress-1>', on_press)
    canvas.bind('<B1-Motion>', on_drag)
    canvas.bind('<ButtonRelease-1>', on_release)
    overlay.bind('<Escape>', on_escape)
    overlay.focus_force()

    overlay.grab_set()
    root.wait_window(overlay)
    return result.get('region')
