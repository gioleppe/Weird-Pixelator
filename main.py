import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import colorsys
import os
import struct
from PIL import Image, ImageTk, ImageFilter, ImageOps
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
        self.animation_frames = []
        self.animation_preview_images = []
        self.animation_status_var = tk.StringVar(value="No frames added yet.")
        self.palette_entries = []
        self.palette_status_var = tk.StringVar(value="Load an image and extract a palette from the preview.")
        self.palette_format_var = tk.StringVar(value="HEX File")
        self.palette_sort_var = tk.StringVar(value="Frequency")
        self.theme_name_var = tk.StringVar(value="Classic Gray")
        self.invert_state = tk.BooleanVar(value=False)
        self.folder_path = tk.StringVar()
        self.blend_filename_var = tk.StringVar(value="No file")
        self.preview_title_var = tk.StringVar(value="No image loaded")
        self.preview_hint_var = tk.StringVar(value="Upload an image to start creating a glitchy preview.")
        self._slider_value_bindings = []
        self.themes = self._create_theme_presets()
        self.theme = self.themes[self.theme_name_var.get()]

        self.root.geometry("1080x720")
        self.root.minsize(920, 660)
        self._build_ui_shell()
        self._sync_crop_controls_to_image(reset_values=True)
        self._refresh_animation_preview_strip()
        self._render_empty_preview()

    def _create_theme_presets(self):
        """
        Return the available app themes.
        """
        return {
            "Classic Gray": {
                "bg": "#c0c0c0",
                "panel": "#d4d0c8",
                "panel_alt": "#ece9d8",
                "panel_soft": "#f3f0e4",
                "border": "#7f7f7f",
                "text": "#111111",
                "muted": "#4e4e4e",
                "canvas": "#808080",
                "field": "#ffffff",
                "field_border": "#7f9db9",
                "accent": "#0a246a",
                "accent_soft": "#b6c7e5",
                "button": "#d4d0c8",
                "button_alt": "#e6e2d8",
                "shadow_dark": "#808080",
                "shadow_light": "#ffffff",
            },
            "XP Blue": {
                "bg": "#dbe7f7",
                "panel": "#ece9d8",
                "panel_alt": "#ffffff",
                "panel_soft": "#f7f4ea",
                "border": "#7f9db9",
                "text": "#0f1728",
                "muted": "#4f6280",
                "canvas": "#6f8db9",
                "field": "#ffffff",
                "field_border": "#7f9db9",
                "accent": "#1f5fbf",
                "accent_soft": "#c8daf5",
                "button": "#d6e3f5",
                "button_alt": "#eef4fd",
                "shadow_dark": "#7f9db9",
                "shadow_light": "#ffffff",
            },
            "Olive Retro": {
                "bg": "#d6d6c2",
                "panel": "#d9d3be",
                "panel_alt": "#ece7d5",
                "panel_soft": "#f5f1e5",
                "border": "#8a8673",
                "text": "#232117",
                "muted": "#5f5a46",
                "canvas": "#8d9278",
                "field": "#fffdf6",
                "field_border": "#9fa27f",
                "accent": "#4f6b2b",
                "accent_soft": "#cfd9b6",
                "button": "#d6d0b8",
                "button_alt": "#e8e2cb",
                "shadow_dark": "#8a8673",
                "shadow_light": "#fffdf6",
            },
            "Windows 98 Beige": {
                "bg": "#c9c1b2",
                "panel": "#d8d0c4",
                "panel_alt": "#efe7da",
                "panel_soft": "#f7f1e7",
                "border": "#8b8173",
                "text": "#1d1a16",
                "muted": "#655c52",
                "canvas": "#8f877c",
                "field": "#fffaf2",
                "field_border": "#9d9283",
                "accent": "#7a0000",
                "accent_soft": "#d8beb8",
                "button": "#d8d0c4",
                "button_alt": "#e8dfd1",
                "shadow_dark": "#8b8173",
                "shadow_light": "#fffaf2",
            },
            "Dark Retro": {
                "bg": "#2e2a26",
                "panel": "#3a342f",
                "panel_alt": "#4a433d",
                "panel_soft": "#544c45",
                "border": "#161311",
                "text": "#f2eadf",
                "muted": "#c2b5a3",
                "canvas": "#1b1714",
                "field": "#241f1b",
                "field_border": "#8a7a67",
                "accent": "#c86b2a",
                "accent_soft": "#7b6758",
                "button": "#4a433d",
                "button_alt": "#5a5148",
                "shadow_dark": "#161311",
                "shadow_light": "#7a6e62",
            },
            "Terminal Green": {
                "bg": "#0b120b",
                "panel": "#132013",
                "panel_alt": "#1a2a1a",
                "panel_soft": "#1f331f",
                "border": "#2f5a2f",
                "text": "#8cff8c",
                "muted": "#5fb35f",
                "canvas": "#050805",
                "field": "#091009",
                "field_border": "#2f5a2f",
                "accent": "#00ff66",
                "accent_soft": "#1f4f2c",
                "button": "#183018",
                "button_alt": "#204020",
                "shadow_dark": "#041004",
                "shadow_light": "#3b6f3b",
            },
        }

    def _build_ui_shell(self):
        """
        Build or rebuild the main app shell for the current theme.
        """
        self.root.configure(bg=self.theme["bg"])
        self._configure_notebook_style()

        if hasattr(self, 'app_shell') and self.app_shell is not None:
            self.app_shell.destroy()

        self.app_shell = tk.Frame(self.root, bg=self.theme["bg"])
        self.app_shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.app_shell.grid_columnconfigure(0, weight=3)
        self.app_shell.grid_columnconfigure(1, weight=2, minsize=360)
        self.app_shell.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_preview_panel()
        self._build_control_sidebar()

    def _capture_ui_state(self):
        """
        Capture current widget state so the UI can be rebuilt for theme changes.
        """
        slider_names = [
            'pixel_slider', 'jitter_slider', 'block_slider', 'sort_slider',
            'hue_slider', 'saturation_slider', 'contrast_slider',
            'random_pixel_slider', 'blur_slider', 'color_reducer_slider', 'legacy_color_slider',
            'blend_slider', 'curvature_slider', 'distortion_slider', 'glow_slider',
            'noise_slider', 'scanline_slider', 'rgb_shift_slider', 'vignette_slider',
        ]
        slider_values = {}
        for name in slider_names:
            if hasattr(self, name):
                slider_values[name] = float(getattr(self, name).get())

        selected_tab = 0
        if hasattr(self, 'controls_notebook'):
            try:
                selected_tab = self.controls_notebook.index(self.controls_notebook.select())
            except tk.TclError:
                selected_tab = 0

        palette_entries = [dict(entry) for entry in self.palette_entries]

        return {
            'sliders': slider_values,
            'invert_state': bool(self.invert_state.get()),
            'crop_values': {
                'left': self.crop_left_var.get(),
                'right': self.crop_right_var.get(),
                'top': self.crop_top_var.get(),
                'bottom': self.crop_bottom_var.get(),
            },
            'crop_preset': self.crop_preset_var.get(),
            'export_compression': self.export_compression_var.get(),
            'folder_path': self.folder_path.get(),
            'blend_image_pil': self.blend_image_pil,
            'blend_filename': self.blend_filename_var.get(),
            'palette_entries': palette_entries,
            'palette_status': self.palette_status_var.get(),
            'palette_format': self.palette_format_var.get(),
            'palette_sort': self.palette_sort_var.get(),
            'selected_tab': selected_tab,
        }

    def _restore_ui_state(self, state):
        """
        Restore widget state after a themed UI rebuild.
        """
        self.begin_bulk_update()
        try:
            for name, value in state['sliders'].items():
                if hasattr(self, name):
                    getattr(self, name).set(value)

            self.invert_state.set(state['invert_state'])
            self.export_compression_var.set(state['export_compression'])
            self.folder_path.set(state['folder_path'])
            self.blend_image_pil = state['blend_image_pil']
            self.blend_filename_var.set(state['blend_filename'])
            self.palette_format_var.set(state['palette_format'])
            self.palette_sort_var.set(state['palette_sort'])

            self._sync_crop_controls_to_image(reset_values=True)
            left = int(float(state['crop_values']['left'])) if state['crop_values']['left'] else 0
            right = int(float(state['crop_values']['right'])) if state['crop_values']['right'] else 0
            top = int(float(state['crop_values']['top'])) if state['crop_values']['top'] else 0
            bottom = int(float(state['crop_values']['bottom'])) if state['crop_values']['bottom'] else 0
            self._set_crop_controls(left, right, top, bottom)
            self._normalize_crop_controls()
            self._set_crop_preset_value(state['crop_preset'])
        finally:
            self.end_bulk_update(refresh=False)

        self.palette_entries = state['palette_entries']
        self.palette_status_var.set(state['palette_status'])
        if self.palette_entries:
            self.update_palette_display()
        else:
            self._reset_palette_output(state['palette_status'])

        self._refresh_animation_preview_strip()

        if hasattr(self, 'controls_notebook'):
            try:
                self.controls_notebook.select(state['selected_tab'])
            except tk.TclError:
                pass

        if self.image_object is not None and self.current_pil_image is not None:
            self.apply_pipeline()
        else:
            self._render_empty_preview()

    def set_theme(self, theme_name):
        """
        Apply a named theme and rebuild the interface.
        """
        if theme_name not in self.themes:
            return

        state = self._capture_ui_state() if hasattr(self, 'app_shell') else None
        self.theme_name_var.set(theme_name)
        self.theme = self.themes[theme_name]
        self._build_ui_shell()

        if state is not None:
            self._restore_ui_state(state)

    def open_app_settings(self):
        """
        Open app settings, including theme selection.
        """
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.configure(bg=self.theme["panel"])
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(
            win,
            text="Theme",
            fg=self.theme["text"],
            bg=self.theme["panel"],
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        theme_var = tk.StringVar(value=self.theme_name_var.get())
        theme_menu = tk.OptionMenu(win, theme_var, *self.themes.keys())
        self._style_option_menu(theme_menu)
        theme_menu.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

        button_row = tk.Frame(win, bg=self.theme["panel"])
        button_row.grid(row=2, column=0, sticky="e", padx=12, pady=(0, 12))

        def apply_and_close():
            selected_theme = theme_var.get()
            win.destroy()
            self.set_theme(selected_theme)

        tk.Button(button_row, text="Cancel", command=win.destroy, **self._button_style(self.theme["button"])).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(button_row, text="Apply", command=apply_and_close, **self._button_style(self.theme["button_alt"])).pack(side=tk.LEFT)

    def _configure_notebook_style(self):
        """
        Configure a compact classic notebook style for the right sidebar tabs.
        """
        style = ttk.Style(self.root)
        try:
            style.theme_use("classic")
        except tk.TclError:
            pass

        style.configure(
            "Weird.TNotebook",
            background=self.theme["bg"],
            borderwidth=1,
            tabmargins=(2, 2, 2, 0)
        )
        style.configure(
            "Weird.TNotebook.Tab",
            background=self.theme["panel"],
            foreground=self.theme["text"],
            padding=(12, 6),
            borderwidth=1,
            relief="raised",
            focuscolor=self.theme["panel"],
        )
        style.map(
            "Weird.TNotebook.Tab",
            background=[("selected", self.theme["panel_alt"]), ("active", self.theme["panel_soft"])],
            foreground=[("selected", self.theme["text"]), ("active", self.theme["text"])],
        )

    def _build_header(self):
        """
        Build the compact top bar.
        """
        self.header_frame = tk.Frame(self.app_shell, bg=self.theme["bg"])
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.header_frame.grid_columnconfigure(0, weight=1)

        title_block = tk.Frame(self.header_frame, bg=self.theme["bg"])
        title_block.grid(row=0, column=0, sticky="w")

        tk.Label(
            title_block,
            text="Weird Pixelator",
            fg=self.theme["text"],
            bg=self.theme["bg"],
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Compact glitch controls with a cleaner preview workflow.",
            fg=self.theme["muted"],
            bg=self.theme["bg"],
            font=("Helvetica", 10)
        ).pack(anchor="w", pady=(2, 0))

        actions = tk.Frame(self.header_frame, bg=self.theme["bg"])
        actions.grid(row=0, column=1, sticky="e")

        self.upload_button = tk.Button(
            actions,
            text="Upload Image",
            command=self.upload_image,
            **self._button_style(self.theme["button"])
        )
        self.upload_button.pack(side=tk.LEFT, padx=(0, 8))

        self.save_button = tk.Button(
            actions,
            text="Save Image",
            command=self.save_image,
            **self._button_style(self.theme["accent_soft"])
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 8))

        self.randomize_settings_button = tk.Button(
            actions,
            text="Randomize Settings",
            command=self.open_randomize_settings,
            **self._button_style(self.theme["button_alt"])
        )
        self.randomize_settings_button.pack(side=tk.LEFT, padx=(0, 8))

        self.settings_button = tk.Button(
            actions,
            text="Settings",
            command=self.open_app_settings,
            **self._button_style(self.theme["button"])
        )
        self.settings_button.pack(side=tk.LEFT)

    def _build_preview_panel(self):
        """
        Build the left preview area.
        """
        self.preview_frame, preview_body = self._create_card(
            self.app_shell,
            "Preview",
            self.preview_hint_var,
            stretch=True
        )
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            preview_body,
            textvariable=self.preview_title_var,
            fg=self.theme["text"],
            bg=self.theme["panel"],
            font=("Helvetica", 13, "bold"),
            anchor="w"
        ).pack(anchor="w")

        self.canvas_wrap = tk.Frame(
            preview_body,
            bg=self.theme["canvas"],
            relief=tk.SUNKEN,
            bd=2,
            highlightthickness=0,
        )
        self.canvas_wrap.configure(width=430, height=430)
        self.canvas_wrap.pack_propagate(False)
        self.canvas_wrap.pack(pady=(10, 0), anchor="center")

        self.canvas = tk.Canvas(
            self.canvas_wrap,
            width=400,
            height=400,
            bg="#000000",
            bd=0,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(
            preview_body,
            text="Live preview updates automatically while you tweak controls.",
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            font=("Helvetica", 10)
        ).pack(anchor="w", pady=(10, 0))

    def _build_control_sidebar(self):
        """
        Build the compact tabbed control sidebar.
        """
        self.sidebar_frame = tk.Frame(self.app_shell, bg=self.theme["bg"])
        self.sidebar_frame.grid(row=1, column=1, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.controls_notebook = ttk.Notebook(self.sidebar_frame, style="Weird.TNotebook")
        self.controls_notebook.grid(row=0, column=0, sticky="nsew")

        self.edit_tab = tk.Frame(self.controls_notebook, bg=self.theme["bg"])
        self.finish_tab = tk.Frame(self.controls_notebook, bg=self.theme["bg"])
        self.crop_tab = tk.Frame(self.controls_notebook, bg=self.theme["bg"])
        self.animate_tab = tk.Frame(self.controls_notebook, bg=self.theme["bg"])
        self.palette_tab = tk.Frame(self.controls_notebook, bg=self.theme["bg"])

        self.controls_notebook.add(self.edit_tab, text="Adjust")
        self.controls_notebook.add(self.finish_tab, text="Finish")
        self.controls_notebook.add(self.crop_tab, text="Crop")
        self.controls_notebook.add(self.animate_tab, text="Animate")
        self.controls_notebook.add(self.palette_tab, text="Palette")

        self._build_adjust_tab()
        self._build_finish_tab()
        self._build_crop_tab()
        self._build_animation_tab()
        self._build_palette_tab()

    def _build_adjust_tab(self):
        """
        Build the main effect controls tab.
        """
        self.edit_tab.grid_columnconfigure(0, weight=1)
        self.edit_tab.grid_columnconfigure(1, weight=1)

        self.pixelate_frame, pixelate_body = self._create_card(self.edit_tab, "Pixelate")
        self.pixelate_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        self.jitter_slider = self._create_compact_slider(pixelate_body, "Row Jitter", 0, 100, self.update_effects, initial=0)
        self.block_slider = self._create_compact_slider(pixelate_body, "Block Shift", 0, 100, self.update_effects, initial=0)
        self.sort_slider = self._create_compact_slider(pixelate_body, "Pixel Sort", 0, 100, self.update_effects, initial=0)
        self.pixel_slider = self._create_compact_slider(
            pixelate_body,
            "Pixelate",
            1.0,
            0.01,
            self.update_effects,
            resolution=0.01,
            initial=1.0,
            formatter=lambda value: f"{float(value):.2f}"
        )

        self.colorize_frame, colorize_body = self._create_card(self.edit_tab, "Colorize")
        self.colorize_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
        self.hue_slider = self._create_compact_slider(colorize_body, "Hue Shift", -180, 180, self.update_colorize, initial=0)
        self.saturation_slider = self._create_compact_slider(
            colorize_body,
            "Saturation",
            0.0,
            2.0,
            self.update_colorize,
            resolution=0.1,
            initial=1.0,
            formatter=lambda value: f"{float(value):.1f}"
        )
        self.contrast_slider = self._create_compact_slider(
            colorize_body,
            "Contrast",
            0.5,
            2.0,
            self.update_colorize,
            resolution=0.1,
            initial=1.0,
            formatter=lambda value: f"{float(value):.1f}"
        )
        self.invert_button = tk.Checkbutton(
            colorize_body,
            text="Invert Colors",
            variable=self.invert_state,
            command=self.toggle_invert,
            bg=self.theme["panel"],
            fg=self.theme["text"],
            activebackground=self.theme["panel"],
            activeforeground=self.theme["text"],
            selectcolor=self.theme["field"],
            highlightthickness=0,
            bd=0,
            anchor="w"
        )
        self.invert_button.pack(fill=tk.X, pady=(4, 0))

        self.randomize_frame, randomize_body = self._create_card(self.edit_tab, "Randomize")
        self.randomize_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        self.randomize_button = tk.Button(
            randomize_body,
            text="Randomize Effects",
            command=self.randomize_effects,
            **self._button_style(self.theme["button"])
        )
        self.randomize_button.pack(fill=tk.X)
        self.random_pixel_slider = self._create_compact_slider(
            randomize_body,
            "Random Pixels",
            0.0,
            1.0,
            self.update_random_pixels,
            resolution=0.01,
            initial=0.0,
            formatter=lambda value: f"{float(value):.2f}"
        )
        self.randomize_settings_inline = tk.Button(
            randomize_body,
            text="Choose Randomized Controls",
            command=self.open_randomize_settings,
            **self._button_style(self.theme["button_alt"])
        )
        self.randomize_settings_inline.pack(fill=tk.X, pady=(6, 0))

        self.confuser_frame, confuser_body = self._create_card(self.edit_tab, "Confuser")
        self.confuser_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
        self.blur_slider = self._create_compact_slider(confuser_body, "Blur", 0, 10, self.update_confuser, initial=0)
        self.color_reducer_slider = self._create_compact_slider(confuser_body, "Color Reducer", 2, 256, self.update_confuser, initial=256)
        self.legacy_color_slider = self._create_compact_slider(confuser_body, "Color Collapse", 2, 256, self.update_confuser, initial=256)

        self.blend_frame, blend_body = self._create_card(self.edit_tab, "Blend")
        self.blend_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.upload_blend_button = tk.Button(
            blend_body,
            text="Upload Blend Image",
            command=self.upload_blend_image,
            **self._button_style(self.theme["button"])
        )
        self.upload_blend_button.pack(fill=tk.X)
        tk.Label(
            blend_body,
            textvariable=self.blend_filename_var,
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            anchor="w"
        ).pack(fill=tk.X, pady=(6, 2))
        self.blend_slider = self._create_compact_slider(
            blend_body,
            "Blend Factor",
            0.0,
            1.0,
            self.update_blend,
            resolution=0.01,
            initial=0.0,
            formatter=lambda value: f"{float(value):.2f}"
        )

    def _build_finish_tab(self):
        """
        Build the finishing and export controls tab.
        """
        self.finish_tab.grid_columnconfigure(0, weight=1)

        self.crt_frame, crt_body = self._create_card(self.finish_tab, "CRT Finish")
        self.crt_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        crt_grid = tk.Frame(crt_body, bg=self.theme["panel"])
        crt_grid.pack(fill=tk.X)
        crt_grid.grid_columnconfigure(0, weight=1)
        crt_grid.grid_columnconfigure(1, weight=1)

        crt_left = tk.Frame(crt_grid, bg=self.theme["panel"])
        crt_left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        crt_right = tk.Frame(crt_grid, bg=self.theme["panel"])
        crt_right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.curvature_slider = self._create_compact_slider(crt_left, "Curvature", 0, 100, self.update_crt, initial=0)
        self.glow_slider = self._create_compact_slider(crt_left, "Glow", 0, 100, self.update_crt, initial=0)
        self.rgb_shift_slider = self._create_compact_slider(crt_left, "RGB Shift", 0, 20, self.update_crt, initial=0)
        self.vignette_slider = self._create_compact_slider(crt_left, "Vignette", 0, 100, self.update_crt, initial=0)

        self.distortion_slider = self._create_compact_slider(crt_right, "Distortion", 0, 100, self.update_crt, initial=0)
        self.noise_slider = self._create_compact_slider(crt_right, "Noise", 0, 100, self.update_crt, initial=0)
        self.scanline_slider = self._create_compact_slider(crt_right, "Scanlines", 0, 100, self.update_crt, initial=0)

        self.export_frame, export_body = self._create_card(self.finish_tab, "Export")
        self.export_frame.grid(row=1, column=0, sticky="nsew")
        tk.Label(export_body, text="Save Style", fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(fill=tk.X)
        self.export_compression_menu = tk.OptionMenu(
            export_body,
            self.export_compression_var,
            "No Compression",
            "Soft CCD",
            "Compact Camera",
            "Memory Saver",
            "Harsh Artifacts",
            command=self.update_export_compression
        )
        self._style_option_menu(self.export_compression_menu)
        self.export_compression_menu.pack(fill=tk.X, pady=(4, 8))

        tk.Label(export_body, text="Save Folder", fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(fill=tk.X)
        folder_row = tk.Frame(export_body, bg=self.theme["panel"])
        folder_row.pack(fill=tk.X, pady=(4, 0))
        self.folder_entry = tk.Entry(folder_row, textvariable=self.folder_path, **self._entry_style())
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.browse_button = tk.Button(
            folder_row,
            text="Browse",
            command=self.select_folder,
            **self._button_style(self.theme["button_alt"])
        )
        self.browse_button.pack(side=tk.LEFT, padx=(8, 0))

        button_row = tk.Frame(export_body, bg=self.theme["panel"])
        button_row.pack(fill=tk.X, pady=(10, 0))
        tk.Button(
            button_row,
            text="Save PNG",
            command=self.save_image,
            **self._button_style(self.theme["button"])
        ).pack(side=tk.LEFT)
        tk.Label(
            export_body,
            text="Compression affects preview and final export.",
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            anchor="w"
        ).pack(fill=tk.X, pady=(8, 0))

    def _build_crop_tab(self):
        """
        Build the crop controls tab.
        """
        self.crop_tab.grid_columnconfigure(0, weight=1)
        self.crop_frame, crop_body = self._create_card(self.crop_tab, "Crop & Aspect")
        self.crop_frame.grid(row=0, column=0, sticky="nsew")

        crop_grid = tk.Frame(crop_body, bg=self.theme["panel"])
        crop_grid.pack(fill=tk.X)
        crop_grid.grid_columnconfigure(0, weight=1)
        crop_grid.grid_columnconfigure(1, weight=1)

        self.crop_left_slider, self.crop_left_entry = self._create_crop_control(crop_grid, 0, 0, "left", "Left")
        self.crop_right_slider, self.crop_right_entry = self._create_crop_control(crop_grid, 0, 1, "right", "Right")
        self.crop_top_slider, self.crop_top_entry = self._create_crop_control(crop_grid, 1, 0, "top", "Top")
        self.crop_bottom_slider, self.crop_bottom_entry = self._create_crop_control(crop_grid, 1, 1, "bottom", "Bottom")

        footer = tk.Frame(crop_body, bg=self.theme["panel"])
        footer.pack(fill=tk.X, pady=(8, 0))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=0)

        self.crop_size_label = tk.Label(
            footer,
            textvariable=self.crop_size_var,
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            anchor="w"
        )
        self.crop_size_label.grid(row=0, column=0, sticky="w")

        preset_row = tk.Frame(footer, bg=self.theme["panel"])
        preset_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        preset_row.grid_columnconfigure(1, weight=1)
        tk.Label(preset_row, text="Preset", fg=self.theme["text"], bg=self.theme["panel"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.crop_preset_menu = tk.OptionMenu(
            preset_row,
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
        self._style_option_menu(self.crop_preset_menu)
        self.crop_preset_menu.grid(row=0, column=1, sticky="ew")

        self.reset_crop_button = tk.Button(
            crop_body,
            text="Reset Crop",
            command=self.reset_crop,
            **self._button_style(self.theme["button_alt"])
        )
        self.reset_crop_button.pack(fill=tk.X, pady=(10, 0))

    def _build_animation_tab(self):
        """
        Build the compact animation tab without scrollbars.
        """
        self.animate_tab.grid_columnconfigure(0, weight=1)
        self.animation_frame, animation_body = self._create_card(self.animate_tab, "Animation Frames")
        self.animation_frame.grid(row=0, column=0, sticky="nsew")

        self.animation_button_row = tk.Frame(animation_body, bg=self.theme["panel"])
        self.animation_button_row.pack(fill=tk.X)
        self.add_frame_button = tk.Button(
            self.animation_button_row,
            text="Add Frame",
            command=self.add_animation_frame,
            **self._button_style(self.theme["button"])
        )
        self.add_frame_button.pack(side=tk.LEFT)

        self.delete_frame_button = tk.Button(
            self.animation_button_row,
            text="Delete Last",
            command=self.delete_last_animation_frame,
            **self._button_style(self.theme["button_alt"])
        )
        self.delete_frame_button.pack(side=tk.LEFT, padx=(8, 0))

        self.export_animation_button = tk.Button(
            self.animation_button_row,
            text="Export",
            command=self.open_animation_export_modal,
            **self._button_style(self.theme["accent_soft"])
        )
        self.export_animation_button.pack(side=tk.RIGHT)

        self.animation_status_label = tk.Label(
            animation_body,
            textvariable=self.animation_status_var,
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            anchor="w",
            justify=tk.LEFT
        )
        self.animation_status_label.pack(fill=tk.X, pady=(8, 6))

        self.animation_preview_inner = tk.Frame(
            animation_body,
            bg=self.theme["panel_soft"],
            highlightbackground=self.theme["border"],
            highlightthickness=1,
            bd=0
        )
        self.animation_preview_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            animation_body,
            text="The panel shows the latest frames so the layout stays compact.",
            fg=self.theme["muted"],
            bg=self.theme["panel"],
            anchor="w"
        ).pack(fill=tk.X, pady=(8, 0))

    def _build_palette_tab(self):
        """
        Build the palette extraction tab.
        """
        self.palette_tab.grid_columnconfigure(0, weight=1)
        self.palette_frame, palette_body = self._create_card(self.palette_tab, "Palette", self.palette_status_var)
        self.palette_frame.grid(row=0, column=0, sticky="nsew")

        self.palette_count_slider = self._create_compact_slider(
            palette_body,
            "Color Count",
            2,
            24,
            self.update_palette_count,
            initial=8,
        )

        format_row = tk.Frame(palette_body, bg=self.theme["panel"])
        format_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(format_row, text="Format", fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(anchor="w")
        self.palette_format_menu = tk.OptionMenu(
            format_row,
            self.palette_format_var,
            "PNG Image (1x)",
            "PNG Image (8x)",
            "PNG Image (32x)",
            "PAL File (JASC)",
            "Photoshop ASE",
            "Paint.net TXT",
            "GIMP GPL",
            "HEX File",
        )
        self._style_option_menu(self.palette_format_menu)
        self.palette_format_menu.pack(fill=tk.X, pady=(4, 0))

        sort_row = tk.Frame(palette_body, bg=self.theme["panel"])
        sort_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(sort_row, text="Sort Colors", fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(anchor="w")
        self.palette_sort_menu = tk.OptionMenu(
            sort_row,
            self.palette_sort_var,
            "Frequency",
            "Hue",
            "Brightness",
            command=self.update_palette_display,
        )
        self._style_option_menu(self.palette_sort_menu)
        self.palette_sort_menu.pack(fill=tk.X, pady=(4, 0))

        self.extract_palette_button = tk.Button(
            palette_body,
            text="Extract Palette",
            command=self.extract_palette_from_preview,
            **self._button_style(self.theme["accent_soft"])
        )
        self.extract_palette_button.pack(fill=tk.X, pady=(0, 6))

        self.save_palette_button = tk.Button(
            palette_body,
            text="Save Palette As",
            command=self.save_palette_as,
            **self._button_style(self.theme["button_alt"])
        )
        self.save_palette_button.pack(fill=tk.X, pady=(0, 10))

        preview_label = tk.Label(
            palette_body,
            text="Preview (click a swatch to copy HEX)",
            fg=self.theme["text"],
            bg=self.theme["panel"],
            anchor="w"
        )
        preview_label.pack(fill=tk.X)

        self.palette_preview_inner = tk.Frame(
            palette_body,
            bg=self.theme["panel_soft"],
            highlightbackground=self.theme["panel_soft"],
            highlightthickness=0,
            bd=0
        )
        self.palette_preview_inner.pack(fill=tk.X, pady=(4, 10))

        values_label = tk.Label(
            palette_body,
            text="Palette Values",
            fg=self.theme["text"],
            bg=self.theme["panel"],
            anchor="w"
        )
        values_label.pack(fill=tk.X)

        self.palette_values_text = tk.Text(
            palette_body,
            height=12,
            wrap=tk.WORD,
            bg=self.theme["field"],
            fg=self.theme["text"],
            insertbackground=self.theme["text"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["field_border"],
            highlightcolor=self.theme["accent"],
            bd=0,
            padx=10,
            pady=10,
        )
        self.palette_values_text.pack(fill=tk.BOTH, expand=True)
        self.palette_values_text.configure(state=tk.DISABLED)
        self._reset_palette_output()

    def _create_card(self, parent, title, subtitle=None, stretch=False):
        """
        Create a classic desktop group container and return the card plus its body frame.
        """
        card = tk.Frame(
            parent,
            bg=self.theme["panel"],
            relief=tk.RAISED,
            bd=2,
            highlightthickness=0,
        )
        if stretch:
            card.grid_propagate(True)

        header = tk.Frame(card, bg=self.theme["panel"])
        header.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(
            header,
            text=title,
            fg=self.theme["text"],
            bg=self.theme["panel"],
            font=("Helvetica", 11, "bold")
        ).pack(anchor="w")

        if subtitle is not None:
            tk.Label(
                header,
                textvariable=subtitle if isinstance(subtitle, tk.Variable) else None,
                text=subtitle if not isinstance(subtitle, tk.Variable) else None,
                fg=self.theme["muted"],
                bg=self.theme["panel"],
                justify=tk.LEFT,
                wraplength=340
            ).pack(anchor="w", pady=(3, 0))

        body = tk.Frame(card, bg=self.theme["panel"])
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        return card, body

    def _set_palette_text(self, text):
        """
        Update the palette text output.
        """
        if not hasattr(self, 'palette_values_text'):
            return

        self.palette_values_text.configure(state=tk.NORMAL)
        self.palette_values_text.delete("1.0", tk.END)
        self.palette_values_text.insert("1.0", text)
        self.palette_values_text.configure(state=tk.DISABLED)

    def _reset_palette_output(self, message=None):
        """
        Clear palette output widgets and status.
        """
        self.palette_entries = []
        if message is None:
            message = "Load an image and extract a palette from the preview."

        self.palette_status_var.set(message)
        if hasattr(self, 'palette_preview_inner'):
            for child in self.palette_preview_inner.winfo_children():
                child.destroy()
            tk.Label(
                self.palette_preview_inner,
                text="Extract a palette to see color swatches here.",
                fg=self.theme["muted"],
                bg=self.theme["panel_soft"],
                justify=tk.LEFT,
                wraplength=300,
            ).pack(anchor="w", padx=0, pady=8)

        self._set_palette_text("No palette extracted yet.")

    def _get_color_luminance(self, rgb):
        """
        Return perceived luminance for an RGB tuple.
        """
        red, green, blue = rgb
        return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)

    def _palette_text_color(self, rgb):
        """
        Choose dark or light text for a swatch.
        """
        return "#11131a" if self._get_color_luminance(rgb) >= 150 else self.theme["text"]

    def _rgb_to_hex(self, rgb):
        """
        Convert RGB to hex.
        """
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def _rgb_to_hsl(self, rgb):
        """
        Convert RGB to HSL components.
        """
        red, green, blue = [channel / 255.0 for channel in rgb]
        hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
        return (
            int(round(hue * 360.0)) % 360,
            int(round(saturation * 100.0)),
            int(round(lightness * 100.0)),
        )

    def _rgb_to_hsv(self, rgb):
        """
        Convert RGB to HSV components.
        """
        red, green, blue = [channel / 255.0 for channel in rgb]
        hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
        return (
            int(round(hue * 360.0)) % 360,
            int(round(saturation * 100.0)),
            int(round(value * 100.0)),
        )

    def _rgb_to_cmyk(self, rgb):
        """
        Convert RGB to CMYK components.
        """
        red, green, blue = [channel / 255.0 for channel in rgb]
        key = 1.0 - max(red, green, blue)
        if key >= 1.0:
            return (0, 0, 0, 100)

        cyan = (1.0 - red - key) / max(0.0001, 1.0 - key)
        magenta = (1.0 - green - key) / max(0.0001, 1.0 - key)
        yellow = (1.0 - blue - key) / max(0.0001, 1.0 - key)
        return (
            int(round(cyan * 100.0)),
            int(round(magenta * 100.0)),
            int(round(yellow * 100.0)),
            int(round(key * 100.0)),
        )

    def _get_palette_export_formats(self):
        """
        Return supported palette export formats.
        """
        return {
            "PNG Image (1x)": {
                "extension": ".png",
                "filetypes": [("PNG Image", "*.png")],
            },
            "PNG Image (8x)": {
                "extension": ".png",
                "filetypes": [("PNG Image", "*.png")],
            },
            "PNG Image (32x)": {
                "extension": ".png",
                "filetypes": [("PNG Image", "*.png")],
            },
            "PAL File (JASC)": {
                "extension": ".pal",
                "filetypes": [("JASC Palette", "*.pal")],
            },
            "Photoshop ASE": {
                "extension": ".ase",
                "filetypes": [("Adobe Swatch Exchange", "*.ase")],
            },
            "Paint.net TXT": {
                "extension": ".txt",
                "filetypes": [("Paint.net Palette", "*.txt")],
            },
            "GIMP GPL": {
                "extension": ".gpl",
                "filetypes": [("GIMP Palette", "*.gpl")],
            },
            "HEX File": {
                "extension": ".txt",
                "filetypes": [("HEX Palette", "*.txt")],
            },
        }

    def _format_palette_color(self, rgb):
        """
        Format a palette color for the on-screen value list.
        """
        hex_value = self._rgb_to_hex(rgb)
        rgb_value = f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"
        hsl = self._rgb_to_hsl(rgb)
        hsv = self._rgb_to_hsv(rgb)
        cmyk = self._rgb_to_cmyk(rgb)

        hsl_value = f"hsl({hsl[0]}°, {hsl[1]}%, {hsl[2]}%)"
        hsv_value = f"hsv({hsv[0]}°, {hsv[1]}%, {hsv[2]}%)"
        cmyk_value = f"cmyk({cmyk[0]}%, {cmyk[1]}%, {cmyk[2]}%, {cmyk[3]}%)"
        return f"{hex_value} | {rgb_value} | {hsl_value} | {hsv_value} | {cmyk_value}"

    def _copy_palette_hex(self, rgb):
        """
        Copy a swatch HEX value to the clipboard.
        """
        hex_value = self._rgb_to_hex(rgb)
        self.root.clipboard_clear()
        self.root.clipboard_append(hex_value)
        self.root.update_idletasks()
        self.palette_status_var.set(f"Copied {hex_value} to the clipboard.")

    def _palette_file_stem(self):
        """
        Return a base filename for palette exports.
        """
        if self.image_object is None or not getattr(self.image_object, 'name', None):
            return "Weird_Pixelator_Palette"

        name_root, _ext = os.path.splitext(self.image_object.name)
        cleaned = name_root.strip() or "Weird_Pixelator_Palette"
        return f"{cleaned}_palette"

    def _write_palette_png(self, file_path, entries, scale):
        """
        Save the palette as a PNG swatch strip.
        """
        colors = [entry["rgb"] for entry in entries]
        swatch_size = max(1, int(scale))
        palette_image = Image.new("RGB", (len(colors) * swatch_size, swatch_size))

        for index, rgb in enumerate(colors):
            swatch = Image.new("RGB", (swatch_size, swatch_size), rgb)
            palette_image.paste(swatch, (index * swatch_size, 0))

        palette_image.save(file_path)

    def _write_palette_jasc(self, file_path, entries):
        """
        Save the palette as a JASC PAL file.
        """
        lines = ["JASC-PAL", "0100", str(len(entries))]
        for entry in entries:
            red, green, blue = entry["rgb"]
            lines.append(f"{red} {green} {blue}")

        with open(file_path, "w", encoding="utf-8") as palette_file:
            palette_file.write("\n".join(lines) + "\n")

    def _write_palette_hex_file(self, file_path, entries):
        """
        Save the palette as a plain HEX list.
        """
        lines = [self._rgb_to_hex(entry["rgb"]) for entry in entries]
        with open(file_path, "w", encoding="utf-8") as palette_file:
            palette_file.write("\n".join(lines) + "\n")

    def _write_palette_gpl(self, file_path, entries):
        """
        Save the palette as a GIMP GPL file.
        """
        lines = [
            "GIMP Palette",
            f"Name: {self._palette_file_stem()}",
            "Columns: 4",
            "#",
        ]
        for index, entry in enumerate(entries, start=1):
            red, green, blue = entry["rgb"]
            lines.append(f"{red:3d} {green:3d} {blue:3d} Color {index}")

        with open(file_path, "w", encoding="utf-8") as palette_file:
            palette_file.write("\n".join(lines) + "\n")

    def _write_palette_paintnet(self, file_path, entries):
        """
        Save the palette as a Paint.net text palette.
        """
        lines = [
            "; paint.net Palette File",
            "; Generated by Weird Pixelator",
            "; Colors are written as AARRGGBB hex values",
        ]
        for entry in entries:
            red, green, blue = entry["rgb"]
            lines.append(f"FF{red:02X}{green:02X}{blue:02X}")

        with open(file_path, "w", encoding="utf-8") as palette_file:
            palette_file.write("\n".join(lines) + "\n")

    def _write_palette_ase(self, file_path, entries):
        """
        Save the palette as an Adobe Swatch Exchange file.
        """
        blocks = []
        for index, entry in enumerate(entries, start=1):
            red, green, blue = entry["rgb"]
            name = f"Color {index}"
            name_data = name.encode("utf-16be") + b"\x00\x00"
            name_length = len(name) + 1
            block_data = b"".join([
                struct.pack(">H", name_length),
                name_data,
                b"RGB ",
                struct.pack(">fff", red / 255.0, green / 255.0, blue / 255.0),
                struct.pack(">H", 0),
            ])
            blocks.append(struct.pack(">HI", 0x0001, len(block_data)) + block_data)

        header = struct.pack(">4sHHI", b"ASEF", 1, 0, len(blocks))
        with open(file_path, "wb") as palette_file:
            palette_file.write(header)
            for block in blocks:
                palette_file.write(block)

    def _export_palette_file(self, entries):
        """
        Save the current palette in the selected export format.
        """
        format_name = self.palette_format_var.get()
        format_info = self._get_palette_export_formats().get(format_name)
        if format_info is None:
            raise ValueError("Unsupported palette format.")

        initial_dir = self.folder_path.get().strip() or os.getcwd()
        file_path = filedialog.asksaveasfilename(
            title="Save Palette",
            defaultextension=format_info["extension"],
            filetypes=format_info["filetypes"],
            initialdir=initial_dir,
            initialfile=f"{self._palette_file_stem()}{format_info['extension']}",
        )
        if not file_path:
            return None

        if format_name == "PNG Image (1x)":
            self._write_palette_png(file_path, entries, 1)
        elif format_name == "PNG Image (8x)":
            self._write_palette_png(file_path, entries, 8)
        elif format_name == "PNG Image (32x)":
            self._write_palette_png(file_path, entries, 32)
        elif format_name == "PAL File (JASC)":
            self._write_palette_jasc(file_path, entries)
        elif format_name == "Photoshop ASE":
            self._write_palette_ase(file_path, entries)
        elif format_name == "Paint.net TXT":
            self._write_palette_paintnet(file_path, entries)
        elif format_name == "GIMP GPL":
            self._write_palette_gpl(file_path, entries)
        elif format_name == "HEX File":
            self._write_palette_hex_file(file_path, entries)
        else:
            raise ValueError("Unsupported palette format.")

        return file_path

    def _sorted_palette_entries(self):
        """
        Return palette entries in the currently selected sort order.
        """
        entries = list(self.palette_entries)
        sort_mode = self.palette_sort_var.get()

        if sort_mode == "Hue":
            entries.sort(key=lambda entry: self._rgb_to_hsv(entry["rgb"]))
            return entries

        if sort_mode == "Brightness":
            entries.sort(key=lambda entry: self._get_color_luminance(entry["rgb"]))
            return entries

        entries.sort(key=lambda entry: (-entry["count"], -self._get_color_luminance(entry["rgb"])))
        return entries

    def update_palette_count(self, _=None):
        """
        Re-extract the palette when a palette already exists and the count changes.
        """
        if self.palette_entries:
            self._extract_palette_from_preview(save_to_file=False)

    def update_palette_display(self, _=None):
        """
        Refresh the palette swatches and value list.
        """
        if not self.palette_entries:
            self._reset_palette_output(self.palette_status_var.get())
            return

        for child in self.palette_preview_inner.winfo_children():
            child.destroy()

        sorted_entries = self._sorted_palette_entries()
        for column in range(8):
            self.palette_preview_inner.grid_columnconfigure(column, weight=1)

        for index, entry in enumerate(sorted_entries):
            rgb = entry["rgb"]
            hex_value = self._rgb_to_hex(rgb)
            tile = tk.Frame(
                self.palette_preview_inner,
                bg=hex_value,
                highlightbackground=hex_value,
                highlightthickness=0,
                bd=0,
                cursor="hand2",
                width=14,
                height=14,
            )
            tile.grid(row=index // 8, column=index % 8, sticky="nsew", padx=0, pady=0)
            tile.grid_propagate(False)

            for widget in (tile,):
                widget.bind("<Button-1>", lambda _event, color=rgb: self._copy_palette_hex(color))

        lines = []
        for index, entry in enumerate(sorted_entries, start=1):
            color_text = self._format_palette_color(entry["rgb"])
            ratio_text = f"{entry['ratio'] * 100:.1f}%"
            lines.append(f"{index}. {color_text} • {ratio_text}")

        self._set_palette_text("\n".join(lines))

    def _extract_palette_from_preview(self, save_to_file=False):
        """
        Extract a palette from the current rendered preview image.
        """
        if self.image_object is None or self.current_pil_image is None:
            messagebox.showerror("Error", "Load an image before extracting a palette.")
            return

        preview_image = self.render_current_image(for_preview=True)
        if preview_image is None:
            messagebox.showerror("Error", "Unable to render the current preview for palette extraction.")
            return

        color_count = max(2, min(24, int(float(self.palette_count_slider.get()))))
        entries = image_effects.extract_palette(preview_image, color_count)
        if not entries:
            self._reset_palette_output("No colors could be extracted from the current preview.")
            return

        self.palette_entries = entries
        self.palette_status_var.set(f"Extracted {len(entries)} colors from the current preview.")
        self.update_palette_display()

        if save_to_file:
            file_path = self._export_palette_file(self._sorted_palette_entries())
            if file_path:
                self.palette_status_var.set(f"Saved palette to {os.path.basename(file_path)}")

    def extract_palette_from_preview(self):
        """
        Extract a palette from the current preview.
        """
        self._extract_palette_from_preview(save_to_file=False)

    def save_palette_as(self):
        """
        Save the current extracted palette using the selected export format.
        """
        if not self.palette_entries:
            messagebox.showerror("Error", "Extract a palette before saving it.")
            return

        try:
            file_path = self._export_palette_file(self._sorted_palette_entries())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save palette: {e}")
            return

        if file_path:
            self.palette_status_var.set(f"Saved palette to {os.path.basename(file_path)}")

    def _style_option_menu(self, menu):
        """
        Apply the shared dark style to an OptionMenu.
        """
        if self.is_macos:
            field_bg = "#d7dbe4"
            text_color = "#11131a"
            active_bg = "#c8cfdb"
        else:
            field_bg = self.theme["field"]
            text_color = self.theme["text"]
            active_bg = self.theme["panel_alt"]

        menu.configure(
            bg=field_bg,
            fg=text_color,
            activebackground=active_bg,
            activeforeground=text_color,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            bd=2,
            relief=tk.RAISED,
            width=14,
            anchor="w"
        )
        menu["menu"].configure(bg=field_bg, fg=text_color, activebackground=active_bg, activeforeground=text_color)

    def _entry_style(self):
        """
        Shared entry styling.
        """
        return {
            "bg": self.theme["field"],
            "fg": self.theme["text"],
            "insertbackground": self.theme["text"],
            "relief": tk.SUNKEN,
            "highlightthickness": 1,
            "highlightbackground": self.theme["field_border"],
            "highlightcolor": self.theme["accent"],
            "bd": 2,
        }

    def _create_compact_slider(self, parent, label_text, from_, to, command, resolution=1, initial=0, formatter=None):
        """
        Create a compact slider row with a live numeric readout.
        """
        row = tk.Frame(parent, bg=self.theme["panel"])
        row.pack(fill=tk.X, pady=(0, 6))

        header = tk.Frame(row, bg=self.theme["panel"])
        header.pack(fill=tk.X)
        tk.Label(header, text=label_text, fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(side=tk.LEFT)

        value_var = tk.StringVar()
        tk.Label(header, textvariable=value_var, fg=self.theme["muted"], bg=self.theme["panel"], anchor="e").pack(side=tk.RIGHT)

        scale_var = tk.DoubleVar(value=initial)
        format_value = formatter or (lambda value: str(int(round(float(value)))))
        value_var.set(format_value(initial))

        def sync_label(*_args):
            value_var.set(format_value(scale_var.get()))

        scale_var.trace_add("write", sync_label)
        self._slider_value_bindings.append((scale_var, value_var))

        scale = tk.Scale(
            row,
            from_=from_,
            to=to,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            variable=scale_var,
            showvalue=False,
            bg=self.theme["panel"],
            fg=self.theme["text"],
            troughcolor=self.theme["button_alt"],
            activebackground=self.theme["accent"],
            highlightthickness=0,
            bd=1,
            relief=tk.FLAT,
            sliderlength=18,
            width=10,
            command=command,
        )
        scale.pack(fill=tk.X, pady=(3, 0))
        scale.set(initial)
        return scale

    def _create_crop_control(self, parent, row, column, edge, label):
        """
        Create a compact crop control with entry and slider.
        """
        target_var = {
            "left": self.crop_left_var,
            "right": self.crop_right_var,
            "top": self.crop_top_var,
            "bottom": self.crop_bottom_var,
        }[edge]

        container = tk.Frame(parent, bg=self.theme["panel"])
        container.grid(row=row, column=column, sticky="nsew", padx=(0, 6) if column == 0 else (6, 0), pady=(0, 8))
        parent.grid_rowconfigure(row, weight=1)

        header = tk.Frame(container, bg=self.theme["panel"])
        header.pack(fill=tk.X)
        tk.Label(header, text=label, fg=self.theme["text"], bg=self.theme["panel"], anchor="w").pack(side=tk.LEFT)
        entry = tk.Entry(header, textvariable=target_var, width=7, justify=tk.RIGHT, **self._entry_style())
        entry.pack(side=tk.RIGHT)
        entry.bind("<Return>", lambda _event: self.commit_crop_entry(edge))
        entry.bind("<FocusOut>", lambda _event: self.commit_crop_entry(edge))

        slider = tk.Scale(
            container,
            from_=0,
            to=0,
            resolution=1,
            orient=tk.HORIZONTAL,
            bg=self.theme["panel"],
            fg=self.theme["text"],
            troughcolor=self.theme["button_alt"],
            activebackground=self.theme["accent"],
            highlightthickness=0,
            bd=1,
            relief=tk.FLAT,
            sliderlength=18,
            width=10,
            showvalue=False,
            command=lambda _value: self.update_crop(edge)
        )
        slider.pack(fill=tk.X, pady=(4, 0))
        slider.set(0)
        return slider, entry

    def _render_empty_preview(self):
        """
        Draw an empty-state placeholder in the preview canvas.
        """
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())
        self.canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill=self.theme["canvas"], outline="")
        self.canvas.create_text(
            canvas_width / 2,
            canvas_height / 2 - 12,
            text="No image loaded",
            fill=self.theme["text"],
            font=("Helvetica", 16, "bold")
        )
        self.canvas.create_text(
            canvas_width / 2,
            canvas_height / 2 + 16,
            text="Upload a file to start editing.",
            fill=self.theme["muted"],
            font=("Helvetica", 11)
        )

    def _update_preview_metadata(self, rendered_size=None):
        """
        Refresh the preview title and status text.
        """
        if self.image_object is None or self.current_pil_image is None:
            self.preview_title_var.set("No image loaded")
            self.preview_hint_var.set("Upload an image to start creating a glitchy preview.")
            return

        source_width, source_height = self.current_pil_image.size
        self.preview_title_var.set(self.image_object.name)

        preview_text = f"Source {source_width} x {source_height}"
        crop_text = self.crop_size_var.get()
        if crop_text and crop_text != "Final Size: -":
            preview_text += f" • {crop_text}"
        if rendered_size is not None and rendered_size != (source_width, source_height):
            preview_text += f" • Preview {rendered_size[0]} x {rendered_size[1]}"

        self.preview_hint_var.set(preview_text)

    def _button_style(self, background):
        """
        Shared button styling for the classic UI.
        """
        if self.is_macos:
            background = "#d4d0c8" if background != self.theme["accent_soft"] else "#dbe7f7"
            foreground = "#11131a"
            active_background = "#c6c1b8" if background != "#dbe7f7" else "#c8d8f2"
            disabled_foreground = "#5f6776"
        else:
            foreground = self.theme["text"]
            active_background = self.theme["panel_alt"]
            disabled_foreground = foreground

        return {
            "bg": background,
            "fg": foreground,
            "activebackground": active_background,
            "activeforeground": foreground,
            "disabledforeground": disabled_foreground,
            "highlightbackground": self.theme["shadow_light"],
            "highlightcolor": self.theme["shadow_light"],
            "bd": 2,
            "relief": tk.RAISED,
            "padx": 12,
            "pady": 8,
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

    def _update_animation_status(self):
        """
        Refresh the frame counter shown in the animation section.
        """
        frame_count = len(self.animation_frames)
        if frame_count == 0:
            self.animation_status_var.set("No frames added yet.")
            return

        first_width, first_height = self.animation_frames[0].size
        suffix = " • showing latest 6" if frame_count > 6 else ""
        self.animation_status_var.set(f"{frame_count} frame(s) • base {first_width} x {first_height}{suffix}")

    def _update_animation_scroll_region(self, _event=None):
        """
        Legacy no-op kept for compatibility with the updated compact layout.
        """
        return

    def _resize_animation_preview_window(self, event):
        """
        Legacy no-op kept for compatibility with the updated compact layout.
        """
        return

    def _refresh_animation_preview_strip(self):
        """
        Rebuild the compact thumbnail grid for captured animation frames.
        """
        for child in self.animation_preview_inner.winfo_children():
            child.destroy()

        self.animation_preview_images = []

        if not self.animation_frames:
            empty_label = tk.Label(
                self.animation_preview_inner,
                text="Capture frames from the current preview to build an animation.",
                fg=self.theme["muted"],
                bg=self.theme["panel_soft"],
                justify=tk.LEFT,
                wraplength=300
            )
            empty_label.pack(anchor="w", padx=12, pady=18)
            self._update_animation_status()
            return

        for column in range(3):
            self.animation_preview_inner.grid_columnconfigure(column, weight=1)

        visible_frames = list(enumerate(self.animation_frames, start=1))[-6:]

        for display_index, (frame_index, frame) in enumerate(visible_frames):
            tile = tk.Frame(
                self.animation_preview_inner,
                bg=self.theme["panel_alt"],
                highlightbackground=self.theme["border"],
                highlightthickness=1,
                bd=0
            )
            tile.grid(row=display_index // 3, column=display_index % 3, sticky="nsew", padx=4, pady=4)

            thumb = frame.copy()
            thumb.thumbnail((92, 92), Image.LANCZOS)
            photo = ImageTk.PhotoImage(thumb)
            self.animation_preview_images.append(photo)

            preview_label = tk.Label(tile, image=photo, bg=self.theme["panel_alt"])
            preview_label.pack(padx=8, pady=(8, 4))

            caption = tk.Label(
                tile,
                text=f"Frame {frame_index}\n{frame.size[0]} x {frame.size[1]}",
                fg=self.theme["text"], bg=self.theme["panel_alt"],
                justify=tk.CENTER
            )
            caption.pack(padx=8, pady=(0, 8))

        self._update_animation_status()

    def _get_animation_export_formats(self):
        """
        Return the supported animation export formats.
        """
        return {
            "GIF": {
                "extension": ".gif",
                "filetypes": [("GIF Animation", "*.gif")],
            },
            "MP4": {
                "extension": ".mp4",
                "filetypes": [("MP4 Video", "*.mp4")],
            },
            "Animated WebP": {
                "extension": ".webp",
                "filetypes": [("Animated WebP", "*.webp")],
            },
        }

    def _prepare_animation_frames(self, target_size=None, flatten_alpha=False):
        """
        Normalize captured frames to a shared export size.
        """
        if not self.animation_frames:
            return []

        if target_size is None:
            target_size = self.animation_frames[0].size

        prepared_frames = []
        for frame in self.animation_frames:
            working = frame.convert("RGBA")
            if working.size != target_size:
                working = ImageOps.pad(working, target_size, method=Image.LANCZOS, color=(0, 0, 0, 255))

            if flatten_alpha:
                background = Image.new("RGB", target_size, (0, 0, 0))
                background.paste(working, mask=working.getchannel("A"))
                prepared_frames.append(background)
            else:
                prepared_frames.append(working)

        return prepared_frames

    def add_animation_frame(self):
        """
        Capture the current full-resolution render as the next animation frame.
        """
        if self.image_object is None:
            messagebox.showerror("Error", "Load an image before adding animation frames.")
            return

        frame_image = self.render_current_image(for_preview=False)
        if frame_image is None:
            messagebox.showerror("Error", "Unable to render the current frame.")
            return

        self.animation_frames.append(frame_image.copy())
        self._refresh_animation_preview_strip()

    def delete_last_animation_frame(self):
        """
        Remove the most recently captured animation frame.
        """
        if not self.animation_frames:
            messagebox.showerror("Error", "There are no animation frames to delete.")
            return

        self.animation_frames.pop()
        self._refresh_animation_preview_strip()

    def clear_animation_frames(self):
        """
        Remove all captured animation frames.
        """
        self.animation_frames.clear()
        self._refresh_animation_preview_strip()

    def open_animation_export_modal(self):
        """
        Open a modal window for choosing animation export settings.
        """
        if not self.animation_frames:
            messagebox.showerror("Error", "Add at least one frame before exporting an animation.")
            return

        formats = self._get_animation_export_formats()
        modal = tk.Toplevel(self.root)
        modal.title("Export Animation")
        modal.configure(bg=self.theme["panel"])
        modal.transient(self.root)
        modal.grab_set()
        modal.resizable(False, False)

        format_var = tk.StringVar(value="GIF")
        fps_var = tk.IntVar(value=8)

        tk.Label(
            modal,
            text=f"Frames: {len(self.animation_frames)}\nFrames with different sizes will be padded to the first frame when exported.",
            fg=self.theme["muted"], bg=self.theme["panel"],
            justify=tk.LEFT
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8))

        tk.Label(modal, text="Format:", fg=self.theme["text"], bg=self.theme["panel"]).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        format_menu = tk.OptionMenu(modal, format_var, *formats.keys())
        self._style_option_menu(format_menu)
        format_menu.grid(row=1, column=1, sticky="ew", padx=12, pady=4)

        tk.Label(modal, text="FPS:", fg=self.theme["text"], bg=self.theme["panel"]).grid(row=2, column=0, sticky="w", padx=12, pady=4)
        fps_spinbox = tk.Spinbox(
            modal,
            from_=1,
            to=60,
            textvariable=fps_var,
            width=8,
            bg=self.theme["field"],
            fg=self.theme["text"],
            insertbackground=self.theme["text"],
            buttonbackground=self.theme["button"],
            relief=tk.SUNKEN,
            bd=2
        )
        fps_spinbox.grid(row=2, column=1, sticky="w", padx=12, pady=4)

        button_row = tk.Frame(modal, bg=self.theme["panel"])
        button_row.grid(row=3, column=0, columnspan=2, sticky="e", padx=12, pady=(12, 12))

        tk.Button(button_row, text="Cancel", command=modal.destroy, **self._button_style(self.theme["button"])).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            button_row,
            text="Export",
            command=lambda: self._export_animation_from_modal(modal, format_var.get(), fps_var.get()),
            **self._button_style(self.theme["button_alt"])
        ).pack(side=tk.LEFT)

    def _export_animation_from_modal(self, modal, format_name, fps_value):
        """
        Validate modal settings and export the animation.
        """
        formats = self._get_animation_export_formats()
        format_info = formats.get(format_name)
        if format_info is None:
            messagebox.showerror("Error", "Unsupported animation format.")
            return

        try:
            fps = max(1, min(60, int(fps_value)))
        except (TypeError, ValueError):
            messagebox.showerror("Error", "FPS must be a whole number between 1 and 60.")
            return

        initial_dir = self.folder_path.get().strip() or os.getcwd()
        file_path = filedialog.asksaveasfilename(
            title="Export Animation",
            defaultextension=format_info["extension"],
            filetypes=format_info["filetypes"],
            initialdir=initial_dir,
            initialfile=f"Weird_Pixellator_Animation{format_info['extension']}"
        )
        if not file_path:
            return

        try:
            self.export_animation(file_path, format_name, fps)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export animation: {e}")
            return

        modal.destroy()
        messagebox.showinfo("Success", f"Animation exported to {file_path}")

    def export_animation(self, file_path, format_name, fps):
        """
        Export the captured frame sequence to the selected animation format.
        """
        if not self.animation_frames:
            raise ValueError("No animation frames available.")

        duration_ms = max(1, int(round(1000 / max(1, fps))))
        base_width, base_height = self.animation_frames[0].size

        if format_name == "GIF":
            frames = self._prepare_animation_frames(target_size=(base_width, base_height), flatten_alpha=False)
            frames[0].save(
                file_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration_ms,
                loop=0,
                disposal=2
            )
            return

        if format_name == "Animated WebP":
            frames = self._prepare_animation_frames(target_size=(base_width, base_height), flatten_alpha=False)
            frames[0].save(
                file_path,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=duration_ms,
                loop=0,
                lossless=True,
                quality=90,
                method=6
            )
            return

        if format_name == "MP4":
            try:
                import imageio.v2 as imageio
            except ImportError as exc:
                raise RuntimeError("MP4 export requires the imageio packages from requirements.txt.") from exc

            video_size = (base_width + (base_width % 2), base_height + (base_height % 2))
            frames = self._prepare_animation_frames(target_size=video_size, flatten_alpha=True)
            with imageio.get_writer(
                file_path,
                fps=fps,
                codec="libx264",
                quality=8,
                pixelformat="yuv420p",
                macro_block_size=1
            ) as writer:
                for frame in frames:
                    writer.append_data(np.array(frame))
            return

        raise ValueError(f"Unsupported export format: {format_name}")

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
            self.clear_animation_frames()
            self._reset_palette_output("Ready to extract a palette from the current preview.")

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
            self._update_preview_metadata()
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
        self._update_preview_metadata()

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
        if img is None:
            self.tk_img = None
            self._render_empty_preview()
            self._update_preview_metadata()
            return

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
        self._update_preview_metadata(rendered_size=img.size)

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
        win.configure(bg=self.theme["panel"])
        win.transient(self.root)
        win.grab_set()

        # Layout checkboxes in two columns, alphabetically
        sorted_keys = sorted(self.randomize_settings.keys(), key=lambda key: key.replace('_', ' '))
        left_keys = sorted_keys[::2]
        right_keys = sorted_keys[1::2]

        row = 0
        for k in left_keys:
            cb = tk.Checkbutton(
                win,
                text=k.replace('_',' ').title(),
                variable=self.randomize_settings[k],
                bg=self.theme["panel"],
                fg=self.theme["text"],
                activebackground=self.theme["panel"],
                activeforeground=self.theme["text"],
                selectcolor=self.theme["field"],
            )
            cb.grid(row=row, column=0, sticky='w', padx=10, pady=2)
            row += 1

        row = 0
        for k in right_keys:
            if k not in self.randomize_settings:
                self.randomize_settings[k] = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(
                win,
                text=k.replace('_',' ').title(),
                variable=self.randomize_settings[k],
                bg=self.theme["panel"],
                fg=self.theme["text"],
                activebackground=self.theme["panel"],
                activeforeground=self.theme["text"],
                selectcolor=self.theme["field"],
            )
            cb.grid(row=row, column=1, sticky='w', padx=10, pady=2)
            row += 1

        # Buttons
        btn_frame = tk.Frame(win, bg=self.theme["panel"])
        btn_frame.grid(row=max(len(left_keys), len(right_keys))+1, column=0, columnspan=2, pady=10)

        def select_all():
            for v in self.randomize_settings.values():
                v.set(True)

        def deselect_all():
            for v in self.randomize_settings.values():
                v.set(False)

        tk.Button(btn_frame, text="Select All", command=select_all, **self._button_style(self.theme["button"])).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Deselect All", command=deselect_all, **self._button_style(self.theme["button"])).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=win.destroy, **self._button_style(self.theme["button_alt"])).pack(side=tk.LEFT, padx=5)

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