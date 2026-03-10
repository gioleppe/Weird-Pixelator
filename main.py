import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
from PIL import Image, ImageTk, ImageFilter
import numpy as np
from image_object import ImageObject
import image_effects

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Weird Pixelator")
        self.is_macos = self.root.tk.call("tk", "windowingsystem") == "aqua"

        self.image_object = None
        self.current_pil_image = None
        self.pipeline_image = None
        self.full_resolution_image = None
        self.blend_image_pil = None
        self.randomize_settings = self._create_randomize_settings()
        self.preview_delay_ms = 75
        self._pending_preview_job = None
        self._suspend_preview_updates = False
        self._updating_crop_entries = False
        self._syncing_crop_controls = False
        self.crop_left_var = tk.StringVar(value="0")
        self.crop_right_var = tk.StringVar(value="0")
        self.crop_top_var = tk.StringVar(value="0")
        self.crop_bottom_var = tk.StringVar(value="0")
        self.crop_size_var = tk.StringVar(value="Final Size: -")
        self.crop_preset_var = tk.StringVar(value="Free")
        self._updating_crop_preset = False
        self.export_compression_var = tk.StringVar(value="No Compression")

        # Canvas for displaying the image
        self.canvas = tk.Canvas(root, width=400, height=400, bg="gray")
        self.canvas.pack(pady=10)

        # Button to upload image
        self.upload_button = tk.Button(root, text="Upload Image", command=self.upload_image, **self._button_style("#444"))
        self.upload_button.pack(pady=5)

        # --- Main Controls Container ---
        self.main_controls_container = tk.Frame(root)
        self.main_controls_container.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Correctly configure the grid layout for all sections
        self.main_controls_container.grid_columnconfigure(0, weight=1)
        self.main_controls_container.grid_columnconfigure(1, weight=1)
        self.main_controls_container.grid_columnconfigure(2, weight=1)
        self.main_controls_container.grid_columnconfigure(3, weight=1)
        self.main_controls_container.grid_columnconfigure(4, weight=1)
        self.main_controls_container.grid_columnconfigure(5, weight=1)
        self.main_controls_container.grid_rowconfigure(0, weight=1)
        self.main_controls_container.grid_rowconfigure(1, weight=1)

        # --- Pixelate Section ---
        self.pixelate_frame = tk.LabelFrame(
            self.main_controls_container, 
            text="Pixelate", 
            padx=10, pady=10,
            fg="white", bg="#2e2e2e", # Dark background for better contrast
            highlightbackground="white", highlightthickness=1
        )
        self.pixelate_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        root.configure(bg="#2e2e2e") # Set app background

        # Glitch Styles inside Pixelate Section
        tk.Label(self.pixelate_frame, text="Row Jitter:", fg="white", bg="#2e2e2e").grid(row=0, column=0, sticky="w")
        self.jitter_slider = tk.Scale(self.pixelate_frame, from_=0, to=100, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_effects)
        self.jitter_slider.set(0)
        self.jitter_slider.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(self.pixelate_frame, text="Block Shift:", fg="white", bg="#2e2e2e").grid(row=1, column=0, sticky="w")
        self.block_slider = tk.Scale(self.pixelate_frame, from_=0, to=100, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_effects)
        self.block_slider.set(0)
        self.block_slider.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(self.pixelate_frame, text="Pixel Sort:", fg="white", bg="#2e2e2e").grid(row=2, column=0, sticky="w")
        self.sort_slider = tk.Scale(self.pixelate_frame, from_=0, to=100, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_effects)
        self.sort_slider.set(0)
        self.sort_slider.grid(row=2, column=1, sticky="ew", padx=5)

        tk.Label(self.pixelate_frame, text="Pixelate:", fg="white", bg="#2e2e2e").grid(row=3, column=0, sticky="w")
        self.pixel_slider = tk.Scale(self.pixelate_frame, from_=1.0, to=0.01, resolution=0.01, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_effects)
        self.pixel_slider.set(1.0)
        self.pixel_slider.grid(row=3, column=1, sticky="ew", padx=5)

        self.pixelate_frame.columnconfigure(1, weight=1)

        # --- CRT Section ---
        self.crt_frame = tk.LabelFrame(
            self.main_controls_container,
            text="CRT",
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.crt_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=(5, 0))

        for col in range(4):
            self.crt_frame.grid_columnconfigure(col, weight=1)

        tk.Label(self.crt_frame, text="Curvature:", fg="white", bg="#2e2e2e").grid(row=0, column=0, sticky="w")
        self.curvature_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.curvature_slider.set(0)
        self.curvature_slider.grid(row=0, column=1, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="Distortion:", fg="white", bg="#2e2e2e").grid(row=0, column=2, sticky="w")
        self.distortion_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.distortion_slider.set(0)
        self.distortion_slider.grid(row=0, column=3, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="Glow:", fg="white", bg="#2e2e2e").grid(row=1, column=0, sticky="w")
        self.glow_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.glow_slider.set(0)
        self.glow_slider.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="Noise:", fg="white", bg="#2e2e2e").grid(row=1, column=2, sticky="w")
        self.noise_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.noise_slider.set(0)
        self.noise_slider.grid(row=1, column=3, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="RGB Shift:", fg="white", bg="#2e2e2e").grid(row=2, column=0, sticky="w")
        self.rgb_shift_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=20,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.rgb_shift_slider.set(0)
        self.rgb_shift_slider.grid(row=2, column=1, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="Scanlines:", fg="white", bg="#2e2e2e").grid(row=2, column=2, sticky="w")
        self.scanline_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.scanline_slider.set(0)
        self.scanline_slider.grid(row=2, column=3, sticky="ew", padx=5)

        tk.Label(self.crt_frame, text="Vignette:", fg="white", bg="#2e2e2e").grid(row=3, column=0, sticky="w")
        self.vignette_slider = tk.Scale(
            self.crt_frame,
            from_=0, to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_crt
        )
        self.vignette_slider.set(0)
        self.vignette_slider.grid(row=3, column=1, sticky="ew", padx=5)

        # --- Crop Section ---
        self.crop_frame = tk.LabelFrame(
            self.main_controls_container,
            text="Crop",
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.crop_frame.grid(row=1, column=4, columnspan=2, sticky="nsew", padx=5, pady=(5, 0))
        for col in range(4):
            self.crop_frame.grid_columnconfigure(col, weight=1)

        tk.Label(self.crop_frame, text="Left:", fg="white", bg="#2e2e2e").grid(row=0, column=0, sticky="w")
        self.crop_left_slider = tk.Scale(
            self.crop_frame,
            from_=0, to=0,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=lambda _value: self.update_crop("left")
        )
        self.crop_left_slider.set(0)
        self.crop_left_slider.grid(row=1, column=0, sticky="ew", padx=5)

        self.crop_left_entry = tk.Entry(self.crop_frame, textvariable=self.crop_left_var, bg="#444", fg="white", insertbackground="white", width=8)
        self.crop_left_entry.grid(row=2, column=0, sticky="ew", padx=5)
        self.crop_left_entry.bind("<Return>", lambda _event: self.commit_crop_entry("left"))
        self.crop_left_entry.bind("<FocusOut>", lambda _event: self.commit_crop_entry("left"))

        tk.Label(self.crop_frame, text="Right:", fg="white", bg="#2e2e2e").grid(row=0, column=1, sticky="w")
        self.crop_right_slider = tk.Scale(
            self.crop_frame,
            from_=0, to=0,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=lambda _value: self.update_crop("right")
        )
        self.crop_right_slider.set(0)
        self.crop_right_slider.grid(row=1, column=1, sticky="ew", padx=5)

        self.crop_right_entry = tk.Entry(self.crop_frame, textvariable=self.crop_right_var, bg="#444", fg="white", insertbackground="white", width=8)
        self.crop_right_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.crop_right_entry.bind("<Return>", lambda _event: self.commit_crop_entry("right"))
        self.crop_right_entry.bind("<FocusOut>", lambda _event: self.commit_crop_entry("right"))

        tk.Label(self.crop_frame, text="Top:", fg="white", bg="#2e2e2e").grid(row=0, column=2, sticky="w")
        self.crop_top_slider = tk.Scale(
            self.crop_frame,
            from_=0, to=0,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=lambda _value: self.update_crop("top")
        )
        self.crop_top_slider.set(0)
        self.crop_top_slider.grid(row=1, column=2, sticky="ew", padx=5)

        self.crop_top_entry = tk.Entry(self.crop_frame, textvariable=self.crop_top_var, bg="#444", fg="white", insertbackground="white", width=8)
        self.crop_top_entry.grid(row=2, column=2, sticky="ew", padx=5)
        self.crop_top_entry.bind("<Return>", lambda _event: self.commit_crop_entry("top"))
        self.crop_top_entry.bind("<FocusOut>", lambda _event: self.commit_crop_entry("top"))

        tk.Label(self.crop_frame, text="Bottom:", fg="white", bg="#2e2e2e").grid(row=0, column=3, sticky="w")
        self.crop_bottom_slider = tk.Scale(
            self.crop_frame,
            from_=0, to=0,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=lambda _value: self.update_crop("bottom")
        )
        self.crop_bottom_slider.set(0)
        self.crop_bottom_slider.grid(row=1, column=3, sticky="ew", padx=5)

        self.crop_bottom_entry = tk.Entry(self.crop_frame, textvariable=self.crop_bottom_var, bg="#444", fg="white", insertbackground="white", width=8)
        self.crop_bottom_entry.grid(row=2, column=3, sticky="ew", padx=5)
        self.crop_bottom_entry.bind("<Return>", lambda _event: self.commit_crop_entry("bottom"))
        self.crop_bottom_entry.bind("<FocusOut>", lambda _event: self.commit_crop_entry("bottom"))

        self.crop_size_label = tk.Label(self.crop_frame, textvariable=self.crop_size_var, fg="#c8c8c8", bg="#2e2e2e")
        self.crop_size_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(6, 0))

        tk.Label(self.crop_frame, text="Preset:", fg="#c8c8c8", bg="#2e2e2e").grid(row=3, column=2, sticky="e", padx=(5, 0), pady=(6, 0))
        self.crop_preset_menu = tk.OptionMenu(
            self.crop_frame,
            self.crop_preset_var,
            "Free",
            "1:1",
            "3:2",
            "4:5",
            "16:9",
            "9:16",
            "21:9",
            command=self.apply_crop_preset
        )
        self.crop_preset_menu.configure(bg="#444", fg="white", activebackground="#555", activeforeground="white", highlightthickness=0)
        self.crop_preset_menu["menu"].configure(bg="#444", fg="white")
        self.crop_preset_menu.grid(row=3, column=3, sticky="ew", padx=5, pady=(6, 0))

        self.reset_crop_button = tk.Button(
            self.crop_frame,
            text="Reset Crop",
            command=self.reset_crop,
            **self._button_style("#444")
        )
        self.reset_crop_button.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=(8, 0))

        # --- Export Compression Section ---
        self.export_frame = tk.LabelFrame(
            self.main_controls_container,
            text="Export Compression",
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.export_frame.grid(row=0, column=5, sticky="nsew", padx=5)
        self.export_frame.grid_columnconfigure(0, weight=1)

        tk.Label(self.export_frame, text="Save Style:", fg="white", bg="#2e2e2e").pack(anchor="w")
        self.export_compression_menu = tk.OptionMenu(
            self.export_frame,
            self.export_compression_var,
            "No Compression",
            "Soft CCD",
            "Compact Camera",
            "Memory Saver",
            "Harsh Artifacts",
            command=self.update_export_compression
        )
        self.export_compression_menu.configure(bg="#444", fg="white", activebackground="#555", activeforeground="white", highlightthickness=0)
        self.export_compression_menu["menu"].configure(bg="#444", fg="white")
        self.export_compression_menu.pack(fill=tk.X, pady=(4, 8))

        tk.Label(
            self.export_frame,
            text="Live preview + save",
            fg="#c8c8c8", bg="#2e2e2e",
            justify=tk.LEFT,
            wraplength=160
        ).pack(anchor="w")

        # --- Colorize Section ---
        self.colorize_frame = tk.LabelFrame(
            self.main_controls_container, 
            text="Colorize", 
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.colorize_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # Hue Slider
        tk.Label(self.colorize_frame, text="Hue Shift:", fg="white", bg="#2e2e2e").grid(row=0, column=0, sticky="w")
        self.hue_slider = tk.Scale(self.colorize_frame, from_=-180, to=180, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_colorize)
        self.hue_slider.set(0)
        self.hue_slider.grid(row=0, column=1, sticky="ew", padx=5)

        # Saturation Slider
        tk.Label(self.colorize_frame, text="Saturation:", fg="white", bg="#2e2e2e").grid(row=1, column=0, sticky="w")
        self.saturation_slider = tk.Scale(self.colorize_frame, from_=0.0, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_colorize)
        self.saturation_slider.set(1.0)
        self.saturation_slider.grid(row=1, column=1, sticky="ew", padx=5)

        # Contrast Slider
        tk.Label(self.colorize_frame, text="Contrast:", fg="white", bg="#2e2e2e").grid(row=2, column=0, sticky="w")
        self.contrast_slider = tk.Scale(self.colorize_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_colorize)
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=2, column=1, sticky="ew", padx=5)

        # Invert Button
        self.invert_button = tk.Checkbutton(
            self.colorize_frame, 
            text="Invert Colors", 
            command=self.toggle_invert,
            bg="#2e2e2e", fg="white", selectcolor="#444"
        )
        self.invert_button.grid(row=3, column=0, columnspan=2, pady=5)
        self.invert_state = tk.BooleanVar(value=False)
        self.invert_button.config(variable=self.invert_state)

        self.colorize_frame.columnconfigure(1, weight=1)

        # --- Randomize Section ---
        self.randomize_frame = tk.LabelFrame(
            self.main_controls_container, 
            text="Randomize", 
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.randomize_frame.grid(row=0, column=2, sticky="nsew", padx=5)

        # Randomize Button
        self.randomize_button = tk.Button(
            self.randomize_frame, 
            text="Randomize Effects", 
            command=self.randomize_effects,
            **self._button_style("#444")
        )
        self.randomize_button.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Random Pixel Randomization Slider
        tk.Label(self.randomize_frame, text="Random Pixels:", fg="white", bg="#2e2e2e").pack(anchor="w")
        self.random_pixel_slider = tk.Scale(
            self.randomize_frame, 
            from_=0.0, to=1.0, 
            resolution=0.01, 
            orient=tk.HORIZONTAL, 
            bg="#2e2e2e", fg="white", troughcolor="#444", 
            command=self.update_random_pixels
        )
        self.random_pixel_slider.set(0.0)
        self.random_pixel_slider.pack(fill=tk.X, padx=5, pady=5)

        # --- Save Section ---
        self.save_frame = tk.Frame(root, bg="#2e2e2e")
        self.save_frame.pack(pady=10, padx=10, fill=tk.X)

        # Folder Selector
        self.folder_path = tk.StringVar()
        self.folder_entry = tk.Entry(self.save_frame, textvariable=self.folder_path, bg="#444", fg="white")
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.browse_button = tk.Button(
            self.save_frame, text="Browse", command=self.select_folder, **self._button_style("#444")
        )
        self.browse_button.pack(side=tk.LEFT, padx=5)

        # Save Button
        self.save_button = tk.Button(
            self.save_frame, text="Save Image", command=self.save_image, **self._button_style("#444")
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Randomize Settings Button
        self.randomize_settings_button = tk.Button(
            self.save_frame, text="Settings", command=self.open_randomize_settings, **self._button_style("#666")
        )
        self.randomize_settings_button.pack(side=tk.LEFT, padx=5)

        # --- Confuser Section ---
        self.confuser_frame = tk.LabelFrame(
            self.main_controls_container, 
            text="Confuser", 
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.confuser_frame.grid(row=0, column=3, sticky="nsew", padx=5)

        # Blur Slider
        tk.Label(self.confuser_frame, text="Blur:", fg="white", bg="#2e2e2e").grid(row=0, column=0, sticky="w")
        self.blur_slider = tk.Scale(
            self.confuser_frame, 
            from_=0, to=10, 
            resolution=1, 
            orient=tk.HORIZONTAL, 
            bg="#2e2e2e", fg="white", troughcolor="#444", 
            command=self.update_confuser
        )
        self.blur_slider.set(0)
        self.blur_slider.grid(row=0, column=1, sticky="ew", padx=5)

        # Color Reducer Slider
        tk.Label(self.confuser_frame, text="Color Reducer:", fg="white", bg="#2e2e2e").grid(row=1, column=0, sticky="w")
        self.color_reducer_slider = tk.Scale(
            self.confuser_frame, 
            from_=2, to=256, 
            resolution=1, 
            orient=tk.HORIZONTAL, 
            bg="#2e2e2e", fg="white", troughcolor="#444", 
            command=self.update_confuser
        )
        self.color_reducer_slider.set(256)
        self.color_reducer_slider.grid(row=1, column=1, sticky="ew", padx=5)

        # Legacy Color Collapse Slider (previous buggy behavior kept as an option)
        tk.Label(self.confuser_frame, text="Color Collapse:", fg="white", bg="#2e2e2e").grid(row=2, column=0, sticky="w")
        self.legacy_color_slider = tk.Scale(
            self.confuser_frame,
            from_=2, to=256,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg="#2e2e2e", fg="white", troughcolor="#444",
            command=self.update_confuser
        )
        self.legacy_color_slider.set(256)
        self.legacy_color_slider.grid(row=2, column=1, sticky="ew", padx=5)

        self.confuser_frame.columnconfigure(1, weight=1)

        # --- Blend Section ---
        self.blend_frame = tk.LabelFrame(
            self.main_controls_container,
            text="Blend",
            padx=10, pady=10,
            fg="white", bg="#2e2e2e",
            highlightbackground="white", highlightthickness=1
        )
        self.blend_frame.grid(row=0, column=4, sticky="nsew", padx=5)

        # Upload Blend Image Button
        self.upload_blend_button = tk.Button(self.blend_frame, text="Upload Blend Image", command=self.upload_blend_image, **self._button_style("#444"))
        self.upload_blend_button.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,5))

        # Label to show selected blend filename
        self.blend_filename_var = tk.StringVar(value="No file")
        tk.Label(self.blend_frame, textvariable=self.blend_filename_var, fg="white", bg="#2e2e2e").grid(row=1, column=0, columnspan=2, sticky="w")

        # Blend Factor Slider
        tk.Label(self.blend_frame, text="Blend Factor:", fg="white", bg="#2e2e2e").grid(row=2, column=0, sticky="w")
        self.blend_slider = tk.Scale(self.blend_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, bg="#2e2e2e", fg="white", troughcolor="#444", command=self.update_blend)
        self.blend_slider.set(0.0)
        self.blend_slider.grid(row=2, column=1, sticky="ew", padx=5)

        self.blend_frame.columnconfigure(1, weight=1)
        self._sync_crop_controls_to_image(reset_values=True)

    def _button_style(self, background):
        """
        Use readable button text on macOS while preserving the dark look elsewhere.
        """
        foreground = "#111111" if self.is_macos else "white"
        return {
            "bg": background,
            "fg": foreground,
            "activebackground": background,
            "activeforeground": foreground,
            "disabledforeground": foreground,
            "highlightbackground": background,
        }

    def _create_randomize_settings(self):
        """
        Create the default Randomize settings state.
        """
        keys = [
            'pixel_scale', 'jitter', 'block', 'sort',
            'hue', 'saturation', 'contrast', 'invert',
            'random_pixels', 'blur', 'color_reducer', 'legacy_collapse', 'blend',
            'curvature', 'distortion', 'glow', 'noise', 'rgb_shift', 'scanlines', 'vignette',
            'compression'
        ]
        defaults = {key: True for key in keys}
        defaults['random_pixels'] = False
        defaults['blur'] = False
        defaults['legacy_collapse'] = False
        return {key: tk.BooleanVar(value=defaults[key]) for key in keys}

    def _reset_controls_for_new_image(self):
        """
        Reset all effect controls so a newly loaded image starts clean.
        """
        self.begin_bulk_update()
        try:
            self.pixel_slider.set(1.0)
            self.jitter_slider.set(0)
            self.block_slider.set(0)
            self.sort_slider.set(0)

            self.hue_slider.set(0)
            self.saturation_slider.set(1.0)
            self.contrast_slider.set(1.0)
            self.invert_state.set(False)

            self.random_pixel_slider.set(0.0)

            self.blur_slider.set(0)
            self.color_reducer_slider.set(256)
            self.legacy_color_slider.set(256)

            self.curvature_slider.set(0)
            self.distortion_slider.set(0)
            self.glow_slider.set(0)
            self.noise_slider.set(0)
            self.scanline_slider.set(0)
            self.rgb_shift_slider.set(0)
            self.vignette_slider.set(0)

            self.blend_slider.set(0.0)
            self.blend_image_pil = None
            self.blend_filename_var.set("No file")
            self.export_compression_var.set("No Compression")
            self._sync_crop_controls_to_image(reset_values=True)

            self.pipeline_image = None
            self.full_resolution_image = None
        finally:
            self.end_bulk_update(refresh=False)

    def _set_crop_entry_value(self, edge, value):
        """
        Update a crop entry without triggering recursive commits.
        """
        target_var = {
            "left": self.crop_left_var,
            "right": self.crop_right_var,
            "top": self.crop_top_var,
            "bottom": self.crop_bottom_var,
        }[edge]
        self._updating_crop_entries = True
        try:
            target_var.set(str(int(value)))
        finally:
            self._updating_crop_entries = False

    def _set_crop_preset_value(self, value):
        """
        Update the crop preset selector without triggering preset reapplication.
        """
        self._updating_crop_preset = True
        try:
            self.crop_preset_var.set(value)
        finally:
            self._updating_crop_preset = False

    def _set_crop_controls(self, left, right, top, bottom):
        """
        Update all crop controls in one synchronized operation.
        """
        self._syncing_crop_controls = True
        try:
            self.crop_left_slider.set(left)
            self.crop_right_slider.set(right)
            self.crop_top_slider.set(top)
            self.crop_bottom_slider.set(bottom)
            self._set_crop_entry_value("left", left)
            self._set_crop_entry_value("right", right)
            self._set_crop_entry_value("top", top)
            self._set_crop_entry_value("bottom", bottom)
        finally:
            self._syncing_crop_controls = False

    def _get_crop_presets(self):
        """
        Return supported crop aspect presets.
        """
        return {
            "1:1": 1.0,
            "3:2": 3.0 / 2.0,
            "4:5": 4.0 / 5.0,
            "16:9": 16.0 / 9.0,
            "9:16": 9.0 / 16.0,
            "21:9": 21.0 / 9.0,
        }

    def _update_crop_metadata(self):
        """
        Refresh the live crop size readout and preset state.
        """
        if self.current_pil_image is None:
            self.crop_size_var.set("Final Size: -")
            self._set_crop_preset_value("Free")
            return

        left, top, right, bottom = self._get_active_crop_box(self.current_pil_image.size)
        crop_width = max(1, right - left)
        crop_height = max(1, bottom - top)
        self.crop_size_var.set(f"Final Size: {crop_width} x {crop_height}")

        ratio = crop_width / crop_height if crop_height else 0.0
        matched_preset = "Free"
        for label, target_ratio in self._get_crop_presets().items():
            if abs(ratio - target_ratio) <= 0.03:
                matched_preset = label
                break

        self._set_crop_preset_value(matched_preset)

    def _sync_crop_controls_to_image(self, reset_values=True):
        """
        Sync crop slider ranges and values to the currently loaded image.
        """
        if self.current_pil_image is None:
            max_width = 1
            max_height = 1
        else:
            max_width, max_height = self.current_pil_image.size

        width_limit = max(0, max_width - 1)
        height_limit = max(0, max_height - 1)

        self.crop_left_slider.configure(from_=0, to=width_limit)
        self.crop_right_slider.configure(from_=0, to=width_limit)
        self.crop_top_slider.configure(from_=0, to=height_limit)
        self.crop_bottom_slider.configure(from_=0, to=height_limit)

        if reset_values:
            left = right = top = bottom = 0
        else:
            left = min(width_limit, max(0, int(float(self.crop_left_slider.get()))))
            right = min(width_limit, max(0, int(float(self.crop_right_slider.get()))))
            top = min(height_limit, max(0, int(float(self.crop_top_slider.get()))))
            bottom = min(height_limit, max(0, int(float(self.crop_bottom_slider.get()))))

        self._set_crop_controls(left, right, top, bottom)

        self._normalize_crop_controls()

    def _normalize_crop_controls(self, preferred_edge=None):
        """
        Clamp crop margins so the remaining visible area is always at least 1 pixel.
        """
        if self.current_pil_image is None:
            return

        width, height = self.current_pil_image.size
        width_limit = max(0, width - 1)
        height_limit = max(0, height - 1)

        left = min(width_limit, max(0, int(float(self.crop_left_slider.get()))))
        right = min(width_limit, max(0, int(float(self.crop_right_slider.get()))))
        top = min(height_limit, max(0, int(float(self.crop_top_slider.get()))))
        bottom = min(height_limit, max(0, int(float(self.crop_bottom_slider.get()))))

        if left + right > width_limit:
            if preferred_edge == "right":
                right = max(0, width_limit - left)
            else:
                left = max(0, width_limit - right)

        if top + bottom > height_limit:
            if preferred_edge == "bottom":
                bottom = max(0, height_limit - top)
            else:
                top = max(0, height_limit - bottom)

        max_left = max(0, width_limit - right)
        max_right = max(0, width_limit - left)
        max_top = max(0, height_limit - bottom)
        max_bottom = max(0, height_limit - top)

        self._syncing_crop_controls = True
        try:
            self.crop_left_slider.configure(to=max_left)
            self.crop_right_slider.configure(to=max_right)
            self.crop_top_slider.configure(to=max_top)
            self.crop_bottom_slider.configure(to=max_bottom)

            self.crop_left_slider.set(min(left, max_left))
            self.crop_right_slider.set(min(right, max_right))
            self.crop_top_slider.set(min(top, max_top))
            self.crop_bottom_slider.set(min(bottom, max_bottom))

            self._set_crop_entry_value("left", self.crop_left_slider.get())
            self._set_crop_entry_value("right", self.crop_right_slider.get())
            self._set_crop_entry_value("top", self.crop_top_slider.get())
            self._set_crop_entry_value("bottom", self.crop_bottom_slider.get())
        finally:
            self._syncing_crop_controls = False

        self._update_crop_metadata()

    def _get_active_crop_box(self, image_size):
        """
        Return the active crop rectangle as left, top, right, bottom.
        """
        width, height = image_size
        width_limit = max(0, width - 1)
        height_limit = max(0, height - 1)

        left = min(width_limit, max(0, int(float(self.crop_left_slider.get()))))
        right = min(width_limit, max(0, int(float(self.crop_right_slider.get()))))
        top = min(height_limit, max(0, int(float(self.crop_top_slider.get()))))
        bottom = min(height_limit, max(0, int(float(self.crop_bottom_slider.get()))))

        if left + right > width_limit:
            left = max(0, width_limit - right)
        if top + bottom > height_limit:
            top = max(0, height_limit - bottom)

        return (left, top, width - right, height - bottom)

    def _crop_to_visible_area(self, pil_img, reference_size=None):
        """
        Crop an image to the currently visible area.
        """
        if pil_img is None:
            return None

        target_size = reference_size if reference_size is not None else pil_img.size
        working_img = pil_img
        if pil_img.size != target_size:
            working_img = pil_img.resize(target_size, Image.LANCZOS)

        crop_box = self._get_active_crop_box(target_size)
        if crop_box == (0, 0, target_size[0], target_size[1]):
            return working_img

        return working_img.crop(crop_box)

    def update_crop(self, edge=None):
        """
        Update crop entries and refresh the preview.
        """
        if self._syncing_crop_controls:
            return

        self._normalize_crop_controls(preferred_edge=edge)
        self.request_preview_update()

    def reset_crop(self):
        """
        Reset all crop values back to the full image.
        """
        self._set_crop_controls(0, 0, 0, 0)
        self._normalize_crop_controls()
        self._set_crop_preset_value("Free")
        self.request_preview_update()

    def apply_crop_preset(self, preset_name):
        """
        Apply a predefined aspect ratio to the visible crop area.
        """
        if self._updating_crop_preset or self.current_pil_image is None:
            return

        if preset_name == "Free":
            self._set_crop_preset_value("Free")
            return

        target_ratio = self._get_crop_presets().get(preset_name)
        if target_ratio is None:
            return

        width, height = self.current_pil_image.size
        left, top, right, bottom = self._get_active_crop_box((width, height))
        current_width = max(1, right - left)
        current_height = max(1, bottom - top)

        if current_width / current_height > target_ratio:
            target_height = current_height
            target_width = max(1, int(round(target_height * target_ratio)))
        else:
            target_width = current_width
            target_height = max(1, int(round(target_width / target_ratio)))

        target_width = min(width, max(1, target_width))
        target_height = min(height, max(1, target_height))

        center_x = (left + right) / 2.0
        center_y = (top + bottom) / 2.0
        new_left = int(round(center_x - (target_width / 2.0)))
        new_top = int(round(center_y - (target_height / 2.0)))
        new_left = max(0, min(width - target_width, new_left))
        new_top = max(0, min(height - target_height, new_top))

        new_right = width - (new_left + target_width)
        new_bottom = height - (new_top + target_height)

        self._set_crop_controls(new_left, new_right, new_top, new_bottom)
        self._normalize_crop_controls()
        self._set_crop_preset_value(preset_name)
        self.request_preview_update()

    def commit_crop_entry(self, edge):
        """
        Apply a typed crop size, clamping it to the image bounds.
        """
        if self._updating_crop_entries or self._syncing_crop_controls:
            return

        slider = {
            "left": self.crop_left_slider,
            "right": self.crop_right_slider,
            "top": self.crop_top_slider,
            "bottom": self.crop_bottom_slider,
        }[edge]
        target_var = {
            "left": self.crop_left_var,
            "right": self.crop_right_var,
            "top": self.crop_top_var,
            "bottom": self.crop_bottom_var,
        }[edge]

        current_value = int(float(slider.get()))
        raw_value = target_var.get().strip().lower().replace("px", "")

        if self.current_pil_image is None:
            max_value = 0
        else:
            width, height = self.current_pil_image.size
            if edge == "left":
                max_value = max(0, width - 1 - int(float(self.crop_right_slider.get())))
            elif edge == "right":
                max_value = max(0, width - 1 - int(float(self.crop_left_slider.get())))
            elif edge == "top":
                max_value = max(0, height - 1 - int(float(self.crop_bottom_slider.get())))
            else:
                max_value = max(0, height - 1 - int(float(self.crop_top_slider.get())))

        try:
            parsed_value = int(float(raw_value))
        except ValueError:
            parsed_value = current_value

        clamped_value = max(0, min(max_value, parsed_value))
        self._set_crop_entry_value(edge, clamped_value)

        if current_value != clamped_value:
            slider.set(clamped_value)

        self._normalize_crop_controls(preferred_edge=edge)
        self.request_preview_update()

    def begin_bulk_update(self):
        """
        Temporarily suspend preview refreshes while multiple controls are updated.
        """
        self._suspend_preview_updates = True
        if self._pending_preview_job is not None:
            self.root.after_cancel(self._pending_preview_job)
            self._pending_preview_job = None

    def end_bulk_update(self, refresh=True):
        """
        Resume preview refreshes after a batch of control updates.
        """
        self._suspend_preview_updates = False
        if refresh:
            self.request_preview_update(immediate=True)

    def request_preview_update(self, immediate=False):
        """
        Schedule or perform an interactive preview refresh.
        """
        if self._suspend_preview_updates:
            return

        if self._pending_preview_job is not None:
            self.root.after_cancel(self._pending_preview_job)
            self._pending_preview_job = None

        if immediate:
            self.apply_pipeline()
        else:
            self._pending_preview_job = self.root.after(self.preview_delay_ms, self._run_scheduled_preview)

    def _run_scheduled_preview(self):
        """
        Execute the deferred preview render.
        """
        self._pending_preview_job = None
        if not self._suspend_preview_updates:
            self.apply_pipeline()

    def _crt_effects_enabled(self):
        """
        Return True when any CRT control is active.
        """
        return any([
            int(self.curvature_slider.get()) > 0,
            int(self.distortion_slider.get()) > 0,
            int(self.glow_slider.get()) > 0,
            int(self.noise_slider.get()) > 0,
            int(self.scanline_slider.get()) > 0,
            int(self.rgb_shift_slider.get()) > 0,
            int(self.vignette_slider.get()) > 0,
        ])

    def _get_preview_processing_size(self, image_size):
        """
        Return the target image size for interactive preview processing.
        """
        self.canvas.update_idletasks()
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())

        img_width, img_height = image_size
        ratio = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        preview_scale = min(1.0, ratio * 1.25)

        return (
            max(1, int(img_width * preview_scale)),
            max(1, int(img_height * preview_scale)),
        )

    def update_export_compression(self, _=None):
        """
        Refresh the preview when the export compression style changes.
        """
        self.request_preview_update()

    def apply_export_compression(self, img):
        """
        Apply the selected export compression profile to an image.
        """
        profile = self.export_compression_var.get() if hasattr(self, 'export_compression_var') else "No Compression"
        return image_effects.apply_export_compression(img, profile)

    def render_current_image(self, for_preview=False):
        """
        Render the current image using the active controls.
        For preview rendering, CRT effects are applied on a reduced-size copy for speed.
        """
        if self.image_object is None or self.current_pil_image is None:
            return None

        base_reference_size = self.current_pil_image.size
        base_source = self._crop_to_visible_area(self.current_pil_image, base_reference_size)
        blend_source = self._crop_to_visible_area(self.blend_image_pil, base_reference_size)

        if for_preview:
            preview_size = self._get_preview_processing_size(base_source.size)
            if preview_size != base_source.size:
                base_source = base_source.resize(preview_size, Image.LANCZOS)
                if blend_source is not None:
                    blend_source = blend_source.resize(preview_size, Image.LANCZOS)

        img = self.process_effects_on_image(base_source)

        if blend_source is not None:
            try:
                overlay_processed = self.process_effects_on_image(blend_source)
                blend_factor = float(self.blend_slider.get()) if hasattr(self, 'blend_slider') else 0.0
                if blend_factor > 0.0:
                    img = image_effects.blend_images(img, overlay_processed, blend_factor)
            except Exception:
                pass

        if img is None:
            return None

        img = self.apply_crt_effects(img)
        return self.apply_export_compression(img)

    def apply_pipeline(self):
        """
        Applies all effects in a pipeline, ensuring modifications are cumulative.
        """
        if self.image_object:
            preview_img = self.render_current_image(for_preview=True)
            if preview_img is not None:
                self.pipeline_image = preview_img
                self.display_image(preview_img)

    def update_effects(self, _=None):
        self.request_preview_update()

    def update_colorize(self, _=None):
        self.request_preview_update()

    def update_confuser(self, _=None):
        """
        Updates the confuser effects (blur and color reduction) based on the sliders.
        """
        # Re-run the full pipeline so confuser effects are applied in sequence
        self.request_preview_update()

    def update_crt(self, _=None):
        """
        Updates the CRT effects.
        """
        self.request_preview_update()

    def process_effects_on_image(self, pil_img):
        """
        Apply the current UI-controlled effects to a given PIL image and return the result.
        This mirrors the main pipeline but operates on an arbitrary image (used for blending).
        """
        if pil_img is None:
            return None

        # Pixelate: use a temporary ImageObject so we can call the existing pixelate func
        arr = np.array(pil_img.convert("RGBA"))
        temp_obj = ImageObject(name="temp", size=pil_img.size, pixel_array=arr)

        scale_factor = float(self.pixel_slider.get())
        jitter_val = int(self.jitter_slider.get())
        block_val = int(self.block_slider.get())
        sort_val = int(self.sort_slider.get())

        img = image_effects.pixelate(temp_obj, scale_factor, jitter_val, block_val, sort_val)

        # Colorize effects
        hue_shift = int(self.hue_slider.get())
        saturation_factor = float(self.saturation_slider.get())
        contrast_factor = float(self.contrast_slider.get())
        invert_factor = float(self.invert_state.get())

        img = image_effects.adjust_hue(img, hue_shift)
        img = image_effects.adjust_saturation(img, saturation_factor)
        img = image_effects.adjust_contrast(img, contrast_factor)
        img = image_effects.adjust_invert(img, invert_factor)

        # Confuser effects
        try:
            blur_radius = int(self.blur_slider.get())
            color_bins = int(self.color_reducer_slider.get())
            legacy_bins = int(self.legacy_color_slider.get())
        except Exception:
            blur_radius = 0
            color_bins = 256
            legacy_bins = 256

        if blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(blur_radius))

        if color_bins < 256:
            img = image_effects.reduce_colors(img, color_bins)

        # Apply legacy collapse if requested
        if legacy_bins < 256:
            img = image_effects.reduce_colors_legacy(img, legacy_bins)

        # Random pixelization (applies to RGB only)
        try:
            random_factor = float(self.random_pixel_slider.get())
        except Exception:
            random_factor = 0.0

        if random_factor > 0.0:
            img = image_effects.randomize_pixels(img, random_factor)

        return img

    def apply_crt_effects(self, img):
        """
        Apply CRT-style post-processing to the fully composited image.
        """
        if img is None:
            return None

        scanline_strength = int(self.scanline_slider.get())
        curvature_strength = int(self.curvature_slider.get())
        distortion_strength = int(self.distortion_slider.get())
        glow_strength = int(self.glow_slider.get())
        noise_strength = int(self.noise_slider.get())
        rgb_shift = int(self.rgb_shift_slider.get())
        vignette_strength = int(self.vignette_slider.get())

        img = image_effects.apply_horizontal_distortion(img, distortion_strength)
        img = image_effects.apply_screen_curvature(img, curvature_strength)
        img = image_effects.apply_scanlines(img, scanline_strength)
        img = image_effects.apply_rgb_shift(img, rgb_shift)
        img = image_effects.apply_phosphor_glow(img, glow_strength)
        img = image_effects.apply_static_noise(img, noise_strength)
        img = image_effects.apply_vignette(img, vignette_strength)
        return img

    def upload_blend_image(self):
        """
        Uploads an image to be used as the blend overlay.
        """
        path = filedialog.askopenfilename(title="Select an Image to Blend", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGBA")
            self.blend_image_pil = img
            self.blend_filename_var.set(os.path.basename(path))
            self.request_preview_update(immediate=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load blend image: {e}")

    def update_blend(self, _=None):
        """
        Re-run pipeline when blend slider changes.
        """
        self.request_preview_update()

    def reset_pipeline(self):
        """
        Resets the pipeline to the original image.
        """
        self.pipeline_image = None
        self.request_preview_update(immediate=True)

    def upload_image(self):
        # Use root.after to decouple the dialog from the button event
        self.root.after(50, self._execute_upload)

    def _execute_upload(self):
        try:
            # On some macOS versions, the native dialog crashes if not called carefully
            file_path = filedialog.askopenfilename(
                title="Select an Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
            )
            
            if not file_path:
                return

            # Load image using Pillow
            img = Image.open(file_path).convert("RGBA")
            width, height = img.size
            pixel_array = np.array(img)

            # Create ImageObject
            self.image_object = ImageObject(name=os.path.basename(file_path), size=(width, height), pixel_array=pixel_array)

            # Keep a reference to the PIL Image object
            self.current_pil_image = img

            # Reset all effects so the new image starts from a clean state
            self._reset_controls_for_new_image()

            self.pipeline_image = img.copy()

            # Display image on canvas
            self.display_image(img)
            
        except Exception as e:
            print(f"Error loading or processing image: {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image(self, img):
        self.canvas.update_idletasks() # Ensure canvas dimensions are updated
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img_width, img_height = img.size
        ratio = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        new_width = max(1, int(img_width * ratio))
        new_height = max(1, int(img_height * ratio))
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

        self.tk_img = ImageTk.PhotoImage(resized_img)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width/2, canvas_height/2, anchor=tk.CENTER, image=self.tk_img)

    def randomize_effects(self):
        """
        Randomizes all effect sliders to create a unique combination of effects.
        """
        import random
        # Randomize only the parameters enabled in settings
        get = lambda key, default=True: self.randomize_settings.get(key, tk.BooleanVar(value=default)).get()

        self.begin_bulk_update()
        try:
            # Pixelate group
            if get('pixel_scale'):
                self.pixel_slider.set(random.uniform(0.01, 1.0))
            if get('jitter'):
                self.jitter_slider.set(random.randint(0, 100))
            if get('block'):
                self.block_slider.set(random.randint(0, 100))
            if get('sort'):
                self.sort_slider.set(random.randint(0, 100))

            # Colorize group
            if get('hue'):
                self.hue_slider.set(random.randint(-180, 180))
            if get('saturation'):
                self.saturation_slider.set(random.uniform(0.0, 2.0))
            if get('contrast'):
                self.contrast_slider.set(random.uniform(0.5, 2.0))
            if get('invert'):
                self.invert_state.set(random.choice([True, False]))

            # Random pixels
            if get('random_pixels'):
                self.random_pixel_slider.set(random.uniform(0.0, 1.0))

            # Confuser group
            if get('blur'):
                self.blur_slider.set(random.randint(0, 10))
            if get('color_reducer'):
                self.color_reducer_slider.set(random.randint(2, 256))
            if get('legacy_collapse'):
                self.legacy_color_slider.set(random.randint(2, 256))

            # CRT group
            if get('curvature'):
                self.curvature_slider.set(random.randint(0, 65))
            if get('distortion'):
                self.distortion_slider.set(random.randint(0, 55))
            if get('glow'):
                self.glow_slider.set(random.randint(0, 60))
            if get('noise'):
                self.noise_slider.set(random.randint(0, 35))
            if get('scanlines'):
                self.scanline_slider.set(random.randint(0, 85))
            if get('rgb_shift'):
                self.rgb_shift_slider.set(random.randint(0, 6))
            if get('vignette'):
                self.vignette_slider.set(random.randint(0, 65))

            # Blend
            if get('blend') and hasattr(self, 'blend_slider'):
                self.blend_slider.set(random.uniform(0.0, 1.0))

            # Export compression
            if get('compression') and hasattr(self, 'export_compression_var'):
                self.export_compression_var.set(random.choice([
                    "No Compression",
                    "Soft CCD",
                    "Compact Camera",
                    "Memory Saver",
                    "Harsh Artifacts",
                ]))
        finally:
            self.end_bulk_update(refresh=True)

    def update_random_pixels(self, _=None):
        """
        Gradually randomizes the color of random pixels based on the slider value.
        """
        # Re-run the full pipeline so randomization is persistent and composes with other effects
        self.request_preview_update()

    def open_randomize_settings(self):
        """
        Open a modal window where the user can toggle which parameters are affected by Randomize.
        """
        win = tk.Toplevel(self.root)
        win.title("Randomize Settings")
        win.configure(bg="#2e2e2e")
        win.transient(self.root)
        win.grab_set()

        # Layout checkboxes in two columns, alphabetically
        sorted_keys = sorted(self.randomize_settings.keys(), key=lambda key: key.replace('_', ' '))
        left_keys = sorted_keys[::2]
        right_keys = sorted_keys[1::2]

        row = 0
        for k in left_keys:
            cb = tk.Checkbutton(win, text=k.replace('_',' ').title(), variable=self.randomize_settings[k], bg="#2e2e2e", fg="white", selectcolor="#444")
            cb.grid(row=row, column=0, sticky='w', padx=10, pady=2)
            row += 1

        row = 0
        for k in right_keys:
            if k not in self.randomize_settings:
                self.randomize_settings[k] = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(win, text=k.replace('_',' ').title(), variable=self.randomize_settings[k], bg="#2e2e2e", fg="white", selectcolor="#444")
            cb.grid(row=row, column=1, sticky='w', padx=10, pady=2)
            row += 1

        # Buttons
        btn_frame = tk.Frame(win, bg="#2e2e2e")
        btn_frame.grid(row=max(len(left_keys), len(right_keys))+1, column=0, columnspan=2, pady=10)

        def select_all():
            for v in self.randomize_settings.values():
                v.set(True)

        def deselect_all():
            for v in self.randomize_settings.values():
                v.set(False)

        tk.Button(btn_frame, text="Select All", command=select_all, **self._button_style("#444")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Deselect All", command=deselect_all, **self._button_style("#444")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=win.destroy, **self._button_style("#666")).pack(side=tk.LEFT, padx=5)

    def toggle_invert(self):
        """
        Toggles the invert effect on the image.
        """
        # Variable is already updated by the Checkbutton; just re-run the pipeline
        self.request_preview_update()

    def select_folder(self):
        """
        Opens a dialog to select a folder and updates the folder path.
        """
        folder_selected = filedialog.askdirectory(title="Select Folder")
        if folder_selected:
            self.folder_path.set(folder_selected)

    def save_image(self):
        """
        Saves the current image to the selected folder.
        """
        if self.image_object is None:
            messagebox.showerror("Error", "No image to save.")
            return

        folder = self.folder_path.get()
        if not folder:
            folder = filedialog.askdirectory(title="Select Folder")
            if not folder:
                messagebox.showerror("Error", "No folder selected.")
                return

        # Prompt for filename (without extension)
        default_name = "Weird_Pixellator_Output"
        name = simpledialog.askstring("Save As", "Enter file name (without extension):", initialvalue=default_name)
        if not name:
            return
        name = name.strip()
        if name == "":
            messagebox.showerror("Error", "Invalid file name.")
            return

        # Ensure .png extension
        base_filename = f"{name}.png"
        file_path = os.path.join(folder, base_filename)

        # If file exists, append a numeric suffix
        if os.path.exists(file_path):
            i = 1
            name_root = name
            while True:
                candidate = os.path.join(folder, f"{name_root}_{i}.png")
                if not os.path.exists(candidate):
                    file_path = candidate
                    break
                i += 1

        try:
            final_image = self.render_current_image(for_preview=False)
            if final_image is None:
                messagebox.showerror("Error", "No image to save.")
                return
            self.full_resolution_image = final_image
            final_image.save(file_path)
            messagebox.showinfo("Success", f"Image saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()