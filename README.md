# Screen OCR Translator

A desktop tool that continuously reads text from a region of your screen, translates it to English, and displays the result in a floating overlay. Useful for games, videos, subtitles, comics/manga, PDFs, or any on-screen text in a language you don't read.

Built with EasyOCR (offline text recognition) and Google Translate via `deep-translator`.

## Features

- **Live overlay translation** — pick a screen region once, and it re-captures and re-translates several times per second.
- **Two output modes** — draw translations *in place* over the original text, show them in a *separate scrollable window* (easy to read/copy), or *both*.
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

### GPU acceleration (NVIDIA / CUDA)

`pip install` gives you the **CPU-only** PyTorch build. OCR still works, but each
capture takes a couple hundred milliseconds. With an NVIDIA GPU you can install a
CUDA build for a large speedup (roughly 5× in testing), and the app will use it
automatically — no code or config changes needed.

Pick the CUDA index matching your GPU/driver and reinstall torch:

```bash
# CUDA 13.0 — required for RTX 50-series (Blackwell); works on most recent NVIDIA GPUs/drivers
pip install --force-reinstall --no-deps --index-url https://download.pytorch.org/whl/cu130 torch torchvision

# CUDA 12.8 — for older GPUs/drivers
pip install --force-reinstall --no-deps --index-url https://download.pytorch.org/whl/cu128 torch torchvision
```

Verify CUDA is picked up:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

When you click **Start**, the status line shows which device is in use (e.g.
`Running — GPU: NVIDIA GeForce RTX 5080`).

## Usage

```bash
python main.py
```

1. **Select the OCR script** from the dropdown if your text isn't Latin-based (e.g. Japanese, Chinese, Korean, Russian).
2. Click **Select Region** and drag a box over the text you want translated. Press `Esc` to cancel.
3. Adjust the **refresh interval** (default 0.5s) if desired — lower is more responsive but uses more CPU/GPU.
4. Choose **Output to**: *Overlay on original* (drawn on top of the source text, sized to match, fully click-through), *Separate window* (a movable, scrollable window showing the original text and its translation — handy for reading or copying), or *Both*.
5. Click **Start**.
5. Click **Stop** to pause, or close the window to exit.

### Notes

- **Source language is always auto-detected** by Google Translate. The dropdown only selects which character set EasyOCR uses to *read* glyphs — EasyOCR can't combine incompatible scripts (e.g. CJK + Latin + Cyrillic) in a single model, so pick the one matching your source text.
- On a CPU-only machine, OCR takes a couple hundred milliseconds per capture, so a larger interval is easier on the CPU. With a CUDA GPU (see [GPU acceleration](#gpu-acceleration-nvidia--cuda)) OCR is ~5× faster, so the low default interval stays responsive.
- The overlay is click-through and excluded from screen capture, so it won't block your input and won't get re-translated by its own OCR.

## Project structure

| File | Responsibility |
|------|----------------|
| `main.py` | Tkinter control panel; wires everything together and polls the worker for results. |
| `region_selector.py` | Full-screen, all-monitor drag-to-select overlay; returns the chosen region. |
| `ocr_worker.py` | Background thread: grabs the region on an interval, runs EasyOCR, translates changed text. |
| `overlay_window.py` | Borderless, click-through, always-on-top window that draws translations over the original text. |
| `text_panel.py` | Optional separate scrollable window listing the original text and its translation. |

## Building a standalone .exe

A [PyInstaller](https://pyinstaller.org/) spec (`screen_ocr_translator.spec`) is
included. It produces a one-folder Windows app in `dist/ScreenOCRTranslator/`.

**Size / GPU caveat:** the bundle includes PyTorch. With the **CPU** build it's
roughly **600–800 MB**; with the **CUDA (GPU)** build it's **~3.5 GB**, which
exceeds GitHub's **2 GB per-file** release-asset limit. For a distributable
build, use CPU-only torch — it runs on any Windows PC, and users who want GPU
speed can run from source. Do this in a **clean virtual environment** so it
doesn't disturb a CUDA install you use for development:

```bash
python -m venv build-env
build-env\Scripts\activate           # Windows
pip install -r requirements.txt      # pulls CPU-only torch by default
pip install pyinstaller
pyinstaller screen_ocr_translator.spec
```

The app is then in `dist/ScreenOCRTranslator/` — run `ScreenOCRTranslator.exe`.
Zip that folder to distribute it. (The first run still downloads EasyOCR's model
weights, so an internet connection is needed once.)

To publish it as a GitHub release:

```bash
# from the repo, after zipping dist/ScreenOCRTranslator into ScreenOCRTranslator-win64.zip
gh release create v1.0.0 ScreenOCRTranslator-win64.zip \
  --title "v1.0.0" --notes "Standalone Windows build (CPU)."
```

## How it works

1. `region_selector` returns a `(left, top, width, height)` rectangle in absolute screen coordinates.
2. `OcrWorker` (a background thread) uses `mss` to grab that rectangle on each tick, feeds the frame to EasyOCR, and joins the recognized lines.
3. If the recognized text differs from the previous capture, it's translated with `deep-translator`'s `GoogleTranslator(source='auto', target='en')` and pushed onto a thread-safe queue.
4. The Tkinter main loop polls that queue and updates the floating overlay window.

## License

MIT
