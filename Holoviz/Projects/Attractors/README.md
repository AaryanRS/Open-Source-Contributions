# ✨ Clifford Attractor Explorer

An interactive visualization of **Clifford attractors** built with the HoloViz ecosystem.

Explore how small changes to four mathematical parameters can produce completely different chaotic patterns — from spirals and rings to butterfly-like structures.

<img width="1342" height="1216" alt="Screenshot 2026-10-22 202020" src="https://github.com/user-attachments/assets/6716e4aa-9bd3-4b1a-b958-b28f06f4245b" />


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

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/30fd8c7b-ebf5-4748-86f6-7a0c8d998f9d" width="100%"></td>
    <td><img src="https://github.com/user-attachments/assets/06e5acee-3c41-452c-9423-669be510a5a3" width="100%"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/af768b4b-5708-4dfb-ae52-cfdd85a545b0" width="100%"></td>
    <td><img src="https://github.com/user-attachments/assets/54ea8a46-3a70-4fa7-877b-40e64ad8fa3e" width="100%"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/14dc0261-fa99-4f05-ab8e-5f9deac37a6f" width="100%"></td>
    <td></td>
  </tr>
</table>
---

## 🌌 A Small Mathematical System. Endless Patterns.

Experiment with the parameters, change the colors, and see what emerges.

**Sometimes the most interesting visualizations come from the simplest equations.**
