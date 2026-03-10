# Weird Pixelator — Working Features and Workflow

This document describes the features currently working in Weird Pixelator and explains how the app behaves in normal use.

It is intended to be a practical reference for what is reliable right now.

## Current Scope

The app is working as a compact single-image glitch editor with:
- live preview editing
- crop and aspect controls
- finishing effects
- animation frame capture/export
- palette extraction/export

The preview is interactive and updates as controls change. Final saved images are rendered from the full image instead of the reduced preview.

## Features Intentionally Excluded From This Working List

These are intentionally excluded from the approved working feature set:
- Random Pixels
- Legacy Collapse / Color Collapse

`Noise` is still included and is considered working. It remains the supported noise-style effect.

---

## Typical Workflow

### 1. Load an image
- Click `Upload Image`
- Choose a supported image file
- The image is loaded into the preview
- Editing controls reset to their default clean state
- Crop controls reset to full image
- Blend image is cleared
- Animation frames are cleared
- Palette output is cleared

### 2. Adjust the base glitch look
Use the `Adjust` tab to shape the main look of the image:
- pixelation and glitch displacement
- color shifting and tonal adjustments
- blur and color reduction
- optional blend overlay

The preview updates automatically while controls change.

### 3. Apply finishing effects
Use the `Finish` tab to add CRT-style display effects and preview-only camera/compression emulation.

### 4. Optionally crop the image
Use the `Crop` tab to trim the image or force a specific aspect ratio.

### 5. Save still image, build animation, or extract palette
From there you can:
- save a still PNG
- capture animation frames and export them
- extract a palette from the current preview look

---

## Detailed Working Features

## 1. Image Loading and Preview

### Working behavior
- Images can be loaded from disk through the upload button.
- The preview canvas displays the current image scaled to fit the available area.
- Preview updates are delayed slightly to keep slider interaction responsive.
- The preview metadata shows:
  - source dimensions
  - crop size when crop is active
  - preview render size when different from source

### Important behavior
- The preview is not always full resolution.
- For speed, preview rendering may use a reduced-size version of the current image.
- Final still-image save uses the full-resolution image.

---

## 2. Adjust Tab

The `Adjust` tab controls the main image-processing pipeline.

### Pixelate card

#### Pixelate
- Downsamples and upscales the image to create blocky pixelation.
- Lower values create stronger pixelation.

#### Row Jitter
- Randomly offsets horizontal rows.
- Produces fine broken-signal movement.

#### Block Shift
- Moves larger rectangular chunks sideways.
- Produces harsher digital tearing.

#### Pixel Sort
- Sorts small horizontal segments by brightness.
- Produces streaky glitch artifacts.

### Colorize card

#### Hue Shift
- Rotates image hue across the full color range.

#### Saturation
- Reduces or boosts color intensity.

#### Contrast
- Reduces or boosts contrast.

#### Invert Colors
- Inverts RGB values while preserving alpha behavior.

### Randomize card

#### Randomize Effects
- Randomizes enabled controls to generate new looks quickly.

#### Randomize Settings
- Opens a chooser for which controls are allowed to randomize.

### Confuser card

#### Blur
- Applies Gaussian blur.

#### Color Reducer
- Reduces the number of visible colors using palette quantization.

### Blend card

#### Upload Blend Image
- Loads a second image to use as an overlay source.

#### Blend Factor
- Controls how much of the processed blend image is mixed into the processed base image.

### Important behavior
- Blend is processed through the same core effect pipeline before compositing.
- Adjust-tab controls affect both preview rendering and final still-image rendering.

---

## 3. Finish Tab

The `Finish` tab contains display-style finishing effects and export-related tools.

## CRT Finish card

These effects are applied after the core image adjustments.

### Curvature
- Simulates curved-screen edge falloff and slight inset.

### Distortion
- Adds horizontal waviness similar to unstable CRT sync.

### Glow
- Adds phosphor-like bloom.

### Noise
- Adds static-like RGB noise.
- This is the supported noise feature.

### Scanlines
- Adds alternating horizontal dark scanlines.

### RGB Shift
- Offsets color channels for convergence-style separation.

### Vignette
- Darkens edges to push a screen-like look.

## Export card

