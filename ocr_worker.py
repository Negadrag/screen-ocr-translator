import threading
import time

import mss
import numpy as np
from deep_translator import GoogleTranslator

# Each preset is a set of EasyOCR language codes that are safe to load
# together (EasyOCR only allows combining scripts it considers compatible).
LANGUAGE_PRESETS = {
    'Latin (English, French, German, Spanish, Italian, Portuguese)':
        ['en', 'fr', 'de', 'es', 'it', 'pt'],
    'Japanese': ['ja', 'en'],
    'Chinese (Simplified)': ['ch_sim', 'en'],
    'Chinese (Traditional)': ['ch_tra', 'en'],
    'Korean': ['ko', 'en'],
    'Russian (Cyrillic)': ['ru', 'en'],
    'English only': ['en'],
}


class OcrWorker(threading.Thread):
    """Background thread that repeatedly grabs a screen region, OCRs each
    text block (keeping its position/size), and translates new text.

    Results are pushed to a thread-safe queue as (kind, payload) tuples:
      - ('status', str)
      - ('error', str)
      - ('blocks', list[dict])  where each dict has:
            x, y, w, h  -> block rectangle relative to the region (pixels)
            text        -> translated (English) text
            bg          -> sampled background color as '#rrggbb'
            fg          -> readable foreground color as '#rrggbb'
    """

    def __init__(self, region, lang_preset, interval, result_queue):
        super().__init__(daemon=True)
        self.region = region
        self.lang_preset = lang_preset
        self.interval = interval
        self.result_queue = result_queue
        self._stop_event = threading.Event()
        self._reader = None
        self._cache = {}  # original text -> translated text

    def stop(self):
        self._stop_event.set()

    def _get_reader(self):
        import easyocr
        import torch
        langs = LANGUAGE_PRESETS[self.lang_preset]
        gpu = torch.cuda.is_available()
        return easyocr.Reader(langs, gpu=gpu, verbose=False)

    def run(self):
        try:
            self.result_queue.put(('status', 'Loading OCR model (first run downloads weights)...'))
            self._reader = self._get_reader()
            self.result_queue.put(('status', 'Running'))
        except Exception as e:
            self.result_queue.put(('error', f'Failed to load OCR model: {e}'))
            return

        left, top, width, height = self.region
        monitor = {'left': left, 'top': top, 'width': width, 'height': height}

        with mss.mss() as sct:
            while not self._stop_event.is_set():
                start_time = time.time()
                try:
                    shot = sct.grab(monitor)
                    frame = np.array(shot)[:, :, :3]  # BGRA -> BGR
                    blocks = self._process(frame)
                    self.result_queue.put(('blocks', blocks))
                except Exception as e:
                    self.result_queue.put(('error', str(e)))

                elapsed = time.time() - start_time
                sleep_time = max(0.1, self.interval - elapsed)
                self._stop_event.wait(sleep_time)

    def _process(self, frame):
        """OCR the frame and return a list of positioned, translated blocks."""
        results = self._reader.readtext(frame, paragraph=True)
        blocks = []
        for item in results:
            bbox, raw = item[0], item[1]
            text = (raw or '').strip()
            if not text:
                continue

            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            left = int(min(xs))
            top = int(min(ys))
            right = int(max(xs))
            bottom = int(max(ys))
            w = right - left
            h = bottom - top
            if w < 4 or h < 4:
                continue

            bg, fg = self._sample_colors(frame, left, top, right, bottom)
            blocks.append({
                'x': left, 'y': top, 'w': w, 'h': h,
                'text': self._translate_cached(text),
                'bg': bg, 'fg': fg,
            })
        return blocks

    def _translate_cached(self, text):
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        out = self._translate(text)
        if len(self._cache) > 500:
            self._cache.clear()
        self._cache[text] = out
        return out

    @staticmethod
    def _sample_colors(frame, left, top, right, bottom):
        """Estimate the block's background color (median pixel) and pick a
        contrasting text color. frame is in BGR order."""
        fh, fw = frame.shape[:2]
        l = max(0, left)
        t = max(0, top)
        r = min(fw, right)
        b = min(fh, bottom)
        if r <= l or b <= t:
            return '#000000', '#ffffff'
        roi = frame[t:b, l:r].reshape(-1, 3)
        med = np.median(roi, axis=0)
        blue, green, red = (int(med[0]), int(med[1]), int(med[2]))
        bg = f'#{red:02x}{green:02x}{blue:02x}'
        luminance = 0.299 * red + 0.587 * green + 0.114 * blue
        fg = '#000000' if luminance > 140 else '#ffffff'
        return bg, fg

    @staticmethod
    def _translate(text):
        try:
            return GoogleTranslator(source='auto', target='en').translate(text)
        except Exception as e:
            return f'[translation error: {e}]'
