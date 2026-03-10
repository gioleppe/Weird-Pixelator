from PIL import Image, ImageFilter
import numpy as np
from PIL import ImageEnhance
from io import BytesIO


def extract_palette(image, color_count):
    """
    Extract a representative palette from an image.
    Returns a list of dicts with `rgb`, `count`, and `ratio` keys.
    """
    if image is None:
        return []

    color_count = max(1, min(256, int(color_count)))
    rgba = image.convert("RGBA")
    arr = np.array(rgba)

    if arr.ndim != 3 or arr.shape[2] < 3:
        return []

    alpha = arr[..., 3] if arr.shape[2] >= 4 else None
    if alpha is not None and np.any(alpha > 0):
        rgb_pixels = arr[alpha > 0][:, :3]
        if rgb_pixels.size == 0:
            return []
        palette_source = Image.fromarray(rgb_pixels.reshape((-1, 1, 3)).astype(np.uint8), mode="RGB")
    else:
        palette_source = rgba.convert("RGB")

    quantized = palette_source.quantize(colors=color_count, method=Image.MEDIANCUT)
    palette_values = quantized.getpalette() or []
    palette_indices = np.array(quantized).reshape(-1)
    if palette_indices.size == 0:
        return []

    unique_indices, counts = np.unique(palette_indices, return_counts=True)
    total = max(1, int(np.sum(counts)))
    entries = []

    for palette_index, count in zip(unique_indices.tolist(), counts.tolist()):
        offset = int(palette_index) * 3
        if offset + 2 >= len(palette_values):
            continue

        rgb = tuple(int(channel) for channel in palette_values[offset:offset + 3])
        entries.append({
            "rgb": rgb,
            "count": int(count),
            "ratio": float(count) / float(total),
        })

    entries.sort(key=lambda entry: entry["count"], reverse=True)
    return entries[:color_count]


