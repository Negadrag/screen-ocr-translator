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
    """Background thread that repeatedly grabs a screen region, OCRs it,
    and translates any new text. Results are pushed to a thread-safe queue
    as (kind, payload) tuples: kind is 'status', 'text', or 'error'."""

    def __init__(self, region, lang_preset, interval, result_queue):
        super().__init__(daemon=True)
        self.region = region
        self.lang_preset = lang_preset
        self.interval = interval
        self.result_queue = result_queue
        self._stop_event = threading.Event()
        self._reader = None
        self._last_text = None

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
                    frame = np.array(shot)[:, :, :3]  # BGRA -> BGR (OpenCV order)
                    results = self._reader.readtext(frame, detail=0, paragraph=True)
                    text = '\n'.join(results).strip()

                    if text and text != self._last_text:
                        self._last_text = text
                        translated = self._translate(text)
                        self.result_queue.put(('text', translated))
                    elif not text and self._last_text is not None:
                        self._last_text = None
                        self.result_queue.put(('text', ''))
                except Exception as e:
                    self.result_queue.put(('error', str(e)))

                elapsed = time.time() - start_time
                sleep_time = max(0.1, self.interval - elapsed)
                self._stop_event.wait(sleep_time)

    @staticmethod
    def _translate(text):
        try:
            return GoogleTranslator(source='auto', target='en').translate(text)
        except Exception as e:
            return f'[translation error: {e}]'
