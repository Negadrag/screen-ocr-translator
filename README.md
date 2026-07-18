# Screen OCR Translator

A desktop tool that continuously reads text from a region of your screen, translates it to English, and displays the result in a floating overlay. Useful for games, videos, subtitles, comics/manga, PDFs, or any on-screen text in a language you don't read.

Built with EasyOCR (offline text recognition) and Google Translate via `deep-translator`.

## Features

- **Live overlay translation** — pick a screen region once, and it re-captures and re-translates several times per second.
- **Multi-monitor drag-to-select** — dim overlay spanning all monitors; drag a box around the text you care about.
- **Auto-detected source language** — Google auto-detects what language the text is in; you only pick which *character set* (script) the OCR model should read.
- **Script presets** — Latin (English/French/German/Spanish/Italian/Portuguese), Japanese, Simplified/Traditional Chinese, Korean, Russian (Cyrillic), or English-only.
- **Change detection** — only re-translates when the on-screen text actually changes, to save CPU and translation calls.
- **GPU aware** — uses CUDA automatically if available, otherwise runs on CPU.

## Requirements

- Python 3.9+ (developed on 3.14, Windows 11)
- Internet connection (for Google translation and the one-time OCR model download)

## Installation

```bash
git clone https://github.com/Negadrag/screen-ocr-translator.git
cd screen-ocr-translator
pip install -r requirements.txt
```

The first run downloads EasyOCR's detection/recognition model weights (a few hundred MB), which are then cached locally.

> **Note:** EasyOCR pulls in PyTorch + torchvision, which is a large (multi-GB) install.

## Usage

```bash
python main.py
```

1. **Select the OCR script** from the dropdown if your text isn't Latin-based (e.g. Japanese, Chinese, Korean, Russian).
2. Click **Select Region** and drag a box over the text you want translated. Press `Esc` to cancel.
3. Adjust the **refresh interval** (default 2s) if desired — lower is more responsive but uses more CPU.
4. Click **Start**. The translated English text appears in a floating overlay near the captured region.
5. Click **Stop** to pause, or close the window to exit.

### Notes

- **Source language is always auto-detected** by Google Translate. The dropdown only selects which character set EasyOCR uses to *read* glyphs — EasyOCR can't combine incompatible scripts (e.g. CJK + Latin + Cyrillic) in a single model, so pick the one matching your source text.
- On a CPU-only machine, OCR takes a couple hundred milliseconds per capture — fine for the default 2s interval. With a CUDA GPU it's much faster, so you can lower the interval.

## Project structure

| File | Responsibility |
|------|----------------|
| `main.py` | Tkinter control panel; wires everything together and polls the worker for results. |
| `region_selector.py` | Full-screen, all-monitor drag-to-select overlay; returns the chosen region. |
| `ocr_worker.py` | Background thread: grabs the region on an interval, runs EasyOCR, translates changed text. |
| `overlay_window.py` | Borderless always-on-top window that displays the translated text. |

## How it works

1. `region_selector` returns a `(left, top, width, height)` rectangle in absolute screen coordinates.
2. `OcrWorker` (a background thread) uses `mss` to grab that rectangle on each tick, feeds the frame to EasyOCR, and joins the recognized lines.
3. If the recognized text differs from the previous capture, it's translated with `deep-translator`'s `GoogleTranslator(source='auto', target='en')` and pushed onto a thread-safe queue.
4. The Tkinter main loop polls that queue and updates the floating overlay window.

## License

MIT
