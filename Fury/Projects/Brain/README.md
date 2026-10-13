# 🧠 FURY Brain Visualization

> An anatomically grounded 3D human brain visualization built with **FURY 2.x**, using real cortical surface and atlas data.

![FURY](https://img.shields.io/badge/FURY-2.x-blue)
![Python](https://img.shields.io/badge/Python-3.14-green)
![NumPy](https://img.shields.io/badge/NumPy-2.x-orange)
![Nilearn](https://img.shields.io/badge/Nilearn-0.14-purple)
![NiBabel](https://img.shields.io/badge/NiBabel-5.4-red)

---

## ✨ Current Features

- Real **fsaverage5 human cortical surface**
- **Destrieux anatomical atlas** for cortical regions
- **600 cortex-aware visualization nodes** by default
- Nodes rendered as **FURY point primitives**, not spheres
- Restrained **scientific blue / cyan / teal** color palette
- Dark scientific background
- Nodes distributed across actual cortical geometry
- Slow continuous brain rotation
- Mouse rotation and zoom
- PNG snapshot output
- Built-in smoke test

> **Note:** The 600 nodes are visualization nodes sampled from the cortical surface. They are not individual biological neurons.

---

## 🧩 Technology Stack

| Library | Purpose |
|---|---|
| **FURY** | 3D rendering, scene, points, camera, animation, interaction |
| **NumPy** | Coordinates, arrays, node sampling and calculations |
| **Nilearn** | fsaverage5 brain surface and Destrieux atlas data |
| **NiBabel** | Reads GIFTI cortical surface files |
| **OpenCV** | Reserved for later MP4 export |

---

## ⚙️ Environment

Tested project environment:

```text
Windows 11
Python 3.14.7
FURY 2.1.0.dev30+g349e75924.d20261010
NumPy 2.5.2
Nilearn 0.14.1
NiBabel 5.4.2
OpenCV 5.0.0
GPU: NVIDIA RTX 5060
```

---

## 📦 Installation

FURY is already expected to be installed from the development checkout. Install the supporting packages with:

```powershell
python -m pip install -U nilearn nibabel opencv-python
```

Check the environment:

```powershell
python -m pip check
```

Expected result:

```text
No broken requirements found.
```

Verify imports:

```powershell
python -c "import fury, numpy, nilearn, nibabel, cv2; print('FURY:', fury.__version__); print('NumPy:', numpy.__version__); print('Nilearn:', nilearn.__version__); print('NiBabel:', nibabel.__version__); print('OpenCV:', cv2.__version__)"
```

---

## ▶️ Run

### Smoke test

Runs a smaller scene and renders one PNG frame:

```powershell
python Brain_Visualization.py --smoke-test
```

### Full visualization

Run the default 600-node visualization:

```powershell
python Brain_Visualization.py --nodes 600
```

### Save a PNG

```powershell
python Brain_Visualization.py --nodes 600 --snapshot
```

Output:

```text
brain_output/brain_scientific_points.png
```

### Change the node count

```powershell
python Brain_Visualization.py --nodes 300
```

or:

```powershell
python Brain_Visualization.py --nodes 1000
```

The allowed range in the current script is **100–2000**.

---

## 🖱️ Controls

| Action | Control |
|---|---|
| Rotate | Mouse drag |
| Zoom | Mouse wheel |
| Exit | Close window |
| Automatic rotation | Enabled by default |

---

## 🧠 Data Pipeline

```text
Nilearn
   ↓
fsaverage5 cortical surface + Destrieux atlas
   ↓
NiBabel
   ↓
GIFTI vertices / triangle data
   ↓
NumPy
   ↓
600 cortex-aware node positions
   ↓
FURY
   ↓
Interactive 3D visualization
```

The current implementation uses the standardized **fsaverage5** cortical template. It is anatomically grounded, but it is **not an individual patient's MRI**.

---

## 📁 Output

Generated files are stored in:

```text
brain_output/
```

Typical output:

```text
brain_output/
└── brain_scientific_points.png
```

---

## 🔧 Main Parameters

The most useful settings are near the top of `Brain_Visualization.py`:

```python
DEFAULT_NODE_COUNT = 600
POINT_SIZE = 4.0
POINT_OPACITY = 0.96
SURFACE_OPACITY = 0.10
ROTATION_DEGREES = 0.14
```

These control:

- `DEFAULT_NODE_COUNT` → number of cortical points
- `POINT_SIZE` → visual point size
- `POINT_OPACITY` → point transparency
- `SURFACE_OPACITY` → anatomical surface visibility
- `ROTATION_DEGREES` → automatic rotation speed

---

## 🚧 Roadmap

Planned next stages:

```text
✅ Anatomical cortical surface
✅ Anatomical region mapping
✅ 600 cortex-aware point nodes
⬜ Brain-like neural connections
⬜ Long-range connections
⬜ Animated neural activity
⬜ Click-to-select brain regions
⬜ Highlight selected region and connections
⬜ MP4 animation export
⬜ Final visual polish
```

---

## 📌 Scientific Note

The current node positions are **synthetic visualization data** sampled from anatomical cortical geometry. They should not be interpreted as measured neuronal locations or real functional/anatomical connectivity.

Real connectome or neuroimaging data can be integrated in a later version.

---

## 🛠️ Troubleshooting

### FURY import error

Make sure the FURY development environment is active and verify:

```powershell
python -c "import fury; print(fury.__version__)"
```

### Dataset download problem

Nilearn downloads the required fsaverage5 and atlas files automatically on first use. Check your internet connection and run the script again.

### Broken Python dependencies

Run:

```powershell
python -m pip check
```

### Slow rendering

Try fewer nodes:

```powershell
python Brain_Visualization.py --nodes 300
```

---

## 📄 Project Status

**Current stage:** Anatomical brain + scientific point-node visualization.

The next implementation stage is the neural connectivity layer, which will build on the existing 600 cortex-aware node positions.

---

## 📝 Changelog

### v0.1 — Scientific Cortex + Point Nodes

- Added fsaverage5 cortical surface
- Added Destrieux atlas integration
- Added 600 cortex-aware nodes
- Switched from spheres to true point primitives
- Added scientific color palette
- Added automatic rotation
- Added PNG snapshot
- Added smoke test
