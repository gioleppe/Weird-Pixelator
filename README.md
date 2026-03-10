# Weird Pixelator

Weird Pixelator is a desktop image tool for glitch art, color manipulation, blending, CRT effects, crop controls, and retro export compression.

## Features

- pixelation and glitch effects
- color controls and invert
- CRT-style post-processing
- four-edge crop with live size readout and presets
- blend image overlay
- save/export with retro compression profiles
- randomized effect generation

## Run locally

1. Create or activate a Python environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start the app:
   - `python main.py`

## Build macOS app

Use the included build script:

- `./scripts/build_macos.sh`

The script uses the checked-in source icon:

- `icon.png`

The packaged app is created in `dist/`.

## Repository hygiene

The project ignores local and generated files such as:

- `.venv/`
- `build/`
- `dist/`
- generated macOS icon assets

## License

No license file has been added yet.
