
import time
from pathlib import Path

import datashader as ds
import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
from datashader import transfer_functions as tf
from holoviews.operation.datashader import datashade
from PIL import Image

hv.extension("bokeh")


# ============================================================
# Visual system
# ============================================================

BG = "#030711"
PANEL_BG = "#081626"
PANEL_BG_2 = "#0b1b2d"
BORDER = "rgba(105, 185, 240, 0.14)"
TEXT = "#edf7ff"
MUTED = "#7890a8"
CYAN = "#4de7ff"
VIOLET = "#a875ff"
PLOT_BG = "#020811"

RAW_CSS = f"""
html, body {{
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100%;
    background:
        radial-gradient(circle at 82% 3%, rgba(105, 73, 255, 0.105), transparent 24%),
        radial-gradient(circle at 3% 82%, rgba(0, 213, 255, 0.065), transparent 27%),
        linear-gradient(135deg, #02050c 0%, #06111d 48%, #080d1b 100%) !important;
    color: {TEXT} !important;
}}

.clifford-app {{
    width: 100%;
    min-height: 100vh;
    box-sizing: border-box;
    padding: 16px 18px 26px 18px;
}}

.topbar {{
    min-height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    margin-bottom: 16px;
    box-sizing: border-box;
    background: linear-gradient(135deg, rgba(7,22,38,.97), rgba(5,17,31,.92));
    border: 1px solid rgba(94,180,240,.13);
    border-radius: 15px;
    box-shadow: 0 14px 36px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.025);
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 11px;
}}

.brand-mark {{
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 9px;
    color: #04101a;
    background: linear-gradient(135deg, #58e9ff, #8e72ff);
    box-shadow: 0 0 24px rgba(77,231,255,.25);
}}

.brand-name {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -.25px;
}}

.brand-subtitle {{
    color: #6d87a2;
    font-size: 9px;
    margin-top: 2px;
}}

.system-status {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #8ba2bb;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.15px;
    text-transform: uppercase;
}}

.status-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: {CYAN};
    box-shadow: 0 0 13px rgba(77,231,255,.95);
}}

.sidebar {{
    width: 290px;
    min-width: 290px;
}}

.section-card {{
    box-sizing: border-box;
    padding: 15px;
    background: linear-gradient(145deg, rgba(8,23,40,.98), rgba(5,14,25,.98));
    border: 1px solid {BORDER};
    border-radius: 15px;
    box-shadow: 0 16px 38px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.022);
}}

.card-kicker {{
    color: #56738f;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

.card-title {{
    color: #e8f4ff;
    font-size: 13px;
    font-weight: 760;
    margin-bottom: 13px;
}}

.hero {{
    padding: 4px 6px 14px 6px;
}}

.hero-kicker {{
    color: {CYAN};
    font-size: 9px;
    font-weight: 850;
    letter-spacing: 2.1px;
    text-transform: uppercase;
    margin-bottom: 5px;
}}

.hero-title {{
    color: #f2f8ff;
    font-size: 35px;
    line-height: 1.02;
    font-weight: 830;
    letter-spacing: -1.8px;
}}

.hero-description {{
    color: #758ca5;
    font-size: 12px;
    line-height: 1.55;
    max-width: 760px;
    margin-top: 7px;
}}

.hero-badge {{
    color: #8deeff;
    background: rgba(62,181,224,.07);
    border: 1px solid rgba(77,231,255,.18);
    border-radius: 999px;
    padding: 7px 11px;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1.3px;
    text-transform: uppercase;
}}

.metric-card {{
    min-height: 67px;
    box-sizing: border-box;
    padding: 11px 13px;
    background: linear-gradient(145deg, rgba(8,25,43,.97), rgba(5,16,29,.97));
    border: 1px solid rgba(101,185,243,.11);
    border-radius: 12px;
}}

.metric-label {{
    color: #5d7590;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}}

.metric-value {{
    color: #edf7ff;
    font-size: 18px;
    font-weight: 790;
    margin-top: 5px;
    white-space: nowrap;
}}

.metric-accent {{
    color: {CYAN};
    text-shadow: 0 0 18px rgba(77,231,255,.14);
}}

.visual-frame {{
    box-sizing: border-box;
    background:
        radial-gradient(circle at 50% 45%, rgba(37,89,140,.04), transparent 49%),
        {PLOT_BG};
    border: 1px solid rgba(75,193,255,.15);
    border-radius: 17px;
    padding: 10px;
    overflow: hidden;
    box-shadow: 0 26px 75px rgba(0,0,0,.34), inset 0 0 65px rgba(14,79,140,.02);
}}

.visual-header {{
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px;
}}

.visual-title {{
    color: #dff0ff;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}

.visual-meta {{
    color: #536c86;
    font-size: 8px;
    font-family: monospace;
}}

.plot-area {{
    background: {PLOT_BG};
    border-radius: 11px;
    overflow: hidden;
}}

.plot-area .bk-toolbar,
.plot-area .bk-toolbar-box {{
    background: {PLOT_BG} !important;
    border: none !important;
}}

.plot-area .bk-toolbar {{
    opacity: .70;
}}

.info-card {{
    min-height: 79px;
    box-sizing: border-box;
    padding: 12px 14px;
    background: linear-gradient(145deg, rgba(8,22,38,.95), rgba(5,14,25,.97));
    border: 1px solid rgba(102,181,238,.10);
    border-radius: 13px;
}}

.info-title {{
    color: #56718c;
    font-size: 8px;
    font-weight: 850;
    letter-spacing: 1.45px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

.info-main {{
    color: #e8f4ff;
    font-size: 12px;
    font-weight: 760;
}}

.info-secondary {{
    color: #637c97;
    font-size: 9px;
    margin-top: 4px;
}}

.footer {{
    color: #405873;
    font-size: 9px;
    padding: 8px 3px 0 3px;
}}

.control-label {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
}}

.control-name {{
    color: #b8cde2;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .5px;
}}

.control-value {{
    color: {CYAN};
    font-size: 10px;
    font-family: monospace;
    font-weight: 700;
}}

.preset-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
}}

.control-block {{
    margin: 0 0 11px 0;
}}

.select-block {{
    margin-top: 2px;
}}

.clifford-app .bk-input {{
    background: #071624 !important;
    color: #e8f4ff !important;
    border-color: rgba(102,190,242,.18) !important;
}}

.clifford-app input {{
    color: #e8f4ff !important;
}}

::-webkit-scrollbar {{
    width: 8px;
}}

::-webkit-scrollbar-track {{
    background: #02050c;
}}

::-webkit-scrollbar-thumb {{
    background: #14304a;
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: #1e4667;
}}
"""