### Save Style / Export Compression Profiles
These profile names are camera-look emulations. They are meant to imitate old digital-camera and low-quality compressed-image looks in the preview.

Available emulations:
- `No Compression`
- `Soft CCD`
- `Compact Camera`
- `Memory Saver`
- `Harsh Artifacts`

### What these emulations do
- They simulate different levels of JPEG-like degradation, resizing artifacts, and low-end camera compression behavior.
- They are intended as look-development tools so you can preview old-camera style rendering.

### Important behavior
- These compression emulations affect both the preview and the final still-image export.
- If a compression profile is selected, the saved still image is intended to match the look you are seeing in the preview, subject to normal preview scaling differences.

### Save PNG
- Saves the current fully rendered still image as PNG.
- Uses the current crop and active working effects.
- Uses full-resolution rendering.

### Save Folder
- Lets the user select an output folder.

---

## 4. Crop Tab

The `Crop` tab is working as a constrained crop system.

### Supported controls
- Left crop
- Right crop
- Top crop
- Bottom crop
- Text entry for exact crop values
- Sliders for interactive crop values
- Crop size readout
- Preset aspect ratio selection
- Reset Crop

### Presets
- Free
- 1:1
- 3:2
- 4:5
- 16:9
- 9:16
- 21:9

### Important behavior
- Crop values are clamped so at least 1 pixel remains visible.
- Opposing crop sliders update their maximums dynamically.
- Typed entry values are sanitized and clamped.
- Crop affects preview and final render.

---

## 5. Animate Tab

The `Animate` tab is working as a frame-capture and export workflow.

### Supported actions
- Add Frame
- Delete Last
- Export animation

### Working behavior
- `Add Frame` captures the current full rendered image as a frame.
- The frame strip shows recent captured frames.
- The status line reports frame count and base frame size.

### Export formats
- GIF
- MP4
- Animated WebP

### Export behavior
- FPS is configurable in the export modal.
- Frames of different sizes are normalized to the first frame size.
- MP4 export pads dimensions to even values when needed.

### Important behavior
- Animation export requires at least one captured frame.
- Animation frames are based on the rendered image state at the time of capture.

---

## 6. Palette Tab

The `Palette` tab is working as a palette extraction and export tool.

### Extract Palette
- Extracts a representative palette from the current preview image.
- Uses the currently visible preview look, not just the original source file.

### Color Count
- Controls how many colors to extract.

### Sort Colors
Supported sorting:
- Frequency
- Hue
- Brightness

### Preview swatches
- Displays a compact grid of tiny color cubes.
- Clicking a swatch copies its HEX value to the clipboard.

### Palette Values
- Shows a detailed textual readout for each extracted color.
- Includes multiple color representations for readability.

### Save Palette As
- Saves the currently extracted palette using the selected format.
- Requires a palette to be extracted first.

### Supported palette export formats
- PNG Image (1x)
- PNG Image (8x)
- PNG Image (32x)
- PAL File (JASC)
- Photoshop ASE
- Paint.net TXT
- GIMP GPL
- HEX File

### Important behavior
- Palette export is based on the currently extracted palette state.
- Swatch click copies HEX only; it does not save automatically.
- Palette tools require an image to be loaded first.

---

## 7. Randomize Behavior

Randomization is working for the approved controls only.

### Supported behavior
- A single button can randomize enabled controls.
- A settings modal allows per-control inclusion/exclusion.
- Compression-emulation profile can also be randomized in preview.

### Exclusions from approved feature set
- `Random Pixels` is not part of the approved working list.
- `Legacy Collapse / Color Collapse` is not part of the approved working list.

---

## 8. Output Behavior Summary

### Preview includes
- active glitch adjustments
- active blend processing
- active crop
- active CRT finish effects
- selected compression emulation profile

### Final still PNG export includes
- active glitch adjustments
- active blend processing
- active crop
- active CRT finish effects

### Final still PNG export also includes
- the selected compression emulation profile

---

## 9. Reliable User-Facing Behavior Summary

Right now the software works well as:
- a glitch still-image editor
- a crop-and-finish editor
- a frame capture tool for simple animated exports
- a palette extraction/export utility based on the current visual look

The most important working design rule is:

> The preview is where you explore the look interactively, and final still-image export renders the same effect stack, including the selected compression emulation profile.