def apply_data_bending(image, amount, mode="Byte Shift"):
    """
    Apply a stable databending-style JPEG byte corruption pass.
    The effect is deterministic for the same image, amount, and mode so the
    live preview does not flicker unpredictably.
    """
    if image is None or amount <= 0:
        return image

    amount = max(0.0, min(100.0, float(amount)))
    base = image.convert("RGBA")
    rgb = base.convert("RGB")
    alpha = base.getchannel("A")

    jpeg_buffer = BytesIO()
    rgb.save(jpeg_buffer, format="JPEG", quality=82, optimize=False)
    source_bytes = jpeg_buffer.getvalue()
    if len(source_bytes) < 1024:
        return image

    start = 512
    end = len(source_bytes) - 2
    if end <= start + 32:
        return image

    sample_step = max(1, len(source_bytes) // 2048)
    seed_sample = np.frombuffer(source_bytes[::sample_step], dtype=np.uint8)
    base_seed = int(seed_sample.sum())
    base_seed += rgb.size[0] * 131 + rgb.size[1] * 17 + int(round(amount * 97))
    base_seed += sum(ord(char) for char in str(mode)) * 13

    def _corrupt_bytes(scale):
        rng = np.random.default_rng(base_seed + int(scale * 1000))
        bent_bytes = bytearray(source_bytes)
        payload = bent_bytes[start:end]
        payload_length = len(payload)
        if payload_length < 64:
            return None

        strength = max(0.02, min(1.0, (amount / 100.0) * scale))
        chunk_size = max(24, min(payload_length // 3, int(payload_length * (0.008 + 0.06 * strength))))
        if chunk_size >= payload_length:
            chunk_size = max(24, payload_length // 4)

        position_limit = max(1, payload_length - chunk_size)
        pos_a = int(rng.integers(0, position_limit))
        pos_b = int(rng.integers(0, position_limit))

        if mode == "Byte Swap":
            chunk_a = payload[pos_a:pos_a + chunk_size]
            chunk_b = payload[pos_b:pos_b + chunk_size]
            payload[pos_a:pos_a + chunk_size] = chunk_b
            payload[pos_b:pos_b + chunk_size] = chunk_a
        elif mode == "Repeat Burst":
            burst = payload[pos_a:pos_a + chunk_size]
            fade = np.linspace(1.0, 0.45, num=len(burst), dtype=np.float32)
            softened = (np.frombuffer(bytes(burst), dtype=np.uint8).astype(np.float32) * fade).clip(0, 255).astype(np.uint8)
            payload[pos_b:pos_b + chunk_size] = softened.tobytes()
        else:
            shift = max(1, min(chunk_size - 1, int(chunk_size * (0.12 + 0.7 * strength))))
            chunk = payload[pos_a:pos_a + chunk_size]
            payload[pos_a:pos_a + chunk_size] = chunk[shift:] + chunk[:shift]

        bent_bytes[start:end] = payload
        return bytes(bent_bytes)

    for scale in (1.0, 0.7, 0.45, 0.25):
        candidate = _corrupt_bytes(scale)
        if candidate is None:
            continue
        try:
            bent = Image.open(BytesIO(candidate)).convert("RGB")
            result = bent.convert("RGBA")
            result.putalpha(alpha)
            return result.convert(image.mode)
        except Exception:
            continue

    return image


def _stack_glitch_bands(stacked, target_height):
    """
    Resample a glitched band stack back to the original height.
    """
    if stacked.shape[0] == target_height:
        return stacked

    sampled_indices = np.linspace(0, stacked.shape[0] - 1, num=target_height)
    sampled_indices = np.clip(np.round(sampled_indices).astype(int), 0, stacked.shape[0] - 1)
    return stacked[sampled_indices]


def _apply_tomato_style_datamosh(arr, amount, mode):
    """
    AVI-style still-image mode using reordered horizontal bands.
    Only `AVI Style` and `Reverse` are handled here.
    """
    height, width = arr.shape[:2]
    seed_sample = arr[::max(1, height // 24), ::max(1, width // 24), :3]
    seed = int(seed_sample.sum()) + width * 53 + height * 29 + int(amount * 101) + sum(ord(ch) for ch in mode)
    rng = np.random.default_rng(seed)

    strength = amount / 100.0
    band_height = max(2, min(max(2, height // 6), int(height * (0.012 + strength * 0.08))))
    bands = []
    for start in range(0, height, band_height):
        end = min(height, start + band_height)
        bands.append(arr[start:end].copy())

    if len(bands) < 2:
        return arr

    if mode == "Reverse":
        final_bands = list(reversed(bands))
    else:
        count = max(2, min(len(bands), 2 + int(round(strength * 8))))
        step = max(1, int(round(1 + (1.0 - strength) * 4)))
        anchor = int(rng.integers(0, len(bands)))
        repeat_count = max(1, int(round(1 + strength * 6)))
        grouped = [bands[index:index + count] for index in range(0, len(bands), step)]
        overlapped = [band for group in grouped for band in group]
        bloom_band = bands[anchor]
        final_bands = overlapped[:anchor] + [bloom_band.copy() for _ in range(repeat_count)] + overlapped[anchor:]

    stacked = np.vstack(final_bands)
    stacked = _stack_glitch_bands(stacked, height)

    if strength > 0.25:
        smear_width = max(1, int(round(width * (0.003 + strength * 0.02))))
        shifted = np.roll(stacked[..., :3], smear_width, axis=1)
        blend_amount = min(0.45, 0.08 + strength * 0.3)
        stacked_rgb = stacked[..., :3].astype(np.float32)
        stacked[..., :3] = (stacked_rgb * (1.0 - blend_amount) + shifted.astype(np.float32) * blend_amount).clip(0, 255).astype(np.uint8)

    return stacked


def _apply_legacy_datamosh(arr, amount, mode):
    """
    Restore two of the earlier macroblock-based datamosh looks.
    """
    height, width = arr.shape[:2]
    block_size = max(4, min(24, 4 + int(amount / 8)))
    result = arr.copy()
    seed = int(arr[::max(1, height // 32), ::max(1, width // 32), :3].sum())
    seed += width * 37 + height * 19 + int(amount * 101) + sum(ord(char) for char in mode)
    rng = np.random.default_rng(seed)

    for y in range(0, height - block_size + 1, block_size):
        for x in range(0, width - block_size + 1, block_size):
            if rng.random() > (amount / 100.0) * 0.72:
                continue

            if mode == "Block Echo":
                source_x = min(width - block_size, max(0, x - block_size * int(1 + amount / 35)))
                source_y = y
            else:
                source_x = min(width - block_size, max(0, x - block_size * int(1 + amount / 30)))
                source_y = max(0, y - int(rng.integers(0, block_size + 1)))

            block = result[source_y:source_y + block_size, source_x:source_x + block_size].copy()

            if mode == "Block Echo":
                tint = np.array([1.05, 0.96, 1.08], dtype=np.float32)
                block[..., :3] = (block[..., :3].astype(np.float32) * tint).clip(0, 255).astype(np.uint8)

            result[y:y + block_size, x:x + block_size] = block

    return result


def apply_datamosh(image, amount, mode="AVI Style"):
    """
    Four-mode datamosh effect:
    - `AVI Style`: tomato-inspired band reorder/duplication
    - `P-Frame Smear`: earlier smear look
    - `Block Echo`: earlier echo look
    - `Reverse`: reversed AVI-style bands
    """
    if image is None or amount <= 0:
        return image

    amount = max(0.0, min(100.0, float(amount)))
    arr = np.array(image.convert("RGBA"))
    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    height, width = arr.shape[:2]
    if height < 6 or width < 6:
        return image

    if mode in ("AVI Style", "Reverse"):
        glitched = _apply_tomato_style_datamosh(arr, amount, mode)
    else:
        glitched = _apply_legacy_datamosh(arr, amount, mode)

    return Image.fromarray(glitched, mode=image.mode)

def pixelate(image_object, scale_factor, jitter_val=0, block_val=0, sort_val=0):
    """
    Pixelates the image with 3 blendable glitch styles.
    - jitter_val: Horizontal row jitter (0-100)
    - block_val: Random block displacement (0-100)
    - sort_val: Horizontal pixel sorting (0-100)
    """
    if image_object is None:
        return None

    original_width, original_height = image_object.size
    source_arr = np.array(image_object.pixel_array, copy=True)

    # For pixelated previews, do the glitch work on the reduced-resolution image.
    # This preserves the aesthetic while avoiding unnecessary full-resolution passes.
    if scale_factor < 1.0:
        reduced_width = max(1, int(original_width * scale_factor))
        reduced_height = max(1, int(original_height * scale_factor))
        working_img = Image.fromarray(source_arr).resize((reduced_width, reduced_height), Image.NEAREST)
        arr = np.array(working_img)
    else:
        arr = source_arr

    height, width = arr.shape[:2]

    # 1. Style: Row Jitter (Fine horizontal displacement)
    if jitter_val > 0 and width > 1:
        probability = jitter_val / 100.0
        rows = np.flatnonzero(np.random.random(height) < probability)
        if rows.size > 0:
            max_shift = max(1, int(jitter_val / 2))
            shifts = np.random.randint(-max_shift, max_shift + 1, size=rows.size)
            column_indices = (np.arange(width)[None, :] - shifts[:, None]) % width
            arr[rows] = arr[rows[:, None], column_indices]

    # 2. Style: Block Displacement (Large chunks shifted)
    if block_val > 0 and width > 1 and height > 1:
        num_blocks = int(block_val / 5)
        for _ in range(num_blocks):
            max_h = max(2, int(height * (block_val / 100)))
            max_w = max(2, int(width * (block_val / 100)))
            h_size = np.random.randint(1, min(height, max_h) + 1)
            w_size = np.random.randint(1, min(width, max_w) + 1)
            y = np.random.randint(0, height - h_size + 1)
            x = np.random.randint(0, width - w_size + 1)
            shift = np.random.randint(-int(block_val), int(block_val) + 1)
            arr[y:y+h_size, x:x+w_size] = np.roll(arr[y:y+h_size, x:x+w_size], shift, axis=1)

    # 3. Style: Pixel Sorting (Sort segments by brightness)
    if sort_val > 0 and width > 1 and height > 0:
        for _ in range(int(sort_val)):
            y = np.random.randint(0, height)
            x_start = np.random.randint(0, width - 1)
            max_length = max(2, int(width * (sort_val / 100)))
            length = np.random.randint(1, max_length + 1)
            x_end = min(width, x_start + length)
            
            # Extract segment
            segment = arr[y, x_start:x_end]
            if len(segment) <= 1:
                continue
            # Sort by sum of RGB values (brightness proxy)
            brightness = np.sum(segment[:, :3], axis=1)
            indices = np.argsort(brightness)
            arr[y, x_start:x_end] = segment[indices]

    # Apply Pixelation (Downsample/Upsample)
    img = Image.fromarray(arr)
    if scale_factor < 1.0:
        img = img.resize((original_width, original_height), Image.NEAREST)
    
    return img

def adjust_hue(image, hue_shift):
    """
    Adjusts the hue of the image.
    hue_shift: Value in degrees (-180 to 180).
    """
    if image is None:
        return None

    img = image.convert("HSV")
    arr = np.array(img)
    arr[..., 0] = (arr[..., 0].astype(int) + int(hue_shift * 255 / 360)) % 256
    return Image.fromarray(arr, mode="HSV").convert(image.mode)

def adjust_saturation(image, saturation_factor):
    """
    Adjusts the saturation of the image.
    saturation_factor: 1.0 is no change, <1.0 is less saturated, >1.0 is more saturated.
    """
    if image is None:
        return None

    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(saturation_factor)

def adjust_contrast(image, contrast_factor):
    """
    Adjusts the contrast of the image.
    contrast_factor: 1.0 is no change, <1.0 is less contrast, >1.0 is more contrast.
    """
    if image is None:
        return None

    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(contrast_factor)

def adjust_invert(image, invert_factor):
    """
    Gradually inverts the image colors based on the invert_factor.
    invert_factor: 0.0 is original, 1.0 is fully inverted.
    """
    if image is None:
        return None

    arr = np.array(image).astype(float)

    # Separate RGB and Alpha channels if present
    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = arr[..., :3]
        alpha = arr[..., 3:]
    else:
        rgb = arr
        alpha = None

    inverted_rgb = 255 - rgb  # Fully inverted for RGB
    blended_rgb = rgb * (1 - invert_factor) + inverted_rgb * invert_factor

    if alpha is not None:
        combined = np.concatenate((blended_rgb, alpha), axis=-1)
        mode = "RGBA"
    else:
        combined = blended_rgb
        mode = "RGB"

    return Image.fromarray(combined.clip(0, 255).astype(np.uint8), mode=mode)

def invert_image(image, invert_state):
    """
    Conditionally inverts the image colors based on invert_state.
    Only inverts RGB channels, leaving alpha (transparency) unchanged.
    """
    if image is None or not invert_state:
        return image

    arr = np.array(image).astype(float)
    # Separate RGB and Alpha channels
    rgb = arr[..., :3]
    alpha = arr[..., 3:] if arr.shape[-1] == 4 else None

    # Invert only the RGB channels
    inverted_rgb = 255 - rgb

    # Combine back with Alpha channel if it exists
    if alpha is not None:
        combined = np.concatenate((inverted_rgb, alpha), axis=-1)
    else:
        combined = inverted_rgb

    # Ensure the output is in the correct mode
    mode = "RGBA" if alpha is not None else "RGB"
    return Image.fromarray(combined.clip(0, 255).astype(np.uint8), mode=mode)

def randomize_pixels(image, random_factor):
    """
    Optimized randomization of pixel colors based on the random_factor.
    random_factor: 0.0 means no randomization, 1.0 means all pixels are randomized.
    """
    if image is None:
        return None

    arr = np.array(image).astype(float)
    height, width = arr.shape[0], arr.shape[1]
    channels = arr.shape[2] if arr.ndim == 3 else 1

    # Generate random indices for pixels to randomize
    num_pixels = int(random_factor * height * width)
    if num_pixels == 0:
        return image
    indices = np.random.choice(height * width, size=num_pixels, replace=False)

    # Convert flat indices to 2D coordinates
    y_coords, x_coords = np.unravel_index(indices, (height, width))

    # Randomize only RGB channels, preserve alpha if present
    if channels >= 3:
        random_rgb = np.random.randint(0, 256, size=(num_pixels, 3))
        arr[y_coords, x_coords, :3] = random_rgb
    else:
        # Grayscale or unexpected format: randomize the single channel
        arr[y_coords, x_coords] = np.random.randint(0, 256, size=(num_pixels,))

    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)

def reduce_colors(image, color_bins):
    """
    Reduces the number of colors in the image by quantizing the color space.
    color_bins: Number of color bins (e.g., 256 for full color, lower for fewer colors).
    """
    if image is None:
        return None

    # Clamp color_bins to valid range
    color_bins = max(1, min(256, int(color_bins)))

    # Use Pillow's quantize for better color reduction (palette-based)
    # Preserve alpha channel if present
    img = image.convert("RGBA")
    arr = np.array(img)
    has_alpha = (arr.ndim == 3 and arr.shape[2] == 4)

    if has_alpha:
        # Separate alpha, quantize RGB, then reattach alpha
        rgb_img = Image.fromarray(arr[..., :3], mode="RGB")
        quant = rgb_img.quantize(colors=color_bins, method=Image.MEDIANCUT)
        quant_rgb = quant.convert("RGB")
        quant_arr = np.array(quant_rgb)
        combined = np.dstack((quant_arr, arr[..., 3]))
        return Image.fromarray(combined, mode="RGBA")
    else:
        rgb_img = image.convert("RGB")
        quant = rgb_img.quantize(colors=color_bins, method=Image.MEDIANCUT)
        return quant.convert(image.mode)


def reduce_colors_legacy(image, color_bins):
    """
    Legacy/broken color reducer kept for aesthetic: coarse quantization
    that also affects alpha (matches the previous buggy behavior you liked).
    """
    if image is None:
        return None

    arr = np.array(image)
    color_bins = max(1, min(256, int(color_bins)))
    factor = max(1, 256 // color_bins)

    # Apply naive quantization to the entire array (including alpha if present)
    quantized_arr = (arr // factor) * factor + factor // 2
    return Image.fromarray(quantized_arr.clip(0, 255).astype(np.uint8), mode=image.mode)


def apply_horizontal_distortion(image, strength):
    """
    Add subtle wavy horizontal distortion like an unstable CRT signal.
    strength: 0-100.
    """
    if image is None or strength <= 0:
        return image

    arr = np.array(image)
    if arr.ndim != 3:
        return image

    height, width = arr.shape[:2]
    amplitude = max(1, int((strength / 100.0) * max(2, width * 0.02)))
    frequency = 2.0 + (strength / 100.0) * 6.0

    distorted = arr.copy()
    rows = np.arange(height)
    offsets = np.round(np.sin(rows / max(1.0, height / frequency) * np.pi * 2.0) * amplitude).astype(int)

    for row, offset in enumerate(offsets):
        distorted[row] = np.roll(arr[row], offset, axis=0)

    return Image.fromarray(distorted, mode=image.mode)


def apply_screen_curvature(image, strength):
    """
    Darken corners and slightly compress edges to suggest CRT glass curvature.
    strength: 0-100.
    """
    if image is None or strength <= 0:
        return image

    arr = np.array(image).astype(np.float32)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    height, width = arr.shape[:2]
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)
    center_x = max((width - 1) / 2.0, 1.0)
    center_y = max((height - 1) / 2.0, 1.0)

    x_norm = (x_indices - center_x) / center_x
    y_norm = (y_indices - center_y) / center_y
    radial = x_norm ** 2 + y_norm ** 2

    amount = strength / 100.0
    edge_mask = 1.0 - np.clip(radial * 0.18 * amount, 0.0, 0.22)
    arr[..., :3] *= edge_mask[..., np.newaxis]

    inset_x = int(width * 0.015 * amount)
    inset_y = int(height * 0.015 * amount)
    if inset_x > 0 or inset_y > 0:
        curved = Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)
        shrunk = curved.resize((max(1, width - inset_x * 2), max(1, height - inset_y * 2)), Image.LANCZOS)
        canvas = Image.new(image.mode, (width, height), (0, 0, 0, 255) if 'A' in image.mode else (0, 0, 0))
        canvas.paste(shrunk, (inset_x, inset_y))
        return canvas

    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)


def apply_phosphor_glow(image, strength):
    """
    Add a soft bloom to bright areas for a phosphor glow effect.
    strength: 0-100.
    """
    if image is None or strength <= 0:
        return image

    amount = strength / 100.0
    base = image.convert("RGBA")
    radius = max(1, int(1 + amount * 6))
    glow = base.filter(ImageFilter.GaussianBlur(radius))
    return Image.blend(base, glow, min(0.55, amount * 0.55)).convert(image.mode)


def apply_static_noise(image, strength):
    """
    Add RGB noise like CRT static.
    strength: 0-100.
    """
    if image is None or strength <= 0:
        return image

    arr = np.array(image).astype(np.float32)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    amplitude = 5.0 + (strength / 100.0) * 35.0
    noise = np.random.normal(0.0, amplitude, size=arr[..., :3].shape)
    arr[..., :3] += noise
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)


def apply_scanlines(image, intensity):
    """
    Add dark horizontal scanlines for a CRT-like display effect.
    intensity: 0-100.
    """
    if image is None or intensity <= 0:
        return image

    strength = max(0.0, min(1.0, intensity / 100.0))
    arr = np.array(image).astype(np.float32)

    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    darken_factor = 1.0 - (0.55 * strength)
    mask = np.ones((arr.shape[0], 1, 1), dtype=np.float32)
    mask[1::2, :, :] = darken_factor
    arr[..., :3] *= mask

    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)


def apply_rgb_shift(image, shift_amount):
    """
    Slightly offset the red and blue channels to mimic CRT convergence issues.
    shift_amount: 0-20 pixels.
    """
    if image is None or shift_amount <= 0:
        return image

    arr = np.array(image)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    shift = int(shift_amount)
    shifted = arr.copy()
    shifted[..., 0] = np.roll(arr[..., 0], shift, axis=1)
    shifted[..., 2] = np.roll(arr[..., 2], -shift, axis=1)
    return Image.fromarray(shifted, mode=image.mode)


def apply_vignette(image, strength):
    """
    Darken image edges to simulate a curved CRT screen.
    strength: 0-100.
    """
    if image is None or strength <= 0:
        return image

    amount = max(0.0, min(1.0, strength / 100.0))
    arr = np.array(image).astype(np.float32)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return image

    height, width = arr.shape[:2]
    y_indices, x_indices = np.ogrid[:height, :width]
    center_x = max((width - 1) / 2.0, 1.0)
    center_y = max((height - 1) / 2.0, 1.0)

    distance = np.sqrt(((x_indices - center_x) / center_x) ** 2 + ((y_indices - center_y) / center_y) ** 2)
    distance = np.clip(distance / np.sqrt(2.0), 0.0, 1.0)

    mask = 1.0 - (0.85 * amount * (distance ** 1.8))
    mask = np.clip(mask, 0.15, 1.0)
    arr[..., :3] *= mask[..., np.newaxis]

    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), mode=image.mode)


def blend_images(base_image, overlay_image, factor):
    """
    Blend `overlay_image` into `base_image` using `factor` (0.0..1.0).
    The overlay is resized to match the base image size.
    Both images are converted to RGBA to preserve transparency.
    """
    if base_image is None:
        return overlay_image if overlay_image is not None else None
    if overlay_image is None or factor <= 0.0:
        return base_image

    base = base_image.convert("RGBA")
    overlay = overlay_image.convert("RGBA")

    if overlay.size != base.size:
        overlay = overlay.resize(base.size, Image.LANCZOS)

    # Use Image.blend which linearly interpolates between two images
    blended = Image.blend(base, overlay, factor)
    return blended


def _jpeg_roundtrip(image, quality, subsampling=2):
    """
    Run an image through JPEG encoding/decoding to introduce compression artifacts.
    """
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, subsampling=subsampling, optimize=False)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def apply_export_compression(image, profile_name):
    """
    Apply save-only compression that mimics old digital camera artifacts.
    """
    if image is None or not profile_name or profile_name == "No Compression":
        return image

    base = image.convert("RGBA")
    rgb = base.convert("RGB")
    alpha = base.getchannel("A")
    width, height = rgb.size

    if profile_name == "Soft CCD":
        rgb = _jpeg_roundtrip(rgb, quality=58, subsampling=1)
    elif profile_name == "Compact Camera":
        reduced = rgb.resize((max(1, int(width * 0.92)), max(1, int(height * 0.92))), Image.BILINEAR)
        rgb = _jpeg_roundtrip(reduced.resize((width, height), Image.BILINEAR), quality=38, subsampling=2)
    elif profile_name == "Memory Saver":
        reduced = rgb.resize((max(1, int(width * 0.84)), max(1, int(height * 0.84))), Image.BILINEAR)
        rgb = _jpeg_roundtrip(reduced.resize((width, height), Image.BILINEAR), quality=22, subsampling=2)
        rgb = _jpeg_roundtrip(rgb, quality=20, subsampling=2)
    elif profile_name == "Harsh Artifacts":
        reduced = rgb.resize((max(1, int(width * 0.72)), max(1, int(height * 0.72))), Image.NEAREST)
        rgb = _jpeg_roundtrip(reduced.resize((width, height), Image.NEAREST), quality=10, subsampling=2)
        rgb = _jpeg_roundtrip(rgb, quality=8, subsampling=2)
    else:
        return image

    compressed = rgb.convert("RGBA")
    compressed.putalpha(alpha)
    return compressed
