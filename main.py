import queue
import tkinter as tk
from tkinter import ttk

from ocr_worker import LANGUAGE_PRESETS, OcrWorker
from overlay_window import TranslationOverlay
from region_selector import select_region


class ControlPanel:
    def __init__(self, root):
        self.root = root
        root.title('Screen OCR Translator')
        root.geometry('420x260')
        root.resizable(False, False)

        self.region = None
        self.worker = None
        self.result_queue = queue.Queue()
        self.overlay = TranslationOverlay(root)

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        pad = {'padx': 10, 'pady': 6}
        frame = ttk.Frame(self.root)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text='Text script (for OCR):').grid(row=0, column=0, columnspan=2, sticky='w', **pad)
        self.lang_var = tk.StringVar(value='Latin (English, French, German, Spanish, Italian, Portuguese)')
        lang_combo = ttk.Combobox(
            frame, textvariable=self.lang_var, values=list(LANGUAGE_PRESETS.keys()),
            state='readonly', width=45,
        )
        lang_combo.grid(row=1, column=0, columnspan=2, sticky='w', **pad)

        ttk.Label(frame, text='Refresh interval (seconds):').grid(row=2, column=0, sticky='w', **pad)
        self.interval_var = tk.DoubleVar(value=0.5)
        ttk.Spinbox(
            frame, from_=0.2, to=10.0, increment=0.1,
            textvariable=self.interval_var, width=8,
        ).grid(row=2, column=1, sticky='w', **pad)

        self.region_label = ttk.Label(frame, text='No region selected')
        self.region_label.grid(row=3, column=0, columnspan=2, sticky='w', **pad)

        self.select_btn = ttk.Button(frame, text='Select Region', command=self.on_select_region)
        self.select_btn.grid(row=4, column=0, sticky='we', **pad)

        self.toggle_btn = ttk.Button(frame, text='Start', command=self.on_toggle, state='disabled')
        self.toggle_btn.grid(row=4, column=1, sticky='we', **pad)

        self.status_var = tk.StringVar(value='Idle')
        ttk.Label(frame, textvariable=self.status_var, foreground='gray').grid(
            row=5, column=0, columnspan=2, sticky='w', **pad)

        note = ('Translations are drawn on top of the original text, sized to fit. '
                'Source language is auto-detected; the dropdown only sets which '
                'character set the OCR model reads.')
        ttk.Label(frame, text=note, wraplength=390, foreground='#555').grid(
            row=6, column=0, columnspan=2, sticky='w', **pad)

        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def on_select_region(self):
        self.root.withdraw()
        region = select_region(self.root)
        self.root.deiconify()
        if region:
            self.region = region
            self.region_label.config(text=f'Region: {region[2]}x{region[3]} at ({region[0]}, {region[1]})')
            self.toggle_btn.config(state='normal')

    def on_toggle(self):
        if self.worker is None:
            self.start_worker()
        else:
            self.stop_worker()

    def start_worker(self):
        if not self.region:
            return
        self.worker = OcrWorker(
            region=self.region,
            lang_preset=self.lang_var.get(),
            interval=self.interval_var.get(),
            result_queue=self.result_queue,
        )
        self.overlay.set_region(self.region)
        self.worker.start()
        self.toggle_btn.config(text='Stop')
        self.select_btn.config(state='disabled')
        self.status_var.set('Starting...')

    def stop_worker(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.toggle_btn.config(text='Start')
        self.select_btn.config(state='normal')
        self.status_var.set('Idle')
        self.overlay.update_blocks([])

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == 'status':
                    self.status_var.set(payload)
                elif kind == 'blocks':
                    self.overlay.update_blocks(payload)
                elif kind == 'error':
                    self.status_var.set(f'Error: {payload}')
        except queue.Empty:
            pass
        self.root.after(50, self._poll_queue)

    def on_close(self):
        self.stop_worker()
        self.overlay.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    ControlPanel(root)
    root.mainloop()


if __name__ == '__main__':
    main()