pn.extension(raw_css=[RAW_CSS])


# ============================================================
# Material styling helper
# ============================================================

MATERIAL_DARK = """
:host {
    --design-background-color: #071624;
    --design-background-text-color: #e8f4ff;
    --design-surface-color: #071624;
    --design-surface-text-color: #e8f4ff;
    --design-primary-color: #4de7ff;
    --design-primary-text-color: #031018;
    --design-secondary-color: #a875ff;
    --design-secondary-text-color: #ffffff;
}
"""


# ============================================================
# Clifford presets
# ============================================================

PRESETS = {
    "Classic": (-1.40, 1.60, 1.00, 0.70),
    "Spiral": (-1.40, 1.30, 1.00, 0.70),
    "Ring": (-1.70, 1.80, -1.90, -0.40),
    "Butterfly": (1.10, -1.32, -1.03, 1.54),
    "Chaos": (-1.90, -1.90, -1.90, -1.00),
}

PALETTES = {
    "Neon Aurora": [
        "#05101b", "#073950", "#00b9d9", "#4de7ff",
        "#6f67ff", "#a95fff", "#ff63b1", "#ffd79f", "#fff8ef",
    ],
    "Cyber Sunset": [
        "#10071d", "#2b0d4d", "#65159a", "#c82982",
        "#ff4f66", "#ff914d", "#ffd166", "#fff0c7",
    ],
    "Arctic Pulse": [
        "#041019", "#063651", "#087a9b", "#11bfd3",
        "#63e6f7", "#b7f5ff", "#edfdff", "#ffffff",
    ],
    "Plasma Bloom": [
        "#090511", "#291052", "#59139a", "#981ebd",
        "#e53c9e", "#ff6767", "#ffb43f", "#fff1b2",
    ],
}


