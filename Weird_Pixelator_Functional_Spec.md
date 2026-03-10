# Weird Pixelator – Functional Specification

## Overview

Weird Pixelator is a creative desktop tool for modifying images with a variety of artistic and experimental effects. It is designed for users who want to explore glitch art, color manipulation, image blending, and random visual transformations. The application provides an interactive interface for real-time experimentation and creative image processing.

---

## Core Features

### 1. Image Upload and Display

- Users can upload images in common formats (PNG, JPG, JPEG, GIF, BMP).
- The uploaded image is displayed on a central canvas for preview and editing.
- The interface automatically resizes the preview to fit the display area.

### 2. Pixelation and Glitch Effects

- **Pixelate**: Users can control the pixelation level, reducing image resolution for a blocky effect.
- **Row Jitter**: Applies horizontal displacement to random rows, creating a glitchy, distorted look.
- **Block Shift**: Randomly shifts large blocks of pixels horizontally, enhancing the glitch effect.
- **Pixel Sort**: Sorts segments of pixels by brightness, producing streaks and abstract patterns.
- All glitch effects are adjustable via intuitive sliders and can be blended together.

### 3. Color Manipulation

- **Hue Shift**: Adjusts the overall hue of the image, allowing for dramatic color changes.
- **Saturation**: Increases or decreases color intensity.
- **Contrast**: Modifies the contrast for more vivid or muted images.
- **Invert Colors**: Option to invert all colors for a negative effect, with gradual or full inversion.

### 4. Randomization

- **Randomize Effects**: Instantly applies a random combination of all available effects for creative inspiration.
- **Random Pixels**: Randomizes the color of a user-defined percentage of pixels, introducing noise and unpredictability.
- Users can customize which parameters are affected by the randomization feature.

### 5. Confuser Effects

- **Blur**: Applies a Gaussian blur to soften the image.
- **Color Reducer**: Reduces the number of colors using palette quantization for a posterized look.
- **Color Collapse (Legacy)**: Applies a coarse, buggy color quantization for unique, unpredictable results.

### 6. Image Blending

- Users can upload a second image to blend with the main image.
- The blend factor is adjustable, allowing for subtle overlays or strong composites.
- The overlay image is automatically resized to match the main image.

### 7. Saving and Export

- Users can select a destination folder and save the processed image.
- The application prompts for a filename and ensures no files are overwritten by appending numeric suffixes if needed.
- Images are saved in PNG format to preserve quality and transparency.

### 8. User Interface and Experience

- All controls are organized into labeled sections for clarity: Pixelate, Colorize, Randomize, Confuser, Blend, and Save.
- Sliders, buttons, and checkboxes provide real-time feedback and immediate visual results.
- The interface is designed for ease of use, with a dark theme for comfortable creative work.

---

## Workflow Summary

1. Upload an image to begin editing.
2. Experiment with pixelation, glitch, color, and confuser effects using the provided controls.
3. Optionally upload a second image to blend with the current image.
4. Use the randomize feature for unexpected creative results.
5. Save the final image to a chosen location.

---

## Creative Intent

Weird Pixelator is intended as a playful, experimental tool for artists, designers, and anyone interested in creative image manipulation. Its unique combination of glitch, color, and blending effects encourages exploration and serendipity in digital art.

---
