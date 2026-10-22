# ✨ Clifford Attractor Explorer

An interactive visualization of **Clifford attractors** built with the HoloViz ecosystem.

Explore how small changes to four mathematical parameters can produce completely different chaotic patterns — from spirals and rings to butterfly-like structures.

![Clifford Attractor Explorer](images/hero.png)

---

## 🎨 What is a Clifford Attractor?

A Clifford attractor is a mathematical system that generates complex patterns from a simple iterative equation:

```text
xₙ₊₁ = sin(a·yₙ) + c·cos(a·xₙ)

yₙ₊₁ = sin(b·xₙ) + d·cos(b·yₙ)
```

By changing `a`, `b`, `c`, and `d`, the resulting shape can change dramatically.

That's what makes these systems fun to explore — **simple rules, surprisingly complex results.**

---

## 🚀 Features

- 🎛️ Interactive `a`, `b`, `c`, `d` parameter controls
- 🖼️ Preset gallery
  - Classic
  - Spiral
  - Ring
  - Butterfly
  - Chaos
- 🌈 Multiple color themes
- ✨ Datashader-powered rendering
- 🔄 Live parameter animation
- 💾 Save generated attractors as images
- ⚡ Supports large point counts for detailed patterns

![Presets](images/presets.png)

---

## 🧩 Built With

- **Python**
- **Panel** — interactive application UI
- **HoloViews** — visualization composition
- **Datashader** — rendering large point datasets
- **Colorcet** — scientific and perceptually designed color palettes
- **NumPy** — numerical computation
- **Pillow** — image export

---

## 🧠 Why I Built This

This project started as a way to explore **mathematical visualization and chaotic systems** while experimenting with the HoloViz ecosystem.

There isn't a specific real-world dataset behind it. Instead, the visualization generates the data itself and lets you interactively explore how mathematical parameters affect the resulting structure.

It's also a fun example of how **HoloViews + Datashader + Panel** can be combined to build interactive visual experiences from mathematical systems.

![Animation](images/animation.gif)

---

## ▶️ Run Locally

Clone the repository:

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

Install the dependencies:

```bash
pip install numpy panel holoviews datashader colorcet pillow
```

Run the application:

```bash
python clifford_attractor.py
```

The Panel application will open in your browser.

---

## 📸 Gallery

Add your favorite generated patterns here:

![Classic](images/classic.png)

![Spiral](images/spiral.png)

![Butterfly](images/butterfly.png)

---

## 🌌 A Small Mathematical System. Endless Patterns.

Experiment with the parameters, change the colors, and see what emerges.

**Sometimes the most interesting visualizations come from the simplest equations.**