# ============================================================
# Generator
# ============================================================

def generate_clifford(a, b, c, d, n_points):
    x = np.empty(n_points, dtype=np.float32)
    y = np.empty(n_points, dtype=np.float32)

    x[0] = 0.1
    y[0] = 0.1

    for i in range(1, n_points):
        xp = x[i - 1]
        yp = y[i - 1]

        x[i] = np.sin(a * yp) + c * np.cos(a * xp)
        y[i] = np.sin(b * xp) + d * np.cos(b * yp)

    return x, y


# ============================================================
# App
# ============================================================

class CliffordLab:

    def __init__(self):
        self.x = None
        self.y = None
        self.last_runtime = 0.0
        self.current_preset = "Classic"
        self.animation_callback = None
        self.animation_frame = 0
        self._setting_preset = False

        self.a = pn.ui.FloatSlider(
            start=-2, end=2, step=.01, value=-1.4,
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )
        self.b = pn.ui.FloatSlider(
            start=-2, end=2, step=.01, value=1.6,
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )
        self.c = pn.ui.FloatSlider(
            start=-2, end=2, step=.01, value=1.0,
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )
        self.d = pn.ui.FloatSlider(
            start=-2, end=2, step=.01, value=.7,
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )
        self.points = pn.ui.IntSlider(
            start=50_000, end=2_000_000, step=50_000, value=750_000,
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )
        self.color_theme = pn.ui.Select(
            options=list(PALETTES),
            value="Neon Aurora",
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
            margin=0,
        )

        self.generate_button = pn.ui.Button(
            label="✦ Generate",
            color="primary",
            variant="contained",
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
        )
        self.animate_button = pn.ui.Button(
            label="◈ Animate",
            color="secondary",
            variant="outlined",
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
        )
        self.save_button = pn.ui.Button(
            label="↓ Save image",
            color="default",
            variant="outlined",
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
        )

        self.preset_buttons = {}
        for name in PRESETS:
            button = pn.ui.Button(
                label=name,
                color="primary" if name == "Classic" else "default",
                variant="contained" if name == "Classic" else "outlined",
                sizing_mode="stretch_width",
                dark_theme=True,
                stylesheets=[MATERIAL_DARK],
            )
            button.on_click(
                lambda event, preset=name: self.use_preset(preset)
            )
            self.preset_buttons[name] = button

        self.random_button = pn.ui.Button(
            label="✦ Random",
            color="secondary",
            variant="outlined",
            sizing_mode="stretch_width",
            dark_theme=True,
            stylesheets=[MATERIAL_DARK],
        )
        self.random_button.on_click(self.random_preset)

        for slider in (self.a, self.b, self.c, self.d):
            slider.param.watch(self.manual_parameter_changed, "value")

        self.color_theme.param.watch(self.color_changed, "value")
        self.generate_button.on_click(self.generate)
        self.animate_button.on_click(self.toggle_animation)
        self.save_button.on_click(self.save_image)

        self.status = pn.pane.Markdown(
            "Ready.",
            styles={"color": "#6f879f", "font-size": "10px", "margin": "0"},
        )

        self.plot = pn.pane.HoloViews(
            height=590,
            sizing_mode="stretch_width",
            margin=0,
        )

        self._build_dynamic_panels()
        self.generate()

    # --------------------------------------------------------
    # Small HTML helpers
    # --------------------------------------------------------

    @staticmethod
    def control_label(name, value):
        return pn.pane.HTML(
            f"""
            <div class="control-label">
                <span class="control-name">{name}</span>
                <span class="control-value">{value}</span>
            </div>
            """
        )

    @staticmethod
    def metric_html(label, value, accent=False):
        cls = "metric-value metric-accent" if accent else "metric-value"
        return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="{cls}">{value}</div>
        </div>
        """

    @staticmethod
    def info_html(title, value, secondary):
        return f"""
        <div class="info-card">
            <div class="info-title">{title}</div>
            <div class="info-main">{value}</div>
            <div class="info-secondary">{secondary}</div>
        </div>
        """

    # --------------------------------------------------------
    # Dynamic panels
    # --------------------------------------------------------

    def _build_dynamic_panels(self):
        self.metric_points = pn.pane.HTML("", sizing_mode="stretch_width")
        self.metric_generation = pn.pane.HTML("", sizing_mode="stretch_width")
        self.metric_mode = pn.pane.HTML("", sizing_mode="stretch_width")
        self.metric_parameters = pn.pane.HTML("", sizing_mode="stretch_width")
        self.current_field = pn.pane.HTML("", sizing_mode="stretch_width")

    def update_dynamic_panels(self):
        self.metric_points.object = self.metric_html(
            "POINTS", f"{self.points.value:,}", True
        )
        self.metric_generation.object = self.metric_html(
            "GENERATION", f"{self.last_runtime:.2f}s", True
        )
        self.metric_mode.object = self.metric_html(
            "MODE", self.current_preset.upper(), False
        )
        self.metric_parameters.object = self.metric_html(
            "A / B / C / D",
            f"{self.a.value:.2f} · {self.b.value:.2f} · "
            f"{self.c.value:.2f} · {self.d.value:.2f}",
            True,
        )
        self.current_field.object = self.info_html(
            "CURRENT FIELD",
            self.current_preset,
            f"a={self.a.value:.2f} · b={self.b.value:.2f} · "
            f"c={self.c.value:.2f} · d={self.d.value:.2f}",
        )

    # --------------------------------------------------------
    # Presets
    # --------------------------------------------------------

    def use_preset(self, name):
        values = PRESETS[name]
        self._setting_preset = True
        try:
            self.a.value, self.b.value, self.c.value, self.d.value = values
        finally:
            self._setting_preset = False

        self.current_preset = name
        self.generate()

    def random_preset(self, event=None):
        rng = np.random.default_rng()
        self._setting_preset = True
        try:
            self.a.value = round(rng.uniform(-2, 2), 2)
            self.b.value = round(rng.uniform(-2, 2), 2)
            self.c.value = round(rng.uniform(-2, 2), 2)
            self.d.value = round(rng.uniform(-2, 2), 2)
        finally:
            self._setting_preset = False

        self.current_preset = "Random"
        self.generate()

    def manual_parameter_changed(self, event):
        if not self._setting_preset:
            self.current_preset = "Custom"
        self.update_dynamic_panels()

    # --------------------------------------------------------
    # Generate / render
    # --------------------------------------------------------

    def generate(self, event=None):
        self.stop_animation()

        start = time.perf_counter()

        self.x, self.y = generate_clifford(
            self.a.value,
            self.b.value,
            self.c.value,
            self.d.value,
            self.points.value,
        )

        self.last_runtime = time.perf_counter() - start

        self.update_plot()
        self.update_dynamic_panels()

        self.status.object = (
            f"**{self.current_preset}** · "
            f"{self.points.value:,} particles · "
            f"{self.last_runtime:.2f}s generation"
        )

    def update_plot(self):
        frame = pd.DataFrame({"x": self.x, "y": self.y})

        points = hv.Points(frame, kdims=["x", "y"])

        plot = datashade(
            points,
            aggregator=ds.count(),
            cmap=PALETTES[self.color_theme.value],
            how="eq_hist",
        )

        plot = plot.opts(
            bgcolor=PLOT_BG,
            responsive=True,
            min_height=590,
            xlabel="",
            ylabel="",
            show_grid=False,
            show_frame=False,
            padding=.03,
            toolbar="right",
            xaxis=None,
            yaxis=None,
        )

        self.plot.object = plot

    def color_changed(self, event):
        if self.x is not None:
            self.update_plot()

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    def toggle_animation(self, event=None):
        if self.animation_callback is None:
            self.animate_button.label = "■ Stop animation"
            self.animation_frame = 0
            self.animation_callback = pn.state.add_periodic_callback(
                self.animation_step,
                period=180,
            )
        else:
            self.stop_animation()

    def stop_animation(self):
        if self.animation_callback is not None:
            self.animation_callback.stop()
            self.animation_callback = None
        self.animate_button.label = "◈ Animate"

    def animation_step(self):
        t = self.animation_frame * .035
        self.animation_frame += 1

        self._setting_preset = True
        try:
            self.a.value = np.clip(self.a.value + .018 * np.sin(t), -2, 2)
            self.b.value = np.clip(
                self.b.value + .018 * np.cos(t * 1.1), -2, 2
            )
            self.c.value = np.clip(
                self.c.value + .015 * np.sin(t * .8), -2, 2
            )
            self.d.value = np.clip(
                self.d.value + .020 * np.cos(t * .7), -2, 2
            )
        finally:
            self._setting_preset = False

        self.current_preset = "Animation"

        self.x, self.y = generate_clifford(
            self.a.value,
            self.b.value,
            self.c.value,
            self.d.value,
            self.points.value,
        )

        self.update_plot()
        self.update_dynamic_panels()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save_image(self, event=None):
        if self.x is None:
            return

        self.status.object = "Rendering high-resolution image..."

        canvas = ds.Canvas(plot_width=1800, plot_height=1200)

        frame = pd.DataFrame({"x": self.x, "y": self.y})

        aggregate = canvas.points(
            frame,
            "x",
            "y",
            agg=ds.count(),
        )

        image = tf.shade(
            aggregate,
            cmap=PALETTES[self.color_theme.value],
            how="eq_hist",
        )

        rgba = image.data.view(np.uint8).reshape(
            image.data.shape[0],
            image.data.shape[1],
            4,
        )

        output = Path.cwd() / "clifford_attractor.png"

        Image.fromarray(rgba, mode="RGBA").save(output)

        self.status.object = f"Saved → `{output}`"

    # --------------------------------------------------------
    # View
    # --------------------------------------------------------

    def view(self):

        topbar = pn.pane.HTML(
            """
            <div class="topbar">
                <div class="brand">
                    <div class="brand-mark">✦</div>
                    <div>
                        <div class="brand-name">CLIFFORD LAB</div>
                        <div class="brand-subtitle">
                            NONLINEAR SYSTEMS LABORATORY
                        </div>
                    </div>
                </div>

                <div class="system-status">
                    <span class="status-dot"></span>
                    VISUALIZATION SYSTEM ONLINE
                </div>
            </div>
            """
        )

        preset_grid = pn.GridBox(
            self.preset_buttons["Classic"],
            self.preset_buttons["Spiral"],
            self.preset_buttons["Ring"],
            self.preset_buttons["Butterfly"],
            self.preset_buttons["Chaos"],
            self.random_button,
            ncols=2,
        )

        preset_card = pn.Column(
            pn.pane.HTML(
                '<div class="card-kicker">LIBRARY</div>'
                '<div class="card-title">Preset Gallery</div>'
            ),
            preset_grid,
            css_classes=["section-card"],
            margin=0,
            sizing_mode="stretch_width",
        )

        parameter_card = pn.Column(
            pn.pane.HTML(
                '<div class="card-kicker">CONTROLS</div>'
                '<div class="card-title">Parameter Space</div>'
            ),

            pn.Column(
                self.control_label("A", f"{self.a.value:.2f}"),
                self.a,
                pn.Spacer(height=10),
                margin=0,
            ),

            pn.Column(
                self.control_label("B", f"{self.b.value:.2f}"),
                self.b,
                pn.Spacer(height=10),
                margin=0,
            ),

            pn.Column(
                self.control_label("C", f"{self.c.value:.2f}"),
                self.c,
                pn.Spacer(height=10),
                margin=0,
            ),

            pn.Column(
                self.control_label("D", f"{self.d.value:.2f}"),
                self.d,
                pn.Spacer(height=11),
                margin=0,
            ),

            pn.Column(
                self.control_label("POINT DENSITY", f"{self.points.value:,}"),
                self.points,
                pn.Spacer(height=11),
                margin=0,
            ),

            pn.pane.HTML(
                '<div class="card-kicker" style="margin-top:2px;">'
                'COLOR ATMOSPHERE'
                '</div>'
            ),

            self.color_theme,
            css_classes=["section-card"],
            margin=0,
            sizing_mode="stretch_width",
        )

        control_card = pn.Column(
            pn.pane.HTML(
                '<div class="card-kicker">ACTIONS</div>'
                '<div class="card-title">Control Deck</div>'
            ),

            pn.Row(
                self.generate_button,
                self.animate_button,
                styles={"gap": "8px"},
                margin=0,
            ),

            pn.Spacer(height=8),

            self.save_button,

            pn.Spacer(height=8),

            self.status,

            css_classes=["section-card"],
            margin=0,
            sizing_mode="stretch_width",
        )

        sidebar = pn.Column(
            preset_card,
            pn.Spacer(height=12),
            parameter_card,
            pn.Spacer(height=12),
            control_card,
            width=290,
            sizing_mode="fixed",
            margin=0,
        )

        hero = pn.Row(
            pn.Column(
                pn.pane.HTML(
                    '<div class="hero-kicker">'
                    'HOLOVIZ / DYNAMICAL SYSTEMS'
                    '</div>'
                ),
                pn.pane.HTML(
                    '<div class="hero-title">Clifford Lab</div>'
                ),
                pn.pane.HTML(
                    '<div class="hero-description">'
                    'Explore nonlinear systems, chaotic attractors '
                    'and generative geometry with millions of '
                    'interactive particles.'
                    '</div>'
                ),
                margin=0,
                sizing_mode="stretch_width",
            ),
            pn.Spacer(sizing_mode="stretch_width"),
            pn.pane.HTML(
                '<div class="hero-badge">REAL-TIME FIELD</div>'
            ),
            align="center",
            margin=0,
            sizing_mode="stretch_width",
        )

        metrics = pn.Row(
            self.metric_points,
            self.metric_generation,
            self.metric_mode,
            self.metric_parameters,
            styles={"gap": "12px"},
            margin=(0, 0, 12, 0),
            sizing_mode="stretch_width",
        )

        plot_frame = pn.Column(
            pn.pane.HTML(
                """
                <div class="visual-header">
                    <div class="visual-title">Attractor Field</div>
                    <div class="visual-meta">
                        DATASHADER / EQ-HIST / LIVE
                    </div>
                </div>
                """
            ),
            pn.Column(
                self.plot,
                css_classes=["plot-area"],
                margin=0,
                sizing_mode="stretch_width",
            ),
            css_classes=["visual-frame"],
            margin=0,
            sizing_mode="stretch_width",
        )

        info_strip = pn.Row(
            self.current_field,
            pn.pane.HTML(
                self.info_html(
                    "RENDER PIPELINE",
                    "Millions → pixels",
                    "HoloViews + Datashader aggregation",
                )
            ),
            pn.pane.HTML(
                self.info_html(
                    "ENGINE",
                    "Panel 1.10",
                    "Material UI + HoloViews + Datashader",
                )
            ),
            styles={"gap": "12px"},
            margin=(12, 0, 0, 0),
            sizing_mode="stretch_width",
        )

        main = pn.Column(
            hero,
            metrics,
            plot_frame,
            info_strip,
            pn.pane.HTML(
                '<div class="footer">'
                'Clifford attractor explorer · interactive nonlinear '
                'dynamics · rendered with HoloViz'
                '</div>'
            ),
            margin=0,
            sizing_mode="stretch_width",
        )

        return pn.Column(
            topbar,
            pn.Row(
                sidebar,
                main,
                styles={"gap": "14px"},
                align="start",
                margin=0,
                sizing_mode="stretch_width",
            ),
            css_classes=["clifford-app"],
            margin=0,
            sizing_mode="stretch_width",
        )


app = CliffordLab()

if __name__ == "__main__":
    pn.serve(
        app.view(),
        show=True,
        title="Clifford Lab",
    )
