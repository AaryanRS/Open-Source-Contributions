from pathlib import Path

import colorcet as cc
import datashader as ds
import holoviews as hv
import numpy as np
import panel as pn

from datashader import Canvas, transfer_functions as tf
from holoviews.operation.datashader import datashade
from PIL import Image as PILImage


# ============================================================
# HoloViz / Panel setup
# ============================================================

hv.extension("bokeh")

pn.extension(
    notifications=True,
    sizing_mode="stretch_width",
)

pn.config.raw_css.append("""
:root {
    --attractor-bg: #07111d;
    --attractor-card: #0d1826;
    --attractor-border: #1d2b3a;
    --attractor-text: #e8eef5;
    --attractor-muted: #91a0b2;
}

.attractor-header {
    padding: 10px 0 4px 0;
}

.attractor-subtitle {
    color: var(--attractor-muted);
    font-size: 14px;
}

.attractor-stat {
    background: var(--attractor-card);
    border: 1px solid var(--attractor-border);
    border-radius: 10px;
    padding: 12px 14px;
}
""")


# ============================================================
# Presets
# ============================================================

PRESETS = {
    "Classic": (-1.4, 1.6, 1.0, 0.7),
    "Spiral": (-1.4, 1.3, 1.0, 0.7),
    "Ring": (-1.7, 1.8, -1.9, -0.4),
    "Butterfly": (1.1, -1.32, -1.03, 1.54),
    "Chaos": (-1.9, -1.9, -1.9, -1.0),
}


# ============================================================
# Color themes
# ============================================================

COLOR_THEMES = {
    "Fire": cc.fire,
    "Ice": cc.CET_L4,
    "Viridis": cc.CET_L17,
    "Turbo": cc.CET_R4,
    "Plasma": cc.CET_L9,
    "Magma": cc.CET_L8,
    "Rainbow": cc.rainbow,
    "Cool": cc.coolwarm,
}


# ============================================================
# Clifford attractor generator
# ============================================================

def generate_clifford(a, b, c, d, n_points):
    """
    Generate a Clifford attractor.

    x[n+1] = sin(a*y[n]) + c*cos(a*x[n])
    y[n+1] = sin(b*x[n]) + d*cos(b*y[n])
    """

    n_points = int(n_points)

    x = np.empty(n_points, dtype=np.float32)
    y = np.empty(n_points, dtype=np.float32)

    x[0] = 0.0
    y[0] = 0.0

    for i in range(1, n_points):
        x_prev = x[i - 1]
        y_prev = y[i - 1]

        x[i] = (
            np.sin(a * y_prev)
            + c * np.cos(a * x_prev)
        )

        y[i] = (
            np.sin(b * x_prev)
            + d * np.cos(b * y_prev)
        )

    return x, y


# ============================================================
# Main application
# ============================================================

class CliffordExplorer:

    def __init__(self):

        self.current_parameters = PRESETS["Classic"]
        self.animation_callback = None
        self.animation_phase = 0.0
        self.animation_base = PRESETS["Classic"]

        # ----------------------------------------------------
        # Preset gallery
        # ----------------------------------------------------

        self.preset = pn.widgets.RadioBoxGroup(
            name="Preset Gallery",
            options=[
                "Classic",
                "Spiral",
                "Ring",
                "Butterfly",
                "Chaos",
                "Random",
            ],
            value="Classic",
            inline=False,
        )

        # ----------------------------------------------------
        # Color themes
        # ----------------------------------------------------

        self.color_theme = pn.widgets.Select(
            name="Color Theme",
            options=list(COLOR_THEMES.keys()),
            value="Fire",
        )

        # ----------------------------------------------------
        # Parameters
        # ----------------------------------------------------

        self.a = pn.widgets.FloatSlider(
            name="a",
            start=-2.0,
            end=2.0,
            step=0.01,
            value=-1.4,
        )

        self.b = pn.widgets.FloatSlider(
            name="b",
            start=-2.0,
            end=2.0,
            step=0.01,
            value=1.6,
        )

        self.c = pn.widgets.FloatSlider(
            name="c",
            start=-2.0,
            end=2.0,
            step=0.01,
            value=1.0,
        )

        self.d = pn.widgets.FloatSlider(
            name="d",
            start=-2.0,
            end=2.0,
            step=0.01,
            value=0.7,
        )

        self.points = pn.widgets.IntSlider(
            name="Points",
            start=50_000,
            end=1_000_000,
            step=50_000,
            value=500_000,
        )

        # ----------------------------------------------------
        # Action buttons
        # ----------------------------------------------------

        self.generate_button = pn.widgets.Button(
            name="Generate",
            button_type="primary",
            height=42,
        )

        self.animate_button = pn.widgets.Button(
            name="Animate",
            button_type="light",
            height=42,
        )

        self.save_button = pn.widgets.Button(
            name="Save Image",
            button_type="light",
            height=42,
        )

        # ----------------------------------------------------
        # Information
        # ----------------------------------------------------

        self.parameter_display = pn.pane.Markdown(
            "",
            sizing_mode="stretch_width",
        )

        self.status = pn.pane.Markdown(
            "Ready.",
            css_classes=["attractor-subtitle"],
        )

        # ----------------------------------------------------
        # Main visualization
        # ----------------------------------------------------

        self.plot = pn.pane.HoloViews(
            self.create_plot(
                *self.current_parameters
            ),
            sizing_mode="stretch_both",
            min_height=700,
            margin=0,
        )

        # ----------------------------------------------------
        # Connect events
        # ----------------------------------------------------

        self.preset.param.watch(
            self.preset_changed,
            "value",
        )

        self.generate_button.on_click(
            self.generate_clicked
        )

        self.animate_button.on_click(
            self.animate_clicked
        )

        self.save_button.on_click(
            self.save_clicked
        )

        self.color_theme.param.watch(
            self.color_changed,
            "value",
        )

        self.update_parameter_display()


    # ========================================================
    # Random parameters
    # ========================================================

    def random_parameters(self):

        return (
            np.random.uniform(-2, 2),
            np.random.uniform(-2, 2),
            np.random.uniform(-2, 2),
            np.random.uniform(-2, 2),
        )


    # ========================================================
    # Current colormap
    # ========================================================

    def current_cmap(self):

        return COLOR_THEMES[
            self.color_theme.value
        ]


    # ========================================================
    # Preset handling
    # ========================================================

    def preset_changed(self, event):

        if event.new == "Random":
            values = self.random_parameters()
        else:
            values = PRESETS[event.new]

        self.a.value = values[0]
        self.b.value = values[1]
        self.c.value = values[2]
        self.d.value = values[3]

        self.update_parameter_display()


    # ========================================================
    # Color change
    # ========================================================

    def color_changed(self, event):

        self.plot.object = self.create_plot(
            self.a.value,
            self.b.value,
            self.c.value,
            self.d.value,
        )

        self.status.object = (
            f"Color theme: **{event.new}**"
        )


    # ========================================================
    # Create attractor plot
    # ========================================================

    def create_plot(self, a, b, c, d):

        x, y = generate_clifford(
            a,
            b,
            c,
            d,
            self.points.value,
        )

        data = hv.Points(
            {
                "x": x,
                "y": y,
            },
            kdims=["x", "y"],
        )

        image = datashade(
            data,
            aggregator=ds.count(),
            cmap=self.current_cmap(),
            how="eq_hist",
        )

        return image.opts(
            bgcolor="#07111d",
            responsive=True,
            min_height=700,
            xaxis=None,
            yaxis=None,
            toolbar="above",
        )


    # ========================================================
    # Generate
    # ========================================================

    def generate_clicked(self, event):

        if self.preset.value == "Random":

            values = self.random_parameters()

            self.a.value = values[0]
            self.b.value = values[1]
            self.c.value = values[2]
            self.d.value = values[3]

        values = (
            self.a.value,
            self.b.value,
            self.c.value,
            self.d.value,
        )

        self.current_parameters = values

        self.plot.object = self.create_plot(
            *values
        )

        self.update_parameter_display()

        self.status.object = (
            f"Generated with "
            f"{self.points.value:,} points "
            f"using **{self.color_theme.value}**."
        )


    # ========================================================
    # Parameter display
    # ========================================================

    def update_parameter_display(self):

        a, b, c, d = (
            self.a.value,
            self.b.value,
            self.c.value,
            self.d.value,
        )

        self.parameter_display.object = f"""
<div class="attractor-stat">

**Current parameters**

`a = {a:.2f}`  
`b = {b:.2f}`  
`c = {c:.2f}`  
`d = {d:.2f}`

**Theme:** `{self.color_theme.value}`

</div>
"""


    # ========================================================
    # Animation
    # ========================================================

    def animate_clicked(self, event):

        if self.animation_callback is None:

            self.animation_base = (
                self.a.value,
                self.b.value,
                self.c.value,
                self.d.value,
            )

            self.animation_phase = 0.0

            self.animation_callback = (
                pn.state.add_periodic_callback(
                    self.animation_step,
                    period=180,
                )
            )

            self.animate_button.name = "Stop Animation"
            self.animate_button.button_type = "danger"

            self.status.object = (
                "Animation running..."
            )

        else:

            self.animation_callback.stop()
            self.animation_callback = None

            self.animate_button.name = "Animate"
            self.animate_button.button_type = "light"

            self.status.object = (
                "Animation stopped."
            )


    def animation_step(self):

        self.animation_phase += 0.08

        base_a, base_b, base_c, base_d = (
            self.animation_base
        )

        a = (
            base_a
            + 0.25 * np.sin(
                self.animation_phase
            )
        )

        b = (
            base_b
            + 0.25 * np.cos(
                self.animation_phase * 1.15
            )
        )

        c = (
            base_c
            + 0.25 * np.sin(
                self.animation_phase * 0.8
            )
        )

        d = (
            base_d
            + 0.25 * np.cos(
                self.animation_phase * 1.3
            )
        )

        values = (
            float(np.clip(a, -2, 2)),
            float(np.clip(b, -2, 2)),
            float(np.clip(c, -2, 2)),
            float(np.clip(d, -2, 2)),
        )

        self.a.value = values[0]
        self.b.value = values[1]
        self.c.value = values[2]
        self.d.value = values[3]

        self.current_parameters = values

        self.plot.object = self.create_plot(
            *values
        )

        self.update_parameter_display()


    # ========================================================
    # Save image
    # ========================================================

    def save_clicked(self, event):

        a, b, c, d = (
            self.current_parameters
        )

        x, y = generate_clifford(
            a,
            b,
            c,
            d,
            self.points.value,
        )

        x_min = float(np.min(x))
        x_max = float(np.max(x))
        y_min = float(np.min(y))
        y_max = float(np.max(y))

        canvas = Canvas(
            plot_width=1600,
            plot_height=1200,
            x_range=(x_min, x_max),
            y_range=(y_min, y_max),
        )

        aggregate = canvas.points(
            {
                "x": x,
                "y": y,
            },
            "x",
            "y",
            agg=ds.count(),
        )

        shaded = tf.shade(
            aggregate,
            cmap=self.current_cmap(),
            how="eq_hist",
        )

        shaded = tf.dynspread(
            shaded,
            max_px=3,
            threshold=0.5,
        )

        rgba = (
            shaded.data
            .view(np.uint8)
            .reshape(
                shaded.data.shape[0],
                shaded.data.shape[1],
                4,
            )
        )

        output_path = (
            Path(__file__).resolve().parent
            / "clifford_attractor.png"
        )

        PILImage.fromarray(
            rgba,
            "RGBA",
        ).save(
            output_path
        )

        self.status.object = (
            f"Saved `{output_path.name}` "
            f"using the **{self.color_theme.value}** theme."
        )

        pn.state.notifications.success(
            f"Saved {output_path.name}",
            duration=3000,
        )


    # ========================================================
    # Build UI
    # ========================================================

    def view(self):

        sidebar = pn.Column(

            pn.pane.Markdown(
                """
## Preset Gallery

Pick a starting shape, choose a color,
then press **Generate**.
"""
            ),

            pn.Card(
                self.preset,
                title="Attractor Presets",
                collapsed=False,
                sizing_mode="stretch_width",
            ),

            pn.Card(
                self.color_theme,
                title="Color Theme",
                collapsed=False,
                sizing_mode="stretch_width",
            ),

            pn.Card(
                self.a,
                self.b,
                self.c,
                self.d,
                title="Parameters",
                collapsed=False,
                sizing_mode="stretch_width",
            ),

            pn.Card(
                self.points,
                title="Resolution",
                collapsed=True,
                sizing_mode="stretch_width",
            ),

            pn.Row(
                self.generate_button,
                self.animate_button,
                sizing_mode="stretch_width",
            ),

            self.save_button,

            self.parameter_display,

            self.status,

            width=320,
        )


        main = pn.Column(

            pn.pane.Markdown(
                """
# Clifford Attractor Explorer

Explore how four parameters create complex mathematical structures.

Change the parameters, switch the color theme,
generate new shapes, or animate the system.
""",
                css_classes=["attractor-header"],
            ),

            self.plot,

            sizing_mode="stretch_both",
            min_height=780,
        )


        return pn.template.FastListTemplate(
            title="Clifford Attractor Explorer",
            sidebar=[sidebar],
            main=[main],
            accent_base_color="#00a6ff",
            header_background="#07111d",
            main_layout=None,
        )


# ============================================================
# Start application
# ============================================================

app = CliffordExplorer()

if __name__ == "__main__":

    pn.serve(
        app.view(),
        show=True,
        title="Clifford Attractor Explorer",
    )